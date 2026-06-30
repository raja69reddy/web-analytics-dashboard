"""
Ingest raw_scrape_pages → dim_pages (word_count + title enrichment).

Usage:
    python ingestion/scraper.py --mode full
    python ingestion/scraper.py --mode incremental --since 2024-01-01
"""
import argparse
import os
import sys
from datetime import date

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from sqlalchemy import text

from utils.db import get_engine, query_df
from utils.helpers import parse_url_parts


def run(mode: str, since: date | None = None) -> None:
    where = "" if mode == "full" else f"WHERE scraped_at >= '{since}'"
    # latest scrape per URL
    sql = f"""
        SELECT DISTINCT ON (url)
            url, title, word_count, scraped_at
        FROM raw_scrape_pages
        {where}
        ORDER BY url, scraped_at DESC
    """
    df = query_df(sql)
    if df.empty:
        print("Nothing to ingest.")
        return

    engine = get_engine()
    with engine.begin() as conn:
        for row in df.itertuples(index=False):
            parts = parse_url_parts(row.url)
            conn.execute(
                text("""
                    INSERT INTO dim_pages
                        (url, url_path, url_domain, page_section, page_title, word_count, first_seen, last_seen)
                    VALUES
                        (:url, :url_path, :url_domain, :page_section, :title, :word_count, CURRENT_DATE, CURRENT_DATE)
                    ON CONFLICT (url) DO UPDATE SET
                        page_title  = EXCLUDED.page_title,
                        word_count  = EXCLUDED.word_count,
                        last_seen   = CURRENT_DATE,
                        updated_at  = NOW()
                """),
                {
                    "url":        row.url,
                    "title":      row.title,
                    "word_count": row.word_count,
                    **parts,
                },
            )
    print(f"Scraper ingestion complete ({len(df):,} pages upserted into dim_pages).")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["full", "incremental"], default="full")
    parser.add_argument("--since", default=None)
    args = parser.parse_args()
    since = date.fromisoformat(args.since) if args.since else None
    run(args.mode, since)


if __name__ == "__main__":
    main()
