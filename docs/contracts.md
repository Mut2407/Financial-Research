# DATA CONTRACT: OHLCV INGESTION (v1.0)

**Data Producer:** Ingestion Service / Adapter (Nguồn sinh dữ liệu)
**Data Consumer:** Data Engineering / ETL Pipeline (Nguồn tiêu thụ dữ liệu)

## 1. Mục tiêu
Văn bản này quy định định dạng, tiêu chuẩn chất lượng (Data Quality) và cam kết SLA bắt buộc đối với dữ liệu thô (Raw Data) do các tiến trình Ingestion thu thập trước khi đẩy vào Data Lake, nhằm phục vụ cho các module phân tích của hệ thống.

## 2. Định dạng & Lưu trữ (Raw Layer)
- **Format file:** `.json`
- **Cấu trúc JSON:** Bắt buộc tuân theo Schema `DailyStockPrice` và `IngestionMetadata` đã định nghĩa.
- **Quy tắc ánh xạ (Mapping):** Tiến trình Producer phải tự động ánh xạ tên cột từ API gốc sang chuẩn hệ thống trước khi ghi file:
  - `time` -> `trading_date`
  - `open`, `high`, `low`, `close` -> `open_price`, `high_price`, `low_price`, `close_price`
- **Phân vùng local PoC:**
  `data/raw/ohlcv/year=YYYY/month=MM/day=DD/batch_<UTC timestamp>.json`
- **Phân vùng đích khi scale lên S3:**
  `s3://<raw-bucket-name>/ohlcv/year=YYYY/month=MM/day=DD/batch_<UTC timestamp>.json`

## 3. SLA & Cam Kết Thời Gian (Service Level Agreement)
- **Chu kỳ chạy:** Tiến trình Producer tự động chạy vào cuối mỗi ngày giao dịch.
- **Thời gian khả dụng (Availability):** Dữ liệu thô phải sẵn sàng tại S3 Raw Bucket muộn nhất vào **18:00 (Giờ VN - UTC+7)** mỗi ngày để hệ thống ETL tiếp quản.

## 4. Quy tắc Chất lượng dữ liệu (Data Quality - DQ Rules)
Tiến trình Producer bắt buộc xử lý các ngoại lệ sau trước khi dữ liệu hạ cánh:
1. **Tính toàn vẹn (Completeness):** Bất kỳ mã cổ phiếu nào thiếu các trường bắt buộc (đặc biệt là `trading_date`, `close_price`, `volume`) sẽ bị reject (từ chối).
2. **Logic Giá trị:** Giá (Open/High/Low/Close) <= 0 hoặc Volume < 0 bị đánh dấu là Bad Data.
3. **Logic Kỹ thuật:** Giá `high_price` bắt buộc phải >= `low_price`.
4. **Phạm vi dữ liệu (Scope):** Bootstrap PoC dùng universe 100 mã hiện có; live ingestion nhận batch nhỏ do người dùng chỉ định.

## 5. Curated Layer

- Format: Parquet.
- Partition: `data/curated/ohlcv/ticker=<TICKER>/part-000.parquet`.
- Khóa logic: `(ticker, trading_date)`.
- Cột canonical: `ticker`, `trading_date`, `open_price`, `high_price`, `low_price`, `close_price`, `volume`.
- Cột dẫn xuất: `return_pct`, `ma20`, `rsi_14`.
