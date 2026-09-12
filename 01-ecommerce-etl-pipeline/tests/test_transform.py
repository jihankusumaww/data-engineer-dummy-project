"""
Unit test sederhana untuk transform layer.
Jalankan dengan: pytest tests/
"""
import sys
from pathlib import Path

import pandas as pd
import pytest

sys.path.append(str(Path(__file__).resolve().parent.parent / "src"))

from transform import clean_sales_data, run_quality_checks, DataQualityError


@pytest.fixture
def sample_raw_df():
    return pd.DataFrame({
        "order_id": ["1", "2", "2"],  # ada duplikat
        "order_date": ["2024-01-01", "02/01/2024", "02/01/2024"],
        "customer_name": [" Budi ", "", "Ani"],
        "customer_email": ["budi@mail.com", "x@mail.com", "x@mail.com"],
        "product_name": ["Kaos", " Kaos ", "Kaos"],
        "category": ["Fashion", "Fashion", "Fashion"],
        "quantity": ["2", "", "1"],
        "unit_price": ["75000", "75000", "75000"],
        "city": ["Jakarta", "Bandung", "Bandung"],
    })


def test_clean_removes_duplicates(sample_raw_df):
    result = clean_sales_data(sample_raw_df)
    assert result["order_id"].is_unique


def test_clean_fills_missing_quantity(sample_raw_df):
    result = clean_sales_data(sample_raw_df)
    assert (result["quantity"] > 0).all()


def test_clean_normalizes_dates(sample_raw_df):
    result = clean_sales_data(sample_raw_df)
    assert all(len(d) == 10 and d[4] == "-" for d in result["order_date"])


def test_clean_handles_missing_name(sample_raw_df):
    result = clean_sales_data(sample_raw_df)
    assert "Unknown Customer" in result["customer_name"].values


def test_quality_check_passes_on_clean_data(sample_raw_df):
    result = clean_sales_data(sample_raw_df)
    run_quality_checks(result)  # tidak boleh raise


def test_quality_check_fails_on_bad_data():
    bad_df = pd.DataFrame({
        "order_id": [1],
        "date_id": ["2024-01-01"],
        "quantity": [0],  # invalid: harus > 0
        "unit_price": [1000],
        "customer_email": ["a@mail.com"],
        "order_date": ["2024-01-01"],
    })
    with pytest.raises(DataQualityError):
        run_quality_checks(bad_df)
