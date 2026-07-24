# Pipeline Architecture and Data Source Report

**Project:** Financial Data Pipeline

**Date:** 2026-07-19

## 1. Executive Summary

This project uses a single data source for the full pipeline: **`vnstock` with the `VCI` provider**. The pipeline is organized into three main stages:

1. **Master data collection** for listed companies.
2. **Universe building** for a fixed 100-ticker basket.
3. **Market data validation** through OHLCV smoke testing.

The implementation no longer depends on Hugging Face datasets. The same provider layer is used for both master data and market data, which keeps the pipeline consistent and easier to explain in a report.

## 2. Data Source Used

The current source stack is:

- **Access library:** `vnstock`
- **Data provider:** `VCI`

In practice:

- `Reference().equity.list(source="VCI")` is used to retrieve the ticker universe.
- `Reference().equity.list_by_exchange(source="VCI")` is used to obtain exchange labels.
- `Company(symbol, source="VCI").overview()` is used to enrich each ticker with company metadata.
- `Quote(symbol, source="VCI").history(...)` is used to retrieve OHLCV market data.

### Why this source setup

- One unified source for both master data and market data.
- No dependency on external static CSV datasets such as Hugging Face.
- Easier to explain in documentation: **`vnstock` is the access layer, `VCI` is the data provider**.

## 3. Pipeline Architecture

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

### Stage 1: Master Data Collection

File: [src/download_listed_companies.py](../src/download_listed_companies.py)

Responsibilities:

- Pull all symbols from `Reference().equity.list(source="VCI")`.
- Pull exchange labels from `Reference().equity.list_by_exchange(source="VCI")`.
- Normalize exchange names so that the final master file uses:
  - `HOSE`
  - `HNX`
  - `UPCOM`
- Enrich each ticker using `Company(symbol, source="VCI").overview()`.
- Save the result to [data/listed_companies.csv](../data/listed_companies.csv).

Current selection rule:

- `70` tickers from `HOSE`
- `20` tickers from `HNX`
- `10` tickers from `UPCOM`

This produces a fixed **100-ticker master set**.

### Stage 2: Universe Building

File: [src/build_universe.py](../src/build_universe.py)

Responsibilities:

- Read [data/listed_companies.csv](../data/listed_companies.csv).
- Normalize schema and market labels if needed.
- Build the final versioned universe.
- Save the output to [universe/ticker_universe_v1.csv](../universe/ticker_universe_v1.csv).

Final output columns:

- `ticker`
- `name`
- `market`
- `sector`
- `version`
- `effective_date`

### Stage 3: Smoke Test and Evidence

File: [src/smoke_test.py](../src/smoke_test.py)

Responsibilities:

- Read [universe/ticker_universe_v1.csv](../universe/ticker_universe_v1.csv).
- Take the first 10 tickers.
- Call `StockProvider.get_ohlcv()` for each ticker.
- Classify failures with normalized error codes.
- Save the summary report to [reports/smoke_test_report.csv](../reports/smoke_test_report.csv).
- Save a direct OHLCV sample evidence file to [reports/ohlcv_samples_10_tickers.csv](../reports/ohlcv_samples_10_tickers.csv).

## 4. OHLCV Structure

The OHLCV DataFrame returned by the provider contains these columns:

- `time`
- `open`
- `high`
- `low`
- `close`
- `volume`

This is the actual market data used for downstream analysis.

## 5. Current Evidence Files

The pipeline currently produces these evidence artifacts:

- [data/listed_companies.csv](../data/listed_companies.csv)
- [universe/ticker_universe_v1.csv](../universe/ticker_universe_v1.csv)
- [reports/smoke_test_report.csv](../reports/smoke_test_report.csv)
- [reports/ohlcv_samples_10_tickers.csv](../reports/ohlcv_samples_10_tickers.csv)

### Verified results

- The universe file contains **100 tickers**.
- The smoke test covers **10 tickers**.
- The current smoke test report shows **10/10 PASS**.
- The OHLCV sample file shows direct rows of `time`, `open`, `high`, `low`, `close`, `volume` for each tested ticker.

## 6. Implementation Notes

### Master data quality

The master data file is enriched from the provider, so it contains more than just ticker and company name. It includes fields such as:

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

### Error handling in smoke test

The smoke test writes a normalized `error_code` field so failures are easier to explain:

- `OK`
- `NO_DATA`
- `RATE_LIMIT`
- `INVALID_TICKER`
- `SOURCE_ERROR`

## 7. Recommended Report Wording

You can describe the pipeline like this:

> The project uses a unified data pipeline based on `vnstock` and the `VCI` provider. `Reference()` is used to collect listed symbols and exchange metadata, `Company().overview()` is used to enrich master data, and `Quote().history()` is used to retrieve OHLCV market data. The pipeline produces a versioned universe of 100 tickers and validates the first 10 tickers through a smoke test report and a separate OHLCV evidence file.

## 8. Conclusion

This architecture is consistent, reproducible, and easier to defend in a project report because it relies on one source of truth for both master data and market data. The outputs are versioned, the universe is fixed at 100 tickers, and the market-data smoke test has both summary and direct OHLCV evidence.
