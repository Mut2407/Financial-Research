from vnstock.api.quote import Quote


class StockProvider:

    def get_ohlcv(
        self,
        ticker,
        start="2025-01-01",
        end="2025-12-31",
        interval="1D"
    ):

        quote = Quote(
            symbol=ticker,
            source="VCI"
        )

        return quote.history(
            start=start,
            end=end,
            interval=interval
        )
