from datetime import date

from backend.app.analysis.signal_fusion import (
    SignalFusionResult,
    build_signal_fusion_result,
)
from backend.app.data.signal_fusion_repository import (
    SignalFusionRepository,
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

        return build_signal_fusion_result(
            symbol=signal_input.symbol,
            trade_date=signal_input.trade_date,
            net_foreign=signal_input.net_foreign,
            broker_net=signal_input.broker_net,
            first_close=signal_input.first_close,
            last_close=signal_input.last_close,
            foreign_windows=signal_input.foreign_windows,
            broker_windows=signal_input.broker_windows,
        )