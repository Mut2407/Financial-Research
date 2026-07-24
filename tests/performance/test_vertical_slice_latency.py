import time

import duckdb
import pandas as pd
import pytest
from fastapi.testclient import TestClient

from src.api.dependencies import get_data_service
from src.api.services.data_service import DataService
from src.pipeline.ingestion import ingest_tickers
from src.pipeline.transform import transform_raw_data


pytestmark = [pytest.mark.integration, pytest.mark.performance]


class DeterministicBatchSource:
    provider_name = "PERFORMANCE_FIXTURE"

    def __init__(self, frame: pd.DataFrame):
        self.frame = frame
        self.calls = 0

    def history(self, ticker: str, start: str, end: str, interval: str):
        self.calls += 1
        return self.frame.copy(), 1


def test_twenty_ticker_vertical_slice_records_stage_latency(
    settings_factory,
    ohlcv_frame: pd.DataFrame,
    monkeypatch,
    record_property,
):
    from src.api.main import app
    import src.api.main as main_module

    config = settings_factory()
    source = DeterministicBatchSource(ohlcv_frame)
    tickers = [f"T{index:03d}" for index in range(20)]

    started = time.perf_counter()
    ingestion = ingest_tickers(
        tickers,
        "2025-01-01",
        "2025-01-31",
        source=source,
        config=config,
    )
    ingestion_ms = (time.perf_counter() - started) * 1000

    started = time.perf_counter()
    transformation = transform_raw_data(config=config)
    transformation_ms = (time.perf_counter() - started) * 1000

    connection = duckdb.connect(":memory:")
    app.dependency_overrides[get_data_service] = lambda: DataService(connection, config)
    monkeypatch.setattr(main_module, "settings", config)
    try:
        with TestClient(app) as client:
            started = time.perf_counter()
            response = client.get("/prices", params={"ticker": tickers[-1], "limit": 1000})
            api_ms = (time.perf_counter() - started) * 1000
    finally:
        app.dependency_overrides.clear()
        connection.close()

    record_property("batch_tickers", len(tickers))
    record_property("batch_rows", transformation["rows"])
    record_property("ingestion_ms", round(ingestion_ms, 3))
    record_property("transformation_ms", round(transformation_ms, 3))
    record_property("consumption_api_ms", round(api_ms, 3))

    assert source.calls == 20
    assert ingestion["requested"] == ingestion["passed"] == 20
    assert ingestion["failed"] == 0
    assert transformation["rows"] == 500
    assert transformation["tickers"] == 20
    assert len(transformation["output_files"]) == 20
    assert response.status_code == 200
    assert response.json()["ticker"] == tickers[-1]
    assert response.json()["total_records"] == 25
