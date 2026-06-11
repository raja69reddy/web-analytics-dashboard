"""
Ingest raw_clickstream_events → fct_events + dim_pages + dim_dates.

Usage:
    python ingestion/clickstream.py --mode full
    python ingestion/clickstream.py --mode incremental --since 2024-01-01
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
        for url in set(u for u in urls if u):
            parts = parse_url_parts(url)
            conn.execute(
                text("""
                    INSERT INTO dim_pages (url, url_path, url_domain, page_section, first_seen, last_seen)
                    VALUES (:url, :url_path, :url_domain, :page_section, CURRENT_DATE, CURRENT_DATE)
                    ON CONFLICT (url) DO UPDATE SET last_seen = CURRENT_DATE
                """),
                {"url": url, **parts},
            )


def _load_fct_events(df, mode: str) -> None:
    engine = get_engine()

    page_map = query_df("SELECT url, page_id FROM dim_pages")
    df = df.merge(page_map, left_on="page_url", right_on="url", how="left")

    df["date_id"] = df["event_time"].apply(
        lambda t: date_to_id(t.date()) if hasattr(t, "date") else None
    )

    cols = [
        "event_time", "date_id", "session_id", "user_pseudo_id",
        "page_id", "event_name", "scroll_depth_pct", "event_value", "device_category",
    ]
    df_out = df[cols].copy()

    with engine.begin() as conn:
        if mode == "full":
            conn.execute(text("TRUNCATE fct_events RESTART IDENTITY"))

    df_out.to_sql("fct_events", engine, if_exists="append", index=False, method="multi", chunksize=500)
    print(f"  Loaded {len(df_out):,} rows into fct_events.")


def run(mode: str, since: date | None = None) -> None:
    where = "" if mode == "full" else f"WHERE event_time >= '{since}'"
    df = query_df(f"SELECT * FROM raw_clickstream_events {where}")
    if df.empty:
        print("Nothing to ingest.")
        return

    df["_date"] = df["event_time"].apply(lambda t: t.date() if hasattr(t, "date") else t)
    populate_dim_dates(df["_date"].min(), df["_date"].max())
    _upsert_pages(df["page_url"].dropna().tolist())
    _load_fct_events(df, mode)
    print("Clickstream ingestion complete.")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["full", "incremental"], default="full")
    parser.add_argument("--since", default=None, help="YYYY-MM-DD (incremental only)")
    args = parser.parse_args()
    since = date.fromisoformat(args.since) if args.since else None
    run(args.mode, since)


if __name__ == "__main__":
    main()
