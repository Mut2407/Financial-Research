import os
from typing import Any

import requests


API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000").rstrip("/")
DEFAULT_TIMEOUT = 30


class ApiClientError(RuntimeError):
    pass


def _request(method: str, path: str, *, timeout: int = DEFAULT_TIMEOUT, **kwargs) -> Any:
    try:
        response = requests.request(method, f"{API_BASE_URL}{path}", timeout=timeout, **kwargs)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as error:
        detail = ""
        if getattr(error, "response", None) is not None:
            try:
                detail = f": {error.response.json().get('detail', error.response.text)}"
            except ValueError:
                detail = f": {error.response.text}"
        raise ApiClientError(f"Backend request failed ({method} {path}){detail}") from error


def get_health() -> dict:
    return _request("GET", "/health", timeout=5)


def get_companies(limit: int = 100) -> dict:
    return _request("GET", "/companies", params={"page": 1, "limit": limit})


def get_prices(
    ticker: str,
    start_date: str | None = None,
    end_date: str | None = None,
    limit: int = 10000, 
) -> dict:
    params: dict[str, Any] = {"ticker": ticker, "page": 1, "limit": limit}
    if start_date:
        params["start_date"] = start_date
    if end_date:
        params["end_date"] = end_date
    return _request("GET", "/prices", params=params)


def run_pipeline(tickers: list[str], start_date: str, end_date: str, interval: str = "1D") -> dict:
    return _request(
        "POST",
        "/pipeline/run",
        timeout=180,
        json={
            "tickers": tickers,
            "start_date": start_date,
            "end_date": end_date,
            "interval": interval,
        },
    )
