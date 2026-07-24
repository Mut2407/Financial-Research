import os

import pandas as pd
import pytest

from src.pipeline.source import (
    SourceConfigurationError,
    VnstockApiSource,
    build_market_data_source,
)


pytestmark = pytest.mark.unit


class FakeEquity:
    def __init__(self, outcomes):
        self.outcomes = list(outcomes)
        self.calls = []

    def ohlcv(self, **kwargs):
        self.calls.append(kwargs)
        outcome = self.outcomes.pop(0)
        if isinstance(outcome, Exception):
            raise outcome
        return outcome


class FakeMarket:
    def __init__(self, equity: FakeEquity):
        self._equity = equity
        self.symbols = []

    def equity(self, symbol: str):
        self.symbols.append(symbol)
        return self._equity


def test_authenticated_unified_api_call_uses_official_key_and_1d_contract(monkeypatch):
    monkeypatch.delenv("VNSTOCK_API_KEY", raising=False)
    expected = pd.DataFrame({"time": ["2025-01-01"], "close": [100.0]})
    equity = FakeEquity([expected])
    market = FakeMarket(equity)
    source = VnstockApiSource(
        "test-key",
        market_factory=lambda: market,
        sleeper=lambda _: None,
    )

    frame, attempts = source.history("FPT", "2025-01-01", "2025-01-31", "1D")

    assert os.environ["VNSTOCK_API_KEY"] == "test-key"
    assert market.symbols == ["FPT"]
    assert equity.calls == [
        {"start": "2025-01-01", "end": "2025-01-31", "resolution": "1D"}
    ]
    assert frame.equals(expected)
    assert attempts == 1
    assert "test-key" not in repr(source)


def test_source_retries_and_applies_backoff_plus_free_tier_rate_limit(monkeypatch):
    monkeypatch.delenv("VNSTOCK_API_KEY", raising=False)
    now = [0.0]
    sleeps = []

    def sleep(seconds: float):
        sleeps.append(seconds)
        now[0] += seconds

    equity = FakeEquity(
        [ConnectionError("temporary"), pd.DataFrame({"close": [1.0]})]
    )
    source = VnstockApiSource(
        "test-key",
        requests_per_minute=60,
        retries=2,
        backoff_seconds=0.25,
        market_factory=lambda: FakeMarket(equity),
        clock=lambda: now[0],
        sleeper=sleep,
    )

    frame, attempts = source.history("FPT", "2025-01-01", "2025-01-31", "1D")

    assert frame["close"].tolist() == [1.0]
    assert attempts == 2
    assert sleeps == [0.25, 0.75]


def test_source_raises_after_configured_attempts(monkeypatch):
    monkeypatch.delenv("VNSTOCK_API_KEY", raising=False)
    equity = FakeEquity([TimeoutError("provider timeout"), TimeoutError("provider timeout")])
    source = VnstockApiSource(
        "test-key",
        retries=2,
        backoff_seconds=0,
        market_factory=lambda: FakeMarket(equity),
        clock=lambda: 0,
        sleeper=lambda _: None,
    )

    with pytest.raises(TimeoutError, match="provider timeout"):
        source.history("FPT", "2025-01-01", "2025-01-31", "1D")

    assert len(equity.calls) == 2


@pytest.mark.parametrize(
    ("kwargs", "message"),
    [
        ({"api_key": ""}, "VNSTOCK_API_KEY is required"),
        ({"api_key": "key", "requests_per_minute": 0}, "between 1 and 60"),
        ({"api_key": "key", "requests_per_minute": 61}, "between 1 and 60"),
        ({"api_key": "key", "retries": 0}, "retries must be at least 1"),
    ],
)
def test_source_rejects_invalid_auth_or_free_tier_configuration(kwargs: dict, message: str):
    with pytest.raises(SourceConfigurationError, match=message):
        VnstockApiSource(**kwargs)


def test_source_rejects_non_daily_interval_before_api_call(monkeypatch):
    monkeypatch.delenv("VNSTOCK_API_KEY", raising=False)
    called = False

    def market_factory():
        nonlocal called
        called = True
        return FakeMarket(FakeEquity([]))

    source = VnstockApiSource("test-key", market_factory=market_factory)

    with pytest.raises(ValueError, match="interval 1D only"):
        source.history("FPT", "2025-01-01", "2025-01-31", "1H")

    assert called is False


def test_source_factory_reads_vnstock_specific_configuration(settings_factory):
    config = settings_factory(
        data_provider="VNSTOCK_FREE",
        vnstock_api_key="test-key",
        vnstock_requests_per_minute=30,
    )

    source = build_market_data_source(config)

    assert isinstance(source, VnstockApiSource)
    assert source.provider_name == "VNSTOCK_FREE"
    assert source.requests_per_minute == 30


def test_source_factory_rejects_unknown_provider(settings_factory):
    config = settings_factory(
        data_provider="UNKNOWN",
        vnstock_api_key="test-key",
    )

    with pytest.raises(SourceConfigurationError, match="Unsupported DATA_PROVIDER"):
        build_market_data_source(config)


def test_locked_vnstock_client_exposes_expected_unified_api_contract():
    import inspect

    from vnstock import Market
    from vnstock.ui.domains.market.equity import EquityMarket

    assert "symbol" in inspect.signature(Market.equity).parameters
    parameters = inspect.signature(EquityMarket.ohlcv).parameters
    assert {"start", "end", "resolution"}.issubset(parameters)
    assert parameters["resolution"].default == "1D"
