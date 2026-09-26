from typing import Protocol


class DataProvider(Protocol):
    @property
    def name(self) -> str:
        ...

    def is_available(self) -> bool:
        ...


class MarketDataProvider(DataProvider, Protocol):
    def get_daily_prices(
        self,
        symbol: str,
        period: str = "5d",
    ):
        ...