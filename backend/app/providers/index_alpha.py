import os
from dataclasses import dataclass
from datetime import date

import requests
from dotenv import load_dotenv


load_dotenv()


BASE_URL = "https://api.indexalpha.id"


@dataclass
class ForeignFlow:
    symbol: str
    trade_date: date
    foreign_buy: int
    foreign_sell: int
    net_foreign: int


@dataclass
class BrokerSummary:
    symbol: str
    trade_date: date
    broker_code: str
    buy_freq: int
    buy_volume: int
    buy_value: int
    sell_freq: int
    sell_volume: int
    sell_value: int
    buy_avg: float
    sell_avg: float

    @property
    def net_value(self) -> int:
        return self.buy_value - self.sell_value

    @property
    def net_volume(self) -> int:
        return self.buy_volume - self.sell_volume


class IndexAlphaProvider:
    name = "index_alpha"

    def __init__(self):
        self.api_key = os.getenv("INDEX_ALPHA_API_KEY")

    def is_available(self) -> bool:
        return bool(self.api_key)

    def _get_headers(self):
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Accept": "application/json",
        }

    def get_foreign_flow(
        self,
        symbol: str,
        trade_date: date,
        market: str = "ALL",
    ) -> ForeignFlow:
        if not self.is_available():
            raise RuntimeError(
                "INDEX_ALPHA_API_KEY tidak ditemukan."
            )

        response = requests.get(
            f"{BASE_URL}/foreign-flow",
            params={
                "ticker": symbol,
                "from": trade_date.isoformat(),
                "to": trade_date.isoformat(),
                "market": market,
            },
            headers=self._get_headers(),
            timeout=15,
        )

        response.raise_for_status()

        payload = response.json()

        if not payload.get("success"):
            raise RuntimeError(
                payload.get("error")
                or "Index Alpha mengembalikan response gagal."
            )

        data = payload["data"]

        return ForeignFlow(
            symbol=symbol,
            trade_date=trade_date,
            foreign_buy=int(data["foreign_buy"]),
            foreign_sell=int(data["foreign_sell"]),
            net_foreign=int(data["net_foreign"]),
        )

    def get_broker_summary(
        self,
        symbol: str,
        trade_date: date,
        investor: str = "all",
        market: str = "RG",
    ) -> list[BrokerSummary]:
        if not self.is_available():
            raise RuntimeError(
                "INDEX_ALPHA_API_KEY tidak ditemukan."
            )

        response = requests.get(
            f"{BASE_URL}/stocks/broker-summary",
            params={
                "ticker": symbol,
                "from": trade_date.isoformat(),
                "to": trade_date.isoformat(),
                "investor": investor,
                "market": market,
            },
            headers=self._get_headers(),
            timeout=15,
        )

        response.raise_for_status()

        payload = response.json()

        if not payload.get("success"):
            raise RuntimeError(
                payload.get("error")
                or "Index Alpha mengembalikan response gagal."
            )

        rows = payload["data"]

        return [
            BrokerSummary(
                symbol=symbol,
                trade_date=trade_date,
                broker_code=row["code"],
                buy_freq=int(row["buy_freq"]),
                buy_volume=int(row["buy_volume"]),
                buy_value=int(row["buy_value"]),
                sell_freq=int(row["sell_freq"]),
                sell_volume=int(row["sell_volume"]),
                sell_value=int(row["sell_value"]),
                buy_avg=float(row["buy_avg"]),
                sell_avg=float(row["sell_avg"]),
            )
            for row in rows
        ]