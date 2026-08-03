from functools import lru_cache
from pathlib import Path

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


PROJECT_ROOT = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    """Shared runtime configuration loaded from environment variables/.env."""

    app_name: str = "Financial Data Platform API"
    environment: str = "local"
    data_provider: str = "VNSTOCK_FREE"
    vnstock_api_key: SecretStr = SecretStr("")
    vnstock_requests_per_minute: int = 60
    data_provider_api_key: SecretStr = SecretStr("")

    raw_data_dir: Path = Path("data/raw/ohlcv")
    curated_data_dir: Path = Path("data/curated/ohlcv")
    seed_raw_data_dir: Path = Path("reports/raw/ohlcv")
    universe_path: Path = Path("universe/ticker_universe_v1.csv")
    cors_origins: str = "http://localhost:8501,http://localhost:5173,http://127.0.0.1:5173"

    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    def resolve_path(self, value: Path) -> Path:
        return value if value.is_absolute() else PROJECT_ROOT / value

    @property
    def raw_path(self) -> Path:
        return self.resolve_path(self.raw_data_dir)

    @property
    def curated_path(self) -> Path:
        return self.resolve_path(self.curated_data_dir)

    @property
    def seed_raw_path(self) -> Path:
        return self.resolve_path(self.seed_raw_data_dir)

    @property
    def universe_file(self) -> Path:
        return self.resolve_path(self.universe_path)

    @property
    def allowed_origins(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
