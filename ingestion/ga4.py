"""
GA4 CSV ingestion pipeline: data/raw/ga4_sessions.csv -> raw_ga4_sessions

Usage:
    python ingestion/ga4.py --mode full
    python ingestion/ga4.py --mode incremental
"""
import argparse
import os
import sys
from pathlib import Path

import pandas as pd
from sqlalchemy import text

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from utils.db import get_engine

CSV_PATH = Path(__file__).resolve().parent.parent / "data" / "raw" / "ga4_sessions.csv"
TABLE = "raw_ga4_sessions"


def load_csv() -> pd.DataFrame:
    df = pd.read_csv(CSV_PATH)

    # Strip whitespace from string columns
    for col in df.select_dtypes(include="object").columns:
        df[col] = df[col].str.strip()

    # Convert session_date to proper DATE
    df["session_date"] = pd.to_datetime(df["session_date"]).dt.date

    # Fill nulls with 0 for numeric columns
    num_cols = df.select_dtypes(include="number").columns
    df[num_cols] = df[num_cols].fillna(0)

    # Map CSV columns to DB column names
    df = df.rename(columns={
        "channel": "channel_grouping",
        "avg_session_duration": "session_duration_s",
    })

    # Derive boolean bounce from bounce_rate float
    df["bounce"] = df["bounce_rate"] > 0.5

    # Drop columns with no matching DB column
    df = df.drop(columns=["bounce_rate", "users"], errors="ignore")

    return df


def _existing_dates(engine) -> set:
    with engine.connect() as conn:
        rows = conn.execute(text(f"SELECT DISTINCT session_date FROM {TABLE}"))
        return {r[0] for r in rows}


def ingest(mode: str) -> int:
    engine = get_engine()
    df = load_csv()

    if mode == "incremental":
        existing = _existing_dates(engine)
        df = df[~df["session_date"].isin(existing)]
        if df.empty:
            print("No new dates to insert.")
            return 0

    with engine.begin() as conn:
        if mode == "full":
            conn.execute(text(f"TRUNCATE {TABLE} RESTART IDENTITY"))

    df.to_sql(TABLE, engine, if_exists="append", index=False, method="multi", chunksize=500)

    count = len(df)
    print(f"Inserted {count} rows into {TABLE}")
    return count


def main():
    parser = argparse.ArgumentParser(description="Ingest GA4 CSV into raw_ga4_sessions")
    parser.add_argument("--mode", choices=["full", "incremental"], default="full",
                        help="full: truncate and reload; incremental: only insert new dates")
    args = parser.parse_args()
    ingest(args.mode)


if __name__ == "__main__":
    main()
