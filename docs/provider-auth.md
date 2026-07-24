# Contract xác thực Vnstock Free API

## Contract đã chốt

| Thuộc tính | Giá trị |
|---|---|
| Tier | Free |
| Python client | `vnstock>=4.0.3,<5`, lock hiện tại trong `uv.lock` |
| Public API surface | `Market().equity(symbol).ohlcv(start, end, resolution="1D")` trong lock 4.0.x |
| Credential | `VNSTOCK_API_KEY` |
| Interval | Chỉ `1D` |
| Rate guard | 1–60 request/phút |
| CI runner | GitHub-hosted |
| Latency policy | Characterization-only; không hard-fail khi SLO còn `TBD` |

Vnstock không công bố một REST base URL/header contract để ứng dụng tự gọi trực tiếp bằng `requests`. Contract public được hỗ trợ là Unified API thông qua client `vnstock.Market`; client kết nối REST provider ở bên dưới. Không sao chép URL nội bộ từ SDK thành application contract vì URL đó có thể thay đổi mà không có cam kết tương thích.

API/FE/CLI của dự án vẫn dùng tên canonical `interval="1D"`; adapter map sang `resolution="1D"` của package 4.0.x. Unit test kiểm tra chữ ký dependency để phát hiện breaking change khi nâng lock.

Nguồn chính thức:

- [Vnstock Free Market Data / Unified UI](https://vnstocks.com/docs/vnstock/du-lieu-thi-truong-market-data)
- [So sánh Free và Sponsor](https://vnstocks.com/docs/vnstock/so-sanh-free-va-sponsor)
- [Lịch sử phiên bản và xác thực API key](https://vnstocks.com/docs/tai-lieu/lich-su-phien-ban)

## Cấu hình local

Sao chép `.env.example` thành `.env` và chỉ điền file local:

```dotenv
DATA_PROVIDER="VNSTOCK_FREE"
VNSTOCK_API_KEY="<điền key tại máy local>"
VNSTOCK_REQUESTS_PER_MINUTE="60"
```

`DATA_PROVIDER_API_KEY` là vị trí dự phòng cho provider khác và không được adapter Vnstock sử dụng.

`VNSTOCK_API_KEY` được Pydantic giữ bằng `SecretStr`, không đưa vào response, frontend, report, Dockerfile hay source control. Adapter chỉ chuyển key sang biến môi trường chính thức trước khi lazy-import `vnstock.Market`.

## GitHub Actions

1. Vào repository **Settings → Secrets and variables → Actions**.
2. Tạo repository secret tên chính xác `VNSTOCK_API_KEY`.
3. Mở **Actions → QA → Run workflow**.
4. Job `Manual Vnstock Free API contract` gọi đúng một ticker `FPT` trong 14 ngày gần nhất, kiểm tra schema/DQ và ghi `source_latency_ms` vào JUnit.

Push và pull request không gọi Vnstock. Live job chỉ chạy khi `workflow_dispatch`, nên không tiêu quota trong CI thường lệ.

## Guard và hành vi lỗi

- Thiếu key: fail-fast trước request.
- `VNSTOCK_REQUESTS_PER_MINUTE` ngoài 1–60: fail-fast.
- Interval khác `1D`: trả validation error ở FE/CLI/API boundary và bị source từ chối lần nữa.
- Lỗi tạm thời: tối đa 3 attempt với exponential backoff; mỗi attempt vẫn qua rate limiter.
- Provider lỗi: ghi failure evidence mới, không xóa Raw/Curated hiện có.
- Không tự động fallback sang guest/VCI adapter vì fallback sẽ làm sai contract xác thực và quota kỳ vọng.

## Nâng cấp sau PoC

Free tier không đáp ứng mục tiêu cao hơn 60 RPM. Khi cần 180–600 RPM, phải chốt sponsor tier và chuyển sang private `vnstock_data`; không chỉ tăng biến rate limit. Khi có public direct-HTTP contract riêng, cần cung cấp base URL, authentication header, schema và điều khoản rate limit trước khi thay Unified client bằng `httpx`/`requests`.
