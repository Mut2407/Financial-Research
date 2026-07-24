"""
Batch processing with checkpoint support and conservative rate limiting.
Processes 100 tickers with checkpoint recovery for failed items.
"""

import json
import logging
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import pandas as pd

from ohlcv import OHLCVAdapter, OHLCVWorker, load_tickers_from_universe, classify_error


class CheckpointManager:
    """Manages checkpoint state for batch processing."""

    def __init__(self, checkpoint_dir: str | Path = "reports/checkpoints"):
        self.checkpoint_dir = Path(checkpoint_dir)
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)

    def get_checkpoint_path(self, batch_id: str) -> Path:
        return self.checkpoint_dir / f"batch_{batch_id}_checkpoint.json"

    def load_checkpoint(self, batch_id: str) -> dict:
        """Load existing checkpoint or return empty state."""
        checkpoint_path = self.get_checkpoint_path(batch_id)
        if checkpoint_path.exists():
            with checkpoint_path.open("r", encoding="utf-8") as f:
                return json.load(f)
        return {
            "batch_id": batch_id,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "started_at": None,
            "completed": [],
            "failed": [],
            "pending": [],
        }

    def save_checkpoint(self, batch_id: str, state: dict) -> None:
        """Save checkpoint state."""
        checkpoint_path = self.get_checkpoint_path(batch_id)
        with checkpoint_path.open("w", encoding="utf-8") as f:
            json.dump(state, f, indent=2, ensure_ascii=False)

    def mark_ticker_completed(self, batch_id: str, ticker: str, result: dict) -> None:
        """Mark ticker as completed."""
        state = self.load_checkpoint(batch_id)
        if state["started_at"] is None:
            state["started_at"] = datetime.now(timezone.utc).isoformat()

        if ticker in state["pending"]:
            state["pending"].remove(ticker)
        if ticker not in state["completed"]:
            state["completed"].append(ticker)

        state["last_updated_at"] = datetime.now(timezone.utc).isoformat()
        self.save_checkpoint(batch_id, state)

    def mark_ticker_failed(self, batch_id: str, ticker: str, error: str) -> None:
        """Mark ticker as failed."""
        state = self.load_checkpoint(batch_id)
        if state["started_at"] is None:
            state["started_at"] = datetime.now(timezone.utc).isoformat()

        if ticker in state["pending"]:
            state["pending"].remove(ticker)
        if ticker not in state["failed"]:
            state["failed"].append({"ticker": ticker, "error": error, "timestamp": datetime.now(timezone.utc).isoformat()})

        state["last_updated_at"] = datetime.now(timezone.utc).isoformat()
        self.save_checkpoint(batch_id, state)


