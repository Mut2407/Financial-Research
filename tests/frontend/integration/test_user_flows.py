from pathlib import Path

import pytest
import requests
from streamlit.testing.v1 import AppTest

from utils.api_client import ApiClientError


pytestmark = [pytest.mark.integration, pytest.mark.frontend]
APP_PATH = Path(__file__).resolve().parents[3] / "frontend" / "app.py"


class FakeResponse:
    def __init__(self, payload: dict, status_code: int = 200):
        self._payload = payload
        self.status_code = status_code
        self.text = ""

    def raise_for_status(self):
        if self.status_code >= 400:
            error = requests.HTTPError(str(self.status_code))
            error.response = self
            raise error

    def json(self):
        return self._payload


def _market_api(method: str, url: str, **kwargs):
    if url.endswith("/companies"):
        return FakeResponse(
            {
                "data": [{"ticker": "FPT", "name": "FPT Corp", "market": "HOSE", "sector": "Technology"}],
                "page": 1,
                "limit": 100,
                "total_records": 1,
            }
        )
    if url.endswith("/prices"):
        return FakeResponse(
            {
                "ticker": "FPT",
                "data": [
                    {
                        "ticker": "FPT",
                        "trading_date": "2025-01-01",
                        "open_price": 10,
                        "high_price": 12,
                        "low_price": 9,
                        "close_price": 11,
                        "volume": 1000,
                        "return_pct": None,
                        "ma20": 11,
                        "rsi_14": None,
                    },
                    {
                        "ticker": "FPT",
                        "trading_date": "2025-01-02",
                        "open_price": 11,
                        "high_price": 13,
                        "low_price": 10,
                        "close_price": 12,
                        "volume": 1200,
                        "return_pct": 9.0909,
                        "ma20": 11.5,
                        "rsi_14": 50,
                    },
                ],
                "page": 1,
                "limit": 1000,
                "total_records": 2,
            }
        )
    raise AssertionError(f"Unexpected request: {method} {url}")


def test_login_to_dashboard_flow_uses_backend_market_data(monkeypatch):
    monkeypatch.setattr(requests, "request", _market_api)
    app = AppTest.from_file(str(APP_PATH), default_timeout=15).run()

    assert not app.exception
    assert [item.label for item in app.text_input] == ["Username", "Password"]
    app.button[0].click().run()

    assert not app.exception
    assert [metric.label for metric in app.metric] == ["Close", "Volume", "MA20", "RSI 14"]
    assert app.metric[0].value == "12.00"
    assert app.metric[2].value == "11.50"
    assert app.metric[3].value == "50.00"


def test_login_can_navigate_to_registration_and_back():
    app = AppTest.from_file(str(APP_PATH), default_timeout=15).run()

    app.button[1].click().run()
    assert not app.exception
    assert [item.label for item in app.text_input] == ["Email", "Password"]

    app.button[1].click().run()
    assert not app.exception
    assert [item.label for item in app.text_input] == ["Username", "Password"]


def test_dashboard_reports_backend_unavailability_instead_of_mocking_data(monkeypatch):
    monkeypatch.setattr(
        requests,
        "request",
        lambda *args, **kwargs: (_ for _ in ()).throw(requests.ConnectionError("refused")),
    )
    app = AppTest.from_file(str(APP_PATH), default_timeout=15).run()

    app.button[0].click().run()

    assert not app.exception
    assert app.error
    assert "Backend request failed" in app.error[0].value
    assert not app.metric


def test_data_explorer_submission_flow_shows_ingestion_and_api_preview(monkeypatch):
    import views.data_explorer as data_explorer

    monkeypatch.setattr(
        data_explorer,
        "run_pipeline",
        lambda *args, **kwargs: {
            "ingestion": {
                "raw_path": "data/raw/ohlcv/year=2025/month=01/day=31/batch.json",
                "requested": 1,
                "passed": 1,
                "failed": 0,
                "details": [{"ticker": "FPT", "status": "PASS"}],
            },
            "transformation": {"rows": 2, "tickers": 1},
        },
    )
    monkeypatch.setattr(data_explorer, "get_prices", lambda *args, **kwargs: _market_api("GET", "http://test/prices").json())
    app = AppTest.from_string("from views.data_explorer import render\nrender()", default_timeout=15).run()

    app.button[0].click().run()

    assert not app.exception
    assert [metric.value for metric in app.metric] == ["1", "1", "0"]
    assert any("Preview" in item.label for item in app.selectbox)


def test_dashboard_empty_curated_flow_does_not_request_prices(monkeypatch):
    import views.dashboard as dashboard

    monkeypatch.setattr(dashboard, "get_companies", lambda **kwargs: {"data": []})
    monkeypatch.setattr(
        dashboard,
        "get_prices",
        lambda *args, **kwargs: pytest.fail("prices must not be requested when curated is empty"),
    )
    app = AppTest.from_string("from views.dashboard import render\nrender()", default_timeout=15).run()

    assert not app.exception
    assert app.warning
    assert "Curated layer" in app.warning[0].value
    assert not app.metric


def test_data_explorer_rejects_empty_ticker_before_backend_call(monkeypatch):
    import views.data_explorer as data_explorer

    monkeypatch.setattr(
        data_explorer,
        "run_pipeline",
        lambda *args, **kwargs: pytest.fail("backend must not be called for an empty ticker"),
    )
    app = AppTest.from_string("from views.data_explorer import render\nrender()", default_timeout=15).run()
    app.text_input[0].set_value("")

    app.button[0].click().run()

    assert not app.exception
    assert app.error[0].value == "Cần ít nhất một ticker."


def test_data_explorer_displays_pipeline_api_error(monkeypatch):
    import views.data_explorer as data_explorer

    monkeypatch.setattr(
        data_explorer,
        "run_pipeline",
        lambda *args, **kwargs: (_ for _ in ()).throw(ApiClientError("provider unavailable")),
    )
    app = AppTest.from_string("from views.data_explorer import render\nrender()", default_timeout=15).run()

    app.button[0].click().run()

    assert not app.exception
    assert app.error[0].value == "provider unavailable"
    assert not app.metric


def test_settings_health_check_success_flow(monkeypatch):
    import views.settings as settings_view

    monkeypatch.setattr(
        settings_view,
        "get_health",
        lambda: {"status": "ok", "data_ready": True, "curated_files": 2},
    )
    app = AppTest.from_string("from views.settings import render\nrender()", default_timeout=15).run()

    app.button[0].click().run()

    assert not app.exception
    assert app.success[0].value == "Backend đang hoạt động."
    assert any("frontend không hiển thị" in item.value for item in app.info)


def test_settings_health_check_failure_does_not_expose_a_secret(monkeypatch):
    import views.settings as settings_view

    monkeypatch.setattr(
        settings_view,
        "get_health",
        lambda: (_ for _ in ()).throw(ApiClientError("Backend request failed (GET /health)")),
    )
    app = AppTest.from_string("from views.settings import render\nrender()", default_timeout=15).run()

    app.button[0].click().run()

    assert not app.exception
    assert "Backend request failed" in app.error[0].value
    rendered_markdown = " ".join(item.value for item in app.markdown)
    assert "DATA_PROVIDER_API_KEY" not in rendered_markdown
    assert "VNSTOCK_API_KEY" not in rendered_markdown
