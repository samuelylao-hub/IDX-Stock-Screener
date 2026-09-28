from datetime import date
from decimal import Decimal

from backend.app.data.signal_fusion_repository import (
    SignalFusionRepository,
)


def test_bbca_signal_fusion_input_from_database():
    repository = SignalFusionRepository()

    result = repository.get_signal_input(
        symbol="BBCA",
        trade_date=date(2026, 9, 25),
        price_lookback=5,
    )

    assert result.symbol == "BBCA"
    assert result.trade_date == date(2026, 9, 25)

    assert result.net_foreign == Decimal("99028035225.00")
    assert result.broker_net == Decimal("-238477692500.00")

    assert result.first_close == Decimal("6225.00")
    assert result.last_close == Decimal("6250.00")


def test_bbri_signal_fusion_input_without_smart_money_data():
    repository = SignalFusionRepository()

    result = repository.get_signal_input(
        symbol="BBRI",
        trade_date=date(2026, 9, 25),
        price_lookback=5,
    )

    assert result.symbol == "BBRI"
    assert result.trade_date == date(2026, 9, 25)

    assert result.net_foreign is None
    assert result.broker_net is None

    assert result.first_close is not None
    assert result.last_close is not None


def test_broker_zero_net_is_real_data():
    repository = SignalFusionRepository()

    result = repository.get_signal_input(
        symbol="BBCA",
        trade_date=date(2026, 9, 25),
        price_lookback=5,
    )

    assert result.broker_net is not None
