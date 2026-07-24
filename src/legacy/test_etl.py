import pandas as pd
from etl_processor import clean_and_type_data, calculate_indicators

def test_calculate_indicators():
    print("\n Running tests for ETL indicators...")

    dummy_data = {
        'ticker': ['TEST'] * 20,
        'trading_date': pd.date_range(start='2026-01-01', periods=20),
        'close_price': range(1, 21),
        'open_price': range(1, 21),
        'high_price': range(1, 21),
        'low_price': range(1, 21),
        'volume': [100] * 20
    }
    df_dummy = pd.DataFrame(dummy_data)

    df_clean = clean_and_type_data(df_dummy)
    df_result = calculate_indicators(df_clean)

    print("\n========== TEST RESULT ==========")

    print("\n1. Return")
    print(df_result.loc[0:2, ["trading_date", "close_price", "return"]])

    assert df_result.loc[1, "return"] == 100.0, \
        "Return calculation failed!"

    print("\n2. Test Moving Average 20 (MA20)")
    print(df_result.loc[18:19, ['trading_date', 'close_price', 'ma20']])
    assert df_result.loc[19, "ma20"] == 10.5, \
        "MA20 calculation failed!"

    print("\n3. RSI")
    print(df_result.loc[18:19, ["trading_date", "close_price", "rsi_14"]])

    rsi = df_result.loc[19, "rsi_14"]

    assert pd.notna(rsi), \
        "RSI was not calculated!"

    assert 0 <= rsi <= 100, \
        "RSI must be between 0 and 100!"

    print("\nAll indicator tests passed!")


if __name__ == "__main__":
    test_calculate_indicators()
