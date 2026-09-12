"""
Orkestrasi pipeline incremental: extract -> load raw -> transform incremental -> load fact.

Konsep "incremental load" yang ditunjukkan di sini:
1. Setiap run, snapshot baru di-append ke raw_price_snapshot (append-only).
2. pipeline_watermark menyimpan timestamp terakhir yang SUDAH diproses per coin.
3. Saat transform, pipeline hanya memproses baris raw yang timestamp-nya
   LEBIH BARU dari watermark -> tidak memproses ulang data lama (efisien,
   mensimulasikan pola incremental processing di data warehouse skala besar).

Cara pakai:
    python src/pipeline.py

Untuk simulasi data historis (banyak snapshot), jalankan file ini berkali-kali
dengan jeda (atau jadwalkan via cron setiap jam):
    0 * * * * cd /path/project && venv/bin/python src/pipeline.py
"""
import logging
import sqlite3
import sys
from pathlib import Path

import pandas as pd

sys.path.append(str(Path(__file__).resolve().parent))
from extract_api import fetch_price_snapshot, DEFAULT_COINS

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)
logger = logging.getLogger("pipeline")

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "crypto.db"
SCHEMA_PATH = Path(__file__).resolve().parent.parent / "sql" / "schema.sql"


def get_connection() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    with open(SCHEMA_PATH) as f:
        conn.executescript(f.read())
    return conn


def load_raw_snapshot(conn: sqlite3.Connection, rows: list[dict]) -> None:
    """Append snapshot baru ke raw table. Duplikat (coin_id+timestamp) diabaikan."""
    df = pd.DataFrame(rows)
    cur = conn.cursor()
    for _, r in df.iterrows():
        cur.execute(
            """INSERT OR IGNORE INTO raw_price_snapshot
               (coin_id, price_usd, market_cap_usd, fetched_at_utc)
               VALUES (?, ?, ?, ?)""",
            (r.coin_id, r.price_usd, r.market_cap_usd, r.fetched_at_utc),
        )
    conn.commit()
    logger.info("Raw snapshot di-load (append-only)")


def get_watermark(conn: sqlite3.Connection, coin_id: str) -> str:
    row = conn.execute(
        "SELECT last_processed_utc FROM pipeline_watermark WHERE coin_id = ?",
        (coin_id,),
    ).fetchone()
    return row[0] if row else "1970-01-01T00:00:00+00:00"


def set_watermark(conn: sqlite3.Connection, coin_id: str, ts: str) -> None:
    conn.execute(
        """INSERT INTO pipeline_watermark (coin_id, last_processed_utc)
           VALUES (?, ?)
           ON CONFLICT(coin_id) DO UPDATE SET last_processed_utc = excluded.last_processed_utc""",
        (coin_id, ts),
    )
    conn.commit()


def transform_and_load_incremental(conn: sqlite3.Connection, coins: list[str]) -> None:
    """Proses hanya data raw yang lebih baru dari watermark, hitung moving avg & pct change."""
    for coin_id in coins:
        watermark = get_watermark(conn, coin_id)

        new_raw = pd.read_sql(
            """SELECT price_usd, market_cap_usd, fetched_at_utc
               FROM raw_price_snapshot
               WHERE coin_id = ? AND fetched_at_utc > ?
               ORDER BY fetched_at_utc""",
            conn, params=(coin_id, watermark),
        )

        if new_raw.empty:
            logger.info("[%s] Tidak ada data baru untuk diproses", coin_id)
            continue

        # Ambil histori sebelumnya untuk hitung moving average yang menyambung
        history = pd.read_sql(
            """SELECT price_usd, fetched_at_utc FROM fact_price_hourly
               WHERE coin_id = ? ORDER BY fetched_at_utc DESC LIMIT 2""",
            conn, params=(coin_id,),
        )
        prices = list(history["price_usd"][::-1]) + list(new_raw["price_usd"])
        offset = len(prices) - len(new_raw)

        rows_to_insert = []
        prev_price = history["price_usd"].iloc[0] if not history.empty else None
        for i, row in new_raw.iterrows():
            window = prices[max(0, offset + i - 2): offset + i + 1]
            moving_avg_3 = sum(window) / len(window)
            pct_change = ((row.price_usd - prev_price) / prev_price * 100) if prev_price else None

            rows_to_insert.append((
                coin_id, row.price_usd, row.market_cap_usd, row.fetched_at_utc,
                moving_avg_3, pct_change,
            ))
            prev_price = row.price_usd

        conn.executemany(
            """INSERT OR REPLACE INTO fact_price_hourly
               (coin_id, price_usd, market_cap_usd, fetched_at_utc, moving_avg_3, pct_change_from_prev)
               VALUES (?, ?, ?, ?, ?, ?)""",
            rows_to_insert,
        )
        conn.commit()

        set_watermark(conn, coin_id, new_raw["fetched_at_utc"].max())
        logger.info("[%s] %d baris baru diproses (incremental)", coin_id, len(rows_to_insert))


def main():
    logger.info("=== Pipeline crypto dimulai ===")
    conn = get_connection()
    try:
        snapshot = fetch_price_snapshot(DEFAULT_COINS)
        load_raw_snapshot(conn, snapshot)
        transform_and_load_incremental(conn, DEFAULT_COINS)
    finally:
        conn.close()
    logger.info("=== Pipeline selesai. DB: %s ===", DB_PATH)


if __name__ == "__main__":
    main()
