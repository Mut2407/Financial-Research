# PoC Requirements Baseline

## Mục tiêu

Chứng minh trên local một vertical slice chạy được từ nguồn dữ liệu thật đến giao diện tiêu thụ, đủ rõ để nhóm đánh giá tính khả thi, công sức vận hành và hướng scale tiếp theo.

## Functional requirements

| ID | Yêu cầu | Tiêu chí chấp nhận |
|---|---|---|
| FR-01 | Nguồn dữ liệu | Adapter gọi Vnstock Free Unified API bằng `VNSTOCK_API_KEY`, chỉ interval `1D`, có retry, rate limit tối đa 60 RPM và lỗi chuẩn hóa. |
| FR-02 | Raw layer | Ghi JSON có metadata và record theo partition ngày; không ghi record sai contract. |
| FR-03 | Curated layer | Đọc raw, deduplicate theo ticker/ngày, tính Return/MA20/RSI14, ghi Parquet theo ticker. |
| FR-04 | Consumption API | FastAPI/DuckDB đọc trực tiếp curated; hỗ trợ companies, prices, date filter và export. |
| FR-05 | FE–BE | Streamlit chỉ lấy market data qua HTTP API, không sinh OHLCV ngẫu nhiên. |
| FR-06 | Live PoC | Data Explorer cho phép chạy batch nhỏ từ nguồn thật và xem kết quả qua API. |
| FR-07 | Reproducibility | Dependency được khóa bằng `uv.lock`; local runtime dùng Python 3.12. |
| FR-08 | Container | Một lệnh `docker compose up --build` bootstrap pipeline, backend và frontend đúng thứ tự. |

## Data quality rules

1. Các trường OHLCV bắt buộc phải tồn tại.
2. Giá phải lớn hơn 0; volume không âm.
3. `high_price >= low_price`.
4. Ticker được chuẩn hóa uppercase và chỉ chứa ký tự an toàn.
5. Curated loại trùng theo `(ticker, trading_date)`, giữ record mới nhất.

## Configuration requirements

- `uv` quản lý/sync dependency; `uvicorn` chạy FastAPI.
- `.env` chỉ chứa runtime configuration/secrets và không được commit.
- Live ingestion yêu cầu `VNSTOCK_API_KEY`; key để trống trong `.env.example` và chỉ điền ở `.env` local/GitHub Secret.
- Free tier chỉ dùng interval `1D` và không cấu hình vượt 60 request/phút.
- `pyproject.toml` và `uv.lock` là dependency sources chính thức, không duy trì requirements phân tán.

## Non-functional requirements

- Local-first, deterministic bootstrap không phụ thuộc source availability.
- Các query do người dùng cung cấp phải parameterized.
- Source lỗi không làm mất raw/curated đã có.
- Backend health phải phản ánh curated availability.
- Test phải bao phủ ingestion contract, transform và API consumption.

## Ngoài phạm vi PoC

- Production authentication/authorization.
- Scheduler, queue và distributed workers.
- S3/Glue/Athena/MinIO production-equivalent deployment.
- High availability, autoscaling và full observability stack.
- Cam kết SLA market data của bên thứ ba.
