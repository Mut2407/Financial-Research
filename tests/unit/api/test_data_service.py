import duckdb
import pytest

from src.api.services.data_service import DataService


pytestmark = pytest.mark.unit


def test_empty_curated_layer_returns_empty_contract(settings_factory):
    connection = duckdb.connect(":memory:")
    try:
        service = DataService(connection, settings_factory())

        assert service.get_companies(1, 50) == {
            "data": [],
            "page": 1,
            "limit": 50,
            "total_records": 0,
        }
        assert service.get_prices("fpt", None, None, 1, 100)["data"] == []
        assert service.get_prices_for_export("FPT") is None
    finally:
        connection.close()


def test_companies_merge_universe_metadata_and_curated_tickers(curated_settings):
    connection = duckdb.connect(":memory:")
    try:
        result = DataService(connection, curated_settings).get_companies(page=1, limit=10)
    finally:
        connection.close()

    assert result["total_records"] == 2
    assert result["data"] == [
        {"ticker": "FPT", "name": "FPT Corp", "market": "HOSE", "sector": "Technology"},
        {"ticker": "VCB", "name": None, "market": None, "sector": None},
    ]


def test_companies_pagination_is_deterministic(curated_settings):
    connection = duckdb.connect(":memory:")
    try:
        service = DataService(connection, curated_settings)
        first = service.get_companies(page=1, limit=1)
        second = service.get_companies(page=2, limit=1)
    finally:
        connection.close()

    assert first["data"][0]["ticker"] == "FPT"
    assert second["data"][0]["ticker"] == "VCB"
    assert first["total_records"] == second["total_records"] == 2


def test_prices_support_case_normalization_date_filter_and_pagination(curated_settings):
    connection = duckdb.connect(":memory:")
    try:
        result = DataService(connection, curated_settings).get_prices(
            " fpt ", "2025-01-02", "2025-01-02", page=1, limit=1
        )
    finally:
        connection.close()

    assert result["ticker"] == "FPT"
    assert result["total_records"] == 1
    assert result["data"][0]["trading_date"].date().isoformat() == "2025-01-02"
    assert result["data"][0]["close_price"] == 12


def test_ticker_input_is_bound_as_parameter_not_sql(curated_settings):
    connection = duckdb.connect(":memory:")
    try:
        service = DataService(connection, curated_settings)
        result = service.get_prices("FPT' OR 1=1 --", None, None, page=1, limit=100)
        intact = service.get_prices("FPT", None, None, page=1, limit=100)
    finally:
        connection.close()

    assert result["data"] == []
    assert intact["total_records"] == 2


def test_export_query_returns_all_rows_in_trading_date_order(curated_settings):
    connection = duckdb.connect(":memory:")
    try:
        frame = DataService(connection, curated_settings).get_prices_for_export("fpt")
    finally:
        connection.close()

    assert len(frame) == 2
    assert frame["ticker"].unique().tolist() == ["FPT"]
    assert frame["trading_date"].is_monotonic_increasing
