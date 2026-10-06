from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class Alert:
    symbol: str
    trade_date: date
    level: str
    message: str


class AlertEngine:
    def __init__(self):
        self._sent = set()

    def evaluate(self, result, trade_date: date):
        if result.data_quality_status == "LIMITED":
            return Alert(
                result.symbol,
                trade_date,
                "WARNING",
                f"{result.symbol}: data quality LIMITED.",
            )

        if result.early_bullish == "CONFIRMED_BULLISH":
            level = "HIGH"
        elif result.early_bullish == "EARLY_BULLISH":
            level = "EARLY"
        else:
            return None

        key = (result.symbol, trade_date, result.early_bullish)

        if key in self._sent:
            return None

        self._sent.add(key)

        return Alert(
            result.symbol,
            trade_date,
            level,
            f"{result.symbol}: {result.early_bullish} "
            f"(rank {result.ranking_score}, score {result.score}).",
        )

    def evaluate_all(self, results, trade_date: date):
        return [
            alert
            for result in results
            if (alert := self.evaluate(result, trade_date)) is not None
        ]
