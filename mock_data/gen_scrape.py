"""Generate mock scraped page metadata → raw_scrape_pages."""
import argparse
import os
import random
import sys
from datetime import datetime, timezone

import pandas as pd
from faker import Faker

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from utils.db import get_engine

fake = Faker()

PAGES = [
    ("https://example.com/",              "Home"),
    ("https://example.com/blog/",         "Blog Index"),
    ("https://example.com/pricing/",      "Pricing"),
    ("https://example.com/about/",        "About Us"),
    ("https://example.com/contact/",      "Contact"),
    ("https://example.com/blog/post-1/",  "How to Get Started"),
    ("https://example.com/blog/post-2/",  "10 Tips for Growth"),
    ("https://example.com/products/",     "Products"),
]


def _make_row(url: str, title: str) -> dict:
    word_count = random.randint(200, 3500) if "blog" in url else random.randint(50, 600)
    return {
        "scraped_at":       datetime.now(tz=timezone.utc),
        "url":              url,
        "canonical_url":    url,
        "title":            title,
        "meta_description": fake.sentence(nb_words=20)[:160],
        "h1":               title,
        "word_count":       word_count,
        "internal_links":   random.randint(2, 20),
        "external_links":   random.randint(0, 8),
        "images_count":     random.randint(0, 12),
        "has_schema_org":   random.random() < 0.4,
        "page_size_kb":     round(random.uniform(20, 500), 2),
        "load_time_ms":     random.randint(150, 4000),
        "http_status":      200,
    }


def generate() -> pd.DataFrame:
    return pd.DataFrame([_make_row(url, title) for url, title in PAGES])


def load(df: pd.DataFrame, mode: str = "full") -> None:
    engine = get_engine()
    with engine.begin() as conn:
        if mode == "full":
            conn.execute(__import__("sqlalchemy").text("TRUNCATE raw_scrape_pages RESTART IDENTITY"))
    df.to_sql("raw_scrape_pages", engine, if_exists="append", index=False, method="multi", chunksize=500)
    print(f"Loaded {len(df):,} rows into raw_scrape_pages ({mode} mode).")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["full", "incremental"], default="full")
    args = parser.parse_args()
    df = generate()
    load(df, mode=args.mode)


if __name__ == "__main__":
    main()
