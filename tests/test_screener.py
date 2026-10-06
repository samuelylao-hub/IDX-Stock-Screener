from datetime import date

from backend.app.analysis.screener import (
    calculate_signal_score,
    determine_signal,
)


def test_signal_score_neutral_is_zero():
    result = type("Result", (), {
        "foreign_state": "NEUTRAL",
        "broker_state": "NEUTRAL",
        "price_volume_state": "NEUTRAL",
        "alignment": "NEUTRAL",
    })()

    assert calculate_signal_score(result) == 0.0


def test_signal_score_accumulation_uptrend_aligned():
    result = type("Result", (), {
        "foreign_state": "ACCUMULATION",
        "broker_state": "ACCUMULATION",
        "price_volume_state": "UPTREND",
        "alignment": "ALIGNED",
    })()

    assert calculate_signal_score(result) == 100.0


def test_signal_score_distribution_downtrend_divergent():
    result = type("Result", (), {
        "foreign_state": "DISTRIBUTION",
        "broker_state": "DISTRIBUTION",
        "price_volume_state": "DOWNTREND",
        "alignment": "DIVERGENT",
    })()

    assert calculate_signal_score(result) == -90.0


def test_determine_signal_thresholds():
    assert determine_signal(60) == "STRONG_BUY"
    assert determine_signal(25) == "BUY"
    assert determine_signal(0) == "WATCH"
    assert determine_signal(-25) == "SELL"
    assert determine_signal(-60) == "STRONG_SELL"
