import argparse
import json
import logging

from src.pipeline.ingestion import ingest_tickers
from src.pipeline.transform import transform_raw_data
from src.settings import get_settings


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Financial data pipeline")
    subparsers = parser.add_subparsers(dest="command", required=True)

    ingest = subparsers.add_parser("ingest", help="Fetch real OHLCV data from the configured provider")
    ingest.add_argument("--tickers", nargs="+", required=True)
    ingest.add_argument("--start", required=True)
    ingest.add_argument("--end", required=True)
    ingest.add_argument("--interval", default="1D", choices=["1D"])

    subparsers.add_parser("transform", help="Transform canonical raw data into curated Parquet")
    subparsers.add_parser("bootstrap", help="Create curated data from raw data or the committed PoC seed")
    return parser


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
    args = build_parser().parse_args()
    config = get_settings()

    if args.command == "ingest":
        ingestion = ingest_tickers(args.tickers, args.start, args.end, args.interval, config=config)
        transformation = transform_raw_data(input_roots=[config.raw_path, config.seed_raw_path], config=config)
        result = {"ingestion": ingestion, "transformation": transformation}
    elif args.command == "transform":
        result = transform_raw_data(input_roots=[config.raw_path], config=config)
    else:
        existing = list(config.curated_path.rglob("*.parquet")) if config.curated_path.exists() else []
        result = (
            {"status": "skipped", "reason": "curated data already exists", "files": len(existing)}
            if existing
            else transform_raw_data(input_roots=[config.raw_path, config.seed_raw_path], config=config)
        )

    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
