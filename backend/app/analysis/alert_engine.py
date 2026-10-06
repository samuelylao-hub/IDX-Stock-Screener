
from dataclasses import dataclass
from datetime import date

@dataclass(frozen=True)
class Alert:
    symbol: str
    trade_date: date
    level: str
    message: str
    ranking_score: float

class AlertEngine:
    EARLY_THRESHOLD = 40.0
    CONFIRMED_THRESHOLD = 60.0

    def __init__(self):
        self._sent = set()

    def evaluate(self, result, trade_date: date):
        if result.data_quality_status == "LIMITED":
            return None

        if result.early_bullish == "CONFIRMED_BULLISH":
            if result.ranking_score < self.CONFIRMED_THRESHOLD:
                return None
            level = "HIGH"
        elif result.early_bullish == "EARLY_BULLISH":
            if result.ranking_score < self.EARLY_THRESHOLD:
                return None
            level = "EARLY"
        else:
            return None

        key = (result.symbol, trade_date, result.early_bullish)
        if key in self._sent:
            return None

        self._sent.add(key)

        return Alert(
            symbol=result.symbol,
            trade_date=trade_date,
            level=level,
            message=f"{result.symbol}: {result.early_bullish} (rank {result.ranking_score}, score {result.score}).",
            ranking_score=result.ranking_score,
        )

    def evaluate_all(self, results, trade_date: date):
        alerts = []

        for result in results:
            alert = self.evaluate(result, trade_date)
            if alert is not None:
                alerts.append(alert)

        return sorted(alerts, key=lambda item: item.ranking_score, reverse=True)
