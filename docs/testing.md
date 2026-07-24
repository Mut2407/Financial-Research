# Chiến lược kiểm thử và CI

## 1. Phạm vi và nguyên tắc

Bộ test xác minh vertical slice local theo `docs/requirements.md` và `docs/contracts.md`:

```text
Source adapter → Raw JSON → validation/transform → Curated Parquet
      → DuckDB/DataService → FastAPI → Streamlit user flows
```

Test mặc định hoàn toàn deterministic, không gọi internet, không đọc `.env` của người dùng và không cần API key. Test có khả năng gọi nguồn thật phải mang marker `live`; CI mặc định luôn loại marker này.

## 2. Phân vùng test

| Phân vùng | Marker | Nội dung |
|---|---|---|
| Pipeline unit | `unit and not frontend` | Schema OHLCV, DQ rules, error classification, retry/backoff, raw partition, transform, deduplicate, indicator |
| API unit | `unit and not frontend` | DuckDB service, pagination, date filter, export query, parameter binding |
| API integration | `integration and not frontend and not performance` | Health, companies, prices, ZIP manifest, pipeline orchestration và lock |
| Frontend | `frontend` | HTTP client và luồng Login → Dashboard, Register, lỗi backend, Data Explorer |
| Performance | `performance` | Đo p95 consumption API và duration từng stage của vertical slice 20 ticker/500 record |
| Container | `container` | Cấu trúc Compose, dependency ordering, healthcheck và image lock contract |
| Live source | `live` | Vnstock Free API, một ticker/14 ngày, manual dispatch và GitHub Secret |

## 3. Requirement traceability

| Requirement | Bằng chứng tự động | Trạng thái |
|---|---|---|
| FR-01 Source/key/rate-limit/retry/error | `test_source.py`, `test_ingestion.py`, `test_vnstock_api.py` | Deterministic đủ; live được xác minh khi manual job có secret |
| FR-02 Raw JSON, metadata, partition, reject bad data | `test_models.py`, `test_ingestion.py` | Đủ |
| FR-03 Deduplicate, Return/MA20/RSI14, Parquet/ticker | `test_transform.py` | Đủ |
| FR-04 FastAPI/DuckDB/filter/export | `test_data_service.py`, `test_endpoints.py` | Đủ |
| FR-05 FE chỉ dùng HTTP API, không mock runtime | `test_api_client.py`, `test_user_flows.py` | Đủ |
| FR-06 Data Explorer live batch → preview API | `test_pipeline_endpoint.py`, `test_user_flows.py`, live source contract | Đủ; external call chỉ manual để bảo vệ quota |
| FR-07 uv lock/Python 3.12 | GitHub Actions chạy `uv sync --locked`; `.python-version` | Đủ |
| FR-08 Compose startup ordering | `test_compose_contract.py`; CI chạy `docker compose config --quiet` | Static/executable config đủ; full runtime smoke vẫn thủ công |
| NFR parameterized query | `test_ticker_input_is_bound_as_parameter_not_sql` | Đủ |
| NFR source lỗi không xóa dữ liệu cũ | `test_failure_recovery.py`, failure payload và API skip-transform test | Đủ trong local PoC |
| Health phản ánh curated | Test health cho cả curated có dữ liệu và trống | Đủ |
| Raw sẵn sàng trước 18:00 UTC+7 | Không có scheduler/S3 trong PoC | Không thể tự động hóa trong runtime hiện tại |

Những dòng “một phần/chưa có” là gap của phạm vi runtime, không được che bằng test giả tạo.

## 4. Latency measurement và candidate gate

Repo chưa định nghĩa product SLO p50/p95/p99 cho FE, API hoặc transform. Con số duy nhất trong tài liệu dự án là giả định kiến trúc trung bình `5s/request` tại `artifacts/execute/ARCHITECTURE_COMPARISON.md`. Vì vậy suite hiện:

- đo p95 của 30 lần gọi `GET /prices` local;
- đo riêng ingestion, transform và consumption API của vertical slice 20 ticker/500 record;
- ghi các giá trị vào JUnit properties và report duration;
- lưu **5.000 ms** trong `tests/quality_gates.toml` như candidate có truy vết, không phải SLA production.

`enforce = false`, nên CI chưa hard-fail theo con số chưa được phê duyệt.

Mỗi test còn có timeout 30 giây để phát hiện deadlock/hang. Khi Product Owner duyệt SLO chính thức, cập nhật ngưỡng, đặt `enforce = true` và bổ sung các gate riêng cho source, transform, API và FE; không diễn giải 5 giây thành SLO cho mọi tầng.

## 5. Chạy local

Cài dependency đúng lock:

```bash
uv sync --frozen
```

Chạy toàn bộ deterministic suite và tạo báo cáo:

```bash
uv run pytest -m "not live" --timeout=30 \
  --junitxml=reports/tests/junit.xml \
  --cov=src --cov=frontend \
  --cov-report=term-missing \
  --cov-report=xml:reports/tests/coverage.xml \
  --cov-fail-under=80
```

Trên PowerShell có thể chạy cùng lệnh trên một dòng. Các lệnh theo phân vùng:

```bash
uv run pytest -m "unit and not frontend"
uv run pytest -m "integration and not frontend and not performance"
uv run pytest -m "frontend"
uv run pytest -m "performance"
```

## 6. File báo cáo

Mỗi lần chạy pytest tự tạo:

- `reports/tests/test-summary.json`: tổng số pass/fail/skip, số case theo component, thời gian và 10 test chậm nhất.
- `reports/tests/test-results.csv`: từng test, component, marker, outcome, duration và lỗi.
- `reports/tests/junit.xml`: kết quả chuẩn cho GitHub/CI khi truyền `--junitxml`.
- `reports/tests/coverage.xml`: coverage khi truyền `--cov-report=xml`.

Các report runtime bị `.gitignore`; CI lưu chúng dưới dạng artifact 14 ngày.

## 7. GitHub Actions

Workflow `.github/workflows/qa.yml` chạy khi push vào nhánh chính, pull request hoặc manual dispatch. Bốn partition chạy độc lập để dễ khoanh vùng lỗi; sau đó full regression áp gate coverage 80%. Push/PR luôn loại marker `live`.

Manual dispatch bổ sung job `Manual Vnstock Free API contract` trên GitHub-hosted runner. Job đọc repository secret `VNSTOCK_API_KEY`, gọi một ticker và xuất JUnit/report riêng trong 7 ngày. Nếu secret chưa được cấu hình, job fail-fast mà không gọi mạng.

Chạy live local có chủ ý:

```powershell
$env:RUN_VNSTOCK_LIVE_TESTS="1"
uv run pytest -m live --junitxml=reports/tests/live-junit.xml
```

Key được đọc từ `.env` bởi runtime hoặc biến môi trường `VNSTOCK_API_KEY`; không truyền key trên command line. Xem ranh giới secret tại `docs/provider-auth.md`.
