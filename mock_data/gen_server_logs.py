"""Generate mock web server log entries — CSV export or direct DB load."""
import argparse
import os
import random
import sys
import uuid
from datetime import datetime, timedelta, timezone

import pandas as pd
from faker import Faker

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from utils.db import get_engine

CSV_OUT = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "data", "raw", "server_logs.csv"))

CSV_URLS = ["/home", "/about", "/products", "/contact", "/blog"]
CSV_STATUS_WEIGHTS = [200] * 80 + [301] * 5 + [404] * 12 + [500] * 3


def generate_csv(n: int = 2000, days: int = 90) -> pd.DataFrame:
    """Generate n simplified server log rows for CSV export."""
    end = datetime.now(tz=timezone.utc)
    start = end - timedelta(days=days)
    rows = []
    for _ in range(n):
        ts = start + timedelta(seconds=random.randint(0, days * 86400))
        status = random.choice(CSV_STATUS_WEIGHTS)
        rows.append({
            "log_timestamp":  ts.strftime("%Y-%m-%d %H:%M:%S"),
            "ip_address":     fake.ipv4_public(),
            "request_method": random.choices(["GET", "POST"], weights=[85, 15])[0],
            "url":            random.choice(CSV_URLS),
            "status_code":    status,
            "response_size":  random.randint(512, 80000) if status == 200 else random.randint(100, 2000),
            "user_agent":     fake.user_agent(),
        })
    return pd.DataFrame(rows).sort_values("log_timestamp").reset_index(drop=True)

fake = Faker()

PATHS = [
    "/", "/blog/", "/pricing/", "/about/", "/contact/",
    "/blog/post-1/", "/blog/post-2/", "/products/",
    "/static/css/main.css", "/static/js/app.js", "/favicon.ico",
    "/wp-login.php",           # common bot probe
    "/admin/", "/.env",        # security probes
]

METHODS  = ["GET"] * 90 + ["POST"] * 8 + ["HEAD"] * 2
STATUS_WEIGHTS = [200] * 70 + [301] * 5 + [304] * 8 + [404] * 10 + [500] * 3 + [403] * 4


def _make_row(ts: datetime) -> dict:
    path = random.choice(PATHS)
    status = random.choice(STATUS_WEIGHTS)
    method = "GET" if path.startswith("/static") else random.choice(METHODS)
    return {
        "log_time":        ts,
        "ip_address":      fake.ipv4_public(),
        "method":          method,
        "url":             f"https://example.com{path}",
        "query_string":    f"?ref={fake.slug()}" if random.random() < 0.1 else None,
        "status_code":     status,
        "response_bytes":  random.randint(512, 80_000) if status == 200 else random.randint(100, 2000),
        "referrer":        fake.url() if random.random() < 0.3 else None,
        "user_agent":      fake.user_agent(),
        "response_time_ms": random.randint(20, 3000),
    }


def generate(days: int = 90, requests_per_hour: int = 150) -> pd.DataFrame:
    rows = []
    end = datetime.now(tz=timezone.utc)
    start = end - timedelta(days=days)
    ts = start
    while ts < end:
        hour_count = max(1, int(random.gauss(requests_per_hour, requests_per_hour * 0.3)))
        for _ in range(hour_count):
            jitter = timedelta(seconds=random.randint(0, 3599))
            rows.append(_make_row(ts + jitter))
        ts += timedelta(hours=1)
    return pd.DataFrame(rows)


def load(df: pd.DataFrame, mode: str = "full") -> None:
    engine = get_engine()
    with engine.begin() as conn:
        if mode == "full":
            conn.execute(__import__("sqlalchemy").text("TRUNCATE raw_server_logs RESTART IDENTITY"))
    df.to_sql("raw_server_logs", engine, if_exists="append", index=False, method="multi", chunksize=500)
    print(f"Loaded {len(df):,} rows into raw_server_logs ({mode} mode).")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["csv", "full", "incremental"], default="csv")
    parser.add_argument("--days", type=int, default=90)
    parser.add_argument("--rows", type=int, default=2000)
    parser.add_argument("--requests-per-hour", type=int, default=150)
    args = parser.parse_args()

    if args.mode == "csv":
        df = generate_csv(n=args.rows, days=args.days)
        os.makedirs(os.path.dirname(CSV_OUT), exist_ok=True)
        df.to_csv(CSV_OUT, index=False)
        print(f"Generated {len(df)} rows saved to data/raw/server_logs.csv")
    else:
        df = generate(days=args.days, requests_per_hour=args.requests_per_hour)
        load(df, mode=args.mode)


if __name__ == "__main__":
    main()
