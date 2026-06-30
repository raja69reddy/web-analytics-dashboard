"""
Ingest raw_ga4_sessions → fct_sessions + dim_pages + dim_dates.

Usage:
    python ingestion/ga4.py --mode full
    python ingestion/ga4.py --mode incremental --since 2024-01-01
"""
import argparse
import os
import sys
from datetime import date

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from sqlalchemy import text

from utils.db import get_engine, query_df
from utils.helpers import date_to_id, parse_url_parts, populate_dim_dates


def _upsert_pages(urls: list[str]) -> None:
    engine = get_engine()
    with engine.begin() as conn:
        for url in set(urls):
            parts = parse_url_parts(url)
            conn.execute(
                text("""
                    INSERT INTO dim_pages (url, url_path, url_domain, page_section, first_seen, last_seen)
                    VALUES (:url, :url_path, :url_domain, :page_section, CURRENT_DATE, CURRENT_DATE)
                    ON CONFLICT (url) DO UPDATE SET last_seen = CURRENT_DATE
                """),
                {"url": url, **parts},
            )


def _load_fct_sessions(df, mode: str) -> None:
    import pandas as pd
    engine = get_engine()

    # resolve page_ids
    page_map = query_df("SELECT url, page_id FROM dim_pages")
    df = df.merge(page_map, left_on="landing_page", right_on="url", how="left")

    df["date_id"]    = df["session_date"].apply(lambda d: date_to_id(d) if hasattr(d, "year") else None)
    df["is_new_user"] = df["new_users"].astype(bool)
    df["bounced"]    = df["bounce"].astype(bool)

    cols = [
        "session_id", "user_pseudo_id", "date_id", "page_id",
        "channel_grouping", "source", "medium", "campaign",
        "country", "device_category", "is_new_user",
        "pageviews", "session_duration_s", "bounced", "conversions", "revenue",
    ]
    df_out = df[cols].copy()

    with engine.begin() as conn:
        if mode == "full":
            conn.execute(text("TRUNCATE fct_sessions RESTART IDENTITY"))

    df_out.to_sql("fct_sessions", engine, if_exists="append", index=False, method="multi", chunksize=500)
    print(f"  Loaded {len(df_out):,} rows into fct_sessions.")


def run(mode: str, since: date | None = None) -> None:
    where = "" if mode == "full" else f"WHERE session_date >= '{since}'"
    df = query_df(f"SELECT * FROM raw_ga4_sessions {where}")
    if df.empty:
        print("Nothing to ingest.")
        return

    dates = df["session_date"].unique()
    populate_dim_dates(min(dates), max(dates))
    _upsert_pages(df["landing_page"].dropna().tolist())
    _load_fct_sessions(df, mode)
    print("GA4 ingestion complete.")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["full", "incremental"], default="full")
    parser.add_argument("--since", default=None, help="YYYY-MM-DD (incremental only)")
    args = parser.parse_args()
    since = date.fromisoformat(args.since) if args.since else None
    run(args.mode, since)


if __name__ == "__main__":
    main()
