import os
import time
from datetime import datetime

import pandas as pd
from vnstock import Company, Reference


TARGET_COUNTS = {
	"HOSE": 70,
	"HNX": 20,
	"UPCOM": 10,
}


def normalize_market(value):
	market = str(value).upper()
	if market in ["HSX", "HOSE"]:
		return "HOSE"
	if market in ["HNX"]:
		return "HNX"
	if market in ["UPCOM", "UPCOMINDEX"]:
		return "UPCOM"
	return market


def main():
	reference = Reference()

	symbols_df = reference.equity.list(source="VCI")
	exchange_df = reference.equity.list_by_exchange(source="VCI")

	symbols_df = symbols_df.rename(columns={"symbol": "ticker", "organ_name": "name"})
	exchange_df = exchange_df.rename(columns={"symbol": "ticker"})
	exchange_df["market"] = exchange_df["exchange"].apply(normalize_market)

	if "ticker" in exchange_df.columns:
		exchange_df = exchange_df.drop_duplicates(subset=["ticker"])

	selected_frames = []
	for market, count in TARGET_COUNTS.items():
		market_frame = exchange_df[exchange_df["market"] == market].head(count)
		selected_frames.append(market_frame)

	base_df = pd.concat(selected_frames, ignore_index=True)
	base_df = base_df.merge(symbols_df, on="ticker", how="left")
	base_df = base_df.drop_duplicates(subset=["ticker"]).reset_index(drop=True)

	request_delay = float(os.getenv("VCI_REQUEST_DELAY_SECONDS", "3.5"))

	def fetch_overview(ticker: str, max_attempts: int = 4):
		for attempt in range(1, max_attempts + 1):
			try:
				return Company(symbol=ticker, source="VCI").overview()
			except Exception as error:
				message = str(error).lower()
				if "rate limit" not in message and "giới hạn api" not in message and "ratelimit" not in message:
					raise

				if attempt == max_attempts:
					raise

				wait_seconds = 22 * attempt
				print(f"Rate limit hit for {ticker}; retrying in {wait_seconds}s ({attempt}/{max_attempts})")
				time.sleep(wait_seconds)

	rows = []
	total = len(base_df)

	for index, row in base_df.iterrows():
		ticker = row["ticker"]
		overview = fetch_overview(ticker)

		if overview.empty:
			rows.append(
				{
					"ticker": ticker,
					"name": row.get("name"),
					"market": row.get("exchange"),
					"sector": None,
					"listing": None,
					"listing_date": None,
					"short_name": None,
					"company_profile": None,
					"com_type_code": None,
					"com_group_code": None,
					"tag": None,
					"icb_code_lv2": None,
					"source": "vnstock:VCI",
				}
			)
			continue

		overview_row = overview.iloc[0].to_dict()
		rows.append(
			{
				"ticker": overview_row.get("symbol", ticker),
				"name": overview_row.get("organ_name") or row.get("name"),
				"market": row.get("exchange"),
				"sector": overview_row.get("sector"),
				"listing": overview_row.get("listing"),
				"listing_date": overview_row.get("listing_date"),
				"short_name": overview_row.get("organ_short_name"),
				"company_profile": overview_row.get("company_profile"),
				"com_type_code": overview_row.get("com_type_code"),
				"com_group_code": overview_row.get("com_group_code"),
				"tag": overview_row.get("tag"),
				"icb_code_lv2": overview_row.get("icb_code_lv2"),
				"source": "vnstock:VCI",
			}
		)

		if (index + 1) % 25 == 0 or index + 1 == total:
			print(f"Processed {index + 1}/{total} symbols")

		time.sleep(request_delay)

	df = pd.DataFrame(rows)

	if "listing" in df.columns:
		df["listing"] = df["listing"].astype("boolean")

	if "listing_date" in df.columns:
		df["listing_date"] = pd.to_datetime(df["listing_date"], errors="coerce").dt.strftime(
			"%Y-%m-%d"
		)

	df["updated_at"] = datetime.now().strftime("%Y-%m-%d")

	df = df.drop_duplicates(subset=["ticker"]).sort_values(by="ticker").reset_index(drop=True)

	df.to_csv("data/listed_companies.csv", index=False, encoding="utf-8-sig")

	print("=" * 40)
	print(f"TOTAL: {len(df)}")
	print("Saved -> data/listed_companies.csv")


if __name__ == "__main__":
	main()
