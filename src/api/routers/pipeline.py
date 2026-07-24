from threading import Lock

from fastapi import APIRouter, HTTPException

from src.api.schemas.api_models import PipelineRunRequest
from src.pipeline.ingestion import ingest_tickers
from src.pipeline.transform import transform_raw_data
from src.settings import get_settings


router = APIRouter(prefix="/pipeline", tags=["Pipeline"])
pipeline_lock = Lock()


@router.post("/run")
def run_pipeline(request: PipelineRunRequest):
    """Run a small synchronous live ingestion suitable for the local PoC."""
    if request.start_date > request.end_date:
        raise HTTPException(status_code=422, detail="start_date must not be after end_date")
    if not pipeline_lock.acquire(blocking=False):
        raise HTTPException(status_code=409, detail="Another ingestion run is already in progress")

    try:
        config = get_settings()
        ingestion = ingest_tickers(
            request.tickers,
            request.start_date.isoformat(),
            request.end_date.isoformat(),
            request.interval,
            config=config,
        )
        transformation = None
        if ingestion["passed"]:
            transformation = transform_raw_data(input_roots=[config.raw_path], config=config)
        return {"ingestion": ingestion, "transformation": transformation}
    except Exception as error:
        raise HTTPException(status_code=502, detail=f"Pipeline failed: {error}") from error
    finally:
        pipeline_lock.release()
