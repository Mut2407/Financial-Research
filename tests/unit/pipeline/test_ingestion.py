import json
from pathlib import Path

import pandas as pd
import pytest

from src.pipeline.ingestion import classify_source_error, ingest_tickers, normalize_history


pytestmark = pytest.mark.unit


class RecordingSource:
    provider_name = "TEST"

    def __init__(self, frame: pd.DataFrame | None = None, error: Exception | None = None):
        self.frame = frame
        self.error = error
        self.calls: list[tuple[str, str, str, str]] = []

    def history(self, ticker: str, start: str, end: str, interval: str):
        self.calls.append((ticker, start, end, interval))
        if self.error:
            raise self.error
        return self.frame.copy(), 1


def test_normalize_history_maps_columns_and_uppercases_ticker(ohlcv_frame: pd.DataFrame):
    records = normalize_history("fpt", ohlcv_frame.head(1))

    assert len(records) == 1
    assert records[0].ticker == "FPT"
    assert records[0].close_price == 11


def test_normalize_history_rejects_missing_required_column(ohlcv_frame: pd.DataFrame):
    with pytest.raises(ValueError, match="missing source columns"):
        normalize_history("FPT", ohlcv_frame.drop(columns="volume"))


@pytest.mark.parametrize(
    ("error", "expected"),
    [
        (RuntimeError("rate limit exceeded"), "RATE_LIMIT"),
        (RuntimeError("no data returned"), "NO_DATA"),
        (RuntimeError("invalid symbol"), "INVALID_TICKER"),
        (ValueError("BAD_DATA: missing source columns"), "BAD_DATA"),
        (RuntimeError("connection reset"), "SOURCE_ERROR"),
    ],
)
def test_source_errors_are_normalized(error: Exception, expected: str):
    assert classify_source_error(error) == expected


def test_ingestion_writes_partitioned_atomic_raw_payload(
    settings_factory, ohlcv_frame: pd.DataFrame
):
    config = settings_factory()
    source = RecordingSource(ohlcv_frame)

    result = ingest_tickers(
        ["fpt", "FPT"], "2025-01-01", "2025-01-31", source=source, config=config
    )

    raw_path = Path(result["raw_path"])
    assert result["requested"] == 1
    assert result["passed"] == 1
    assert result["failed"] == 0
    assert source.calls == [("FPT", "2025-01-01", "2025-01-31", "1D")]
    assert raw_path.name.startswith("batch_") and raw_path.suffix == ".json"
    assert {part.split("=")[0] for part in raw_path.parts if "=" in part} >= {"year", "month", "day"}
    assert not list(config.raw_path.rglob("*.tmp"))

    payload = json.loads(raw_path.read_text(encoding="utf-8"))
    assert payload[0]["metadata"]["provider"] == "TEST"
    assert payload[0]["metadata"]["rows"] == 25
    assert payload[0]["records"][0]["ticker"] == "FPT"


def test_ingestion_records_failure_without_invalid_records(settings_factory):
    config = settings_factory()
    source = RecordingSource(error=RuntimeError("rate limit exceeded"))

    result = ingest_tickers(
        ["FPT"], "2025-01-01", "2025-01-31", source=source, config=config
    )
    payload = json.loads(Path(result["raw_path"]).read_text(encoding="utf-8"))

    assert result["passed"] == 0
    assert result["failed"] == 1
    assert payload[0]["metadata"]["status"] == "FAIL"
    assert payload[0]["metadata"]["error_code"] == "RATE_LIMIT"
    assert payload[0]["records"] == []


@pytest.mark.parametrize("tickers", [[], ["../../secret"], ["FPT;DROP TABLE prices"]])
def test_ingestion_rejects_empty_or_unsafe_ticker_before_source_call(
    settings_factory, ohlcv_frame: pd.DataFrame, tickers: list[str]
):
    source = RecordingSource(ohlcv_frame)

    with pytest.raises(ValueError):
        ingest_tickers(tickers, "2025-01-01", "2025-01-31", source=source, config=settings_factory())

    assert source.calls == []
