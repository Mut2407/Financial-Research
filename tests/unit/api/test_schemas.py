from datetime import date

import pytest
from pydantic import ValidationError

from src.api.schemas.api_models import PipelineRunRequest


pytestmark = pytest.mark.unit


def test_pipeline_request_accepts_daily_interval():
    request = PipelineRunRequest(
        tickers=["FPT", "VCB"], start_date=date(2025, 1, 1), end_date=date(2025, 1, 31), interval="1D"
    )

    assert request.interval == "1D"


def test_pipeline_request_normalizes_and_deduplicates_safe_tickers():
    request = PipelineRunRequest(
        tickers=[" fpt ", "FPT", "vn30-f1m"],
        start_date=date(2025, 1, 1),
        end_date=date(2025, 1, 31),
    )

    assert request.tickers == ["FPT", "VN30-F1M"]


@pytest.mark.parametrize(
    "payload",
    [
        {"tickers": [], "start_date": "2025-01-01", "end_date": "2025-01-31"},
        {"tickers": [f"T{index:03d}" for index in range(21)], "start_date": "2025-01-01", "end_date": "2025-01-31"},
        {"tickers": ["FPT;DROP TABLE"], "start_date": "2025-01-01", "end_date": "2025-01-31"},
        {"tickers": ["../../secret"], "start_date": "2025-01-01", "end_date": "2025-01-31"},
        {"tickers": ["FPT"], "start_date": "2025-01-01", "end_date": "2025-01-31", "interval": "5M"},
        {"tickers": ["FPT"], "start_date": "2025-01-01", "end_date": "2025-01-31", "interval": "1H"},
        {"tickers": ["FPT"], "start_date": "not-a-date", "end_date": "2025-01-31"},
    ],
)
def test_pipeline_request_rejects_invalid_shape(payload: dict):
    with pytest.raises(ValidationError):
        PipelineRunRequest.model_validate(payload)
