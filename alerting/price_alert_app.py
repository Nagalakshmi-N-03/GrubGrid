"""
price_alert_app.py
Streamlit dashboard showing competitor price gaps.
Uses pg8000 (pure Python) for Streamlit Cloud compatibility.
"""

import os
import pandas as pd
import streamlit as st
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

# ─── Connection ───────────────────────────────────────────
import ssl
ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE

NEON_CONN = os.getenv(
    "NEON_CONN_STR",
    "postgresql+pg8000://neondb_owner:npg_2JvT7gUCOMSy@ep-rapid-darkness-ao16vhgr-pooler.c-2.ap-southeast-1.aws.neon.tech/neondb"
)

st.set_page_config(page_title="GrubGrid Price Alerts", page_icon="🍔", layout="wide")
st.title("🍔 GrubGrid — Competitor Price Alert Dashboard")
st.caption("Real-time view of where competitors are undercutting our menu prices.")


@st.cache_data(ttl=60)
def load_data():
    engine = create_engine(NEON_CONN)
    with engine.connect() as conn:
        df = pd.read_sql(text("""
            SELECT
                restaurant_name,
                item_name,
                our_price,
                competitor_name,
                competitor_price,
                price_gap,
                ROUND((price_gap / NULLIF(our_price, 0)) * 100, 1) AS gap_pct,
                scraped_at::date AS scraped_date
            FROM competitor_prices
            ORDER BY price_gap ASC
        """), conn)
    return df


try:
    df = load_data()
except Exception as e:
    st.error(f"Could not connect to database: {e}")
    st.stop()

# ── Sidebar filters ───────────────────────────────────────
st.sidebar.header("Filters")
restaurants = ["All"] + sorted(df["restaurant_name"].unique().tolist())
selected_restaurant = st.sidebar.selectbox("Restaurant", restaurants)

competitors = ["All"] + sorted(df["competitor_name"].unique().tolist())
selected_competitor = st.sidebar.selectbox("Competitor", competitors)

show_undercut_only = st.sidebar.checkbox("Show undercut items only", value=True)
gap_threshold = st.sidebar.slider("Min price gap (₹)", 0, 100, 5)

# ── Apply filters ─────────────────────────────────────────
filtered = df.copy()
if selected_restaurant != "All":
    filtered = filtered[filtered["restaurant_name"] == selected_restaurant]
if selected_competitor != "All":
    filtered = filtered[filtered["competitor_name"] == selected_competitor]
if show_undercut_only:
    filtered = filtered[filtered["price_gap"] < 0]
filtered = filtered[filtered["price_gap"].abs() >= gap_threshold]

# ── KPI row ───────────────────────────────────────────────
col1, col2, col3, col4 = st.columns(4)
undercut = df[df["price_gap"] < 0]
col1.metric("Total Items Tracked", len(df))
col2.metric("Items Undercut", len(undercut))
col3.metric("Avg Price Gap", f"₹{undercut['price_gap'].mean():.2f}" if len(undercut) else "₹0")
col4.metric("Worst Gap", f"₹{undercut['price_gap'].min():.2f}" if len(undercut) else "₹0")

st.divider()

# ── Table ─────────────────────────────────────────────────
st.subheader(f"Price Comparison ({len(filtered)} rows)")

def highlight_gap(val):
    if isinstance(val, float):
        if val < -50:
            return "background-color: #ff4444; color: white"
        elif val < 0:
            return "background-color: #ffaaaa"
        else:
            return "background-color: #aaffaa"
    return ""

styled = filtered.style.map(highlight_gap, subset=["price_gap"])
st.dataframe(styled, use_container_width=True, height=400)

# ── Bar chart ─────────────────────────────────────────────
st.subheader("🔴 Most Undercut Items")
worst = (
    undercut.groupby(["restaurant_name", "item_name"])["price_gap"]
    .mean()
    .sort_values()
    .head(10)
    .reset_index()
)
worst.columns = ["Restaurant", "Item", "Avg Gap (₹)"]
st.bar_chart(worst.set_index("Item")["Avg Gap (₹)"])

st.caption("Data refreshes every 60 seconds.")