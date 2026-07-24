from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Optional
from zoneinfo import ZoneInfo

import pandas as pd
from pydantic import BaseModel, Field, ValidationError, model_validator
from vnstock.api.quote import Quote


VN_TZ = ZoneInfo("Asia/Ho_Chi_Minh")
DEFAULT_START_DATE = "2025-01-01"
DEFAULT_END_DATE = "2025-12-31"
DEFAULT_INTERVAL = "1D"
REQUIRED_SOURCE_COLUMNS = ["time", "open", "high", "low", "close", "volume"]
NORMALIZED_COLUMNS = [
    "ticker",
    "trading_date",
    "open_price",
    "high_price",
    "low_price",
    "close_price",
    "volume",
]


class IngestionMetadata(BaseModel):
    version: str = Field("1.0")
    provider: str = Field(...)
    source: str = Field(...)
    ticker: str = Field(...)
    status: str = Field(...)
    error_code: str = Field(...)
    rows: int = Field(..., ge=0)
    attempts: int = Field(..., ge=1)
    requested_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class DailyStockPrice(BaseModel):
    ticker: str = Field(..., min_length=1)
    trading_date: datetime = Field(...)
    open_price: float = Field(..., gt=0)
    high_price: float = Field(..., gt=0)
    low_price: float = Field(..., gt=0)
    close_price: float = Field(..., gt=0)
    volume: int = Field(..., ge=0)

    @model_validator(mode="after")
    def validate_price_logic(self):
        if self.high_price < self.low_price:
            raise ValueError("high_price phải lớn hơn hoặc bằng low_price")
        return self


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def vn_now_date() -> datetime.date:
    return datetime.now(VN_TZ).date()


def classify_error(error: Exception) -> str:
    message = str(error).lower()

    if any(token in message for token in ["rate limit", "ratelimit", "giới hạn api"]):
        return "RATE_LIMIT"

    if any(token in message for token in ["no data", "emptydata", "no rows"]):
        return "NO_DATA"

    if any(token in message for token in ["invalid", "not found", "không hợp lệ", "symbol"]):
        return "INVALID_TICKER"

    if any(token in message for token in ["bad data", "completeness", "missing", "high_price", "low_price"]):
        return "BAD_DATA"

    return "SOURCE_ERROR"


@dataclass
class OhlcvRunResult:
    report: pd.DataFrame
    raw_json_path: Path
    csv_path: Path
    report_path: Path


class OHLCVAdapter:
    def __init__(
        self,
        source: str = "VCI",
        retries: int = 3,
        backoff_seconds: float = 2.0,
        logger: Optional[logging.Logger] = None,
    ):
        self.source = source
        self.retries = retries
        self.backoff_seconds = backoff_seconds
        self.logger = logger or logging.getLogger(__name__)

    # retry 3 lần
    # tối đa 3 lần cho mỗi ticker.
    # Nếu lần đầu lỗi, nó chờ rồi thử lại theo backoff tăng dần: 2 giây, rồi 4 giây, rồi 8 giây nếu vẫn còn lỗi.
    def fetch(
        self,
        ticker: str,
        start: str = DEFAULT_START_DATE,
        end: str = DEFAULT_END_DATE,
        interval: str = DEFAULT_INTERVAL,
    ) -> tuple[pd.DataFrame, int]:
        quote = Quote(symbol=ticker, source=self.source)

        for attempt in range(1, self.retries + 1):
            self.logger.info(
                "ohlcv.fetch start source=%s ticker=%s time=%s attempt=%s/%s",
                self.source,
                ticker,
                utc_now_iso(),
                attempt,
                self.retries,
            )

            try:
                data = quote.history(start=start, end=end, interval=interval)
                row_count = 0 if data is None else len(data)
                self.logger.info(
                    "ohlcv.fetch success source=%s ticker=%s time=%s attempt=%s rows=%s",
                    self.source,
                    ticker,
                    utc_now_iso(),
                    attempt,
                    row_count,
                )
                return data, attempt
            except Exception as error:
                self.logger.warning(
                    "ohlcv.fetch error source=%s ticker=%s time=%s attempt=%s/%s error=%s",
                    self.source,
                    ticker,
                    utc_now_iso(),
                    attempt,
                    self.retries,
                    error,
                )
                if attempt >= self.retries:
                    raise

                sleep_seconds = self.backoff_seconds * (2 ** (attempt - 1))
                self.logger.info(
                    "ohlcv.fetch backoff source=%s ticker=%s time=%s sleep_seconds=%.2f",
                    self.source,
                    ticker,
                    utc_now_iso(),
                    sleep_seconds,
                )
                time.sleep(sleep_seconds)

        raise RuntimeError(f"Failed to fetch OHLCV for {ticker}")


