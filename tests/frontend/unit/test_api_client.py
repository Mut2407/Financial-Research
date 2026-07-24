import requests
import pytest

from utils import api_client
from utils.api_client import ApiClientError


pytestmark = [pytest.mark.unit, pytest.mark.frontend]


class FakeResponse:
    def __init__(self, payload=None, *, status_code: int = 200, text: str = ""):
        self.payload = payload
        self.status_code = status_code
        self.text = text

    def raise_for_status(self):
        if self.status_code >= 400:
            error = requests.HTTPError(f"HTTP {self.status_code}")
            error.response = self
            raise error

    def json(self):
        return self.payload


def test_get_prices_builds_only_supplied_filters(monkeypatch):
    captured = {}

    def fake_request(method, url, **kwargs):
        captured.update({"method": method, "url": url, **kwargs})
        return FakeResponse({"data": []})

    monkeypatch.setattr(api_client.requests, "request", fake_request)

    result = api_client.get_prices("FPT", start_date="2025-01-01", limit=25)

    assert result == {"data": []}
    assert captured["method"] == "GET"
    assert captured["url"].endswith("/prices")
    assert captured["params"] == {
        "ticker": "FPT",
        "page": 1,
        "limit": 25,
        "start_date": "2025-01-01",
    }
    assert captured["timeout"] == 30


def test_run_pipeline_sends_contract_payload_and_extended_timeout(monkeypatch):
    captured = {}

    def fake_request(method, url, **kwargs):
        captured.update({"method": method, "url": url, **kwargs})
        return FakeResponse({"ingestion": {"passed": 1}})

    monkeypatch.setattr(api_client.requests, "request", fake_request)

    api_client.run_pipeline(["FPT"], "2025-01-01", "2025-01-31", "1D")

    assert captured["method"] == "POST"
    assert captured["timeout"] == 180
    assert captured["json"] == {
        "tickers": ["FPT"],
        "start_date": "2025-01-01",
        "end_date": "2025-01-31",
        "interval": "1D",
    }


def test_connection_error_is_wrapped_without_leaking_transport_details(monkeypatch):
    monkeypatch.setattr(
        api_client.requests,
        "request",
        lambda *args, **kwargs: (_ for _ in ()).throw(requests.ConnectionError("refused")),
    )

    with pytest.raises(ApiClientError, match=r"Backend request failed \(GET /health\)"):
        api_client.get_health()


def test_backend_error_includes_api_detail(monkeypatch):
    monkeypatch.setattr(
        api_client.requests,
        "request",
        lambda *args, **kwargs: FakeResponse({"detail": "Curated data unavailable"}, status_code=503),
    )

    with pytest.raises(ApiClientError, match="Curated data unavailable"):
        api_client.get_companies()
