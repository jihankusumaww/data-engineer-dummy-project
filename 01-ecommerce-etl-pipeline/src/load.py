
import logging
import sqlite3
from pathlib import Path
import pandas as pd

logger = logging.getLogger(__name__)

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "warehouse.db"
SCHEMA_PATH = Path(__file__).resolve().parent.parent / "sql" / "schema.sql"


def init_schema(conn: sqlite3.Connection) -> None:
    with open(SCHEMA_PATH, "r") as f:
        conn.executescript(f.read())
    logger.info("Schema (dim & fact tables) berhasil dibuat")


def _upsert_dim_customer(conn: sqlite3.Connection, df: pd.DataFrame) -> dict:
    customers = df[["customer_name", "customer_email", "city"]].drop_duplicates(subset=["customer_email"])
    customers.to_sql("dim_customer", conn, if_exists="append", index=False)
    mapping = pd.read_sql("SELECT customer_id, customer_email FROM dim_customer", conn)
    return dict(zip(mapping["customer_email"], mapping["customer_id"]))


def _upsert_dim_product(conn: sqlite3.Connection, df: pd.DataFrame) -> dict:
    products = df[["product_name", "category", "unit_price"]].drop_duplicates(subset=["product_name", "unit_price"])
    products.to_sql("dim_product", conn, if_exists="append", index=False)
    mapping = pd.read_sql("SELECT product_id, product_name, unit_price FROM dim_product", conn)
    return {(r.product_name, r.unit_price): r.product_id for r in mapping.itertuples()}


def _upsert_dim_date(conn: sqlite3.Connection, df: pd.DataFrame) -> dict:
    dates = pd.to_datetime(df["order_date"].unique())
    date_df = pd.DataFrame({
        "date_id": dates.strftime("%Y%m%d").astype(int),
        "full_date": dates.strftime("%Y-%m-%d"),
        "year": dates.year,
        "month": dates.month,
        "day": dates.day,
        "day_of_week": dates.day_name(),
    })
    date_df.to_sql("dim_date", conn, if_exists="append", index=False)
    return dict(zip(date_df["full_date"], date_df["date_id"]))


def load_to_warehouse(df: pd.DataFrame, db_path: Path = DB_PATH) -> None:
    """Load dataframe bersih ke warehouse SQLite dengan skema star schema."""
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    try:
        init_schema(conn)

        customer_map = _upsert_dim_customer(conn, df)
        product_map = _upsert_dim_product(conn, df)
        date_map = _upsert_dim_date(conn, df)

        fact = pd.DataFrame({
            "order_id": df["order_id"],
            "date_id": df["order_date"].map(date_map),
            "customer_id": df["customer_email"].map(customer_map),
            "quantity": df["quantity"],
            "unit_price": df["unit_price"],
            "total_amount": df["total_amount"],
        })
        # product_id perlu tuple key (nama + harga), jadi di-map manual per baris
        fact["product_id"] = [
            product_map[(name, price)] for name, price in zip(df["product_name"], df["unit_price"])
        ]

        fact.to_sql("fact_sales", conn, if_exists="append", index=False)
        conn.commit()
        logger.info("Berhasil load %d baris ke fact_sales", len(fact))
    finally:
        conn.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    from extract import extract_sales_data
    from transform import clean_sales_data, run_quality_checks

    raw = extract_sales_data()
    clean = clean_sales_data(raw)
    run_quality_checks(clean)
    load_to_warehouse(clean)
