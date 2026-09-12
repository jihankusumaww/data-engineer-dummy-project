
import logging
from pathlib import Path
import pandas as pd

logger = logging.getLogger(__name__)

RAW_DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "raw" / "sales_raw.csv"


def extract_sales_data(path: Path = RAW_DATA_PATH) -> pd.DataFrame:
    """Baca file CSV mentah dan kembalikan sebagai DataFrame."""
    logger.info("Extracting data from %s", path)
    if not path.exists():
        raise FileNotFoundError(f"File sumber tidak ditemukan: {path}")

    df = pd.read_csv(path, dtype=str)  # baca semua sebagai string dulu, biar transform yang bersihin
    logger.info("Berhasil extract %d baris", len(df))
    return df


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    data = extract_sales_data()
    print(data.head())
