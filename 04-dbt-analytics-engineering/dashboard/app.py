"""Subscription analytics dashboard for dbt marts in DuckDB."""
import os
import shutil
import subprocess
import sys
from pathlib import Path

import duckdb
import pandas as pd
import streamlit as st

DB_PATH = Path(__file__).resolve().parent.parent / "subscription_analytics.duckdb"
PROJECT_PATH = DB_PATH.parent

st.set_page_config(
    page_title="Revenue Room | Subscription Analytics",
    page_icon="R",
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
    .metric-card,.panel { background:linear-gradient(145deg,rgba(29,45,53,.98),rgba(19,31,38,.98)); border:1px solid var(--line); border-radius:8px; box-shadow:0 10px 24px rgba(0,0,0,.16); }
    .metric-card { min-height:116px; padding:1.1rem 1.2rem; } .metric-label,.panel-note { color:var(--muted); font-size:.78rem; }
    .metric-value { color:var(--ink); font-family:'DM Mono',monospace; font-size:1.45rem; margin-top:.5rem; } .metric-note { color:var(--muted); font-size:.72rem; margin-top:.3rem; }
    .panel { padding:1rem 1.1rem .8rem; } .panel-title { color:var(--ink); font-size:1.05rem; font-weight:600; margin-bottom:.2rem; }
    .signal { background:#123d3a; border:1px solid #28756b; border-radius:8px; color:#d8fff4; padding:1rem 1.2rem; font-family:'DM Mono',monospace; font-size:.75rem; line-height:1.6; }
    </style>
    """,
    unsafe_allow_html=True,
)


def ensure_dbt_marts() -> None:
    if DB_PATH.exists():
        return

    environment = os.environ.copy()
    environment["DBT_PROFILES_DIR"] = str(PROJECT_PATH)
    dbt_command = shutil.which("dbt") or str(Path(sys.executable).with_name("dbt"))
    if not Path(dbt_command).exists() and shutil.which("dbt") is None:
        raise RuntimeError("dbt CLI tidak ditemukan. Pastikan dbt-core terpasang.")
    commands = [
        [dbt_command, "seed", "--profiles-dir", str(PROJECT_PATH)],
        [dbt_command, "run", "--profiles-dir", str(PROJECT_PATH)],
    ]
    with st.spinner("Building subscription marts with dbt..."):
        for command in commands:
            result = subprocess.run(
                command,
                cwd=PROJECT_PATH,
                env=environment,
                capture_output=True,
                text=True,
                check=False,
            )
            if result.returncode != 0:
                raise RuntimeError(result.stdout[-1200:] or result.stderr[-1200:])


def relation_schema(connection: duckdb.DuckDBPyConnection, relation: str) -> str:
    schemas = connection.execute(
        """SELECT table_schema FROM information_schema.tables
           WHERE table_name = ? ORDER BY table_schema""",
        [relation],
    ).fetchall()
    for schema_name, in schemas:
        if schema_name not in {"main", "information_schema", "pg_catalog"}:
            return schema_name
    raise RuntimeError(f"dbt model tidak ditemukan: {relation}")


try:
    ensure_dbt_marts()
except Exception as error:
    st.error(f"dbt marts gagal dibuat: {error}")
    st.stop()

st.markdown('<div class="eyebrow">Analytics engineering / recurring revenue</div>', unsafe_allow_html=True)
st.title("Revenue Room")
st.markdown('<p class="subtitle">MRR, subscriber health, and plan economics from tested dbt marts.</p>', unsafe_allow_html=True)

if not DB_PATH.exists():
    st.warning("DuckDB belum ada. Jalankan `dbt seed && dbt run` dari folder Project 4 terlebih dahulu.")
    st.stop()

con = duckdb.connect(str(DB_PATH), read_only=True)
mart_schema = relation_schema(con, "fct_mrr")
mrr = con.execute(f'SELECT * FROM "{mart_schema}"."fct_mrr" ORDER BY month_start').fetchdf()
customers = con.execute(f'SELECT * FROM "{mart_schema}"."dim_customers"').fetchdf()
subscriptions = con.execute(f'SELECT * FROM "{mart_schema}"."fct_subscriptions"').fetchdf()
con.close()

latest_month = mrr["month_start"].max()
latest_mrr = mrr.loc[mrr["month_start"] == latest_month, "mrr_usd"].sum()
previous_month = mrr[mrr["month_start"] < latest_month]["month_start"].max()
previous_mrr = mrr.loc[mrr["month_start"] == previous_month, "mrr_usd"].sum() if pd.notna(previous_month) else 0
mrr_delta = ((latest_mrr - previous_mrr) / previous_mrr * 100) if previous_mrr else 0
active_customers = int(customers["is_active_subscriber"].fillna(False).sum())
churned_customers = int((~customers["is_active_subscriber"].fillna(False)).sum())
active_rate = active_customers / len(customers) * 100 if len(customers) else 0

with st.sidebar:
    st.markdown("## Revenue Room")
    st.markdown('<div class="section-label">Model health</div>', unsafe_allow_html=True)
    st.success(f"{len(mrr):,} MRR records")
    st.caption(f"Latest month: {latest_month}")
    st.markdown("---")
    st.caption("Sources: marts.fct_mrr, dim_customers, fct_subscriptions")

st.markdown('<div class="section-label">Revenue pulse</div>', unsafe_allow_html=True)
metric_data = [
    ("Latest MRR", f"${latest_mrr:,.2f}", f"{mrr_delta:+.1f}% vs prior month", "var(--cyan)"),
    ("Active subscribers", f"{active_customers:,}", f"{active_rate:.1f}% of customers", "var(--cyan)"),
    ("Churned customers", f"{churned_customers:,}", "Current-state dimension", "var(--red)"),
    ("Paid revenue", f"${subscriptions['total_paid_usd'].sum():,.2f}", "Successful payments only", "var(--amber)"),
]
columns = st.columns(4)
for column, (label, value, note, color) in zip(columns, metric_data):
    with column:
        st.markdown(f'<div class="metric-card"><div class="metric-label">{label}</div><div class="metric-value" style="color:{color}">{value}</div><div class="metric-note">{note}</div></div>', unsafe_allow_html=True)

st.markdown('<div class="section-label">MRR movement</div>', unsafe_allow_html=True)
trend_col, signal_col = st.columns([2.3, 1])
with trend_col:
    st.markdown('<div class="panel"><div class="panel-title">Monthly recurring revenue</div><div class="panel-note">Date-spine model keeps quiet months visible</div>', unsafe_allow_html=True)
    mrr_pivot = mrr.pivot(index="month_start", columns="plan_type", values="mrr_usd").fillna(0)
    st.area_chart(mrr_pivot, color=["#48d6c4", "#f4b860", "#ff7d76"], height=300)
    st.markdown('</div>', unsafe_allow_html=True)
with signal_col:
    top_plan = mrr[mrr["month_start"] == latest_month].sort_values("mrr_usd", ascending=False).iloc[0]["plan_type"]
    st.markdown(f'<div class="signal">MODEL SIGNAL<br><br>{top_plan} leads the latest MRR mix.<br><br>{len(subscriptions):,} subscriptions are modeled across {subscriptions["plan_type"].nunique():,} plans.</div>', unsafe_allow_html=True)

st.markdown('<div class="section-label">Plan economics</div>', unsafe_allow_html=True)
left, right = st.columns(2)
with left:
    st.markdown('<div class="panel"><div class="panel-title">Active subscriber mix</div><div class="panel-note">Current plan distribution</div>', unsafe_allow_html=True)
    plan_dist = customers[customers["is_active_subscriber"].fillna(False)]["current_plan_type"].value_counts()
    st.bar_chart(plan_dist, color="#48d6c4", height=260)
    st.markdown('</div>', unsafe_allow_html=True)
with right:
    st.markdown('<div class="panel"><div class="panel-title">Collected revenue by plan</div><div class="panel-note">Successful payments across subscription lifetime</div>', unsafe_allow_html=True)
    revenue_by_plan = subscriptions.groupby("plan_type")["total_paid_usd"].sum().sort_values(ascending=False)
    st.bar_chart(revenue_by_plan, color="#f4b860", height=260)
    st.markdown('</div>', unsafe_allow_html=True)

st.markdown('<div class="section-label">Customer dimension</div>', unsafe_allow_html=True)
customer_view = customers.rename(columns={"customer_name": "Customer", "country": "Country", "current_plan_type": "Plan", "current_subscription_status": "Status", "current_monthly_price_usd": "Monthly price", "is_active_subscriber": "Active"})
st.dataframe(customer_view.style.format({"Monthly price": "${:,.2f}"}), use_container_width=True, hide_index=True)
