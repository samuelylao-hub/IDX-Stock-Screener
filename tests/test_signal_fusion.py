from datetime import date
from decimal import Decimal

from backend.app.analysis.signal_fusion import (
    build_signal_fusion_result,
    calculate_data_completeness,
    classify_flow_window,
    determine_alignment,
    determine_broker_state,
    determine_flow_persistence,
    determine_foreign_state,
    determine_price_volume_state,
)
from backend.app.data.signal_fusion_repository import FlowWindow


def make_flow_window(
    window_days: int,
    available_days: int,
    net_value: Decimal,
    status: str,
) -> FlowWindow:
    return FlowWindow(
        window_days=window_days,
        available_days=available_days,
        net_value=net_value,
        positive_days=1 if net_value > 0 else 0,
        negative_days=1 if net_value < 0 else 0,
        zero_days=1 if net_value == 0 else 0,
        consistency_ratio=Decimal("1"),
        status=status,
    )


def test_foreign_state():
    assert determine_foreign_state(100) == "ACCUMULATION"
    assert determine_foreign_state(-100) == "DISTRIBUTION"
    assert determine_foreign_state(0) == "NEUTRAL"


def test_broker_state():
    assert determine_broker_state(100) == "ACCUMULATION"
    assert determine_broker_state(-100) == "DISTRIBUTION"
    assert determine_broker_state(0) == "NEUTRAL"


def test_price_volume_state():
    assert determine_price_volume_state(6200, 6300) == "UPTREND"
    assert determine_price_volume_state(6300, 6200) == "DOWNTREND"
    assert determine_price_volume_state(6300, 6300) == "SIDEWAYS"


def test_alignment():
    assert determine_alignment("ACCUMULATION", "ACCUMULATION") == "ALIGNED"
    assert determine_alignment("DISTRIBUTION", "DISTRIBUTION") == "ALIGNED"
    assert determine_alignment("ACCUMULATION", "DISTRIBUTION") == "DIVERGENT"
    assert determine_alignment("DISTRIBUTION", "ACCUMULATION") == "DIVERGENT"
    assert determine_alignment("NEUTRAL", "ACCUMULATION") == "NEUTRAL"


def test_data_completeness():
    assert calculate_data_completeness(True, True, True) == 1.0
    assert calculate_data_completeness(True, False, False) == 1 / 3
    assert calculate_data_completeness(False, False, False) == 0.0


def test_classify_available_one_day_window():
    window = make_flow_window(
        window_days=1,
        available_days=1,
        net_value=Decimal("100"),
        status="AVAILABLE",
    )

    assert classify_flow_window(window) == "ACCUMULATION"


def test_classify_available_negative_one_day_window():
    window = make_flow_window(
        window_days=1,
        available_days=1,
        net_value=Decimal("-100"),
        status="AVAILABLE",
    )

    assert classify_flow_window(window) == "DISTRIBUTION"


def test_classify_insufficient_five_day_window():
    window = make_flow_window(
        window_days=5,
        available_days=1,
        net_value=Decimal("100"),
        status="INSUFFICIENT_DATA",
    )

    assert classify_flow_window(window) == "INSUFFICIENT_DATA"


def test_classify_missing_window():
    assert classify_flow_window(None) == "INSUFFICIENT_DATA"


def test_single_day_persistence():
    windows = {
        1: make_flow_window(
            window_days=1,
            available_days=1,
            net_value=Decimal("100"),
            status="AVAILABLE",
        ),
        5: make_flow_window(
            window_days=5,
            available_days=1,
            net_value=Decimal("100"),
            status="INSUFFICIENT_DATA",
        ),
        20: make_flow_window(
            window_days=20,
            available_days=1,
            net_value=Decimal("100"),
            status="INSUFFICIENT_DATA",
        ),
    }

    assert determine_flow_persistence(windows) == "SINGLE_DAY"


def test_consistent_multi_day_persistence():
    windows = {
        1: make_flow_window(
            window_days=1,
            available_days=1,
            net_value=Decimal("100"),
            status="AVAILABLE",
        ),
        5: make_flow_window(
            window_days=5,
            available_days=5,
            net_value=Decimal("500"),
            status="AVAILABLE",
        ),
        20: make_flow_window(
            window_days=20,
            available_days=20,
            net_value=Decimal("2000"),
            status="AVAILABLE",
        ),
    }

    assert determine_flow_persistence(windows) == "CONSISTENT"


def test_mixed_multi_day_persistence():
    windows = {
        1: make_flow_window(
            window_days=1,
            available_days=1,
            net_value=Decimal("100"),
            status="AVAILABLE",
        ),
        5: make_flow_window(
            window_days=5,
            available_days=5,
            net_value=Decimal("-500"),
            status="AVAILABLE",
        ),
        20: make_flow_window(
            window_days=20,
            available_days=20,
            net_value=Decimal("-2000"),
            status="AVAILABLE",
        ),
    }

    assert determine_flow_persistence(windows) == "MIXED"


def test_bbca_like_divergent_signal():
    result = build_signal_fusion_result(
        symbol="BBCA",
        trade_date=date(2026, 9, 25),
        net_foreign=99_028_035_225,
        broker_net=-238_477_692_500,
        first_close=6225,
        last_close=6250,
    )

    assert result.symbol == "BBCA"
    assert result.trade_date == date(2026, 9, 25)
    assert result.foreign_state == "ACCUMULATION"
    assert result.broker_state == "DISTRIBUTION"
    assert result.price_volume_state == "UPTREND"
    assert result.foreign_1d_state == "INSUFFICIENT_DATA"
    assert result.foreign_5d_state == "INSUFFICIENT_DATA"
    assert result.foreign_20d_state == "INSUFFICIENT_DATA"
    assert result.broker_1d_state == "INSUFFICIENT_DATA"
    assert result.broker_5d_state == "INSUFFICIENT_DATA"
    assert result.broker_20d_state == "INSUFFICIENT_DATA"
    assert result.alignment == "DIVERGENT"
    assert result.data_completeness == 1.0


def test_missing_smart_money_data():
    result = build_signal_fusion_result(
        symbol="BBRI",
        trade_date=date(2026, 9, 25),
        net_foreign=None,
        broker_net=None,
        first_close=5000,
        last_close=5050,
    )

    assert result.foreign_state == "UNKNOWN"
    assert result.broker_state == "UNKNOWN"
    assert result.price_volume_state == "UPTREND"
    assert result.alignment == "INSUFFICIENT_DATA"
    assert result.data_completeness == 1 / 3