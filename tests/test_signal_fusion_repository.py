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


def test_bbca_foreign_flow_windows():
    repository = SignalFusionRepository()

    result = repository.get_foreign_flow_windows(
        symbol="BBCA",
        trade_date=date(2026, 9, 25),
    )

    assert set(result.keys()) == {1, 5, 20}

    one_day = result[1]
    five_day = result[5]
    twenty_day = result[20]

    assert one_day.status == "AVAILABLE"
    assert one_day.available_days == 1
    assert one_day.net_value == Decimal("99028035225.00")
    assert one_day.positive_days == 1
    assert one_day.negative_days == 0
    assert one_day.consistency_ratio == Decimal("1")

    assert five_day.status == "INSUFFICIENT_DATA" or (
        five_day.status == "AVAILABLE"
        and five_day.available_days == 5
    )

    assert twenty_day.status == "INSUFFICIENT_DATA"
    assert twenty_day.available_days == 1


def test_bbca_broker_flow_windows():
    repository = SignalFusionRepository()

    result = repository.get_broker_flow_windows(
        symbol="BBCA",
        trade_date=date(2026, 9, 25),
    )

    assert set(result.keys()) == {1, 5, 20}

    one_day = result[1]
    five_day = result[5]
    twenty_day = result[20]

    assert one_day.status == "AVAILABLE"
    assert one_day.available_days == 1
    assert one_day.net_value == Decimal("-238477692500.00")
    assert one_day.negative_days == 1
    assert one_day.positive_days == 0
    assert one_day.consistency_ratio == Decimal("1")

    assert five_day.status == "INSUFFICIENT_DATA" or (
        five_day.status == "AVAILABLE"
        and five_day.available_days == 5
    )

    assert twenty_day.status == "INSUFFICIENT_DATA"
    assert twenty_day.available_days == 1


def test_signal_input_contains_multi_day_windows():
    repository = SignalFusionRepository()

    result = repository.get_signal_input(
        symbol="BBCA",
        trade_date=date(2026, 9, 25),
        price_lookback=5,
    )

    assert set(result.foreign_windows.keys()) == {1, 5, 20}
    assert set(result.broker_windows.keys()) == {1, 5, 20}

    assert result.foreign_windows[1].net_value == Decimal(
        "99028035225.00"
    )

    assert result.broker_windows[1].net_value == Decimal(
        "-238477692500.00"
    )

    assert result.foreign_windows[20].status == "INSUFFICIENT_DATA"
    assert result.broker_windows[20].status == "INSUFFICIENT_DATA"


def test_bbri_missing_smart_money_windows_are_insufficient():
    repository = SignalFusionRepository()

    result = repository.get_signal_input(
        symbol="BBRI",
        trade_date=date(2026, 9, 25),
        price_lookback=5,
    )

    assert result.foreign_windows[1].status == "INSUFFICIENT_DATA"
    assert result.foreign_windows[5].status == "INSUFFICIENT_DATA"
    assert result.foreign_windows[20].status == "INSUFFICIENT_DATA"

    assert result.broker_windows[1].status == "INSUFFICIENT_DATA"
    assert result.broker_windows[5].status == "INSUFFICIENT_DATA"
    assert result.broker_windows[20].status == "INSUFFICIENT_DATA"


def test_flow_windows_do_not_use_future_data():
    repository = SignalFusionRepository()

    result = repository.get_foreign_flow_windows(
        symbol="BBCA",
        trade_date=date(2026, 9, 23),
    )

    assert result[1].available_days == 0 or (
        result[1].status == "AVAILABLE"
        and result[1].available_days == 1
    )

    assert result[20].status == "INSUFFICIENT_DATA"
    assert result[20].available_days <= 3
