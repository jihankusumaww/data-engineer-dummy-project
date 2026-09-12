import sys
import importlib
from pathlib import Path

SRC_DIR = Path(__file__).resolve().parent.parent / "src"
sys.path.insert(0, str(SRC_DIR))
parser = importlib.import_module("parser")
parse_log_line = parser.parse_log_line
_classify_status = parser._classify_status


def test_parse_valid_line():
    line = '192.168.1.10 - - [10/Jan/2024:08:15:22 +0700] "GET /api/products HTTP/1.1" 200 512 "-" "Mozilla/5.0"'
    result = parse_log_line(line)
    assert result is not None
    assert result["ip_address"] == "192.168.1.10"
    assert result["http_method"] == "GET"
    assert result["path"] == "/api/products"
    assert result["status_code"] == 200
    assert result["response_size"] == 512
    assert result["status_class"] == "success"


def test_parse_malformed_line_returns_none():
    assert parse_log_line("baris rusak yang tidak sesuai format") is None


def test_parse_empty_line_returns_none():
    assert parse_log_line("") is None
    assert parse_log_line("   ") is None


def test_parse_handles_dash_size():
    line = '10.0.0.1 - - [10/Jan/2024:08:15:22 +0700] "GET /health HTTP/1.1" 200 - "-" "curl/8.0"'
    result = parse_log_line(line)
    assert result is not None
    assert result["response_size"] is None


def test_classify_status():
    assert _classify_status(200) == "success"
    assert _classify_status(301) == "success"
    assert _classify_status(404) == "client_error"
    assert _classify_status(500) == "server_error"
