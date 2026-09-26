import yfinance as yf


class YahooProvider:
    @property
    def name(self) -> str:
        return "yahoo"

    def is_available(self) -> bool:
        return True

    def get_daily_prices(
        self,
        symbol: str,
        period: str = "5d",
    ):
        ticker = f"{symbol}.JK"

        return yf.download(
            ticker,
            period=period,
            progress=False,
            auto_adjust=False,
        )