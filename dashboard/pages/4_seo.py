"""SEO & Content Performance."""
import os
import sys

import plotly.express as px
import streamlit as st

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from dashboard.components.filters import date_clause, page_clause, render_filters
from utils.db import query_df

st.set_page_config(page_title="SEO & Content", layout="wide")
st.title("SEO & Content Performance")

f = render_filters(include_channel=False)

# ── Top organic landing pages ─────────────────────────────────────────────────

top_sql = f"""
SELECT p.url_path, p.page_title,
       COUNT(DISTINCT s.session_id)                                    AS organic_sessions,
       SUM(s.pageviews)                                                AS pageviews,
       ROUND(AVG(s.session_duration_s), 1)                             AS avg_time_s,
       ROUND(100.0 * SUM(CASE WHEN s.bounced THEN 1 END)/NULLIF(COUNT(*),0), 2) AS bounce_rate,
       SUM(s.conversions)                                              AS conversions
FROM fct_sessions s
JOIN dim_dates d ON s.date_id = d.date_id
JOIN dim_pages  p ON s.page_id = p.page_id
WHERE s.channel_grouping = 'Organic Search'
  AND {date_clause()} AND {page_clause()}
GROUP BY 1,2
ORDER BY organic_sessions DESC
LIMIT 20
"""
top = query_df(top_sql, f)

st.subheader("Top Organic Landing Pages")
st.dataframe(top, use_container_width=True, hide_index=True)

st.divider()

# ── Word count vs engagement scatter ─────────────────────────────────────────

wc_sql = f"""
SELECT p.url_path, p.word_count,
       ROUND(AVG(s.session_duration_s), 1) AS avg_time_s,
       SUM(s.pageviews)                    AS pageviews,
       ROUND(100.0 * SUM(CASE WHEN s.bounced THEN 1 END)/NULLIF(COUNT(*),0), 2) AS bounce_rate
FROM fct_sessions s
JOIN dim_dates d ON s.date_id = d.date_id
JOIN dim_pages  p ON s.page_id = p.page_id
WHERE p.word_count IS NOT NULL
  AND s.channel_grouping = 'Organic Search'
  AND {date_clause()} AND {page_clause()}
GROUP BY 1,2
HAVING COUNT(*) > 2
"""
wc = query_df(wc_sql, f)

col1, col2 = st.columns(2)
if not wc.empty:
    fig_scatter = px.scatter(
        wc, x="word_count", y="avg_time_s", size="pageviews",
        color="bounce_rate", hover_name="url_path",
        labels={"word_count": "Word Count", "avg_time_s": "Avg Time on Page (s)",
                "bounce_rate": "Bounce Rate %"},
        title="Word Count vs Engagement (bubble = pageviews, color = bounce rate)",
        color_continuous_scale="RdYlGn_r",
    )
    col1.plotly_chart(fig_scatter, use_container_width=True)

# ── Page load time distribution ───────────────────────────────────────────────

load_sql = """
SELECT url, load_time_ms, http_status
FROM raw_scrape_pages
WHERE http_status = 200
ORDER BY scraped_at DESC
"""
load = query_df(load_sql)
if not load.empty:
    fig_load = px.histogram(load, x="load_time_ms", nbins=30,
                            title="Page Load Time Distribution (ms)",
                            labels={"load_time_ms": "Load Time (ms)"})
    col2.plotly_chart(fig_load, use_container_width=True)

# ── Content health table ──────────────────────────────────────────────────────

health_sql = """
SELECT DISTINCT ON (url)
    url, title, word_count, meta_description,
    internal_links, has_schema_org, load_time_ms, http_status
FROM raw_scrape_pages
ORDER BY url, scraped_at DESC
"""
health = query_df(health_sql)
if not health.empty:
    st.subheader("Content Health")
    st.dataframe(health, use_container_width=True, hide_index=True)
