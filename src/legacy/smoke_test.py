import pandas as pd
from provider import StockProvider
import os


def classify_error(error: Exception) -> str:
    message = str(error).lower()

    if any(token in message for token in ["rate limit", "ratelimit", "giới hạn api"]):
        return "RATE_LIMIT"

    if any(token in message for token in ["no data", "emptydata", "no rows"]):
        return "NO_DATA"

    if any(token in message for token in ["invalid", "not found", "không hợp lệ", "symbol"]):
        return "INVALID_TICKER"

    return "SOURCE_ERROR"

# Đọc universe
df = pd.read_csv("universe/ticker_universe_v1.csv")

# Lấy 10 ticker đầu tiên
tickers = df["ticker"].head(10)

provider = StockProvider()

results = []
ohlcv_samples = []

for ticker in tickers:
    print(f"Testing {ticker}...")

    try:
        data = provider.get_ohlcv(ticker)

        if data is None or data.empty:
            status = "FAIL"
            rows = 0
            error_code = "NO_DATA"
            message = "No data returned"

        else:
            status = "PASS"
            rows = len(data)
            error_code = "OK"
            message = "OK"

            sample = data.head(3).copy()
            sample.insert(0, "ticker", ticker)
            sample.insert(1, "sample_row", range(1, len(sample) + 1))
            ohlcv_samples.append(sample)

    except Exception as e:
        status = "FAIL"
        rows = 0
        error_code = classify_error(e)
        message = str(e)

    results.append({
        "ticker": ticker,
        "status": status,
        "error_code": error_code,
        "rows": rows,
        "message": message
    })

report = pd.DataFrame(results)

os.makedirs("reports", exist_ok=True)

report.to_csv(
    "reports/smoke_test_report.csv",
    index=False,
    encoding="utf-8-sig"
)

if ohlcv_samples:
    ohlcv_report = pd.concat(ohlcv_samples, ignore_index=True)
else:
    ohlcv_report = pd.DataFrame(columns=["ticker", "sample_row", "time", "open", "high", "low", "close", "volume"])

ohlcv_report.to_csv(
    "reports/ohlcv_samples_10_tickers.csv",
    index=False,
    encoding="utf-8-sig"
)

print("\n========== SUMMARY ==========")
print(report)
print("=============================")
print("Saved -> reports/smoke_test_report.csv")
print("Saved -> reports/ohlcv_samples_10_tickers.csv")