class OHLCVWorker:
    def __init__(
        self,
        adapter: Optional[OHLCVAdapter] = None,
        output_dir: str | Path = "reports",
        raw_layer_dir: str | Path = "reports/raw/ohlcv",
        sample_rows: int = 3,
        logger: Optional[logging.Logger] = None,
    ):
        self.adapter = adapter or OHLCVAdapter()
        self.output_dir = Path(output_dir)
        self.raw_layer_dir = Path(raw_layer_dir)
        self.sample_rows = sample_rows
        self.logger = logger or logging.getLogger(__name__)

    def _normalize_history_frame(self, ticker: str, data: pd.DataFrame) -> pd.DataFrame:
        missing_columns = [column for column in REQUIRED_SOURCE_COLUMNS if column not in data.columns]
        if missing_columns:
            raise ValueError(f"Missing required OHLCV columns: {missing_columns}")

        normalized = data.copy()
        normalized = normalized.rename(
            columns={
                "time": "trading_date",
                "open": "open_price",
                "high": "high_price",
                "low": "low_price",
                "close": "close_price",
                "volume": "volume",
            }
        )

        normalized.insert(0, "ticker", ticker)
        normalized["trading_date"] = pd.to_datetime(normalized["trading_date"], errors="coerce")
        normalized["open_price"] = pd.to_numeric(normalized["open_price"], errors="coerce")
        normalized["high_price"] = pd.to_numeric(normalized["high_price"], errors="coerce")
        normalized["low_price"] = pd.to_numeric(normalized["low_price"], errors="coerce")
        normalized["close_price"] = pd.to_numeric(normalized["close_price"], errors="coerce")
        normalized["volume"] = pd.to_numeric(normalized["volume"], errors="coerce")

        normalized = normalized[NORMALIZED_COLUMNS]

        records: list[dict] = []
        validation_errors: list[str] = []

        for index, row in enumerate(normalized.to_dict(orient="records"), start=1):
            try:
                model = DailyStockPrice(**row)
                records.append(model.model_dump(mode="json"))
            except (ValidationError, ValueError) as error:
                validation_errors.append(f"row={index}: {error}")

        if validation_errors:
            raise ValueError("BAD_DATA: " + " | ".join(validation_errors))

        return pd.DataFrame(records, columns=NORMALIZED_COLUMNS)

    def run(
        self,
        tickers: Iterable[str],
        start: str = DEFAULT_START_DATE,
        end: str = DEFAULT_END_DATE,
        interval: str = DEFAULT_INTERVAL,
        report_filename: str = "smoke_test_report.csv",
        raw_json_filename: str = "data.json",
        csv_filename: str = "ohlcv_samples_10_tickers.csv",
    ) -> OhlcvRunResult:
        self.output_dir.mkdir(parents=True, exist_ok=True)

        vn_today = vn_now_date()
        raw_partition_dir = (
            self.raw_layer_dir
            / f"year={vn_today:%Y}"
            / f"month={vn_today:%m}"
            / f"day={vn_today:%d}"
        )
        raw_partition_dir.mkdir(parents=True, exist_ok=True)

        report_rows: list[dict] = []
        raw_json_samples: list[dict] = []
        csv_samples: list[pd.DataFrame] = []

        for ticker in tickers:
            requested_at = datetime.now(timezone.utc)
            self.logger.info(
                "worker.ticker start source=%s ticker=%s time=%s",
                self.adapter.source,
                ticker,
                requested_at.isoformat(),
            )

            status = "FAIL"
            error_code = "SOURCE_ERROR"
            message = "Unknown error"
            rows = 0
            attempts = self.adapter.retries
            normalized_df = pd.DataFrame(columns=NORMALIZED_COLUMNS)

            try:
                data, attempts = self.adapter.fetch(
                    ticker=ticker,
                    start=start,
                    end=end,
                    interval=interval,
                )

                if data is None or data.empty:
                    status = "FAIL"
                    error_code = "NO_DATA"
                    message = "No data returned"
                    rows = 0
                else:
                    normalized_df = self._normalize_history_frame(ticker, data)
                    rows = len(normalized_df)
                    status = "PASS"
                    error_code = "OK"
                    message = "OK"
                    sample_df = normalized_df.head(self.sample_rows).copy()
                    sample_df.insert(1, "sample_row", range(1, len(sample_df) + 1))
                    csv_samples.append(sample_df)

            except Exception as error:
                message = str(error)
                error_code = classify_error(error)
                status = "FAIL"
                rows = 0

            metadata = IngestionMetadata(
                provider="vnstock",
                source=self.adapter.source,
                ticker=ticker,
                status=status,
                error_code=error_code,
                rows=rows,
                attempts=attempts,
                requested_at=requested_at,
                completed_at=datetime.now(timezone.utc),
            )

            raw_json_samples.append(
                {
                    "metadata": metadata.model_dump(mode="json"),
                    "records": normalized_df.head(self.sample_rows).to_dict(orient="records"),
                    "sample_rows": normalized_df.head(self.sample_rows).to_dict(orient="records"),
                }
            )

            report_rows.append(
                {
                    "ticker": ticker,
                    "status": status,
                    "error_code": error_code,
                    "rows": rows,
                    "message": message,
                    "source": self.adapter.source,
                    "completed_at": utc_now_iso(),
                }
            )

            self.logger.info(
                "worker.ticker end source=%s ticker=%s time=%s status=%s error_code=%s rows=%s",
                self.adapter.source,
                ticker,
                utc_now_iso(),
                status,
                error_code,
                rows,
            )

        report_df = pd.DataFrame(report_rows)
        report_path = self.output_dir / report_filename
        raw_json_path = raw_partition_dir / raw_json_filename
        csv_path = self.output_dir / csv_filename

        report_df.to_csv(report_path, index=False, encoding="utf-8-sig")

        if csv_samples:
            csv_df = pd.concat(csv_samples, ignore_index=True)
            csv_df = csv_df[["ticker", "sample_row", "trading_date", "open_price", "high_price", "low_price", "close_price", "volume"]]
        else:
            csv_df = pd.DataFrame(
                columns=[
                    "ticker",
                    "sample_row",
                    "trading_date",
                    "open_price",
                    "high_price",
                    "low_price",
                    "close_price",
                    "volume",
                ]
            )

        csv_df.to_csv(csv_path, index=False, encoding="utf-8-sig")

        with raw_json_path.open("w", encoding="utf-8") as handle:
            json.dump(raw_json_samples, handle, ensure_ascii=False, indent=2)

        return OhlcvRunResult(
            report=report_df,
            raw_json_path=raw_json_path,
            csv_path=csv_path,
            report_path=report_path,
        )


def load_tickers_from_universe(
    universe_path: str | Path = "universe/ticker_universe_v1.csv",
    limit: int = 10,
) -> list[str]:
    universe_df = pd.read_csv(universe_path)
    return universe_df["ticker"].head(limit).tolist()
