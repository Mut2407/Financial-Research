from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from src.pipeline.models import OhlcvRecord
from src.settings import Settings, get_settings


CURATED_COLUMNS = [
    "ticker",
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


def _read_raw_records(input_roots: list[Path]) -> tuple[list[dict], int]:
    records: list[dict] = []
    files_read = 0
    seen_files: set[Path] = set()
    for root in input_roots:
        if not root.exists():
            continue
        for path in sorted(root.rglob("*.json")):
            resolved = path.resolve()
            if resolved in seen_files:
                continue
            seen_files.add(resolved)
            payload = json.loads(path.read_text(encoding="utf-8-sig"))
            entries = payload if isinstance(payload, list) else [payload]
            for entry in entries:
                metadata = entry.get("metadata", {})
                if metadata.get("status") not in (None, "PASS"):
                    continue
                for record in entry.get("records", []):
                    records.append(OhlcvRecord.model_validate(record).model_dump())
            files_read += 1
    return records, files_read


def _calculate_indicators(frame: pd.DataFrame) -> pd.DataFrame:
    frame = frame.sort_values(["ticker", "trading_date"]).reset_index(drop=True)
    grouped_close = frame.groupby("ticker", group_keys=False)["close_price"]
    frame["return_pct"] = grouped_close.pct_change(fill_method=None).mul(100)
    frame["ma20"] = grouped_close.transform(lambda values: values.rolling(20, min_periods=1).mean())

    def rsi(values: pd.Series, period: int = 14) -> pd.Series:
        delta = values.diff()
        gains = delta.clip(lower=0)
        losses = -delta.clip(upper=0)
        average_gain = gains.ewm(alpha=1 / period, adjust=False, min_periods=period).mean()
        average_loss = losses.ewm(alpha=1 / period, adjust=False, min_periods=period).mean()
        relative_strength = average_gain / average_loss.replace(0, float("nan"))
        result = 100 - (100 / (1 + relative_strength))
        return result.fillna(100).where(average_gain.notna())

    frame["rsi_14"] = grouped_close.transform(rsi)
    frame[["return_pct", "ma20", "rsi_14"]] = frame[["return_pct", "ma20", "rsi_14"]].round(4)
    return frame[CURATED_COLUMNS]


def transform_raw_data(
    *,
    input_roots: list[Path] | None = None,
    config: Settings | None = None,
) -> dict:
    config = config or get_settings()
    roots = input_roots or [config.raw_path]
    records, files_read = _read_raw_records(roots)
    if not records:
        raise FileNotFoundError(f"No valid raw OHLCV records found under: {roots}")

    frame = pd.DataFrame(records)
    frame["trading_date"] = pd.to_datetime(frame["trading_date"], utc=True).dt.tz_localize(None)
    frame = frame.drop_duplicates(["ticker", "trading_date"], keep="last")
    curated = _calculate_indicators(frame)

    config.curated_path.mkdir(parents=True, exist_ok=True)
    written_files: list[str] = []
    for ticker, ticker_frame in curated.groupby("ticker", sort=True):
        ticker_dir = config.curated_path / f"ticker={ticker}"
        ticker_dir.mkdir(parents=True, exist_ok=True)
        output_path = ticker_dir / "part-000.parquet"
        ticker_frame.drop(columns=["ticker"]).to_parquet(output_path, index=False)
        written_files.append(str(output_path))

    return {
        "input_files": files_read,
        "rows": len(curated),
        "tickers": curated["ticker"].nunique(),
        "output_files": written_files,
    }

