import pytest

import src.api.routers.pipeline as pipeline_router


pytestmark = pytest.mark.integration


def _request_body(**overrides):
    body = {
        "tickers": ["FPT"],
        "start_date": "2025-01-01",
        "end_date": "2025-01-31",
        "interval": "1D",
    }
    body.update(overrides)
    return body


def test_pipeline_endpoint_connects_ingestion_and_transform(api_client, monkeypatch, settings_factory):
    config = settings_factory()
    calls = []

    def fake_ingest(tickers, start, end, interval, *, config):
        calls.append((tickers, start, end, interval, config))
        return {"raw_path": "raw.json", "requested": 1, "passed": 1, "failed": 0, "details": []}

    def fake_transform(*, input_roots, config):
        calls.append((input_roots, config))
        return {"input_files": 1, "rows": 2, "tickers": 1, "output_files": ["FPT.parquet"]}

    monkeypatch.setattr(pipeline_router, "get_settings", lambda: config)
    monkeypatch.setattr(pipeline_router, "ingest_tickers", fake_ingest)
    monkeypatch.setattr(pipeline_router, "transform_raw_data", fake_transform)

    response = api_client.post("/pipeline/run", json=_request_body())

    assert response.status_code == 200
    assert response.json()["transformation"]["rows"] == 2
    assert calls[0][:4] == (["FPT"], "2025-01-01", "2025-01-31", "1D")
    assert calls[1][0] == [config.raw_path]


def test_pipeline_skips_transform_when_all_sources_fail(api_client, monkeypatch, settings_factory):
    monkeypatch.setattr(pipeline_router, "get_settings", settings_factory)
    monkeypatch.setattr(
        pipeline_router,
        "ingest_tickers",
        lambda *args, **kwargs: {
            "raw_path": "raw.json",
            "requested": 1,
            "passed": 0,
            "failed": 1,
            "details": [],
        },
    )
    monkeypatch.setattr(
        pipeline_router,
        "transform_raw_data",
        lambda **kwargs: pytest.fail("transform must not run when ingestion has no passing ticker"),
    )

    response = api_client.post("/pipeline/run", json=_request_body())

    assert response.status_code == 200
    assert response.json()["transformation"] is None


def test_pipeline_rejects_reversed_date_range_before_source_call(api_client, monkeypatch):
    monkeypatch.setattr(
        pipeline_router,
        "ingest_tickers",
        lambda *args, **kwargs: pytest.fail("source must not be called for an invalid date range"),
    )

    response = api_client.post(
        "/pipeline/run",
        json=_request_body(start_date="2025-02-01", end_date="2025-01-01"),
    )

    assert response.status_code == 422
    assert response.json()["detail"] == "start_date must not be after end_date"


@pytest.mark.parametrize("ticker", ["../../secret", "FPT;DROP TABLE"])
def test_pipeline_rejects_unsafe_ticker_at_api_boundary(api_client, monkeypatch, ticker: str):
    monkeypatch.setattr(
        pipeline_router,
        "ingest_tickers",
        lambda *args, **kwargs: pytest.fail("unsafe ticker must not reach ingestion"),
    )

    response = api_client.post("/pipeline/run", json=_request_body(tickers=[ticker]))

    assert response.status_code == 422


def test_pipeline_returns_conflict_when_another_run_holds_lock(api_client):
    assert pipeline_router.pipeline_lock.acquire(blocking=False)
    try:
        response = api_client.post("/pipeline/run", json=_request_body())
    finally:
        pipeline_router.pipeline_lock.release()

    assert response.status_code == 409
