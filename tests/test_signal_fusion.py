from datetime import date

from backend.app.analysis.signal_fusion import (
    build_signal_fusion_result,
    calculate_data_completeness,
    determine_alignment,
    determine_broker_state,
    determine_foreign_state,
    determine_price_volume_state,
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
