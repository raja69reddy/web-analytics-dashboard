"""Traffic & Sessions Overview."""
import os
import sys

import plotly.express as px
import streamlit as st

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from dashboard.components.filters import channel_clause, date_clause, render_filters
from utils.db import query_df

st.set_page_config(page_title="Traffic & Sessions", layout="wide")
st.title("Traffic & Sessions")

f = render_filters()

# ── KPI summary row ──────────────────────────────────────────────────────────

kpi_sql = f"""
SELECT
    COUNT(*)                              AS sessions,
    SUM(CASE WHEN is_new_user THEN 1 END) AS new_users,
    SUM(pageviews)                        AS pageviews,
    ROUND(100.0 * SUM(CASE WHEN bounced THEN 1 END) / NULLIF(COUNT(*),0), 2) AS bounce_rate,
    ROUND(AVG(session_duration_s), 1)     AS avg_duration_s
FROM fct_sessions s
JOIN dim_dates d ON s.date_id = d.date_id
WHERE {date_clause()} AND {channel_clause()}
"""
kpi = query_df(kpi_sql, f)

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Sessions",        f"{int(kpi['sessions'][0] or 0):,}")
c2.metric("New Users",       f"{int(kpi['new_users'][0] or 0):,}")
c3.metric("Pageviews",       f"{int(kpi['pageviews'][0] or 0):,}")
c4.metric("Bounce Rate",     f"{kpi['bounce_rate'][0] or 0:.1f}%")
c5.metric("Avg Duration",    f"{int(kpi['avg_duration_s'][0] or 0)}s")

st.divider()

# ── Sessions over time ───────────────────────────────────────────────────────

trend_sql = f"""
SELECT d.full_date,
       COUNT(*) AS sessions,
       SUM(pageviews) AS pageviews
FROM fct_sessions s
JOIN dim_dates d ON s.date_id = d.date_id
WHERE {date_clause()} AND {channel_clause()}
GROUP BY 1 ORDER BY 1
"""
trend = query_df(trend_sql, f)

fig = px.line(
    trend, x="full_date", y=["sessions", "pageviews"],
    labels={"value": "Count", "full_date": "Date", "variable": "Metric"},
    title="Sessions & Pageviews Over Time",
)
st.plotly_chart(fig, use_container_width=True)

# ── Channel split + new vs returning ────────────────────────────────────────

col_left, col_right = st.columns(2)

ch_sql = f"""
SELECT channel_grouping, COUNT(*) AS sessions
FROM fct_sessions s
JOIN dim_dates d ON s.date_id = d.date_id
WHERE {date_clause()} AND {channel_clause()}
GROUP BY 1 ORDER BY 2 DESC
"""
ch = query_df(ch_sql, f)
fig_ch = px.bar(ch, x="sessions", y="channel_grouping", orientation="h",
                title="Sessions by Channel", labels={"channel_grouping": ""})
col_left.plotly_chart(fig_ch, use_container_width=True)

nr_sql = f"""
SELECT
    CASE WHEN is_new_user THEN 'New' ELSE 'Returning' END AS user_type,
    COUNT(*) AS sessions
FROM fct_sessions s
JOIN dim_dates d ON s.date_id = d.date_id
WHERE {date_clause()} AND {channel_clause()}
GROUP BY 1
"""
nr = query_df(nr_sql, f)
fig_nr = px.pie(nr, names="user_type", values="sessions", title="New vs Returning")
col_right.plotly_chart(fig_nr, use_container_width=True)

# ── Device breakdown ─────────────────────────────────────────────────────────

dev_sql = f"""
SELECT device_category, COUNT(*) AS sessions
FROM fct_sessions s
JOIN dim_dates d ON s.date_id = d.date_id
WHERE {date_clause()} AND {channel_clause()}
GROUP BY 1
"""
dev = query_df(dev_sql, f)
fig_dev = px.bar(dev, x="device_category", y="sessions", title="Sessions by Device")
st.plotly_chart(fig_dev, use_container_width=True)
