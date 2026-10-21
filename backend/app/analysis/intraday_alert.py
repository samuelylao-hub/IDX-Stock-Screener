from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from zoneinfo import ZoneInfo

from backend.app.db.intraday_alert_states import (
    get_latest_intraday_state,
    save_intraday_state,
)


@dataclass(frozen=True)
class IntradayAlert:
    symbol: str
    state: str
    score: float
    momentum: float
    relative_strength: float
    volume_ratio: float
    volume_price_state: str
    market_state: str
    message: str
    reasons: list[str]
    news_state: str = "NO_NEWS"
    news_impact: str = "NO_IMPACT"
    news_detail: str = "No relevant news event."


class IntradayAlertEngine:
    EARLY_THRESHOLD = 60.0

    def __init__(self, persistent: bool = False):
        self.persistent = persistent
        self._sent: set[tuple[str, str, date]] = set()

    def evaluate(
        self,
        result,
        trade_date: date | None = None,
        news_context: dict | None = None,
    ) -> IntradayAlert | None:

        if trade_date is None:
            trade_date = datetime.now(ZoneInfo("Asia/Jakarta")).date()

        if result.state != "EARLY_BULLISH":
            return None

        if result.score < self.EARLY_THRESHOLD:
            return None

        if result.volume_price_state == "DISTRIBUTION":
            return None

        key = (
            result.symbol,
            result.state,
            trade_date,
        )

        if key in self._sent:
            return None

        if self.persistent:
            previous = get_latest_intraday_state(
                result.symbol,
                trade_date,
            )

            if previous and previous[0] == result.state:
                return None

        self._sent.add(key)

        if self.persistent:
            save_intraday_state(
                result.symbol,
                trade_date,
                result.state,
                result.score,
            )

        return IntradayAlert(
            symbol=result.symbol,
            state=result.state,
            score=result.score,
            momentum=result.momentum,
            relative_strength=result.relative_strength,
            volume_ratio=result.volume_ratio,
            volume_price_state=result.volume_price_state,
            market_state=result.market_state,
            message=self._build_message(result, news_context),
            reasons=list(result.reasons),
            news_state=(news_context or {}).get("news_state", "NO_NEWS"),
            news_impact=(news_context or {}).get("impact_state", "NO_IMPACT"),
            news_detail=(news_context or {}).get("detail", "No relevant news event."),
        )

    def evaluate_all(
        self,
        results,
        trade_date: date | None = None,
        news_context_by_symbol: dict | None = None,
    ):
        if trade_date is None:
            trade_date = datetime.now(ZoneInfo("Asia/Jakarta")).date()

        alerts = []

        for result in results:
            alert = self.evaluate(
                result,
                trade_date,
                (news_context_by_symbol or {}).get(result.symbol),
            )

            if alert is not None:
                alerts.append(alert)

        return sorted(
            alerts,
            key=lambda item: item.score,
            reverse=True,
        )

    @staticmethod
    def _build_message(result, news_context: dict | None = None) -> str:
        news_context = news_context or {}
        lines = [
            "🚨 IDX INTRADAY SIGNAL",
            "",
            f"{result.symbol}",
            f"State      : {result.state}",
            f"Score      : {result.score}",
            f"Momentum   : {result.momentum}%",
            f"RS         : {result.relative_strength}%",
            f"Volume     : {result.volume_ratio}x",
            f"VP         : {result.volume_price_state}",
            f"IHSG       : {result.market_state}",
            f"News       : {news_context.get('news_state', 'NO_NEWS')}",
            f"News impact: {news_context.get('impact_state', 'NO_IMPACT')}",
            f"News detail: {news_context.get('detail', 'No relevant news event.')}",
            "",
            "Reason:",
        ]

        reason_labels = {
            "ihsg_bullish": "IHSG bullish",
            "momentum_positive": "Momentum positive",
            "relative_strength_outperforming": (
                "Relative strength outperforming"
            ),
            "volume_price_accumulation": (
                "Volume-price accumulation"
            ),
            "volume_above_average": (
                "Volume above average"
            ),
        }

        for reason in result.reasons:
            lines.append(
                f"• {reason_labels.get(reason, reason)}"
            )

        return "\n".join(lines)
