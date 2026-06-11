"""Conversion Tracking."""
import os
import sys

import plotly.express as px
import streamlit as st

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from dashboard.components.filters import channel_clause, date_clause, render_filters
from utils.db import query_df

st.set_page_config(page_title="Conversions", layout="wide")
st.title("Conversion Tracking")

f = render_filters()

# ── KPI row ──────────────────────────────────────────────────────────────────

kpi_sql = f"""
SELECT
    SUM(conversions)                                                              AS total_conversions,
    SUM(revenue)                                                                  AS total_revenue,
    ROUND(100.0 * SUM(CASE WHEN conversions>0 THEN 1 END) / NULLIF(COUNT(*),0), 4) AS cvr_pct,
    ROUND(SUM(revenue) / NULLIF(SUM(conversions),0), 2)                           AS rev_per_conversion
FROM fct_sessions s
JOIN dim_dates d ON s.date_id = d.date_id
WHERE {date_clause()} AND {channel_clause()}
"""
kpi = query_df(kpi_sql, f)

c1, c2, c3, c4 = st.columns(4)
c1.metric("Conversions",      f"{int(kpi['total_conversions'][0] or 0):,}")
c2.metric("Revenue",          f"${float(kpi['total_revenue'][0] or 0):,.2f}")
c3.metric("CVR",              f"{float(kpi['cvr_pct'][0] or 0):.2f}%")
c4.metric("Rev / Conversion", f"${float(kpi['rev_per_conversion'][0] or 0):,.2f}")

st.divider()

# ── CVR over time ─────────────────────────────────────────────────────────────

cvr_sql = f"""
SELECT d.full_date,
       COUNT(*) AS sessions,
       SUM(conversions) AS conversions,
       ROUND(100.0 * SUM(CASE WHEN conversions>0 THEN 1 END) / NULLIF(COUNT(*),0), 4) AS cvr_pct
FROM fct_sessions s
JOIN dim_dates d ON s.date_id = d.date_id
WHERE {date_clause()} AND {channel_clause()}
GROUP BY 1 ORDER BY 1
"""
cvr = query_df(cvr_sql, f)
fig_cvr = px.line(cvr, x="full_date", y="cvr_pct",
                  title="Conversion Rate Over Time (%)",
                  labels={"cvr_pct": "CVR %", "full_date": "Date"})
st.plotly_chart(fig_cvr, use_container_width=True)

# ── Conversions by channel ────────────────────────────────────────────────────

col1, col2 = st.columns(2)

ch_sql = f"""
SELECT channel_grouping, source, medium,
       SUM(conversions) AS conversions,
       SUM(revenue)     AS revenue,
       ROUND(100.0 * SUM(CASE WHEN conversions>0 THEN 1 END) / NULLIF(COUNT(*),0), 4) AS cvr_pct
FROM fct_sessions s
JOIN dim_dates d ON s.date_id = d.date_id
WHERE {date_clause()} AND {channel_clause()}
GROUP BY 1,2,3
ORDER BY conversions DESC
LIMIT 15
"""
ch = query_df(ch_sql, f)
fig_ch = px.bar(ch, x="channel_grouping", y="conversions",
                color="medium", title="Conversions by Channel")
col1.plotly_chart(fig_ch, use_container_width=True)

rev_sql = f"""
SELECT channel_grouping, SUM(revenue) AS revenue
FROM fct_sessions s
JOIN dim_dates d ON s.date_id = d.date_id
WHERE {date_clause()} AND {channel_clause()}
GROUP BY 1 ORDER BY 2 DESC
"""
rev = query_df(rev_sql, f)
fig_rev = px.pie(rev, names="channel_grouping", values="revenue",
                 title="Revenue Share by Channel")
col2.plotly_chart(fig_rev, use_container_width=True)

# ── Goal completions ──────────────────────────────────────────────────────────

goal_sql = f"""
SELECT event_name AS goal, COUNT(*) AS completions,
       ROUND(AVG(event_value), 2) AS avg_value
FROM fct_events e
JOIN dim_dates d ON e.date_id = d.date_id
WHERE e.event_name IN ('form_submit','purchase','signup','download','contact')
  AND {date_clause()}
GROUP BY 1 ORDER BY 2 DESC
"""
goals = query_df(goal_sql, f)
if not goals.empty:
    st.subheader("Goal Completions")
    st.dataframe(goals, use_container_width=True, hide_index=True)
