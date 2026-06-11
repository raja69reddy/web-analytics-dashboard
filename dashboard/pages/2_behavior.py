"""User Behavior & Funnels."""
import os
import sys

import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from dashboard.components.filters import channel_clause, date_clause, page_clause, render_filters
from utils.db import query_df

st.set_page_config(page_title="User Behavior", layout="wide")
st.title("User Behavior & Funnels")

f = render_filters()

# ── Top pages ────────────────────────────────────────────────────────────────

top_sql = f"""
SELECT p.url_path, p.page_title,
       SUM(s.pageviews)                    AS pageviews,
       ROUND(AVG(s.session_duration_s), 1) AS avg_time_s,
       ROUND(100.0 * SUM(CASE WHEN s.bounced THEN 1 END) / NULLIF(COUNT(*),0), 2) AS exit_rate
FROM fct_sessions s
JOIN dim_dates d ON s.date_id = d.date_id
JOIN dim_pages  p ON s.page_id = p.page_id
WHERE {date_clause()} AND {channel_clause()} AND {page_clause()}
GROUP BY 1,2
ORDER BY pageviews DESC
LIMIT 20
"""
top = query_df(top_sql, f)

st.subheader("Top Pages by Pageviews")
st.dataframe(top, use_container_width=True, hide_index=True)

# ── Scroll depth ─────────────────────────────────────────────────────────────

scroll_sql = f"""
SELECT p.url_path,
       ROUND(AVG(e.scroll_depth_pct), 1) AS avg_scroll_pct,
       COUNT(*)                           AS scroll_events
FROM fct_events e
JOIN dim_dates  d ON e.date_id = d.date_id
JOIN dim_pages  p ON e.page_id = p.page_id
WHERE e.event_name = 'scroll'
  AND {date_clause()}
  AND {page_clause()}
GROUP BY 1
HAVING COUNT(*) > 5
ORDER BY avg_scroll_pct DESC
LIMIT 15
"""
scroll = query_df(scroll_sql, f)

col1, col2 = st.columns(2)
if not scroll.empty:
    fig_scroll = px.bar(scroll, x="avg_scroll_pct", y="url_path", orientation="h",
                        title="Avg Scroll Depth % by Page",
                        labels={"url_path": "", "avg_scroll_pct": "Avg Scroll %"})
    col1.plotly_chart(fig_scroll, use_container_width=True)

# ── Event breakdown ──────────────────────────────────────────────────────────

evt_sql = f"""
SELECT event_name, COUNT(*) AS events
FROM fct_events e
JOIN dim_dates d ON e.date_id = d.date_id
WHERE {date_clause()}
GROUP BY 1 ORDER BY 2 DESC
"""
evt = query_df(evt_sql, f)
fig_evt = px.bar(evt, x="event_name", y="events", title="Events by Type")
col2.plotly_chart(fig_evt, use_container_width=True)

# ── Funnel ───────────────────────────────────────────────────────────────────

funnel_sql = f"""
SELECT
    COUNT(DISTINCT s.session_id)                                               AS landed,
    COUNT(DISTINCT CASE WHEN ev.has_engagement THEN s.session_id END)          AS engaged,
    COUNT(DISTINCT CASE WHEN s.conversions > 0 THEN s.session_id END)          AS converted
FROM fct_sessions s
JOIN dim_dates d ON s.date_id = d.date_id
LEFT JOIN (
    SELECT DISTINCT session_id, TRUE AS has_engagement
    FROM fct_events
    WHERE event_name IN ('click','scroll','form_submit','add_to_cart')
) ev ON ev.session_id = s.session_id
WHERE {date_clause()} AND {channel_clause()}
"""
funnel = query_df(funnel_sql, f)

if not funnel.empty:
    steps = ["Landed", "Engaged", "Converted"]
    vals  = [funnel["landed"][0], funnel["engaged"][0], funnel["converted"][0]]
    fig_funnel = go.Figure(go.Funnel(
        y=steps, x=vals,
        textinfo="value+percent initial",
        marker_color=["#636EFA", "#EF553B", "#00CC96"],
    ))
    fig_funnel.update_layout(title="Session Funnel")
    st.plotly_chart(fig_funnel, use_container_width=True)
