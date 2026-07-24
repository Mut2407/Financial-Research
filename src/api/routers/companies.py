from fastapi import APIRouter, Depends, HTTPException, Query
from src.api.schemas.api_models import CompanyListResponse
from src.api.dependencies import get_data_service
from src.api.services.data_service import DataService

router = APIRouter(prefix="/companies", tags=["Companies"])

@router.get("", response_model=CompanyListResponse)
def get_companies(
    page: int = Query(1, ge=1, description="Trang hiện tại"),
    limit: int = Query(50, ge=1, le=100, description="Số lượng kết quả mỗi trang"),
    data_service: DataService = Depends(get_data_service)
):
    """Return companies that actually exist in the curated layer."""
    try:
        return data_service.get_companies(page, limit)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi Server: {str(e)}")
