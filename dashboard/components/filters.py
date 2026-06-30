"""Sidebar filters — call render_filters() once per page to get the WHERE clause dict."""
from datetime import date, timedelta

import streamlit as st


def render_filters(include_channel: bool = True, include_page: bool = True) -> dict:
    st.sidebar.header("Filters")

    # Date range
    default_end   = date.today()
    default_start = default_end - timedelta(days=89)
    date_range = st.sidebar.date_input(
        "Date range",
        value=(default_start, default_end),
        min_value=date(2020, 1, 1),
        max_value=default_end,
    )
    if isinstance(date_range, (list, tuple)) and len(date_range) == 2:
        start_date, end_date = date_range
    else:
        start_date = end_date = date_range

    filters = {
        "start_date": start_date.isoformat(),
        "end_date":   end_date.isoformat(),
        "start_id":   int(start_date.strftime("%Y%m%d")),
        "end_id":     int(end_date.strftime("%Y%m%d")),
    }

    if include_channel:
        channel = st.sidebar.selectbox(
            "Channel",
            ["All", "Organic Search", "Paid Search", "Direct", "Referral", "Social", "Email"],
        )
        filters["channel"] = None if channel == "All" else channel

    if include_page:
        page_filter = st.sidebar.text_input("Page URL contains", "")
        filters["page_filter"] = page_filter.strip() or None

    return filters


def date_clause(alias: str = "d") -> str:
    return f"{alias}.date_id BETWEEN :start_id AND :end_id"


def channel_clause(alias: str = "s") -> str:
    return f"(:channel IS NULL OR {alias}.channel_grouping = :channel)"


def page_clause(alias: str = "p") -> str:
    return f"(:page_filter IS NULL OR {alias}.url ILIKE '%' || :page_filter || '%')"
