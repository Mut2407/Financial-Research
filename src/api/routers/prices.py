from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
import io
import json
import zipfile
from datetime import date, datetime, timezone
from src.api.schemas.api_models import PriceListResponse
from src.api.dependencies import get_data_service
from src.api.services.data_service import DataService

router = APIRouter(prefix="/prices", tags=["Prices"])

@router.get("", response_model=PriceListResponse)
def get_prices(
    ticker: str = Query(..., description="Mã chứng khoán cần tra cứu"),
    start_date: date | None = Query(None, description="Ngày bắt đầu (YYYY-MM-DD)"),
    end_date: date | None = Query(None, description="Ngày kết thúc (YYYY-MM-DD)"),
    page: int = Query(1, ge=1, description="Trang hiện tại"),
    limit: int = Query(10000, ge=1, le=10000, description="Số lượng kết quả mỗi trang"),
    data_service: DataService = Depends(get_data_service)
):
    """Query curated OHLCV data with optional date filters."""
    if start_date and end_date and start_date > end_date:
        raise HTTPException(status_code=422, detail="start_date must not be after end_date")
    try:
        return data_service.get_prices(
            ticker,
            start_date.isoformat() if start_date else None,
            end_date.isoformat() if end_date else None,
            page,
            limit,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi Server: {str(e)}")


@router.get("/export")
def export_prices(
    ticker: str = Query(..., description="Mã chứng khoán cần Export"),
    format: str = Query("csv", pattern="^(csv|parquet)$", description="Định dạng tải về (csv hoặc parquet)"),
    data_service: DataService = Depends(get_data_service)
):
    """
    API tải dữ liệu thành file ZIP kèm Manifest (Task K14)
    """
    try:
        df = data_service.get_prices_for_export(ticker)
        if df is None or df.empty:
            raise HTTPException(status_code=404, detail=f"Không có dữ liệu cho mã {ticker}")
            
        data_stream = io.BytesIO()
        data_filename = f"{ticker}_data.{format}"
        if format == "csv":
            df.to_csv(data_stream, index=False)
        else:
            df.to_parquet(data_stream, index=False)
            
        manifest = {
            "source": "Local Data Lake (Parquet)",
            "ticker": ticker,
            "export_time": datetime.now(timezone.utc).isoformat(),
            "format": format,
            "row_count": len(df),
            "columns": list(df.columns),
            "schema_version": "1.0"
        }
        
        zip_stream = io.BytesIO()
        with zipfile.ZipFile(zip_stream, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
            zf.writestr(data_filename, data_stream.getvalue())
            zf.writestr("manifest.json", json.dumps(manifest, indent=4))
            
        zip_stream.seek(0)
        return StreamingResponse(
            iter([zip_stream.getvalue()]),
            media_type="application/zip",
            headers={"Content-Disposition": f"attachment; filename={ticker}_export.zip"}
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi Server: {str(e)}")
