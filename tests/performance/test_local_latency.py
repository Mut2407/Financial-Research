import math
import time
import tomllib
from pathlib import Path

import pytest


pytestmark = [pytest.mark.integration, pytest.mark.performance]
GATES = tomllib.loads((Path(__file__).resolve().parents[1] / "quality_gates.toml").read_text(encoding="utf-8"))


def _percentile(values: list[float], percentile: float) -> float:
    ordered = sorted(values)
    return ordered[max(0, math.ceil(percentile * len(ordered)) - 1)]


def test_local_prices_api_p95_latency_characterization(api_client, record_property):
    durations_ms = []
    api_client.get("/prices", params={"ticker": "FPT", "limit": 1000})

    for _ in range(30):
        started = time.perf_counter()
        response = api_client.get("/prices", params={"ticker": "FPT", "limit": 1000})
        durations_ms.append((time.perf_counter() - started) * 1000)
        assert response.status_code == 200

    p95_ms = _percentile(durations_ms, 0.95)
    latency_config = GATES["latency_ms"]
    candidate_ms = latency_config["local_prices_api_p95"]
    record_property("latency_p95_ms", round(p95_ms, 3))
    record_property("latency_candidate_ms", candidate_ms)
    record_property("latency_gate_enforced", latency_config["enforce"])

    assert len(durations_ms) == 30
    if latency_config["enforce"]:
        assert p95_ms <= candidate_ms, (
            f"Local /prices p95 {p95_ms:.1f} ms exceeded {candidate_ms} ms"
        )
