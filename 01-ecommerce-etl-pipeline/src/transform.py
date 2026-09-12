"""
Transform layer: membersihkan data mentah + menjalankan data quality checks
sebelum dimuat ke warehouse.
"""
import logging
import pandas as pd

logger = logging.getLogger(__name__)


class DataQualityError(Exception):
    """Dilempar kalau data tidak lolos pengecekan kualitas minimum."""


def _parse_date(value: str) -> str:
    """Normalisasi tanggal dari format campuran (YYYY-MM-DD atau DD/MM/YYYY) -> YYYY-MM-DD."""
    value = value.strip()
    for fmt in ("%Y-%m-%d", "%d/%m/%Y"):
        try:
            return pd.to_datetime(value, format=fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    raise ValueError(f"Format tanggal tidak dikenali: {value}")


def clean_sales_data(df: pd.DataFrame) -> pd.DataFrame:
    """Bersihkan raw dataframe: trim string, normalisasi tanggal, drop duplikat, handle null."""
    df = df.copy()

    # 1. Isi nilai kosong/NaN dengan string kosong dulu, baru trim whitespace.
    #    (Kalau langsung .astype(str) tanpa fillna, NaN akan jadi literal "nan"
    #    alih-alih string kosong "" -- bug klasik yang gampang lolos QA.)
    text_cols = ["customer_name", "customer_email", "product_name", "category", "city"]
    for col in text_cols:
        df[col] = df[col].fillna("").astype(str).str.strip()

    # 2. Hapus baris duplikat exact (order_id sama persis)
    before = len(df)
    df = df.drop_duplicates(subset=["order_id"], keep="first")
    logger.info("Drop %d baris duplikat", before - len(df))

    # 3. Normalisasi tanggal
    df["order_date"] = df["order_date"].apply(_parse_date)

    # 4. Quantity kosong -> asumsikan 1 (default order quantity), lalu convert ke int
    df["quantity"] = df["quantity"].replace("", pd.NA).fillna("1").astype(int)

    # 5. Customer name kosong -> tandai sebagai "Unknown Customer" (bukan di-drop,
    #    supaya tidak kehilangan data transaksi)
    df["customer_name"] = df["customer_name"].replace("", "Unknown Customer")

    # 6. Convert tipe numerik
    df["unit_price"] = df["unit_price"].astype(float)
    df["order_id"] = df["order_id"].astype(int)

    # 7. Hitung total_amount
    df["total_amount"] = df["quantity"] * df["unit_price"]

    return df.reset_index(drop=True)


def run_quality_checks(df: pd.DataFrame) -> None:
    """Jalankan data quality checks sederhana. Lempar DataQualityError kalau gagal."""
    checks = {
        "tidak ada order_id null": df["order_id"].notnull().all(),
        "order_id unik": df["order_id"].is_unique,
        "quantity > 0": (df["quantity"] > 0).all(),
        "unit_price > 0": (df["unit_price"] > 0).all(),
        "tidak ada email kosong": (df["customer_email"] != "").all(),
        "tidak ada order_date kosong": df["order_date"].notnull().all(),
    }

    failed = [name for name, ok in checks.items() if not ok]
    if failed:
        raise DataQualityError(f"Data quality check gagal pada: {', '.join(failed)}")

    logger.info("Semua %d data quality checks lolos", len(checks))


if __name__ == "__main__":
    import logging as _logging
    from extract import extract_sales_data

    _logging.basicConfig(level=_logging.INFO)
    raw = extract_sales_data()
    clean = clean_sales_data(raw)
    run_quality_checks(clean)
    print(clean.head())
