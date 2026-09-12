"""
Extract layer: mengambil harga crypto terkini dari API publik CoinGecko
(gratis, tanpa API key untuk endpoint simple/price).

Setiap kali dijalankan, fungsi ini mengambil satu "snapshot" harga dan
menyimpannya sebagai raw data (append-only) — pola umum untuk sumber data
yang sifatnya time-series / streaming-like tapi diambil secara batch (polling).
"""
import logging
from datetime import datetime, timezone

import requests

logger = logging.getLogger(__name__)

API_URL = "https://api.coingecko.com/api/v3/simple/price"
DEFAULT_COINS = ["bitcoin", "ethereum", "solana"]


def fetch_price_snapshot(coins: list[str] = None) -> list[dict]:
    """
    Ambil harga terkini untuk daftar coin dari CoinGecko.
    Return list of dict, masing-masing adalah satu baris raw snapshot.
    """
    coins = coins or DEFAULT_COINS
    params = {
        "ids": ",".join(coins),
        "vs_currencies": "usd",
        "include_market_cap": "true",
    }

    logger.info("Fetching harga untuk: %s", coins)
    response = requests.get(API_URL, params=params, timeout=10)
    response.raise_for_status()
    data = response.json()

    fetched_at = datetime.now(timezone.utc).isoformat()
    rows = []
    for coin_id, values in data.items():
        rows.append({
            "coin_id": coin_id,
            "price_usd": values.get("usd"),
            "market_cap_usd": values.get("usd_market_cap"),
            "fetched_at_utc": fetched_at,
        })

    logger.info("Berhasil fetch %d snapshot harga", len(rows))
    return rows


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    print(fetch_price_snapshot())
