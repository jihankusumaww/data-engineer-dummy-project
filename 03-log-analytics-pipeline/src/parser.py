"""
Parser layer: mengubah satu baris raw log (unstructured text) menjadi
dictionary terstruktur. Ini pola "schema-on-read" yang umum dipakai untuk
sumber data non-tabular seperti log server, bukan cuma CSV/API yang sudah rapi.

Format log yang didukung (gaya Nginx/Apache Combined Log Format):
    IP - - [10/Jan/2024:08:15:22 +0700] "GET /api/products HTTP/1.1" 200 512 "-" "UA"
"""
import re
from datetime import datetime
from typing import Optional

LOG_PATTERN = re.compile(
    r'^(?P<ip>\S+) \S+ \S+ '
    r'\[(?P<timestamp>[^\]]+)\] '
    r'"(?P<method>[A-Z]+) (?P<path>\S+) HTTP/[\d.]+" '
    r'(?P<status>\d{3}) (?P<size>\d+|-)'
)

# Contoh timestamp: 10/Jan/2024:08:15:22 +0700
TIMESTAMP_FORMAT = "%d/%b/%Y:%H:%M:%S %z"


def _classify_status(status_code: int) -> str:
    if 200 <= status_code < 400:
        return "success"
    if 400 <= status_code < 500:
        return "client_error"
    return "server_error"


def parse_log_line(line: str) -> Optional[dict]:
    """
    Coba parse satu baris log. Return dict field terstruktur kalau berhasil,
    atau None kalau baris tidak sesuai format (rusak/korup) -- TIDAK melempar
    exception, supaya satu baris rusak tidak menghentikan seluruh pipeline.
    """
    line = line.strip()
    if not line:
        return None

    match = LOG_PATTERN.match(line)
    if not match:
        return None

    try:
        ts = datetime.strptime(match.group("timestamp"), TIMESTAMP_FORMAT)
    except ValueError:
        return None

    status = int(match.group("status"))
    size_raw = match.group("size")

    return {
        "ip_address": match.group("ip"),
        "event_timestamp": ts.isoformat(),
        "http_method": match.group("method"),
        "path": match.group("path"),
        "status_code": status,
        "response_size": int(size_raw) if size_raw != "-" else None,
        "status_class": _classify_status(status),
    }


if __name__ == "__main__":
    sample = '192.168.1.10 - - [10/Jan/2024:08:15:22 +0700] "GET /api/products HTTP/1.1" 200 512 "-" "Mozilla/5.0"'
    print(parse_log_line(sample))
    print(parse_log_line("baris rusak yang tidak sesuai format"))
