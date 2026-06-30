"""Generate mock clickstream events → raw_clickstream_events."""
import argparse
import json
import os
import random
import sys
import uuid
from datetime import datetime, timedelta, timezone

import pandas as pd
from faker import Faker

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from utils.db import get_engine

fake = Faker()

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

EVENTS = [
    ("page_view",    0.40),
    ("scroll",       0.25),
    ("click",        0.18),
    ("form_submit",  0.05),
    ("download",     0.04),
    ("video_play",   0.04),
    ("add_to_cart",  0.03),
    ("purchase",     0.01),
]

EVENT_NAMES  = [e[0] for e in EVENTS]
EVENT_WEIGHTS = [e[1] for e in EVENTS]
DEVICES = ["desktop", "mobile", "tablet"]


def _make_events_for_session(session_id: str, user_id: str, start_ts: datetime, n: int) -> list[dict]:
    page = random.choice(PAGES)
    device = random.choice(DEVICES)
    rows = []
    ts = start_ts
    for _ in range(n):
        name = random.choices(EVENT_NAMES, weights=EVENT_WEIGHTS, k=1)[0]
        rows.append({
            "event_time":        ts,
            "session_id":        session_id,
            "user_pseudo_id":    user_id,
            "event_name":        name,
            "page_url":          page,
            "element_id":        f"#{fake.slug()}" if name == "click" else None,
            "element_class":     f".{fake.slug()}" if name == "click" else None,
            "element_text":      fake.words(nb=3, as_list=False) if name == "click" else None,
            "scroll_depth_pct":  random.randint(10, 100) if name == "scroll" else None,
            "event_value":       round(random.uniform(5, 300), 2) if name in ("purchase", "add_to_cart") else None,
            "event_params":      json.dumps({"label": fake.slug()}) if random.random() < 0.2 else None,
            "device_category":   device,
        })
        ts += timedelta(seconds=random.randint(2, 60))
    return rows


def generate(days: int = 90, sessions_per_day: int = 200) -> pd.DataFrame:
    rows = []
    end = datetime.now(tz=timezone.utc)
    start = end - timedelta(days=days)

    for day_offset in range(days):
        day_start = start + timedelta(days=day_offset)
        count = max(1, int(random.gauss(sessions_per_day, sessions_per_day * 0.15)))
        for _ in range(count):
            session_ts = day_start + timedelta(seconds=random.randint(0, 86399))
            n_events = random.randint(1, 15)
            rows.extend(
                _make_events_for_session(
                    str(uuid.uuid4())[:16],
                    str(uuid.uuid4())[:16],
                    session_ts,
                    n_events,
                )
            )
    return pd.DataFrame(rows)


def load(df: pd.DataFrame, mode: str = "full") -> None:
    engine = get_engine()
    with engine.begin() as conn:
        if mode == "full":
            conn.execute(__import__("sqlalchemy").text("TRUNCATE raw_clickstream_events RESTART IDENTITY"))
    df.to_sql("raw_clickstream_events", engine, if_exists="append", index=False, method="multi", chunksize=500)
    print(f"Loaded {len(df):,} rows into raw_clickstream_events ({mode} mode).")


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
