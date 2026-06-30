"""
Web Analytics Dashboard — entry point.

Run:
    streamlit run dashboard/app.py
"""
import streamlit as st

st.set_page_config(
    page_title="Web Analytics",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("Web Analytics Dashboard")
st.markdown(
    """
    Use the sidebar to filter by date, channel, and page URL.
    Navigate to a section using the **Pages** menu in the sidebar.

    | Page | Contents |
    |------|----------|
    | **Traffic & Sessions** | Sessions over time, channels, new vs returning |
    | **User Behavior** | Top pages, funnel, scroll depth |
    | **Conversions** | Conversion rate, goal completions, drop-off |
    | **SEO & Content** | Organic landing pages, word count vs engagement |
    """
)
