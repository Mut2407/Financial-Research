from pathlib import Path

import pandas as pd

from src.settings import Settings

class DataService:
    def __init__(self, db_conn, config: Settings):
        self.db = db_conn
        self.config = config

    def _parquet_files(self) -> list[Path]:
        root = self.config.curated_path
        return sorted(root.rglob("*.parquet")) if root.exists() else []

    def _scan_expression(self) -> str:
        glob = (self.config.curated_path / "**" / "*.parquet").as_posix().replace("'", "''")
        return f"read_parquet('{glob}', hive_partitioning=true, union_by_name=true)"

    @staticmethod
    def _records(frame: pd.DataFrame) -> list[dict]:
        clean = frame.astype(object).where(pd.notna(frame), None)
        return clean.to_dict(orient="records")

    def get_companies(self, page: int, limit: int):
        files = self._parquet_files()
        if not files:
            return {"data": [], "page": page, "limit": limit, "total_records": 0}

        available = {
            row[0]
            for row in self.db.execute(f"SELECT DISTINCT ticker FROM {self._scan_expression()}").fetchall()
        }
        if self.config.universe_file.exists():
            companies = pd.read_csv(self.config.universe_file)
            companies["ticker"] = companies["ticker"].astype(str).str.upper()
            companies = companies[companies["ticker"].isin(available)]
            companies = companies[["ticker", "name", "market", "sector"]]
            missing_tickers = sorted(available - set(companies["ticker"]))
            if missing_tickers:
                companies = pd.concat(
                    [
                        companies,
                        pd.DataFrame(
                            {
                                "ticker": missing_tickers,
                                "name": [None] * len(missing_tickers),
                                "market": [None] * len(missing_tickers),
                                "sector": [None] * len(missing_tickers),
                            }
                        ),
                    ],
                    ignore_index=True,
                )
        else:
            companies = pd.DataFrame({"ticker": sorted(available)})
            for column in ("name", "market", "sector"):
                companies[column] = None

        companies = companies.sort_values("ticker").reset_index(drop=True)
        total_records = len(companies)
        offset = (page - 1) * limit
        page_frame = companies.iloc[offset : offset + limit]
        return {
            "data": self._records(page_frame),
            "page": page,
            "limit": limit,
            "total_records": total_records,
        }

    def get_prices(self, ticker: str, start_date: str | None, end_date: str | None, page: int, limit: int):
        ticker = ticker.strip().upper()
        if not self._parquet_files():
            return {"ticker": ticker, "data": [], "page": page, "limit": limit, "total_records": 0}

        params = [ticker]
        where_clauses = ["ticker = ?"]
        if start_date:
            where_clauses.append("trading_date >= CAST(? AS DATE)")
            params.append(start_date)
        if end_date:
            where_clauses.append("trading_date <= CAST(? AS DATE)")
            params.append(end_date)
        where_str = " AND ".join(where_clauses)

        count_query = f"SELECT COUNT(*) FROM {self._scan_expression()} WHERE {where_str}"
        total_records = self.db.execute(count_query, params).fetchone()[0]
        offset = (page - 1) * limit

        query = f"""
            SELECT ticker, CAST(trading_date AS DATE) AS trading_date,
                   open_price, high_price, low_price, close_price, volume,
                   return_pct, ma20, rsi_14
            FROM {self._scan_expression()}
            WHERE {where_str}
            ORDER BY trading_date ASC
            LIMIT ? OFFSET ?
        """
        params.extend([limit, offset])
        frame = self.db.execute(query, params).df()
        return {
            "ticker": ticker,
            "data": self._records(frame),
            "page": page,
            "limit": limit,
            "total_records": total_records,
        }

    def get_prices_for_export(self, ticker: str):
        ticker = ticker.strip().upper()
        if not self._parquet_files():
            return None
        query = f"SELECT * FROM {self._scan_expression()} WHERE ticker = ? ORDER BY trading_date ASC"
        return self.db.execute(query, [ticker]).df()
