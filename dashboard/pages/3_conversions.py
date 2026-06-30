"""Conversion Tracking — loads from vw_conversions and vw_funnel."""
import os
import sys

import plotly.graph_objects as go
import streamlit as st

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from dashboard.components.charts import bar_chart, line_chart, pie_chart
from dashboard.components.filters import get_channel_filter, get_date_filter
from dashboard.components.metrics import (
    display_kpi_row,
    format_number,
    format_percentage,
)
from utils.query_runner import run_view

st.set_page_config(
    page_title="Conversion Tracking", page_icon="🎯", layout="wide"
)
st.title("🎯 Conversion Tracking")

# ── Sidebar filters ───────────────────────────────────────────────────────────
with st.sidebar:
    st.header("Filters")
    start_date, end_date = get_date_filter()
    channels = get_channel_filter()
    if channels:
        st.success(f"Channel filter: {len(channels)} selected")

# ── Load data ─────────────────────────────────────────────────────────────────
df_conv  = run_view("vw_conversions")
df_funnel = run_view("vw_funnel")

# Apply date and channel filters to vw_conversions
from dashboard.components.filters import apply_filters  # noqa: E402
import pandas as pd                                     # noqa: E402

df_conv = apply_filters(df_conv, start_date, end_date, channels)

with st.expander("Debug: data shapes", expanded=False):
    st.write({
        "vw_conversions": df_conv.shape,
        "vw_funnel":      df_funnel.shape,
    })

st.info("Conversion sections loading below…")
