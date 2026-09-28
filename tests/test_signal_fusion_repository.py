from datetime import date
from decimal import Decimal

from backend.app.data.signal_fusion_repository import SignalFusionRepository


def test_bbca_historical_prices_returns_five_days():
    repository = SignalFusionRepository()

    result = repository.get_historical_prices(
        symbol="BBCA",
        trade_date=date(2026, 9, 25),
        lookback=5,
    )

    assert len(result) == 5

    assert result[0].trade_date == date(2026, 9, 21)
    assert result[-1].trade_date == date(2026, 9, 25)

    assert result[0].close == Decimal("6225.00")
    assert result[-1].close == Decimal("6250.00")


def test_historical_prices_does_not_use_future_data():
    repository = SignalFusionRepository()

    result = repository.get_historical_prices(
        symbol="BBCA",
        trade_date=date(2026, 9, 23),
        lookback=5,
    )

    assert len(result) == 3

    assert result[0].trade_date == date(2026, 9, 21)
    assert result[-1].trade_date == date(2026, 9, 23)

    assert all(
        point.trade_date <= date(2026, 9, 23)
        for point in result
    )