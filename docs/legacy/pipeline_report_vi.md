# Báo Cáo Kiến Trúc Pipeline Và Nguồn Dữ Liệu

**Dự án:** Financial Data Pipeline

**Ngày:** 2026-07-19

## 1. Tóm tắt

Dự án này sử dụng một nguồn dữ liệu duy nhất cho toàn bộ pipeline: **`vnstock` với provider `VCI`**. Pipeline được tổ chức thành 3 giai đoạn chính:

1. **Thu thập master data** cho các công ty niêm yết.
2. **Dựng universe** cố định gồm 100 ticker.
3. **Kiểm tra market data** bằng smoke test OHLCV.

Giải pháp hiện tại không còn phụ thuộc vào dataset từ Hugging Face. Cùng một lớp truy cập dữ liệu được dùng cho cả master data và market data, nên pipeline nhất quán và dễ mô tả trong báo cáo.

## 2. Nguồn Dữ Liệu Sử Dụng

Stack dữ liệu hiện tại gồm:

- **Thư viện truy cập:** `vnstock`
- **Nhà cung cấp dữ liệu:** `VCI`

Cụ thể:

- `Reference().equity.list(source="VCI")` dùng để lấy danh sách ticker.
- `Reference().equity.list_by_exchange(source="VCI")` dùng để lấy thông tin sàn.
- `Company(symbol, source="VCI").overview()` dùng để làm giàu metadata của từng ticker.
- `Quote(symbol, source="VCI").history(...)` dùng để lấy dữ liệu OHLCV.

### Vì sao chọn kiến trúc này

- Dùng một nguồn duy nhất cho cả master data và market data.
- Không phụ thuộc vào CSV tĩnh từ bên ngoài như Hugging Face.
- Dễ giải thích trong báo cáo: **`vnstock` là lớp truy cập dữ liệu, `VCI` là nhà cung cấp dữ liệu**.

## 3. Kiến Trúc Pipeline

```mermaid
flowchart TD
    A[vnstock + VCI] --> B[Reference.equity.list()]
    A --> C[Reference.equity.list_by_exchange()]
    B --> D[download_listed_companies.py]
    C --> D
    D --> E[data/listed_companies.csv]
    E --> F[build_universe.py]
    F --> G[universe/ticker_universe_v1.csv]
    G --> H[smoke_test.py]
    H --> I[reports/smoke_test_report.csv]
    H --> J[reports/ohlcv_samples_10_tickers.csv]
```

### Giai đoạn 1: Thu Thập Master Data

File: [src/download_listed_companies.py](../src/download_listed_companies.py)

Nhiệm vụ:

- Lấy toàn bộ symbol từ `Reference().equity.list(source="VCI")`.
- Lấy nhãn sàn từ `Reference().equity.list_by_exchange(source="VCI")`.
- Chuẩn hóa tên sàn để file master cuối cùng chỉ dùng:
  - `HOSE`
  - `HNX`
  - `UPCOM`
- Làm giàu từng ticker bằng `Company(symbol, source="VCI").overview()`.
- Lưu kết quả vào [data/listed_companies.csv](../data/listed_companies.csv).

Quy tắc chọn hiện tại:

- `70` ticker từ `HOSE`
- `20` ticker từ `HNX`
- `10` ticker từ `UPCOM`

Như vậy master set có cố định **100 ticker**.

### Giai đoạn 2: Dựng Universe

File: [src/build_universe.py](../src/build_universe.py)

Nhiệm vụ:

- Đọc [data/listed_companies.csv](../data/listed_companies.csv).
- Chuẩn hóa schema và nhãn sàn nếu cần.
- Dựng universe cuối cùng có version.
- Lưu ra [universe/ticker_universe_v1.csv](../universe/ticker_universe_v1.csv).

Các cột cuối cùng:

- `ticker`
- `name`
- `market`
- `sector`
- `version`
- `effective_date`

### Giai đoạn 3: Smoke Test Và Evidence

File: [src/smoke_test.py](../src/smoke_test.py)

Nhiệm vụ:

- Đọc [universe/ticker_universe_v1.csv](../universe/ticker_universe_v1.csv).
- Lấy 10 ticker đầu tiên.
- Gọi `StockProvider.get_ohlcv()` cho từng ticker.
- Chuẩn hóa mã lỗi nếu có fail.
- Lưu report summary vào [reports/smoke_test_report.csv](../reports/smoke_test_report.csv).
- Lưu file evidence OHLCV riêng vào [reports/ohlcv_samples_10_tickers.csv](../reports/ohlcv_samples_10_tickers.csv).

## 4. Cấu Trúc OHLCV

DataFrame OHLCV trả về từ provider có các cột:

- `time`
- `open`
- `high`
- `low`
- `close`
- `volume`

Đây là dữ liệu thị trường thực tế dùng cho các bước phân tích tiếp theo.

## 5. Các File Evidence Hiện Tại

Pipeline hiện tạo ra các file evidence sau:

- [data/listed_companies.csv](../data/listed_companies.csv)
- [universe/ticker_universe_v1.csv](../universe/ticker_universe_v1.csv)
- [reports/smoke_test_report.csv](../reports/smoke_test_report.csv)
- [reports/ohlcv_samples_10_tickers.csv](../reports/ohlcv_samples_10_tickers.csv)

### Kết quả đã xác nhận

- File universe có **100 ticker**.
- Smoke test kiểm tra **10 ticker**.
- Report hiện tại cho thấy **10/10 PASS**.
- File OHLCV sample hiển thị trực tiếp các dòng `time`, `open`, `high`, `low`, `close`, `volume` cho từng ticker được test.

## 6. Ghi Chú Cài Đặt

### Chất lượng master data

File master data được làm giàu trực tiếp từ provider, nên không chỉ có ticker và tên công ty mà còn có các trường như:

- `market`
- `sector`
- `listing`
- `listing_date`
- `short_name`
- `company_profile`
- `com_type_code`
- `com_group_code`
- `tag`
- `icb_code_lv2`

### Xử lý lỗi trong smoke test

Smoke test ghi thêm cột `error_code` chuẩn hóa để dễ mô tả khi có lỗi:

- `OK`
- `NO_DATA`
- `RATE_LIMIT`
- `INVALID_TICKER`
- `SOURCE_ERROR`

## 7. Câu Mô Tả Khuyến Nghị Cho Báo Cáo

Bạn có thể mô tả pipeline như sau:

> Dự án sử dụng một pipeline dữ liệu thống nhất dựa trên `vnstock` và provider `VCI`. `Reference()` được dùng để thu thập danh sách niêm yết và thông tin sàn, `Company().overview()` dùng để làm giàu master data, và `Quote().history()` dùng để lấy dữ liệu OHLCV. Pipeline tạo ra universe version hóa gồm 100 ticker và kiểm tra 10 ticker đầu tiên thông qua report smoke test và file evidence OHLCV riêng.

## 8. Kết Luận

Kiến trúc này nhất quán, dễ tái tạo và dễ giải thích trong báo cáo vì dựa trên một nguồn sự thật duy nhất cho cả master data và market data. Output được version hóa, universe cố định ở mức 100 ticker, và kiểm tra market data có đủ cả report tổng hợp lẫn evidence OHLCV trực tiếp.
