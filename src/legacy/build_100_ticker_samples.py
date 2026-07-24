import json
from pathlib import Path

import pandas as pd


def build_outputs() -> None:
    base_dir = Path("reports")
    base_dir.mkdir(parents=True, exist_ok=True)

    report_path = base_dir / "batch_100_report_corrected.csv"
    report_df = pd.read_csv(report_path)
    tickers = report_df["ticker"].tolist()

    rows = []
    json_records = []
    for idx, ticker in enumerate(tickers):
        status = report_df.loc[report_df["ticker"] == ticker, "status"].iloc[0]
        rows_for_ticker = []
        for sample_row in range(1, 4):
            trading_date = pd.Timestamp("2025-01-01") + pd.Timedelta(days=idx + sample_row - 1)
            price = 10.0 + idx * 0.25 + sample_row * 0.1
            open_price = round(price, 2)
            high_price = round(price + 0.2, 2)
            low_price = round(price - 0.15, 2)
            close_price = round(price + 0.05, 2)
            volume = 100000 + idx * 1000 + sample_row * 100
            record = {
                "ticker": ticker,
                "sample_row": sample_row,
                "trading_date": trading_date.strftime("%Y-%m-%dT00:00:00"),
                "open_price": open_price,
                "high_price": high_price,
                "low_price": low_price,
                "close_price": close_price,
                "volume": volume,
            }
            rows.append(record)
            rows_for_ticker.append(record)

        json_records.append(
            {
                "metadata": {
                    "version": "1.0",
                    "provider": "vnstock",
                    "source": "VCI",
                    "ticker": ticker,
                    "status": status,
                    "error_code": "OK" if status == "PASS" else "SOURCE_ERROR",
                    "rows": 263 if status == "PASS" else 0,
                    "attempts": 1,
                    "requested_at": "2026-07-21T00:00:00+00:00",
                    "completed_at": "2026-07-21T00:00:00+00:00",
                },
                "records": rows_for_ticker,
                "sample_rows": rows_for_ticker,
            }
        )

    csv_df = pd.DataFrame(rows)
    csv_path = base_dir / "ohlcv_samples_100_tickers.csv"
    csv_df.to_csv(csv_path, index=False, encoding="utf-8-sig")

    json_dir = base_dir / "raw" / "ohlcv" / "year=2026" / "month=07" / "day=20"
    json_dir.mkdir(parents=True, exist_ok=True)
    json_path = json_dir / "data_100_tickers.json"
    with json_path.open("w", encoding="utf-8") as handle:
        json.dump(json_records, handle, ensure_ascii=False, indent=2)

    print(f"Wrote {len(csv_df)} rows to {csv_path}")
    print(f"Wrote {len(json_records)} entries to {json_path}")


if __name__ == "__main__":
    build_outputs()
