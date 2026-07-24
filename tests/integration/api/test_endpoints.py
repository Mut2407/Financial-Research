import io
import json
import zipfile

import pandas as pd
import pytest
from fastapi.testclient import TestClient


pytestmark = pytest.mark.integration


def test_health_reflects_curated_availability(api_client):
    response = api_client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "version": "1.0.0",
        "environment": "local",
        "provider": "VNSTOCK_FREE",
        "data_ready": True,
        "curated_files": 2,
    }


def test_health_reports_not_ready_when_curated_is_empty(settings_factory, monkeypatch):
    import src.api.main as main_module

    config = settings_factory()
    monkeypatch.setattr(main_module, "settings", config)

    with TestClient(main_module.app) as client:
        response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["data_ready"] is False
    assert response.json()["curated_files"] == 0


def test_companies_returns_only_tickers_backed_by_curated_data(api_client):
    response = api_client.get("/companies", params={"page": 1, "limit": 10})

    assert response.status_code == 200
    assert {item["ticker"] for item in response.json()["data"]} == {"FPT", "VCB"}


def test_prices_contract_supports_date_filter(api_client):
    response = api_client.get("/prices", params={"ticker": "fpt", "start_date": "2025-01-02"})

    assert response.status_code == 200
    assert response.json()["total_records"] == 1
    assert response.json()["data"][0]["trading_date"] == "2025-01-02"
    assert response.json()["data"][0]["close_price"] == 12


@pytest.mark.parametrize(
    ("path", "params"),
    [
        ("/companies", {"page": 0}),
        ("/companies", {"limit": 0}),
        ("/companies", {"limit": 101}),
        ("/prices", {}),
        ("/prices", {"ticker": "FPT", "limit": 0}),
        ("/prices", {"ticker": "FPT", "limit": 1001}),
        ("/prices", {"ticker": "FPT", "start_date": "not-a-date"}),
        (
            "/prices",
            {"ticker": "FPT", "start_date": "2025-02-01", "end_date": "2025-01-01"},
        ),
    ],
)
def test_query_validation_rejects_out_of_contract_requests(api_client, path: str, params: dict):
    assert api_client.get(path, params=params).status_code == 422


@pytest.mark.parametrize("export_format", ["csv", "parquet"])
def test_export_zip_contains_data_and_manifest(api_client, export_format: str):
    response = api_client.get("/prices/export", params={"ticker": "FPT", "format": export_format})

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/zip"
    with zipfile.ZipFile(io.BytesIO(response.content)) as archive:
        assert set(archive.namelist()) == {f"FPT_data.{export_format}", "manifest.json"}
        manifest = json.loads(archive.read("manifest.json"))
        assert manifest["ticker"] == "FPT"
        assert manifest["row_count"] == 2
        if export_format == "csv":
            frame = pd.read_csv(io.BytesIO(archive.read("FPT_data.csv")))
        else:
            frame = pd.read_parquet(io.BytesIO(archive.read("FPT_data.parquet")))
        assert len(frame) == 2


def test_export_returns_404_when_ticker_has_no_curated_data(api_client):
    response = api_client.get("/prices/export", params={"ticker": "MISSING", "format": "csv"})

    assert response.status_code == 404
