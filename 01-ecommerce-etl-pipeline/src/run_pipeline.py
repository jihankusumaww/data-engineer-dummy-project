
import logging
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent))

from extract import extract_sales_data
from transform import clean_sales_data, run_quality_checks, DataQualityError
from load import load_to_warehouse, DB_PATH

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger("pipeline")


def main() -> None:
    logger.info("=== Pipeline dimulai ===")
    try:
        raw_df = extract_sales_data()
        clean_df = clean_sales_data(raw_df)
        run_quality_checks(clean_df)
        load_to_warehouse(clean_df)
    except DataQualityError as e:
        logger.error("Pipeline dihentikan karena data quality check gagal: %s", e)
        sys.exit(1)
    except Exception:
        logger.exception("Pipeline gagal karena error tak terduga")
        sys.exit(1)
    else:
        logger.info("=== Pipeline selesai. Warehouse tersedia di: %s ===", DB_PATH)


if __name__ == "__main__":
    main()
