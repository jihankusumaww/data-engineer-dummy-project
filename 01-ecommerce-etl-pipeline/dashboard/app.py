import sqlite3
import sys
from pathlib import Path

import pandas as pd
import streamlit as st

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "warehouse.db"
SRC_PATH = Path(__file__).resolve().parent.parent / "src"

st.set_page_config(
    page_title="Commerce Desk | Sales Warehouse",
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
    [data-testid="stSidebar"] { background: #10191e; border-right: 1px solid var(--line); }
    [data-testid="stSidebar"] * { font-family: 'Space Grotesk', sans-serif; }
    .block-container { max-width: 1400px; padding-top: 3rem; }
    h1, h2, h3, p, label { font-family: 'Space Grotesk', sans-serif; }
    h1 { color: var(--ink); font-size: clamp(2rem, 4vw, 3.7rem); line-height: 1; }
    h2 { color: var(--ink); }
    .eyebrow, .section-label {
        color: var(--cyan); font-family: 'DM Mono', monospace; font-size: .72rem;
        letter-spacing: .12em; text-transform: uppercase;
    }
    .eyebrow { margin-bottom: .6rem; }
    .subtitle { color: var(--muted); font-size: 1rem; margin-top: -.9rem; }
    .section-label { margin: 1.8rem 0 .75rem; }
    .hero-note {
        background: #123d3a; border: 1px solid #28756b; border-radius: 8px; color: #d8fff4; padding: 1rem 1.2rem;
        font-family: 'DM Mono', monospace; font-size: .75rem; line-height: 1.6;
        box-shadow: 0 12px 22px rgba(23, 107, 91, .16);
    }
    .metric-card, .panel {
        background: linear-gradient(145deg, rgba(29, 45, 53, .98), rgba(19, 31, 38, .98)); border: 1px solid var(--line);
        border-radius: 8px; box-shadow: 0 10px 24px rgba(39, 64, 57, .07);
    }
    .metric-card { min-height: 116px; padding: 1.1rem 1.2rem; }
    .metric-label { color: var(--muted); font-size: .78rem; }
    .metric-value { color: var(--ink); font-family: 'DM Mono', monospace; font-size: 1.45rem; margin-top: .5rem; }
    .metric-note { color: var(--muted); font-size: .72rem; margin-top: .3rem; }
    .panel { padding: 1rem 1.1rem .8rem; }
    .panel-title { color: var(--ink); font-size: 1.05rem; font-weight: 600; margin-bottom: .2rem; }
    .panel-note { color: var(--muted); font-size: .76rem; margin-bottom: .7rem; }
    .rank-row { align-items: center; border-bottom: 1px solid var(--line); display: flex; gap: .75rem; padding: .7rem 0; }
    .rank-row:last-child { border-bottom: 0; }
    .rank-number { color: var(--red); font-family: 'DM Mono', monospace; font-size: .78rem; width: 1.5rem; }
    .rank-name { color: var(--ink); flex: 1; font-size: .86rem; }
    .rank-value { color: var(--cyan); font-family: 'DM Mono', monospace; font-size: .8rem; }
    .dataframe { border: 1px solid var(--line); }
    </style>
    """,
    unsafe_allow_html=True,
)


def ensure_warehouse() -> None:
    """Build the local warehouse on first launch, including Streamlit Cloud."""
    if DB_PATH.exists():
        return

    sys.path.insert(0, str(SRC_PATH))
    from extract import extract_sales_data
    from load import load_to_warehouse
    from transform import clean_sales_data, run_quality_checks

    raw_df = extract_sales_data()
    clean_df = clean_sales_data(raw_df)
    run_quality_checks(clean_df)
    load_to_warehouse(clean_df)


try:
    ensure_warehouse()
except Exception as error:
    st.error(f"Warehouse gagal dibuat: {error}")
    st.stop()

st.markdown('<div class="eyebrow">Sales intelligence / warehouse overview</div>', unsafe_allow_html=True)
st.title("Commerce Desk")
st.markdown('<p class="subtitle">A compact view of revenue performance, product demand, and customer value.</p>', unsafe_allow_html=True)

conn = sqlite3.connect(DB_PATH)

revenue_by_category = pd.read_sql("""
    SELECT p.category, SUM(f.total_amount) AS revenue, COUNT(f.order_id) AS total_orders
    FROM fact_sales f JOIN dim_product p ON f.product_id = p.product_id
    GROUP BY p.category ORDER BY revenue DESC
""", conn)

top_customers = pd.read_sql("""
    SELECT c.customer_name, c.city, SUM(f.total_amount) AS total_spent, COUNT(f.order_id) AS total_orders
    FROM fact_sales f JOIN dim_customer c ON f.customer_id = c.customer_id
    GROUP BY c.customer_id ORDER BY total_spent DESC LIMIT 10
""", conn)

daily_revenue = pd.read_sql("""
    SELECT d.full_date, SUM(f.total_amount) AS daily_revenue
    FROM fact_sales f JOIN dim_date d ON f.date_id = d.date_id
    GROUP BY d.full_date ORDER BY d.full_date
""", conn)

top_products = pd.read_sql("""
    SELECT p.product_name, SUM(f.quantity) AS total_qty_sold, SUM(f.total_amount) AS revenue
    FROM fact_sales f JOIN dim_product p ON f.product_id = p.product_id
    GROUP BY p.product_name ORDER BY total_qty_sold DESC
""", conn)

conn.close()

total_revenue = revenue_by_category["revenue"].sum()
total_orders = revenue_by_category["total_orders"].sum()
avg_order_value = total_revenue / total_orders if total_orders else 0
total_units = top_products["total_qty_sold"].sum()
best_category = revenue_by_category.iloc[0]["category"] if not revenue_by_category.empty else "N/A"
date_start = daily_revenue["full_date"].min() if not daily_revenue.empty else "N/A"
date_end = daily_revenue["full_date"].max() if not daily_revenue.empty else "N/A"

with st.sidebar:
    st.markdown("## Commerce Desk")
    st.markdown('<div class="section-label">Warehouse scope</div>', unsafe_allow_html=True)
    st.success(f"{total_orders:,} orders loaded")
    st.caption(f"Period: {date_start} to {date_end}")
    st.markdown("---")
    st.caption("Data dari fact_sales dan dimensi star schema hasil ETL.")

st.markdown('<div class="section-label">Performance pulse</div>', unsafe_allow_html=True)
col1, col2, col3, col4 = st.columns(4)
metrics = [
    ("Total revenue", f"Rp {total_revenue:,.0f}", "Gross sales in warehouse"),
    ("Total orders", f"{total_orders:,}", "Validated transactions"),
    ("Average order value", f"Rp {avg_order_value:,.0f}", "Revenue / order"),
    ("Units sold", f"{total_units:,}", f"Top category: {best_category}"),
]
for column, (label, value, note) in zip((col1, col2, col3, col4), metrics):
    with column:
        st.markdown(
            f'<div class="metric-card"><div class="metric-label">{label}</div>'
            f'<div class="metric-value">{value}</div><div class="metric-note">{note}</div></div>',
            unsafe_allow_html=True,
        )

st.markdown('<div class="section-label">Revenue rhythm</div>', unsafe_allow_html=True)
trend_col, note_col = st.columns([2.3, 1])
with trend_col:
    st.markdown('<div class="panel"><div class="panel-title">Daily revenue trend</div><div class="panel-note">How sales moved across the loaded date range</div>', unsafe_allow_html=True)
    trend = daily_revenue.set_index("full_date")["daily_revenue"].rename("Revenue")
    st.area_chart(trend, color="#176b5b", height=300)
    st.markdown('</div>', unsafe_allow_html=True)
with note_col:
    st.markdown(
        f'<div class="hero-note">WAREHOUSE SIGNAL<br><br>'
        f'{best_category} leads the category mix.<br><br>'
        f'{len(top_products):,} products and {len(top_customers):,} priority customers are available in this view.</div>',
        unsafe_allow_html=True,
    )

st.markdown('<div class="section-label">Merchandising view</div>', unsafe_allow_html=True)
col_left, col_right = st.columns(2)

with col_left:
    st.markdown('<div class="panel"><div class="panel-title">Revenue by category</div><div class="panel-note">Where customers are spending</div>', unsafe_allow_html=True)
    st.bar_chart(revenue_by_category.set_index("category")["revenue"], color="#e67c61", height=270)
    category_table = revenue_by_category.rename(columns={"category": "Category", "revenue": "Revenue", "total_orders": "Orders"})
    st.dataframe(category_table.style.format({"Revenue": "Rp {:,.0f}", "Orders": "{:,.0f}"}), use_container_width=True, hide_index=True)
    st.markdown('</div>', unsafe_allow_html=True)

with col_right:
    st.markdown('<div class="panel"><div class="panel-title">Product demand</div><div class="panel-note">Top products ranked by units sold</div>', unsafe_allow_html=True)
    top_five = top_products.head(5)
    for index, row in top_five.iterrows():
        st.markdown(
            f'<div class="rank-row"><span class="rank-number">{top_five.index.get_loc(index) + 1:02d}</span>'
            f'<span class="rank-name">{row["product_name"]}</span>'
            f'<span class="rank-value">{row["total_qty_sold"]:,.0f} units</span></div>',
            unsafe_allow_html=True,
        )
    st.markdown('</div>', unsafe_allow_html=True)

st.markdown('<div class="section-label">Customer value</div>', unsafe_allow_html=True)
customer_table = top_customers.rename(columns={
    "customer_name": "Customer", "city": "City", "total_spent": "Total spent", "total_orders": "Orders",
})
st.dataframe(
    customer_table.style.format({"Total spent": "Rp {:,.0f}", "Orders": "{:,.0f}"}),
    use_container_width=True,
    hide_index=True,
)
