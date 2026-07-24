from __future__ import annotations

import csv
import json
import time
from collections import Counter
from pathlib import Path
from typing import Any

import duckdb
import pandas as pd
import pytest
from fastapi.testclient import TestClient

from src.settings import Settings


def pytest_addoption(parser: pytest.Parser) -> None:
    group = parser.getgroup("qa-reporting")
    group.addoption(
        "--report-dir",
        action="store",
        default="reports/tests",
        help="Directory for JSON and CSV QA summaries.",
    )


def pytest_configure(config: pytest.Config) -> None:
    config._qa_started_at = time.time()  # type: ignore[attr-defined]
    config._qa_results = {}  # type: ignore[attr-defined]


def _component_for(nodeid: str) -> str:
    normalized = nodeid.replace("\\", "/")
    if "/frontend/" in normalized:
        return "frontend"
    if "/performance/" in normalized:
        return "performance"
    if "/container/" in normalized:
        return "container"
    if "/pipeline/" in normalized:
        return "pipeline"
    if "/api/" in normalized:
        return "api"
    if "/test_settings.py::" in normalized:
        return "configuration"
    return "other"


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item: pytest.Item, call: pytest.CallInfo[Any]):
    outcome = yield
    report = outcome.get_result()
    if report.when != "call" and not (report.failed or report.skipped):
        return

    result = {
        "nodeid": report.nodeid,
        "component": _component_for(report.nodeid),
        "outcome": report.outcome,
        "duration_seconds": round(report.duration, 6),
        "markers": sorted(marker.name for marker in item.iter_markers()),
        "phase": report.when,
        "message": "",
    }
    if report.failed:
        result["message"] = str(report.longrepr)
    elif report.skipped:
        result["message"] = str(report.longrepr)
    item.config._qa_results[report.nodeid] = result  # type: ignore[attr-defined]


def pytest_sessionfinish(session: pytest.Session, exitstatus: int) -> None:
    config = session.config
    report_dir = Path(config.getoption("--report-dir"))
    report_dir.mkdir(parents=True, exist_ok=True)
    results = sorted(config._qa_results.values(), key=lambda item: item["nodeid"])  # type: ignore[attr-defined]
    outcomes = Counter(item["outcome"] for item in results)
    components = Counter(item["component"] for item in results)
    summary = {
        "exit_code": exitstatus,
        "duration_seconds": round(time.time() - config._qa_started_at, 3),  # type: ignore[attr-defined]
        "total": len(results),
        "passed": outcomes["passed"],
        "failed": outcomes["failed"],
        "skipped": outcomes["skipped"],
        "by_component": dict(sorted(components.items())),
        "slowest": sorted(results, key=lambda item: item["duration_seconds"], reverse=True)[:10],
    }
    (report_dir / "test-summary.json").write_text(
        json.dumps({"summary": summary, "tests": results}, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    with (report_dir / "test-results.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(
            stream,
            fieldnames=["nodeid", "component", "outcome", "duration_seconds", "markers", "phase", "message"],
        )
        writer.writeheader()
        for result in results:
            writer.writerow({**result, "markers": ",".join(result["markers"])})


@pytest.fixture
def settings_factory(tmp_path: Path):
    def factory(**overrides: Any) -> Settings:
        values: dict[str, Any] = {
            "raw_data_dir": tmp_path / "raw",
            "curated_data_dir": tmp_path / "curated",
            "seed_raw_data_dir": tmp_path / "seed",
            "universe_path": tmp_path / "universe.csv",
        }
        values.update(overrides)
        return Settings(_env_file=None, **values)

    return factory


@pytest.fixture
def ohlcv_frame() -> pd.DataFrame:
    closes = list(range(11, 36))
    return pd.DataFrame(
        {
            "time": pd.date_range("2025-01-01", periods=25),
            "open": [value - 1 for value in closes],
            "high": [value + 1 for value in closes],
            "low": [value - 2 for value in closes],
            "close": closes,
            "volume": [1_000 + value for value in range(25)],
        }
    )


@pytest.fixture
def curated_settings(settings_factory) -> Settings:
    config = settings_factory()
    prices = pd.DataFrame(
        {
            "trading_date": pd.to_datetime(["2025-01-01", "2025-01-02"]),
            "open_price": [10.0, 11.0],
            "high_price": [12.0, 13.0],
            "low_price": [9.0, 10.0],
            "close_price": [11.0, 12.0],
            "volume": [1_000, 1_200],
            "return_pct": [None, 9.0909],
            "ma20": [11.0, 11.5],
            "rsi_14": [None, 50.0],
        }
    )
    for ticker in ("FPT", "VCB"):
        ticker_dir = config.curated_path / f"ticker={ticker}"
        ticker_dir.mkdir(parents=True)
        prices.to_parquet(ticker_dir / "part-000.parquet", index=False)
    pd.DataFrame(
        [
            {"ticker": "FPT", "name": "FPT Corp", "market": "HOSE", "sector": "Technology"},
        ]
    ).to_csv(config.universe_file, index=False)
    return config


@pytest.fixture
def api_client(curated_settings: Settings, monkeypatch: pytest.MonkeyPatch):
    from src.api.dependencies import get_data_service
    from src.api.main import app
    from src.api.services.data_service import DataService
    import src.api.main as main_module

    connection = duckdb.connect(":memory:")
    app.dependency_overrides[get_data_service] = lambda: DataService(connection, curated_settings)
    monkeypatch.setattr(main_module, "settings", curated_settings)
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()
    connection.close()
