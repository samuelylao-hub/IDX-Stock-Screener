from datetime import date

import pytest
from types import SimpleNamespace
from unittest.mock import patch

from backend.app.analysis.alert_engine import AlertEngine




@pytest.fixture(autouse=True)
def mock_alert_database():
    with patch(
        "backend.app.analysis.alert_engine.get_latest_alert_state",
        return_value=None,
    ), patch(
        "backend.app.analysis.alert_engine.save_alert_state",
    ):
        yield


def make_result(**kwargs):
    defaults = {
        "symbol": "BBCA",
        "data_quality_status": "GOOD",
        "early_bullish": "EARLY_BULLISH",
        "ranking_score": 56.0,
        "score": 20.0,
    }
    defaults.update(kwargs)
    return SimpleNamespace(**defaults)


def test_early_bullish_alert():
    alert = AlertEngine().evaluate(make_result(), date(2026, 10, 6))

    assert alert.level == "EARLY"
    assert "EARLY_BULLISH" in alert.message


def test_confirmed_bullish_alert():
    alert = AlertEngine().evaluate(
        make_result(early_bullish="CONFIRMED_BULLISH", ranking_score=80.0),
        date(2026, 10, 6),
    )

    assert alert.level == "HIGH"


def test_normal_no_alert():
    alert = AlertEngine().evaluate(
        make_result(early_bullish="NORMAL"),
        date(2026, 10, 6),
    )

    assert alert is None


def test_duplicate_alert_blocked():
    engine = AlertEngine()
    result = make_result()

    first = engine.evaluate(result, date(2026, 10, 6))
    second = engine.evaluate(result, date(2026, 10, 6))

    assert first is not None
    assert second is None


def test_limited_quality_no_trading_alert():
    alert = AlertEngine().evaluate(
        make_result(data_quality_status="LIMITED"),
        date(2026, 10, 6),
    )

    assert alert is None


def test_new_alert_state():
    alert = AlertEngine().evaluate(
        make_result(early_bullish="EARLY_BULLISH", ranking_score=50.0),
        date(2026, 10, 6),
    )
    assert alert.state == "NEW"

def test_upgrade_alert_state():
    engine = AlertEngine()
    trade_date = date(2026, 10, 6)
    first = engine.evaluate(
        make_result(early_bullish="EARLY_BULLISH", ranking_score=50.0),
        trade_date,
    )
    second = engine.evaluate(
        make_result(early_bullish="CONFIRMED_BULLISH", ranking_score=70.0),
        trade_date,
    )
    assert first.state == "NEW"
    assert second.state == "UPGRADE"

def test_new_confirmed_alert_state():
    alert = AlertEngine().evaluate(
        make_result(early_bullish="CONFIRMED_BULLISH", ranking_score=70.0),
        date(2026, 10, 6),
    )
    assert alert.state == "NEW"

def test_persistent_duplicate_blocked():
    with patch(
        "backend.app.analysis.alert_engine.get_latest_alert_state",
        return_value=(
            "EARLY_BULLISH",
            "EARLY",
            50.0,
            date(2026, 10, 7),
        ),
    ):
        alert = AlertEngine().evaluate(
            make_result(
                early_bullish="EARLY_BULLISH",
                ranking_score=50.0,
            ),
            date(2026, 10, 8),
        )

    assert alert is None


def test_upgrade_from_previous_trade_date():
    with patch(
        "backend.app.analysis.alert_engine.get_latest_alert_state",
        return_value=(
            "EARLY_BULLISH",
            "EARLY",
            50.0,
            date(2026, 10, 7),
        ),
    ):
        alert = AlertEngine().evaluate(
            make_result(
                early_bullish="CONFIRMED_BULLISH",
                ranking_score=70.0,
            ),
            date(2026, 10, 8),
        )

    assert alert is not None
    assert alert.level == "HIGH"
    assert alert.state == "UPGRADE"


def test_confirmed_does_not_downgrade_to_early():
    with patch(
        "backend.app.analysis.alert_engine.get_latest_alert_state",
        return_value=(
            "CONFIRMED_BULLISH",
            "HIGH",
            70.0,
            date(2026, 10, 7),
        ),
    ):
        alert = AlertEngine().evaluate(
            make_result(
                early_bullish="EARLY_BULLISH",
                ranking_score=50.0,
            ),
            date(2026, 10, 8),
        )

    assert alert is None






