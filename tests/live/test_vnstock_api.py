import os
import time
from datetime import date, timedelta

import pytest

from src.pipeline.ingestion import normalize_history
from src.pipeline.source import build_market_data_source


pytestmark = pytest.mark.live


def test_vnstock_free_authenticated_1d_contract(settings_factory, record_property):
    if os.getenv("RUN_VNSTOCK_LIVE_TESTS") != "1":
        pytest.skip("Set RUN_VNSTOCK_LIVE_TESTS=1 to opt in to the external API call")

    api_key = os.getenv("VNSTOCK_API_KEY", "")
    if not api_key:
        pytest.fail("VNSTOCK_API_KEY GitHub Secret is required for the manual live job")

    config = settings_factory(
        data_provider="VNSTOCK_FREE",
        vnstock_api_key=api_key,
        vnstock_requests_per_minute=60,
    )
    source = build_market_data_source(config)
    end = date.today() - timedelta(days=1)
    start = end - timedelta(days=14)

    started = time.perf_counter()
    frame, attempts = source.history("FPT", start.isoformat(), end.isoformat(), "1D")
    latency_ms = (time.perf_counter() - started) * 1000
    records = normalize_history("FPT", frame)

    record_property("provider", source.provider_name)
    record_property("ticker", "FPT")
    record_property("rows", len(records))
    record_property("attempts", attempts)
    record_property("source_latency_ms", round(latency_ms, 3))

    assert not frame.empty
    assert records
    assert all(record.ticker == "FPT" for record in records)
    assert all(record.volume >= 0 for record in records)
