from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
from pydantic import ValidationError

from src.pipeline.models import IngestionMetadata, OhlcvRecord, RawTickerPayload
from src.pipeline.source import MarketDataSource, build_market_data_source
from src.settings import Settings, get_settings


SOURCE_COLUMNS = ["time", "open", "high", "low", "close", "volume"]


def classify_source_error(error: Exception) -> str:
    message = str(error).lower()
    if any(token in message for token in ("rate limit", "ratelimit", "giới hạn api")):
        return "RATE_LIMIT"
    if any(token in message for token in ("no data", "emptydata", "no rows")):
        return "NO_DATA"
    if any(token in message for token in ("invalid", "not found", "symbol")):
        return "INVALID_TICKER"
    if isinstance(error, ValidationError) or "bad_data" in message:
        return "BAD_DATA"
    return "SOURCE_ERROR"


def normalize_history(ticker: str, frame: pd.DataFrame) -> list[OhlcvRecord]:
    missing = [column for column in SOURCE_COLUMNS if column not in frame.columns]
    if missing:
        raise ValueError(f"BAD_DATA: missing source columns {missing}")

    normalized = frame[SOURCE_COLUMNS].rename(
        columns={
            "time": "trading_date",
            "open": "open_price",
            "high": "high_price",
            "low": "low_price",
            "close": "close_price",
        }
    ).copy()
    normalized.insert(0, "ticker", ticker.upper())
    return [OhlcvRecord.model_validate(row) for row in normalized.to_dict(orient="records")]


def _safe_ticker(value: str) -> str:
    ticker = value.strip().upper()
    if not re.fullmatch(r"[A-Z0-9._-]{1,20}", ticker):
        raise ValueError(f"Invalid ticker: {value!r}")
    return ticker


def ingest_tickers(
    tickers: list[str],
    start: str,
    end: str,
    interval: str = "1D",
    *,
    source: MarketDataSource | None = None,
    config: Settings | None = None,
) -> dict:
    config = config or get_settings()
    source = source or build_market_data_source(config)
    clean_tickers = list(dict.fromkeys(_safe_ticker(ticker) for ticker in tickers))
    if not clean_tickers:
        raise ValueError("At least one ticker is required")

    payloads: list[RawTickerPayload] = []
    for ticker in clean_tickers:
        requested_at = datetime.now(timezone.utc)
        attempts = 1
        try:
            frame, attempts = source.history(ticker, start, end, interval)
            if frame is None or frame.empty:
                raise ValueError("NO_DATA: provider returned no rows")
            records = normalize_history(ticker, frame)
            metadata = IngestionMetadata(
                provider=source.provider_name,
                ticker=ticker,
                status="PASS",
                error_code="OK",
                rows=len(records),
                attempts=attempts,
                requested_at=requested_at,
                completed_at=datetime.now(timezone.utc),
            )
        except Exception as error:
            metadata = IngestionMetadata(
                provider=source.provider_name,
                ticker=ticker,
                status="FAIL",
                error_code=classify_source_error(error),
                rows=0,
                attempts=attempts,
                requested_at=requested_at,
                completed_at=datetime.now(timezone.utc),
            )
            records = []
        payloads.append(RawTickerPayload(metadata=metadata, records=records))

    partition_date = datetime.now().astimezone().date()
    output_dir = (
        config.raw_path
        / f"year={partition_date:%Y}"
        / f"month={partition_date:%m}"
        / f"day={partition_date:%d}"
    )
    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    output_path = output_dir / f"batch_{timestamp}.json"
    temporary_path = output_path.with_suffix(".json.tmp")
    temporary_path.write_text(
        json.dumps([payload.model_dump(mode="json") for payload in payloads], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    temporary_path.replace(output_path)

    return {
        "raw_path": str(output_path),
        "requested": len(clean_tickers),
        "passed": sum(payload.metadata.status == "PASS" for payload in payloads),
        "failed": sum(payload.metadata.status == "FAIL" for payload in payloads),
        "details": [payload.metadata.model_dump(mode="json") for payload in payloads],
    }
