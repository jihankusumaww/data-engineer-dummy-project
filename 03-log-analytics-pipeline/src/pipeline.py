"""
Entry point pipeline log analytics: baca file log mentah -> parse tiap baris
-> load ke SQLite (event valid + error log + run summary).

Berbeda dengan pipeline CSV/API biasa, di sini kualitas data ditangani dengan
pendekatan "tolerant parsing": baris yang gagal di-parse TIDAK menghentikan
pipeline, tapi dicatat di parse_error_log supaya bisa diaudit -- karena log
server dari sumber luar sering punya baris korup/format tidak konsisten,
dan tidak realistis kalau satu baris rusak bikin seluruh pipeline gagal.

Cara pakai:
    python src/pipeline.py                          # pakai data/raw/access.log
    python src/pipeline.py path/ke/log_lain.log      # pakai file lain
"""
import logging
import sqlite3
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent))
from parser import parse_log_line

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)
logger = logging.getLogger("pipeline")

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "logs.db"
SCHEMA_PATH = Path(__file__).resolve().parent.parent / "sql" / "schema.sql"
DEFAULT_LOG_PATH = Path(__file__).resolve().parent.parent / "data" / "raw" / "access.log"


def get_connection(db_path: Path = DB_PATH, fresh_schema: bool = True) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    if fresh_schema:
        with open(SCHEMA_PATH) as f:
            conn.executescript(f.read())
    return conn


def process_log_file(conn: sqlite3.Connection, log_path: Path) -> dict:
    """Parse seluruh file log dan load hasilnya ke database. Return ringkasan run."""
    run_id = str(uuid.uuid4())[:8]
    lines = log_path.read_text(encoding="utf-8", errors="replace").splitlines()

    parsed_ok, parse_failed = 0, 0
    events, errors = [], []

    for line in lines:
        if not line.strip():
            continue
        result = parse_log_line(line)
        if result is None:
            parse_failed += 1
            errors.append((line, run_id))
        else:
            parsed_ok += 1
            events.append((
                result["ip_address"], result["event_timestamp"], result["http_method"],
                result["path"], result["status_code"], result["response_size"], result["status_class"],
            ))

    if events:
        conn.executemany(
            """INSERT INTO fact_log_event
               (ip_address, event_timestamp, http_method, path, status_code, response_size, status_class)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            events,
        )
    if errors:
        conn.executemany(
            "INSERT INTO parse_error_log (raw_line, run_id) VALUES (?, ?)",
            errors,
        )

    total = parsed_ok + parse_failed
    success_rate = (parsed_ok / total * 100) if total else 0.0

    conn.execute(
        """INSERT INTO pipeline_run_summary
           (run_id, source_file, total_lines, parsed_ok, parse_failed, parse_success_rate, run_at_utc)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (run_id, str(log_path.name), total, parsed_ok, parse_failed, success_rate,
         datetime.now(timezone.utc).isoformat()),
    )
    conn.commit()

    summary = {
        "run_id": run_id, "total_lines": total, "parsed_ok": parsed_ok,
        "parse_failed": parse_failed, "parse_success_rate": success_rate,
    }
    logger.info(
        "Run %s selesai: %d/%d baris berhasil di-parse (%.1f%%), %d gagal",
        run_id, parsed_ok, total, success_rate, parse_failed,
    )
    return summary


def main():
    log_path = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_LOG_PATH
    logger.info("=== Pipeline log analytics dimulai: %s ===", log_path)

    if not log_path.exists():
        logger.error("File log tidak ditemukan: %s", log_path)
        sys.exit(1)

    conn = get_connection()
    try:
        process_log_file(conn, log_path)
    finally:
        conn.close()
    logger.info("=== Pipeline selesai. DB: %s ===", DB_PATH)


if __name__ == "__main__":
    main()
