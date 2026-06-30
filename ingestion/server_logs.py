"""
Ingest raw_server_logs → dim_pages + dim_dates (no separate fact table; logs
are queried directly from the raw layer for monitoring KPIs).

Usage:
    python ingestion/server_logs.py --mode full
    python ingestion/server_logs.py --mode incremental --since 2024-01-01
"""
import argparse
import os
import sys
from datetime import date

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from utils.db import query_df
from utils.helpers import parse_url_parts, populate_dim_dates


def _upsert_pages(urls: list[str]) -> None:
    from sqlalchemy import text
    from utils.db import get_engine

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


def run(mode: str, since: date | None = None) -> None:
    where = "" if mode == "full" else f"WHERE log_time >= '{since}'"
    df = query_df(f"SELECT log_time, url FROM raw_server_logs {where} AND status_code < 400")
    if df.empty:
        print("Nothing to ingest.")
        return

    df["_date"] = df["log_time"].apply(lambda t: t.date() if hasattr(t, "date") else t)
    populate_dim_dates(df["_date"].min(), df["_date"].max())
    _upsert_pages(df["url"].dropna().tolist())
    print(f"Server logs ingestion complete ({len(df):,} rows processed).")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["full", "incremental"], default="full")
    parser.add_argument("--since", default=None)
    args = parser.parse_args()
    since = date.fromisoformat(args.since) if args.since else None
    run(args.mode, since)


if __name__ == "__main__":
    main()
