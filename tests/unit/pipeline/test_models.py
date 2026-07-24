from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from src.pipeline.models import IngestionMetadata, OhlcvRecord


pytestmark = pytest.mark.unit


def test_ohlcv_record_accepts_contract_compliant_values():
    record = OhlcvRecord(
        ticker="FPT",
        trading_date=datetime(2025, 1, 2, tzinfo=timezone.utc),
        open_price=10,
        high_price=12,
        low_price=9,
        close_price=11,
        volume=0,
    )

    assert record.ticker == "FPT"
    assert record.volume == 0


@pytest.mark.parametrize("field", ["open_price", "high_price", "low_price", "close_price"])
def test_ohlcv_record_rejects_non_positive_prices(field: str):
    values = {
        "ticker": "FPT",
        "trading_date": "2025-01-02T00:00:00Z",
        "open_price": 10,
        "high_price": 12,
        "low_price": 9,
        "close_price": 11,
        "volume": 100,
    }
    values[field] = 0

    with pytest.raises(ValidationError):
        OhlcvRecord.model_validate(values)


def test_ohlcv_record_rejects_negative_volume():
    with pytest.raises(ValidationError, match="greater than or equal to 0"):
        OhlcvRecord(
            ticker="FPT",
            trading_date="2025-01-02T00:00:00Z",
            open_price=10,
            high_price=12,
            low_price=9,
            close_price=11,
            volume=-1,
        )


def test_ohlcv_record_rejects_invalid_price_range():
    with pytest.raises(ValidationError, match="high_price must be greater"):
        OhlcvRecord(
            ticker="FPT",
            trading_date="2025-01-02T00:00:00Z",
            open_price=10,
            high_price=8,
            low_price=9,
            close_price=11,
            volume=100,
        )


def test_ingestion_metadata_requires_at_least_one_attempt():
    with pytest.raises(ValidationError):
        IngestionMetadata(
            provider="VNSTOCK_FREE",
            ticker="FPT",
            status="FAIL",
            error_code="SOURCE_ERROR",
            rows=0,
            attempts=0,
        )
