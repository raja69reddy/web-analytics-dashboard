"""Shared helpers used across ingestion scripts."""
import os
import re
from datetime import date, timedelta
from urllib.parse import urlparse


def date_to_id(d: date) -> int:
    return int(d.strftime("%Y%m%d"))


def populate_dim_dates(start: date, end: date) -> None:
    """Insert missing rows into dim_dates for [start, end]."""
    import pandas as pd
    from utils.db import get_engine

    dates = pd.date_range(start, end, freq="D")
    rows = []
    for d in dates:
        rows.append({
            "date_id":        int(d.strftime("%Y%m%d")),
            "full_date":      d.date(),
            "year":           d.year,
            "quarter":        d.quarter,
            "month":          d.month,
            "month_name":     d.strftime("%B"),
            "week":           int(d.strftime("%V")),
            "day_of_week":    d.isoweekday(),
            "day_name":       d.strftime("%A"),
            "is_weekend":     d.isoweekday() >= 6,
            "is_month_start": d.day == 1,
            "is_month_end":   (d + timedelta(days=1)).month != d.month,
        })
    df = pd.DataFrame(rows)
    engine = get_engine()
    # upsert — skip existing
    from sqlalchemy import text
    with engine.begin() as conn:
        for row in df.itertuples(index=False):
            conn.execute(
                text("""
                    INSERT INTO dim_dates
                        (date_id, full_date, year, quarter, month, month_name,
                         week, day_of_week, day_name, is_weekend, is_month_start, is_month_end)
                    VALUES
                        (:date_id, :full_date, :year, :quarter, :month, :month_name,
                         :week, :day_of_week, :day_name, :is_weekend, :is_month_start, :is_month_end)
                    ON CONFLICT (date_id) DO NOTHING
                """),
                row._asdict(),
            )


def parse_url_parts(url: str) -> dict:
    parsed = urlparse(url)
    path = parsed.path or "/"
    section = path.strip("/").split("/")[0] if path.strip("/") else "home"
    return {"url_path": path, "url_domain": parsed.netloc, "page_section": section}


def clean_url(url: str) -> str:
    """Normalise a URL: strip trailing slash, lowercase scheme+host."""
    url = url.strip()
    parsed = urlparse(url)
    clean = parsed._replace(scheme=parsed.scheme.lower(), netloc=parsed.netloc.lower())
    return clean.geturl().rstrip("/")