class BatchProcessor:
    """Processes batch of tickers with rate limiting and checkpoint support."""

    def __init__(
        self,
        adapter: Optional[OHLCVAdapter] = None,
        checkpoint_manager: Optional[CheckpointManager] = None,
        max_workers: int = 2,  # Very conservative: 2 concurrent requests
        rate_limit_delay: float = 3.0,  # 3 seconds between requests (20/min = 3s min)
        output_dir: str | Path = "reports",
        logger: Optional[logging.Logger] = None,
    ):
        self.adapter = adapter or OHLCVAdapter(retries=3, backoff_seconds=2.0)
        self.checkpoint_manager = checkpoint_manager or CheckpointManager()
        self.max_workers = max_workers
        self.rate_limit_delay = rate_limit_delay
        self.output_dir = Path(output_dir)
        self.logger = logger or logging.getLogger(__name__)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def _process_single_ticker(self, ticker: str, start: str, end: str, interval: str) -> dict:
        """Process a single ticker and return result."""
        worker = OHLCVWorker(
            adapter=self.adapter,
            output_dir=self.output_dir,
            sample_rows=3,
            logger=self.logger,
        )

        try:
            data, attempts = self.adapter.fetch(
                ticker=ticker,
                start=start,
                end=end,
                interval=interval,
            )

            if data is None or data.empty:
                return {
                    "ticker": ticker,
                    "status": "FAIL",
                    "error_code": "NO_DATA",
                    "message": "No data returned",
                    "rows": 0,
                    "attempts": attempts,
                }

            normalized_df = worker._normalize_history_frame(ticker, data)
            rows = len(normalized_df)

            return {
                "ticker": ticker,
                "status": "PASS",
                "error_code": "OK",
                "message": "OK",
                "rows": rows,
                "attempts": attempts,
            }

        except Exception as error:
            error_code = classify_error(error)

            # If rate limit, wait and signal for retry
            if error_code == "RATE_LIMIT":
                self.logger.warning(f"Rate limit hit for {ticker}, waiting before retry...")
                time.sleep(35)  # Wait 35 seconds as suggested by API

            return {
                "ticker": ticker,
                "status": "FAIL",
                "error_code": error_code,
                "message": str(error),
                "rows": 0,
                "attempts": self.adapter.retries,
            }

    def run_batch(
        self,
        tickers: list[str],
        batch_id: str = "batch_100",
        start: str = "2025-01-01",
        end: str = "2025-12-31",
        interval: str = "1D",
        resume: bool = True,
    ) -> dict:
        """
        Process batch of tickers with checkpoint support.

        Args:
            tickers: List of tickers to process
            batch_id: Unique batch identifier for checkpointing
            start: Start date
            end: End date
            interval: Time interval
            resume: If True, resume from last checkpoint

        Returns:
            Dictionary with results, report path, and failed list
        """
        checkpoint = self.checkpoint_manager.load_checkpoint(batch_id)

        # Determine which tickers to process
        if resume and checkpoint["completed"]:
            # Resume mode: process only pending and failed
            pending_tickers = [t for t in tickers if t not in checkpoint["completed"]]
            self.logger.info(
                f"Resuming batch {batch_id}: {len(checkpoint['completed'])} completed, "
                f"{len(pending_tickers)} remaining"
            )
        else:
            # Fresh start
            pending_tickers = tickers.copy()
            checkpoint["pending"] = pending_tickers

        checkpoint["pending"] = pending_tickers
        self.checkpoint_manager.save_checkpoint(batch_id, checkpoint)

        results = []
        last_request_time = time.time()

        self.logger.info(f"Processing {len(pending_tickers)} tickers with max_workers={self.max_workers}")

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_ticker = {
                executor.submit(
                    self._process_single_ticker,
                    ticker,
                    start,
                    end,
                    interval,
                ): ticker
                for ticker in pending_tickers
            }

            for future in as_completed(future_to_ticker):
                ticker = future_to_ticker[future]

                try:
                    result = future.result()
                    results.append(result)

                    # Update checkpoint
                    if result["status"] == "PASS":
                        self.checkpoint_manager.mark_ticker_completed(batch_id, ticker, result)
                    else:
                        self.checkpoint_manager.mark_ticker_failed(batch_id, ticker, result["message"])

                    self.logger.info(
                        f"Processed {ticker}: {result['status']} ({result['error_code']}) - {result['rows']} rows"
                    )

                except Exception as exc:
                    error_msg = f"Exception processing {ticker}: {exc}"
                    self.logger.error(error_msg)
                    self.checkpoint_manager.mark_ticker_failed(batch_id, ticker, error_msg)
                    results.append({
                        "ticker": ticker,
                        "status": "FAIL",
                        "error_code": "PROCESSING_ERROR",
                        "message": error_msg,
                        "rows": 0,
                        "attempts": 0,
                    })

                # Rate limiting: ensure minimum delay between requests
                elapsed = time.time() - last_request_time
                if elapsed < self.rate_limit_delay:
                    time.sleep(self.rate_limit_delay - elapsed)
                last_request_time = time.time()

        # Generate report
        report_df = pd.DataFrame(results)
        report_path = self.output_dir / f"batch_100_report.csv"
        report_df.to_csv(report_path, index=False, encoding="utf-8", errors="replace")

        # Generate failed list
        failed_df = report_df[report_df["status"] == "FAIL"].copy()
        failed_list_path = self.output_dir / f"batch_100_failed_list.csv"
        failed_df.to_csv(failed_list_path, index=False, encoding="utf-8", errors="replace")

        # Final checkpoint
        final_checkpoint = self.checkpoint_manager.load_checkpoint(batch_id)
        final_checkpoint["completed_at"] = datetime.now(timezone.utc).isoformat()
        final_checkpoint["stats"] = {
            "total": len(tickers),
            "passed": len(report_df[report_df["status"] == "PASS"]),
            "failed": len(failed_df),
        }
        self.checkpoint_manager.save_checkpoint(batch_id, final_checkpoint)

        return {
            "batch_id": batch_id,
            "report_df": report_df,
            "report_path": report_path,
            "failed_list_path": failed_list_path,
            "checkpoint_path": self.checkpoint_manager.get_checkpoint_path(batch_id),
            "stats": final_checkpoint["stats"],
        }


def main():
    """Main entry point for batch processing."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )

    logger = logging.getLogger(__name__)

    # Load 100 tickers
    tickers = load_tickers_from_universe(limit=100)
    logger.info(f"Loaded {len(tickers)} tickers")

    # Create batch processor with conservative settings
    processor = BatchProcessor(
        adapter=OHLCVAdapter(retries=3, backoff_seconds=2.0),
        max_workers=2,  # Very conservative: 2 concurrent requests
        rate_limit_delay=3.0,  # 3 seconds between requests to stay under 20/min limit
        logger=logger,
    )

    # Run batch with checkpoint support
    result = processor.run_batch(
        tickers=tickers,
        batch_id="batch_100",
        start="2025-01-01",
        end="2025-12-31",
        interval="1D",
        resume=True,  # Resume from checkpoint if it exists
    )

    # Print summary
    print("\n" + "="*50)
    print("BATCH PROCESSING SUMMARY")
    print("="*50)
    print(f"Batch ID: {result['batch_id']}")
    print(f"Total Tickers: {result['stats']['total']}")
    print(f"Passed: {result['stats']['passed']}")
    print(f"Failed: {result['stats']['failed']}")
    print(f"\nReport saved to: {result['report_path']}")
    print(f"Failed list saved to: {result['failed_list_path']}")
    print(f"Checkpoint saved to: {result['checkpoint_path']}")
    print("="*50 + "\n")

    # Show failed tickers
    if result['stats']['failed'] > 0:
        print("Failed Tickers:")
        failed_df = result['report_df'][result['report_df']['status'] == 'FAIL']
        print(failed_df[['ticker', 'error_code', 'message']].to_string(index=False))

    return result


if __name__ == "__main__":
    main()
