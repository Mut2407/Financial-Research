from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.api.config import settings
from src.api.schemas.api_models import HealthCheckResponse
from src.api.routers import companies, pipeline, prices

app = FastAPI(
    title=settings.app_name,
    description="Consumption API over curated local OHLCV Parquet data",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(companies.router)
app.include_router(prices.router)
app.include_router(pipeline.router)

@app.get("/health", response_model=HealthCheckResponse, tags=["Health Check"])
def health_check():
    curated_files = len(list(settings.curated_path.rglob("*.parquet"))) if settings.curated_path.exists() else 0
    return {
        "status": "ok",
        "version": "1.0.0",
        "environment": settings.environment,
        "provider": settings.data_provider,
        "data_ready": curated_files > 0,
        "curated_files": curated_files,
    }
