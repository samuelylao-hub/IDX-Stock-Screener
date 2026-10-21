from datetime import date, timedelta
from unittest.mock import MagicMock, patch

from backend.app.scheduler import intraday_runner as runner


def make_event(status="OFFICIALLY_CONFIRMED", strength="HIGH"):
    row = [None] * 13
    row[0] = 1
    row[1] = "BBCA"
    row[2] = "Test news"
    row[6] = status
    row[12] = strength
    return tuple(row)


def mock_database():
    connection = MagicMock()
    connection.__enter__.return_value = connection
    connection.__exit__.return_value = False
    return connection


@patch("backend.app.scheduler.intraday_runner.get_news_events_for_symbol")
@patch("backend.app.scheduler.intraday_runner.get_connection")
def test_confirmed_news_returns_context_and_correct_date_window(
    mock_get_connection, mock_get_news
):
    connection = mock_database()
    mock_get_connection.return_value = connection
    mock_get_news.return_value = [make_event()]

    trade_date = date(2026, 10, 19)
    result = runner.load_intraday_news_context(["BBCA"], trade_date)

    assert result["BBCA"]["news_state"] == "CONFIRMED"
    assert result["BBCA"]["impact_state"] == "IMPACT_ELIGIBLE"
    mock_get_news.assert_called_once_with(
        connection=connection,
        symbol="BBCA",
        start_date=trade_date - timedelta(days=3),
        end_date=trade_date + timedelta(days=1),
    )


@patch("backend.app.scheduler.intraday_runner.get_news_events_for_symbol")
@patch("backend.app.scheduler.intraday_runner.get_connection")
def test_no_news_returns_no_impact(mock_get_connection, mock_get_news):
    connection = mock_database()
    mock_get_connection.return_value = connection
    mock_get_news.return_value = []

    result = runner.load_intraday_news_context(["BBCA"], date(2026, 10, 19))

    assert result["BBCA"]["news_state"] == "NO_NEWS"
    assert result["BBCA"]["impact_state"] == "NO_IMPACT"


@patch("backend.app.scheduler.intraday_runner.get_connection")
def test_database_failure_returns_unavailable_without_impact(mock_get_connection):
    mock_get_connection.side_effect = RuntimeError("database unavailable")

    result = runner.load_intraday_news_context(
        ["BBCA", "BBRI"], date(2026, 10, 19)
    )

    assert set(result) == {"BBCA", "BBRI"}
    for context in result.values():
        assert context["news_state"] == "UNAVAILABLE"
        assert context["impact_state"] == "NO_IMPACT"


@patch("backend.app.scheduler.intraday_runner.get_news_events_for_symbol")
@patch("backend.app.scheduler.intraday_runner.get_connection")
def test_symbol_lookup_failure_does_not_mark_news_confirmed(
    mock_get_connection, mock_get_news
):
    connection = mock_database()
    mock_get_connection.return_value = connection
    mock_get_news.side_effect = RuntimeError("lookup failed")

    result = runner.load_intraday_news_context(["BBCA"], date(2026, 10, 19))

    assert result["BBCA"]["news_state"] == "UNAVAILABLE"
    assert result["BBCA"]["impact_state"] == "NO_IMPACT"


def test_empty_symbol_list_does_not_connect_to_database():
    with patch("backend.app.scheduler.intraday_runner.get_connection") as mock_db:
        result = runner.load_intraday_news_context([], date(2026, 10, 19))

    assert result == {}
    mock_db.assert_not_called()


@patch("backend.app.scheduler.intraday_runner.get_news_events_for_symbol")
@patch("backend.app.scheduler.intraday_runner.get_connection")
def test_news_validation_states_map_to_expected_impact(
    mock_get_connection, mock_get_news
):
    connection = mock_database()
    mock_get_connection.return_value = connection

    cases = {
        "BBCA": ("OFFICIALLY_CONFIRMED", "HIGH", "CONFIRMED", "IMPACT_ELIGIBLE"),
        "BBRI": ("CORROBORATED", "MEDIUM_HIGH", "CORROBORATED", "IMPACT_ELIGIBLE"),
        "BMRI": ("REPORTED", "MEDIUM", "REPORTED", "CONTEXT_ONLY"),
        "BBNI": ("CONTRADICTED", "CONFLICTED", "CONFLICTED", "CONFLICTED"),
        "ASII": ("PENDING", "LOW", "UNVERIFIED", "NO_IMPACT"),
    }

    def lookup(**kwargs):
        status, strength, _, _ = cases[kwargs["symbol"]]
        return [make_event(status, strength)]

    mock_get_news.side_effect = lookup
    result = runner.load_intraday_news_context(list(cases), date(2026, 10, 19))

    for symbol, (_, _, expected_news, expected_impact) in cases.items():
        assert result[symbol]["news_state"] == expected_news
        assert result[symbol]["impact_state"] == expected_impact


@patch("backend.app.scheduler.intraday_runner.get_news_events_for_symbol")
@patch("backend.app.scheduler.intraday_runner.get_connection")
def test_one_symbol_lookup_failure_preserves_other_symbol_context(
    mock_get_connection, mock_get_news
):
    connection = mock_database()
    mock_get_connection.return_value = connection

    def lookup(**kwargs):
        if kwargs["symbol"] == "BBCA":
            raise RuntimeError("lookup failed for BBCA")
        return [make_event()]

    mock_get_news.side_effect = lookup
    result = runner.load_intraday_news_context(
        ["BBCA", "BBRI"], date(2026, 10, 19)
    )

    assert result["BBCA"]["news_state"] == "UNAVAILABLE"
    assert result["BBCA"]["impact_state"] == "NO_IMPACT"
    assert result["BBRI"]["news_state"] == "CONFIRMED"
    assert result["BBRI"]["impact_state"] == "IMPACT_ELIGIBLE"
