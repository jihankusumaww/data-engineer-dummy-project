"""Weather and Prefect pipeline observability dashboard."""
import sqlite3
import sys
from pathlib import Path

import pandas as pd
import streamlit as st

sys.path.append(str(Path(__file__).resolve().parent.parent / "src"))
from db import DB_PATH

st.set_page_config(
    page_title="Signal Weather | Prefect Pipeline",
    page_icon="W",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=Space+Grotesk:wght@400;500;600;700&display=swap');
    :root { --ink:#e8eef2; --muted:#8d9aa3; --line:#2c3c45; --cyan:#48d6c4; --amber:#f4b860; --red:#ff7d76; }
    .stApp { background:radial-gradient(circle at 90% 0%,#1d3b3b 0,#10181d 36%,#0b1115 75%); color:var(--ink); }
    [data-testid="stHeader"] { background:transparent; } [data-testid="stSidebar"] { background:#10191e; border-right:1px solid var(--line); }
    [data-testid="stSidebar"] * { font-family:'Space Grotesk',sans-serif; } .block-container { max-width:1400px; padding-top:3rem; }
    h1,h2,h3,p,label { font-family:'Space Grotesk',sans-serif; } h1 { color:var(--ink); font-size:clamp(2rem,4vw,3.7rem); line-height:1; }
    .eyebrow,.section-label { color:var(--cyan); font-family:'DM Mono',monospace; font-size:.72rem; letter-spacing:.12em; text-transform:uppercase; }
    .subtitle { color:var(--muted); font-size:1rem; margin-top:-.9rem; } .section-label { margin:1.8rem 0 .75rem; }
    .metric-card,.panel,.city-card { background:linear-gradient(145deg,rgba(29,45,53,.98),rgba(19,31,38,.98)); border:1px solid var(--line); border-radius:8px; box-shadow:0 10px 24px rgba(0,0,0,.16); }
    .metric-card { min-height:116px; padding:1.1rem 1.2rem; } .metric-label,.panel-note { color:var(--muted); font-size:.78rem; }
    .metric-value { color:var(--ink); font-family:'DM Mono',monospace; font-size:1.45rem; margin-top:.5rem; } .metric-note { color:var(--muted); font-size:.72rem; margin-top:.3rem; }
    .panel { padding:1rem 1.1rem .8rem; } .panel-title { color:var(--ink); font-size:1.05rem; font-weight:600; margin-bottom:.2rem; }
    .city-card { border-top:3px solid var(--cyan); padding:1rem; min-height:115px; } .city-name { color:var(--muted); font-family:'DM Mono',monospace; font-size:.75rem; text-transform:uppercase; }
    .city-temp { color:var(--ink); font-family:'DM Mono',monospace; font-size:1.55rem; margin:.45rem 0; } .city-note { color:var(--muted); font-size:.72rem; }
    .signal { background:#123d3a; border:1px solid #28756b; border-radius:8px; color:#d8fff4; padding:1rem 1.2rem; font-family:'DM Mono',monospace; font-size:.75rem; line-height:1.6; }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown('<div class="eyebrow">Orchestration monitor / multi-city weather</div>', unsafe_allow_html=True)
st.title("Signal Weather")
st.markdown('<p class="subtitle">Current conditions and Prefect run health across the monitored cities.</p>', unsafe_allow_html=True)

if not DB_PATH.exists():
    st.warning("Database belum ada. Jalankan `python src/flows.py` dulu dari root project ini.")
    st.stop()

conn = sqlite3.connect(DB_PATH)
readings = pd.read_sql("SELECT * FROM fact_weather_reading ORDER BY fetched_at_utc DESC", conn)
runs = pd.read_sql("SELECT * FROM pipeline_run_log ORDER BY started_at_utc DESC", conn)
conn.close()

if readings.empty:
    st.warning("Belum ada data cuaca. Jalankan pipeline dulu.")
    st.stop()

latest_per_city = readings.sort_values("fetched_at_utc").groupby("city_name").tail(1)
total_runs = len(runs)
success_runs = int((runs["status"] == "success").sum())
partial_runs = int((runs["status"] == "partial_failure").sum())
success_rate = success_runs / total_runs * 100 if total_runs else 0
latest_run_status = runs.iloc[0]["status"] if not runs.empty else "unknown"

with st.sidebar:
    st.markdown("## Signal Weather")
    st.markdown('<div class="section-label">Pipeline status</div>', unsafe_allow_html=True)
    if latest_run_status == "success":
        st.success("Latest run healthy")
    elif latest_run_status == "partial_failure":
        st.warning("Latest run partial")
    else:
        st.error("Latest run failed")
    st.caption(f"{len(latest_per_city)} cities reporting")
    st.markdown("---")
    st.caption("Prefect flow with retries and partial-failure tolerance.")

st.markdown('<div class="section-label">Operations pulse</div>', unsafe_allow_html=True)
metric_data = [
    ("Cities reporting", f"{len(latest_per_city):,}", "Latest available readings", "var(--cyan)"),
    ("Pipeline runs", f"{total_runs:,}", "Recorded in observability log", "var(--cyan)"),
    ("Healthy runs", f"{success_rate:.1f}%", f"{success_runs:,} full success", "var(--cyan)"),
    ("Partial failures", f"{partial_runs:,}", "Other cities continue processing", "var(--amber)"),
]
columns = st.columns(4)
for column, (label, value, note, color) in zip(columns, metric_data):
    with column:
        st.markdown(f'<div class="metric-card"><div class="metric-label">{label}</div><div class="metric-value" style="color:{color}">{value}</div><div class="metric-note">{note}</div></div>', unsafe_allow_html=True)

st.markdown('<div class="section-label">City conditions</div>', unsafe_allow_html=True)
city_columns = st.columns(min(len(latest_per_city), 5))
for column, (_, row) in zip(city_columns, latest_per_city.iterrows()):
    with column:
        st.markdown(f'<div class="city-card"><div class="city-name">{row["city_name"]}</div><div class="city-temp">{row["temperature_c"]:.1f}°C</div><div class="city-note">Wind {row["windspeed_kmh"]:.0f} km/h<br>Code {int(row["weather_code"])}</div></div>', unsafe_allow_html=True)

st.markdown('<div class="section-label">Weather movement</div>', unsafe_allow_html=True)
chart_col, signal_col = st.columns([2.3, 1])
with chart_col:
    st.markdown('<div class="panel"><div class="panel-title">Temperature by city</div><div class="panel-note">Latest readings from the weather fact table</div>', unsafe_allow_html=True)
    temperature_history = readings.pivot_table(index="observed_at", columns="city_name", values="temperature_c", aggfunc="last").sort_index()
    st.line_chart(temperature_history, height=300)
    st.markdown('</div>', unsafe_allow_html=True)
with signal_col:
    latest_reading_time = latest_per_city["fetched_at_utc"].max()
    st.markdown(f'<div class="signal">FLOW SIGNAL<br><br>{len(latest_per_city)} cities have a current reading.<br><br>Last fetch:<br>{latest_reading_time}</div>', unsafe_allow_html=True)

st.markdown('<div class="section-label">Run observability</div>', unsafe_allow_html=True)
run_view = runs.rename(columns={"run_id": "Run ID", "started_at_utc": "Started", "finished_at_utc": "Finished", "cities_requested": "Requested", "cities_succeeded": "Succeeded", "cities_failed": "Failed", "status": "Status"})
st.dataframe(run_view, use_container_width=True, hide_index=True)

if partial_runs > 0:
    st.info("Partial failure terdeteksi: sebagian kota gagal, tetapi data kota lain tetap diproses. Ini adalah perilaku yang diharapkan dari desain pipeline.")
