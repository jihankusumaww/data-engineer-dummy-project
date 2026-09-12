import sqlite3
import sys
import tempfile
from pathlib import Path

import pandas as pd
import streamlit as st

project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))
from src.pipeline import DB_PATH, get_connection, process_log_file

st.set_page_config(
    page_title="Signal Room | Log Analytics",
    page_icon="S",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=Space+Grotesk:wght@400;500;600;700&display=swap');

    :root {
        --ink: #e8edf0;
        --muted: #8e9ba2;
        --panel: #172229;
        --panel-2: #1d2b32;
        --line: #30414a;
        --cyan: #58d5c2;
        --amber: #f3b45b;
        --red: #ff766f;
    }
    .stApp {
        background: radial-gradient(circle at 90% 0%, #263c3d 0, #111a20 38%, #0b1115 78%);
        color: var(--ink);
    }
    [data-testid="stHeader"] { background: transparent; }
    [data-testid="stSidebar"] { background: #10191e; border-right: 1px solid var(--line); }
    [data-testid="stSidebar"] * { font-family: 'Space Grotesk', sans-serif; }
    .block-container { max-width: 1420px; padding-top: 3rem; }
    h1, h2, h3, p, label { font-family: 'Space Grotesk', sans-serif; }
    h1 { color: var(--ink); font-size: clamp(2rem, 4vw, 3.7rem); line-height: 1; }
    h2 { color: var(--ink); }
    .eyebrow, .section-label { color: var(--cyan); font-family: 'DM Mono', monospace; font-size: .72rem; letter-spacing: .12em; text-transform: uppercase; }
    .eyebrow { margin-bottom: .6rem; }
    .subtitle { color: var(--muted); font-size: 1rem; margin-top: -.9rem; }
    .section-label { margin: 1.8rem 0 .75rem; }
    .metric-card, .panel {
        background: linear-gradient(145deg, rgba(29, 45, 53, .98), rgba(19, 31, 38, .98));
        border: 1px solid var(--line); border-radius: 8px; box-shadow: 0 12px 28px rgba(0,0,0,.16);
    }
    .metric-card { min-height: 116px; padding: 1.1rem 1.2rem; }
    .metric-label { color: var(--muted); font-size: .78rem; }
    .metric-value { color: var(--ink); font-family: 'DM Mono', monospace; font-size: 1.45rem; margin-top: .5rem; }
    .metric-note { color: var(--muted); font-size: .72rem; margin-top: .3rem; }
    .metric-card.good { border-top: 3px solid var(--cyan); }
    .metric-card.warn { border-top: 3px solid var(--amber); }
    .metric-card.bad { border-top: 3px solid var(--red); }
    .panel { padding: 1rem 1.1rem .8rem; }
    .panel-title { color: var(--ink); font-size: 1.05rem; font-weight: 600; margin-bottom: .2rem; }
    .panel-note { color: var(--muted); font-size: .76rem; margin-bottom: .7rem; }
    .signal-box { background: #123d3a; border: 1px solid #28756b; border-radius: 8px; color: #d8fff4; font-family: 'DM Mono', monospace; font-size: .74rem; line-height: 1.65; padding: 1rem 1.1rem; }
    .signal-box.warn { background: #453421; border-color: #976d36; color: #ffe9bd; }
    .dataframe { border: 1px solid var(--line); }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown('<div class="eyebrow">Observability / tolerant parser / event warehouse</div>', unsafe_allow_html=True)
st.title("Signal Room")
st.markdown('<p class="subtitle">A live-looking view of request volume, parser health, and suspicious traffic patterns.</p>', unsafe_allow_html=True)

with st.sidebar:
    st.markdown("## Signal Room")
    st.markdown('<div class="section-label">Data source</div>', unsafe_allow_html=True)
    mode = st.radio("Pilih sumber log", ["Pakai sample data bawaan", "Upload file log sendiri"])

conn = get_connection(DB_PATH, fresh_schema=True)  # schema fresh tiap buka dashboard (demo-friendly)

if mode == "Pakai sample data bawaan":
    sample_path = Path(__file__).resolve().parent.parent / "data" / "raw" / "access.log"
    summary = process_log_file(conn, sample_path)
    st.sidebar.success(f"Memproses sample: {sample_path.name}")
else:
    uploaded = st.sidebar.file_uploader("Upload file .log atau .txt", type=["log", "txt"])
    if uploaded is None:
        st.info("Upload file log di sidebar untuk mulai, atau pilih 'Pakai sample data bawaan'.")
        st.stop()
    with tempfile.NamedTemporaryFile(delete=False, suffix=".log") as tmp:
        tmp.write(uploaded.getvalue())
        tmp_path = Path(tmp.name)
    summary = process_log_file(conn, tmp_path)
    st.sidebar.success(f"Memproses: {uploaded.name}")

if summary["parse_failed"] > 0:
    with st.expander(f"⚠️ Lihat {summary['parse_failed']} baris yang gagal di-parse"):
        errors = pd.read_sql("SELECT raw_line FROM parse_error_log", conn)
        st.dataframe(errors, use_container_width=True, hide_index=True)

events = pd.read_sql("SELECT * FROM fact_log_event", conn)
conn.close()

if events.empty:
    st.warning("Tidak ada event valid yang berhasil di-parse dari file ini.")
    st.stop()

events["event_timestamp"] = pd.to_datetime(events["event_timestamp"])
events["hour"] = events["event_timestamp"].dt.floor("h")
error_rate = (events["status_class"] != "success").mean() * 100
server_errors = int((events["status_class"] == "server_error").sum())
latest_event = events["event_timestamp"].max().strftime("%d %b %Y, %H:%M UTC")

st.markdown('<div class="section-label">Run health</div>', unsafe_allow_html=True)
col1, col2, col3, col4 = st.columns(4)
metrics = [
    ("Total log lines", f"{summary['total_lines']:,}", "Input records inspected", "good"),
    ("Parse success", f"{summary['parse_success_rate']:.1f}%", f"{summary['parsed_ok']:,} valid events", "good"),
    ("Parse failures", f"{summary['parse_failed']:,}", "Retained for audit", "bad" if summary["parse_failed"] else "good"),
    ("HTTP error rate", f"{error_rate:.1f}%", f"{server_errors:,} server errors", "warn" if error_rate else "good"),
]
for column, (label, value, note, state) in zip((col1, col2, col3, col4), metrics):
    with column:
        st.markdown(
            f'<div class="metric-card {state}"><div class="metric-label">{label}</div>'
            f'<div class="metric-value">{value}</div><div class="metric-note">{note}</div></div>',
            unsafe_allow_html=True,
        )

st.caption(f"Latest event: {latest_event} | Run ID: {summary['run_id']}")

signal_text = "Parser healthy. All source lines were converted into structured events." if summary["parse_failed"] == 0 else f"Attention: {summary['parse_failed']:,} source lines could not be parsed and are available for audit."
signal_class = "" if summary["parse_failed"] == 0 else " warn"
st.markdown(f'<div class="signal-box{signal_class}">PIPELINE SIGNAL<br>{signal_text}</div>', unsafe_allow_html=True)

st.markdown('<div class="section-label">Traffic pulse</div>', unsafe_allow_html=True)
requests_per_hour = events.groupby("hour").size()
traffic_col, status_col = st.columns([1.6, 1])
with traffic_col:
    st.markdown('<div class="panel"><div class="panel-title">Requests per hour</div><div class="panel-note">Request volume across the parsed event window</div>', unsafe_allow_html=True)
    st.area_chart(requests_per_hour.rename("Requests"), color="#58d5c2", height=300)
    st.markdown('</div>', unsafe_allow_html=True)

with status_col:
    st.markdown('<div class="panel"><div class="panel-title">Status class mix</div><div class="panel-note">Success versus client and server errors</div>', unsafe_allow_html=True)
    status_dist = events["status_class"].value_counts()
    st.bar_chart(status_dist, color="#f3b45b", height=300)
    st.markdown('</div>', unsafe_allow_html=True)

st.markdown('<div class="section-label">Traffic detail</div>', unsafe_allow_html=True)
col_left, col_right = st.columns(2)
with col_left:
    st.markdown('<div class="panel"><div class="panel-title">Most requested endpoints</div><div class="panel-note">Paths receiving the most traffic</div>', unsafe_allow_html=True)
    top_paths = events["path"].value_counts().head(10)
    st.bar_chart(top_paths, color="#58d5c2", height=300)
    st.markdown('</div>', unsafe_allow_html=True)

with col_right:
    st.markdown('<div class="panel"><div class="panel-title">HTTP method mix</div><div class="panel-note">Read versus write traffic</div>', unsafe_allow_html=True)
    st.bar_chart(events["http_method"].value_counts(), color="#f3b45b", height=300)
    st.markdown('</div>', unsafe_allow_html=True)

st.markdown('<div class="section-label">Investigation queue</div>', unsafe_allow_html=True)
st.markdown('<div class="panel"><div class="panel-title">Top IPs by request count</div><div class="panel-note">High-volume sources worth checking for bot or abuse patterns</div>', unsafe_allow_html=True)
top_ips = events["ip_address"].value_counts().head(10).reset_index()
top_ips.columns = ["ip_address", "request_count"]
st.dataframe(top_ips, use_container_width=True, hide_index=True)
st.markdown('</div>', unsafe_allow_html=True)

with st.expander("Lihat semua event terstruktur"):
    display_events = events.drop(columns=["hour"]).copy()
    display_events["event_timestamp"] = display_events["event_timestamp"].dt.strftime("%Y-%m-%d %H:%M:%S UTC")
    st.dataframe(display_events, use_container_width=True, hide_index=True)
