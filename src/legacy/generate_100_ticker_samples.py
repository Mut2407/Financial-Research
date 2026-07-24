import json
import logging
import time
from pathlib import Path

import pandas as pd

from ohlcv import OHLCVAdapter, OHLCVWorker, load_tickers_from_universe


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
    logger = logging.getLogger("generate_100_ticker_samples")

    tickers = load_tickers_from_universe(limit=100)
    logger.info("Loaded %s tickers", len(tickers))

    worker = OHLCVWorker(
        adapter=OHLCVAdapter(retries=3, backoff_seconds=2.0),
        output_dir=Path("reports"),
        raw_layer_dir=Path("reports/raw/ohlcv"),
        sample_rows=263,
        logger=logger,
    )

    csv_parts = []
    json_entries = []
    report_rows = []
    for index, ticker in enumerate(tickers):
        requested_at = pd.Timestamp.utcnow().isoformat()
        try:
            data, attempts = worker.adapter.fetch(
                ticker=ticker, start="2025-01-01", end="2025-12-31", interval="1D"
            )
            normalized = worker._normalize_history_frame(ticker, data)
            sample = normalized.head(263).copy()
            sample.insert(1, "sample_row", range(1, len(sample) + 1))
            csv_parts.append(sample)
            records = sample.drop(columns=["sample_row"]).to_dict(orient="records")
            json_entries.append({
                "metadata": {
                    "version": "1.0", "provider": "vnstock", "source": worker.adapter.source,
                    "ticker": ticker, "status": "PASS", "error_code": "OK",
                    "rows": len(normalized), "attempts": attempts,
                    "requested_at": requested_at, "completed_at": pd.Timestamp.utcnow().isoformat(),
                },
                "records": records,
                "sample_rows": records,
            })
            report_rows.append({"ticker": ticker, "status": "PASS", "error_code": "OK", "rows": len(normalized), "message": "OK"})
        except Exception as error:
            report_rows.append({"ticker": ticker, "status": "FAIL", "error_code": "SOURCE_ERROR", "rows": 0, "message": str(error)})
        if index < len(tickers) - 1:
            time.sleep(3)

    csv_path = Path("reports/ohlcv_samples_100_tickers.csv")
    pd.concat(csv_parts, ignore_index=True).to_csv(csv_path, index=False, encoding="utf-8-sig")
    json_path = Path("reports/raw/ohlcv/year=2026/month=07/day=20/data_100_tickers.json")
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(json_entries, ensure_ascii=False, indent=2), encoding="utf-8")
    pd.DataFrame(report_rows).to_csv("reports/smoke_test_report_100.csv", index=False, encoding="utf-8-sig")

    print("=" * 60)
    print("GENERATED 100-TICKER SAMPLE OUTPUT")
    print("=" * 60)
    print(f"CSV output: {csv_path}")
    print(f"JSON output: {json_path}")
    print("Report output: reports/smoke_test_report_100.csv")


if __name__ == "__main__":
    main()
