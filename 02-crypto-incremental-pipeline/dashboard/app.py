"""Dashboard visual untuk data hasil crypto incremental pipeline."""
import sqlite3
from pathlib import Path

import pandas as pd
import streamlit as st

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "crypto.db"

st.set_page_config(
    page_title="Crypto Pulse | Incremental Pipeline",
    page_icon="C",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=Space+Grotesk:wght@400;500;600;700&display=swap');

    :root {
        --ink: #e8eef2;
        --muted: #8d9aa3;
        --panel: #172229;
        --line: #2c3c45;
        --cyan: #48d6c4;
        --amber: #f4b860;
        --red: #ff7d76;
    }
    .stApp {
        background: radial-gradient(circle at 90% 0%, #1d3b3b 0, #10181d 36%, #0b1115 75%);
        color: var(--ink);
    }
    [data-testid="stHeader"] { background: transparent; }
    [data-testid="stSidebar"] {
        background: #10191e;
        border-right: 1px solid var(--line);
    }
    [data-testid="stSidebar"] * { font-family: 'Space Grotesk', sans-serif; }
    .block-container { max-width: 1400px; padding-top: 3rem; }
    h1, h2, h3, p, label { font-family: 'Space Grotesk', sans-serif; }
    h1 { letter-spacing: 0; font-size: clamp(2rem, 4vw, 3.8rem); line-height: 1; }
    h2 { color: var(--ink); margin-top: 1.8rem; }
    .eyebrow {
        color: var(--cyan); font-family: 'DM Mono', monospace; font-size: .72rem;
        letter-spacing: .12em; text-transform: uppercase; margin-bottom: .6rem;
    }
    .subtitle { color: var(--muted); font-size: 1rem; margin-top: -.9rem; }
    .section-label {
        color: var(--muted); font-family: 'DM Mono', monospace; font-size: .72rem;
        letter-spacing: .1em; text-transform: uppercase; margin: 1.7rem 0 .7rem;
    }
    .overview-card, .metric-card {
        background: linear-gradient(145deg, rgba(29, 45, 53, .98), rgba(19, 31, 38, .98));
        border: 1px solid var(--line); border-radius: 8px; padding: 1.1rem 1.2rem;
        min-height: 118px; box-shadow: 0 12px 28px rgba(0,0,0,.16);
    }
    .overview-card { border-top: 3px solid var(--cyan); }
    .overview-card.down { border-top-color: var(--red); }
    .overview-card.flat { border-top-color: var(--amber); }
    .coin-name { color: var(--muted); font-family: 'DM Mono', monospace; font-size: .72rem; text-transform: uppercase; }
    .coin-price { color: var(--ink); font-size: 1.45rem; font-weight: 600; margin: .35rem 0 .15rem; }
    .change { font-family: 'DM Mono', monospace; font-size: .8rem; }
    .up { color: var(--cyan); } .down-text { color: var(--red); } .flat-text { color: var(--amber); }
    .metric-card { min-height: 108px; }
    .metric-label { color: var(--muted); font-size: .78rem; }
    .metric-value { color: var(--ink); font-family: 'DM Mono', monospace; font-size: 1.45rem; margin-top: .5rem; }
    .metric-note { color: var(--muted); font-size: .72rem; margin-top: .3rem; }
    .dataframe { border: 1px solid var(--line); }
    [data-testid="stMetric"] { background: transparent; }
    .stButton button { border-color: var(--line); }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown('<div class="eyebrow">Incremental market monitor / live warehouse view</div>', unsafe_allow_html=True)
st.title("Crypto Pulse")
st.markdown('<p class="subtitle">Snapshot harga dari pipeline append-only, diperkaya moving average dan perubahan antar-run.</p>', unsafe_allow_html=True)

if not DB_PATH.exists():
    st.warning("Database belum ada. Jalankan `python src/pipeline.py` dulu minimal beberapa kali "
               "(idealnya dengan jeda) supaya ada data untuk divisualisasikan.")
    st.stop()

conn = sqlite3.connect(DB_PATH)
df = pd.read_sql("SELECT * FROM fact_price_hourly ORDER BY fetched_at_utc", conn)
conn.close()

if df.empty:
    st.warning("Belum ada data di fact_price_hourly. Jalankan pipeline beberapa kali dulu.")
    st.stop()

df["fetched_at_utc"] = pd.to_datetime(df["fetched_at_utc"])

coins = df["coin_id"].unique().tolist()
latest_timestamp = df["fetched_at_utc"].max().strftime("%d %b %Y, %H:%M UTC")

st.markdown('<div class="section-label">Market snapshot</div>', unsafe_allow_html=True)
overview_columns = st.columns(len(coins))
for column, coin in zip(overview_columns, coins):
    latest = df[df["coin_id"] == coin].sort_values("fetched_at_utc").iloc[-1]
    change = latest["pct_change_from_prev"]
    change_text = "N/A" if pd.isna(change) else f"{change:+.2f}%"
    state = "flat" if pd.isna(change) or change == 0 else ("" if change > 0 else "down")
    change_class = "flat-text" if state == "flat" else ("up" if change > 0 else "down-text")
    with column:
        st.markdown(
            f'<div class="overview-card {state}">'
            f'<div class="coin-name">{coin}</div>'
            f'<div class="coin-price">${latest["price_usd"]:,.2f}</div>'
            f'<div class="change {change_class}">{change_text} since previous snapshot</div>'
            '</div>',
            unsafe_allow_html=True,
        )

st.caption(f"Last warehouse refresh: {latest_timestamp}")

with st.sidebar:
    st.markdown("## Explore")
    selected_coin = st.selectbox("Pilih coin", coins)
    st.markdown("---")
    st.markdown("**Pipeline status**")
    st.success(f"{len(df):,} snapshot tersedia")
    st.caption("Sumber: fact_price_hourly\n\nJalankan pipeline kembali untuk menambah snapshot baru.")

coin_df = df[df["coin_id"] == selected_coin].sort_values("fetched_at_utc")
latest = coin_df.iloc[-1]
last_change = latest["pct_change_from_prev"]
change_text = "N/A" if pd.isna(last_change) else f"{last_change:+.2f}%"
change_color = "var(--amber)" if pd.isna(last_change) or last_change == 0 else ("var(--cyan)" if last_change > 0 else "var(--red)")

st.markdown(f'<div class="section-label">Selected asset / {selected_coin}</div>', unsafe_allow_html=True)
col1, col2, col3 = st.columns(3)
with col1:
    st.markdown(f'<div class="metric-card"><div class="metric-label">Latest price / USD</div><div class="metric-value">${latest["price_usd"]:,.2f}</div><div class="metric-note">Most recent processed value</div></div>', unsafe_allow_html=True)
with col2:
    st.markdown(f'<div class="metric-card"><div class="metric-label">Change vs previous</div><div class="metric-value" style="color:{change_color}">{change_text}</div><div class="metric-note">Calculated incrementally</div></div>', unsafe_allow_html=True)
with col3:
    st.markdown(f'<div class="metric-card"><div class="metric-label">Snapshots tracked</div><div class="metric-value">{len(coin_df):,}</div><div class="metric-note">Append-only raw history</div></div>', unsafe_allow_html=True)

st.markdown('<div class="section-label">Price movement</div>', unsafe_allow_html=True)
chart_data = coin_df.set_index("fetched_at_utc")[["price_usd", "moving_avg_3"]].rename(columns={"price_usd": "Price", "moving_avg_3": "Moving avg 3"})
st.area_chart(chart_data, color=["#48d6c4", "#f4b860"], height=330)

st.markdown('<div class="section-label">Processed records</div>', unsafe_allow_html=True)
display_df = coin_df.rename(columns={
    "coin_id": "Coin", "price_usd": "Price (USD)", "market_cap_usd": "Market cap (USD)",
    "fetched_at_utc": "Fetched at", "moving_avg_3": "Moving avg 3", "pct_change_from_prev": "Change (%)",
}).copy()
display_df["Fetched at"] = display_df["Fetched at"].dt.strftime("%Y-%m-%d %H:%M:%S UTC")
st.dataframe(
    display_df.style.format({"Price (USD)": "${:,.2f}", "Market cap (USD)": "${:,.0f}", "Moving avg 3": "${:,.2f}", "Change (%)": "{:+.2f}%"}),
    use_container_width=True,
    hide_index=True,
)
