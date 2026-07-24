from fastapi import Depends, HTTPException

from src.api.database import get_db_connection
from src.api.services.data_service import DataService
from src.settings import get_settings


def get_data_service(db=Depends(get_db_connection)) -> DataService:
    if db is None:
        raise HTTPException(status_code=503, detail="DuckDB is unavailable")
    return DataService(db, get_settings())
