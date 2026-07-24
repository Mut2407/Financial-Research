import pandas as pd
import numpy as np
import os
from pathlib import Path

# BASE_DIR should be the project root (financial-data/)
BASE_DIR = Path(__file__).resolve().parent.parent

def clean_and_type_data(df: pd.DataFrame) -> pd.DataFrame:
    """Ép kiểu dữ liệu và loại bỏ dòng trùng lặp."""
    df['trading_date'] = pd.to_datetime(df['trading_date'])
    df = df.drop_duplicates(subset=['ticker', 'trading_date'], keep='last')

    type_mapping = {
        'open_price': 'float32',
        'high_price': 'float32',
        'low_price': 'float32',
        'close_price': 'float32',
        'volume': 'int64'
    }
    df = df.astype(type_mapping)
    df = df.sort_values(by=['ticker', 'trading_date']).reset_index(drop=True)
    return df

def calculate_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """Tính toán Return, MA20, và RSI 14 ngày."""
    df['return'] = df.groupby('ticker')['close_price'].pct_change() * 100

    df['ma20'] = df.groupby('ticker')['close_price'].transform(
        lambda x: x.rolling(window=20, min_periods=1).mean()
    )

    def calculate_rsi(series: pd.Series, period: int = 14) -> pd.Series:
        delta = series.diff()
        gain = delta.clip(lower=0)
        loss = -1 * delta.clip(upper=0)

        ema_gain = gain.ewm(com=period-1, adjust=False).mean()
        ema_loss = loss.ewm(com=period-1, adjust=False).mean()

        rs = ema_gain / ema_loss
        return 100 - (100 / (1 + rs))

    df['rsi_14'] = df.groupby('ticker')['close_price'].transform(calculate_rsi)
    df[['return', 'ma20', 'rsi_14']] = df[['return', 'ma20', 'rsi_14']].round(2)

    return df

def run_etl_pipeline(input_csv: str, output_dir: str):
    """Hàm chạy luồng ETL chính."""
    print(f"Extracting data from {input_csv}...")
    df_raw = pd.read_csv(input_csv)

    print("Transforming: Cleaning and calculating indicators...")
    df_clean = clean_and_type_data(df_raw)
    df_curated = calculate_indicators(df_clean)

    print("Loading: Writing to Curated Parquet...")
    os.makedirs(output_dir, exist_ok=True)

    df_curated.to_parquet(
        output_dir,
        engine='pyarrow',
        partition_cols=['ticker'],
        index=False
    )
    print(f"ETL Complete! Curated Data saved at: {output_dir}")

if __name__ == "__main__":
    # Try multiple possible input paths
    possible_inputs = [
        BASE_DIR / "reports" / "ohlcv_samples_10_tickers.csv",
        BASE_DIR / "src" / "tests" / "ohlcv_samples_10_tickers_K07.csv",
    ]

    input_file = None
    for path in possible_inputs:
        if path.exists():
            input_file = path
            break

    output_folder = BASE_DIR / "data" / "curated" / "ohlcv"

    if input_file:
        print(f"Using input file: {input_file}")
        run_etl_pipeline(input_csv=str(input_file), output_dir=str(output_folder))
    else:
        print(f"Không tìm thấy file input tại các vị trí: {possible_inputs}")
