"""Generate mock GA4 session rows and load into raw_ga4_sessions."""
import argparse
import os
import random
import sys
import uuid
from datetime import date, timedelta

import pandas as pd
from faker import Faker

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from utils.db import get_engine

fake = Faker()

CHANNELS = [
    ("Organic Search",  "google",      "organic"),
    ("Organic Search",  "bing",        "organic"),
    ("Paid Search",     "google",      "cpc"),
    ("Direct",          "(direct)",    "(none)"),
    ("Referral",        "reddit.com",  "referral"),
    ("Social",          "twitter.com", "social"),
    ("Email",           "newsletter",  "email"),
]

DEVICES = ["desktop", "mobile", "tablet"]
COUNTRIES = ["United States", "United Kingdom", "Canada", "Germany", "Australia", "India"]
BROWSERS = ["Chrome", "Safari", "Firefox", "Edge"]
OS_LIST  = ["Windows", "macOS", "iOS", "Android", "Linux"]

PAGES = [
    "https://example.com/",
    "https://example.com/blog/",
    "https://example.com/pricing/",
    "https://example.com/about/",
    "https://example.com/contact/",
    "https://example.com/blog/post-1/",
    "https://example.com/blog/post-2/",
    "https://example.com/products/",
]


def _make_row(d: date) -> dict:
    channel, source, medium = random.choice(CHANNELS)
    pv = random.randint(1, 12)
    duration = 0 if random.random() < 0.35 else random.gauss(180, 90)
    bounced = pv == 1 and duration < 10
    converted = random.random() < 0.03
    return {
        "session_date":       d,
        "session_id":         str(uuid.uuid4())[:16],
        "user_pseudo_id":     str(uuid.uuid4())[:16],
        "user_id":            None,
        "country":            random.choice(COUNTRIES),
        "city":               fake.city(),
        "device_category":    random.choice(DEVICES),
        "operating_system":   random.choice(OS_LIST),
        "browser":            random.choice(BROWSERS),
        "channel_grouping":   channel,
        "source":             source,
        "medium":             medium,
        "campaign":           "(not set)" if medium not in ("cpc", "email") else fake.slug(),
        "landing_page":       random.choice(PAGES),
        "sessions":           1,
        "new_users":          int(random.random() < 0.55),
        "pageviews":          pv,
        "bounce":             bounced,
        "session_duration_s": max(0.0, round(duration, 2)),
        "conversions":        int(converted),
        "revenue":            round(random.uniform(10, 250), 2) if converted else 0.0,
    }


def generate(days: int = 90, sessions_per_day: int = 200) -> pd.DataFrame:
    rows = []
    end = date.today()
    start = end - timedelta(days=days - 1)
    for n in range(days):
        d = start + timedelta(days=n)
        count = max(1, int(random.gauss(sessions_per_day, sessions_per_day * 0.15)))
        for _ in range(count):
            rows.append(_make_row(d))
    return pd.DataFrame(rows)


def load(df: pd.DataFrame, mode: str = "full") -> None:
    engine = get_engine()
    with engine.begin() as conn:
        if mode == "full":
            conn.execute(__import__("sqlalchemy").text("TRUNCATE raw_ga4_sessions RESTART IDENTITY"))
    df.to_sql("raw_ga4_sessions", engine, if_exists="append", index=False, method="multi", chunksize=500)
    print(f"Loaded {len(df):,} rows into raw_ga4_sessions ({mode} mode).")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["full", "incremental"], default="full")
    parser.add_argument("--days", type=int, default=90)
    parser.add_argument("--sessions-per-day", type=int, default=200)
    args = parser.parse_args()
    df = generate(days=args.days, sessions_per_day=args.sessions_per_day)
    load(df, mode=args.mode)


if __name__ == "__main__":
    main()
