import json
from pathlib import Path

import pandas as pd
import pytest

from src.pipeline.transform import transform_raw_data


pytestmark = pytest.mark.unit


def _entry(ticker: str, close: float, *, status: str = "PASS") -> dict:
    return {
        "metadata": {
            "provider": "TEST",
            "ticker": ticker,
            "status": status,
            "error_code": "OK" if status == "PASS" else "SOURCE_ERROR",
            "rows": 1 if status == "PASS" else 0,
            "attempts": 1,
        },
        "records": []
        if status != "PASS"
        else [
            {
                "ticker": ticker,
                "trading_date": "2025-01-02T00:00:00Z",
                "open_price": 10,
                "high_price": max(12, close),
                "low_price": 9,
                "close_price": close,
                "volume": 1000,
            }
        ],
    }


def _write_raw(path: Path, entries: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(entries), encoding="utf-8")


def test_transform_skips_failed_payloads_and_keeps_latest_duplicate(settings_factory):
    config = settings_factory()
    _write_raw(config.raw_path / "a.json", [_entry("FPT", 11), _entry("VCB", 20, status="FAIL")])
    _write_raw(config.raw_path / "b.json", [_entry("FPT", 12)])

    result = transform_raw_data(config=config)
    curated = pd.read_parquet(config.curated_path / "ticker=FPT" / "part-000.parquet")

    assert result["input_files"] == 2
    assert result["rows"] == 1
    assert result["tickers"] == 1
    assert curated.iloc[0]["close_price"] == 12
    assert not (config.curated_path / "ticker=VCB").exists()


def test_transform_calculates_canonical_indicators(settings_factory, ohlcv_frame: pd.DataFrame):
    config = settings_factory()
    records = []
    for row in ohlcv_frame.to_dict(orient="records"):
        records.append(
            {
                "ticker": "FPT",
                "trading_date": row["time"].isoformat(),
                "open_price": row["open"],
                "high_price": row["high"],
                "low_price": row["low"],
                "close_price": row["close"],
                "volume": row["volume"],
            }
        )
    entry = _entry("FPT", 11)
    entry["metadata"]["rows"] = len(records)
    entry["records"] = records
    _write_raw(config.raw_path / "batch.json", [entry])

    result = transform_raw_data(config=config)
    curated = pd.read_parquet(config.curated_path / "ticker=FPT" / "part-000.parquet")

    assert result["rows"] == 25
    assert list(curated.columns) == [
        "trading_date",
        "open_price",
        "high_price",
        "low_price",
        "close_price",
        "volume",
        "return_pct",
        "ma20",
        "rsi_14",
    ]
    assert curated.iloc[-1]["ma20"] == pytest.approx(sum(range(16, 36)) / 20)
    assert curated.iloc[-1]["rsi_14"] == 100


def test_transform_fails_when_no_valid_raw_records(settings_factory):
    config = settings_factory()
    _write_raw(config.raw_path / "failed.json", [_entry("FPT", 11, status="FAIL")])

    with pytest.raises(FileNotFoundError, match="No valid raw OHLCV"):
        transform_raw_data(config=config)
