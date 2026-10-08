from types import SimpleNamespace

from backend.app.analysis.intraday_alert import (
    IntradayAlertEngine,
)


def _result(
    symbol="BBCA",
    state="EARLY_BULLISH",
    score=70.0,
    momentum=1.2,
    relative_strength=0.8,
    volume_ratio=1.8,
    volume_price_state="ACCUMULATION",
    market_state="BULLISH",
    reasons=None,
):
    if reasons is None:
        reasons = [
            "ihsg_bullish",
            "momentum_positive",
            "relative_strength_outperforming",
            "volume_price_accumulation",
        ]

    return SimpleNamespace(
        symbol=symbol,
        state=state,
        score=score,
        momentum=momentum,
        relative_strength=relative_strength,
        volume_ratio=volume_ratio,
        volume_price_state=volume_price_state,
        market_state=market_state,
        reasons=reasons,
    )


def test_intraday_alert_for_early_bullish():
    engine = IntradayAlertEngine()

    alert = engine.evaluate(
        _result()
    )

    assert alert is not None
    assert alert.symbol == "BBCA"
    assert alert.state == "EARLY_BULLISH"
    assert alert.score == 70.0


def test_intraday_alert_requires_threshold():
    engine = IntradayAlertEngine()

    alert = engine.evaluate(
        _result(
            score=59.99,
        )
    )

    assert alert is None


def test_intraday_alert_blocks_normal():
    engine = IntradayAlertEngine()

    alert = engine.evaluate(
        _result(
            state="NORMAL",
            score=80.0,
        )
    )

    assert alert is None


def test_intraday_alert_blocks_watch():
    engine = IntradayAlertEngine()

    alert = engine.evaluate(
        _result(
            state="WATCH",
            score=80.0,
        )
    )

    assert alert is None


def test_intraday_alert_blocks_distribution():
    engine = IntradayAlertEngine()

    alert = engine.evaluate(
        _result(
            volume_price_state="DISTRIBUTION",
        )
    )

    assert alert is None


def test_intraday_alert_prevents_duplicate():
    engine = IntradayAlertEngine()

    result = _result()

    first = engine.evaluate(result)
    second = engine.evaluate(result)

    assert first is not None
    assert second is None


def test_intraday_alert_all_sorted_by_score():
    engine = IntradayAlertEngine()

    results = [
        _result(
            symbol="BBCA",
            score=65.0,
        ),
        _result(
            symbol="BBRI",
            score=85.0,
        ),
        _result(
            symbol="TLKM",
            score=50.0,
        ),
    ]

    alerts = engine.evaluate_all(results)

    assert len(alerts) == 2
    assert alerts[0].symbol == "BBRI"
    assert alerts[1].symbol == "BBCA"


def test_intraday_alert_message_contains_signal_data():
    engine = IntradayAlertEngine()

    alert = engine.evaluate(
        _result()
    )

    assert alert is not None
    assert "BBCA" in alert.message
    assert "EARLY_BULLISH" in alert.message
    assert "70.0" in alert.message
    assert "1.8x" in alert.message
    assert "ACCUMULATION" in alert.message


def test_intraday_alert_reasons_are_preserved():
    engine = IntradayAlertEngine()

    alert = engine.evaluate(
        _result()
    )

    assert alert is not None
    assert (
        "momentum_positive"
        in alert.reasons
    )
    assert (
        "volume_price_accumulation"
        in alert.reasons
    )
