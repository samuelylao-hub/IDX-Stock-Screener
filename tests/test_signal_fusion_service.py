from datetime import date
from decimal import Decimal

from backend.app.data.signal_fusion_repository import (
    SignalFusionInput,
)
from backend.app.services.signal_fusion_service import (
    SignalFusionService,
)


class FakeSignalFusionRepository:
    def get_signal_input(
        self,
        symbol,
        trade_date,
        price_lookback=5,
        investor_type="all",
        market_segment="RG",
    ):
        return SignalFusionInput(
            symbol=symbol,
            trade_date=trade_date,
            net_foreign=Decimal("99028035225"),
            broker_net=Decimal("-238477692500"),
            first_close=Decimal("6225"),
            last_close=Decimal("6250"),
        )


def test_service_builds_bbca_signal_from_repository():
    service = SignalFusionService(
        repository=FakeSignalFusionRepository()
    )

    result = service.analyze_symbol(
        symbol="BBCA",
        trade_date=date(2026, 9, 25),
    )

    assert result.symbol == "BBCA"
    assert result.trade_date == date(2026, 9, 25)

    assert result.foreign_state == "ACCUMULATION"
    assert result.broker_state == "DISTRIBUTION"
    assert result.price_volume_state == "UPTREND"

    assert result.alignment == "DIVERGENT"
    assert result.data_completeness == 1.0


def test_service_uses_repository_lookback_configuration():
    class RecordingRepository:
        def __init__(self):
            self.arguments = None

        def get_signal_input(
            self,
            symbol,
            trade_date,
            price_lookback=5,
            investor_type="all",
            market_segment="RG",
        ):
            self.arguments = {
                "symbol": symbol,
                "trade_date": trade_date,
                "price_lookback": price_lookback,
                "investor_type": investor_type,
                "market_segment": market_segment,
            }

            return SignalFusionInput(
                symbol=symbol,
                trade_date=trade_date,
                net_foreign=None,
                broker_net=None,
                first_close=Decimal("5000"),
                last_close=Decimal("5050"),
            )

    repository = RecordingRepository()
    service = SignalFusionService(repository=repository)

    result = service.analyze_symbol(
        symbol="BBRI",
        trade_date=date(2026, 9, 25),
        price_lookback=10,
        investor_type="all",
        market_segment="RG",
    )

    assert result.symbol == "BBRI"
    assert result.price_volume_state == "UPTREND"
    assert result.alignment == "INSUFFICIENT_DATA"

    assert repository.arguments == {
        "symbol": "BBRI",
        "trade_date": date(2026, 9, 25),
        "price_lookback": 10,
        "investor_type": "all",
        "market_segment": "RG",
    }
