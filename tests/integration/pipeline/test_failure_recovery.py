import hashlib
from pathlib import Path

import pandas as pd
import pytest

from src.pipeline.ingestion import ingest_tickers


pytestmark = pytest.mark.integration


class FailingSource:
    provider_name = "TEST"

    def history(self, ticker: str, start: str, end: str, interval: str):
        raise ConnectionError("provider unavailable")


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_source_failure_appends_failure_evidence_without_mutating_existing_layers(
    settings_factory,
):
    config = settings_factory()
    previous_raw = config.raw_path / "year=2025" / "month=01" / "day=01" / "batch_previous.json"
    previous_raw.parent.mkdir(parents=True)
    previous_raw.write_text('[{"metadata":{"status":"PASS"},"records":[]}]', encoding="utf-8")

    curated = config.curated_path / "ticker=FPT" / "part-000.parquet"
    curated.parent.mkdir(parents=True)
    pd.DataFrame({"trading_date": ["2025-01-01"], "close_price": [100.0]}).to_parquet(
        curated, index=False
    )
    before = {previous_raw: _digest(previous_raw), curated: _digest(curated)}

    result = ingest_tickers(
        ["FPT"],
        "2025-01-01",
        "2025-01-31",
        source=FailingSource(),
        config=config,
    )

    assert result["failed"] == 1
    assert Path(result["raw_path"]) != previous_raw
    assert all(_digest(path) == digest for path, digest in before.items())
