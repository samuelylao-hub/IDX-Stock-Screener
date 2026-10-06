from datetime import date
from types import SimpleNamespace

from backend.app.analysis.alert_engine import AlertEngine


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
