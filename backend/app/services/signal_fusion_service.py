from datetime import date, timedelta

from backend.app.database import get_connection
from backend.app.analysis.evidence import Evidence
from backend.app.analysis.news_signal import determine_news_signal
from backend.app.analysis.signal_fusion import (
    SignalFusionResult,
    build_signal_fusion_result,
)
from backend.app.data.signal_fusion_repository import (
    SignalFusionRepository,
)
from backend.app.providers.news_repository import (
    get_news_events_for_symbol,
)


class SignalFusionService:
    def __init__(
        self,
        repository: SignalFusionRepository | None = None,
    ):
        self.repository = repository or SignalFusionRepository()

    def analyze_symbol(
        self,
        symbol: str,
        trade_date: date,
        price_lookback: int = 5,
        investor_type: str = "all",
        market_segment: str = "RG",
    ) -> SignalFusionResult:
        signal_input = self.repository.get_signal_input(
            symbol=symbol,
            trade_date=trade_date,
            price_lookback=price_lookback,
            investor_type=investor_type,
            market_segment=market_segment,
        )

        result = build_signal_fusion_result(
            symbol=signal_input.symbol,
            trade_date=signal_input.trade_date,
            net_foreign=signal_input.net_foreign,
            broker_net=signal_input.broker_net,
            first_close=signal_input.first_close,
            last_close=signal_input.last_close,
            foreign_windows=signal_input.foreign_windows,
            broker_windows=signal_input.broker_windows,
        )

        with get_connection() as connection:
            news_events = get_news_events_for_symbol(
                connection=connection,
                symbol=symbol,
                start_date=trade_date - timedelta(days=3),
                end_date=trade_date + timedelta(days=1),
            )

        if news_events:
            latest_event = news_events[0]

            news_signal = determine_news_signal(
                event_count=len(news_events),
                validation_status=latest_event[6],
                evidence_strength=latest_event[12],
            )

            result.news_state = news_signal.state
            result.news_evidence_strength = news_signal.evidence_strength
            result.news_event_count = news_signal.event_count

            result.evidence["news"] = Evidence(
                component="news",
                source="news_events",
                as_of=trade_date,
                available=True,
                status="AVAILABLE",
                detail=(
                    f"{len(news_events)} event(s), "
                    f"latest status={latest_event[6]}, "
                    f"evidence={latest_event[12]}"
                ),
            )
        else:
            news_signal = determine_news_signal(
                event_count=0,
                validation_status=None,
                evidence_strength=None,
            )

            result.news_state = news_signal.state
            result.news_evidence_strength = news_signal.evidence_strength
            result.news_event_count = news_signal.event_count

            result.evidence["news"] = Evidence(
                component="news",
                source="news_events",
                as_of=trade_date,
                available=False,
                status="MISSING",
                detail="No relevant news event in the 3-day window.",
            )

        return result
