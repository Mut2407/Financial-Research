from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, Field, model_validator


class OhlcvRecord(BaseModel):
    ticker: str = Field(min_length=1, max_length=20)
    trading_date: datetime
    open_price: float = Field(gt=0)
    high_price: float = Field(gt=0)
    low_price: float = Field(gt=0)
    close_price: float = Field(gt=0)
    volume: int = Field(ge=0)

    @model_validator(mode="after")
    def validate_price_range(self):
        if self.high_price < self.low_price:
            raise ValueError("high_price must be greater than or equal to low_price")
        return self


class IngestionMetadata(BaseModel):
    schema_version: str = "1.0"
    access_library: str = "vnstock"
    provider: str
    ticker: str
    status: Literal["PASS", "FAIL"]
    error_code: str
    rows: int = Field(ge=0)
    attempts: int = Field(ge=1)
    requested_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class RawTickerPayload(BaseModel):
    metadata: IngestionMetadata
    records: list[OhlcvRecord]
