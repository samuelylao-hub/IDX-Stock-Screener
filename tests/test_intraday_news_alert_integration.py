from datetime import date
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from backend.app.analysis.intraday_alert import IntradayAlertEngine
from backend.app.scheduler import intraday_runner as runner


def make_event(status="OFFICIALLY_CONFIRMED", strength="HIGH"):
    row = [None] * 13
    row[0] = 1
    row[1] = "BBCA"
    row[2] = "Berita uji integrasi BBCA"
    row[6] = status
    row[12] = strength
    return tuple(row)


def make_result(symbol="BBCA"):
    return SimpleNamespace(
        symbol=symbol,
        state="EARLY_BULLISH",
        score=75.0,
        momentum=5.0,
        relative_strength=3.0,
        volume_ratio=2.0,
        volume_price_state="ACCUMULATION",
        market_state="BULLISH",
        reasons=["momentum_positive"],
    )


def mock_connection():
    connection = MagicMock()
    connection.__enter__.return_value = connection
    connection.__exit__.return_value = False
    return connection


@patch("backend.app.scheduler.intraday_runner.get_news_events_for_symbol")
@patch("backend.app.scheduler.intraday_runner.get_connection")
def test_confirmed_database_news_reaches_intraday_alert_message(
    mock_get_connection, mock_get_news
):
    connection = mock_connection()
    mock_get_connection.return_value = connection
    mock_get_news.return_value = [make_event()]

    trade_date = date(2026, 10, 19)
    contexts = runner.load_intraday_news_context(["BBCA"], trade_date)

    alerts = IntradayAlertEngine().evaluate_all(
        [make_result()],
        trade_date=trade_date,
        news_context_by_symbol=contexts,
    )

    assert len(alerts) == 1
    alert = alerts[0]
    assert alert.news_state == "CONFIRMED"
    assert alert.news_impact == "IMPACT_ELIGIBLE"
    assert "News       : CONFIRMED" in alert.message
    assert "News impact: IMPACT_ELIGIBLE" in alert.message
    assert "News detail: News impact eligible with HIGH evidence." in alert.message
    mock_get_news.assert_called_once()


@patch("backend.app.scheduler.intraday_runner.get_news_events_for_symbol")
@patch("backend.app.scheduler.intraday_runner.get_connection")
def test_no_database_news_reaches_alert_without_news_impact(
    mock_get_connection, mock_get_news
):
    connection = mock_connection()
    mock_get_connection.return_value = connection
    mock_get_news.return_value = []

    trade_date = date(2026, 10, 19)
    contexts = runner.load_intraday_news_context(["BBCA"], trade_date)

    alerts = IntradayAlertEngine().evaluate_all(
        [make_result()],
        trade_date=trade_date,
        news_context_by_symbol=contexts,
    )

    assert len(alerts) == 1
    alert = alerts[0]
    assert alert.news_state == "NO_NEWS"
    assert alert.news_impact == "NO_IMPACT"
    assert "News       : NO_NEWS" in alert.message
    assert "News impact: NO_IMPACT" in alert.message
