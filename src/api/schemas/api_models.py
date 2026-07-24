from datetime import date
import re

from pydantic import BaseModel, Field, field_validator

class HealthCheckResponse(BaseModel):
    status: str
    version: str
    environment: str
    provider: str
    data_ready: bool
    curated_files: int

class CompanyResponse(BaseModel):
    ticker: str
    name: str | None = None
    market: str | None = None
    sector: str | None = None

class PriceRecord(BaseModel):
    ticker: str
    trading_date: date
    open_price: float
    high_price: float
    low_price: float
    close_price: float
    volume: float
    return_pct: float | None = None
    ma20: float | None = None
    rsi_14: float | None = None

class PriceListResponse(BaseModel):
    ticker: str
    data: list[PriceRecord]
    page: int
    limit: int
    total_records: int

class CompanyListResponse(BaseModel):
    data: list[CompanyResponse]
    page: int
    limit: int
    total_records: int


class PipelineRunRequest(BaseModel):
    tickers: list[str] = Field(min_length=1, max_length=20)
    start_date: date
    end_date: date
    interval: str = Field(default="1D", pattern="^1D$")

    @field_validator("tickers")
    @classmethod
    def normalize_safe_tickers(cls, values: list[str]) -> list[str]:
        normalized = list(dict.fromkeys(value.strip().upper() for value in values))
        if any(not re.fullmatch(r"[A-Z0-9._-]{1,20}", value) for value in normalized):
            raise ValueError("tickers must contain only safe market-symbol characters")
        return normalized
