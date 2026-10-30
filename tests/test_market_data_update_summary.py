from unittest.mock import patch

import pytest

from backend.app.data import market_data


def _mock_stock_query(mock_connection, symbols):
    conn = mock_connection.return_value.__enter__.return_value
    cursor = conn.cursor.return_value.__enter__.return_value
    cursor.fetchall.return_value = [(symbol,) for symbol in symbols]


def test_update_all_stocks_returns_full_success_summary():
    symbols = ["BBCA", "BBRI"]
    with (
        patch.object(market_data, "is_trading_day", return_value=True),
        patch.object(market_data, "get_connection") as get_connection,
        patch.object(
            market_data, "save_prices_from_yahoo", side_effect=[5, 3]
        ) as save_prices,
    ):
        _mock_stock_query(get_connection, symbols)

        result = market_data.update_all_stocks("5d", symbols=symbols)

    assert result["requested"] == 2
    assert result["success"] == 2
    assert result["failed"] == 0
    assert result["rows_saved"] == 8
    assert result["skipped"] is False
    assert result["failures"] == []
    assert save_prices.call_count == 2


def test_update_all_stocks_reports_partial_failure():
    symbols = ["BBCA", "BBRI", "BMRI"]
    with (
        patch.object(market_data, "is_trading_day", return_value=True),
        patch.object(market_data, "get_connection") as get_connection,
        patch.object(
            market_data,
            "save_prices_from_yahoo",
            side_effect=[5, RuntimeError("Yahoo unavailable"), 3],
        ),
    ):
        _mock_stock_query(get_connection, symbols)

        result = market_data.update_all_stocks("5d", symbols=symbols)

    assert result["requested"] == 3
    assert result["success"] == 2
    assert result["failed"] == 1
    assert result["rows_saved"] == 8
    assert result["failures"][0]["symbol"] == "BBRI"


def test_update_all_stocks_reports_total_failure():
    symbols = ["BBCA", "BBRI"]
    with (
        patch.object(market_data, "is_trading_day", return_value=True),
        patch.object(market_data, "get_connection") as get_connection,
        patch.object(
            market_data,
            "save_prices_from_yahoo",
            side_effect=RuntimeError("Yahoo unavailable"),
        ),
    ):
        _mock_stock_query(get_connection, symbols)

        result = market_data.update_all_stocks("5d", symbols=symbols)

    assert result["requested"] == 2
    assert result["success"] == 0
    assert result["failed"] == 2
    assert result["rows_saved"] == 0
    assert len(result["failures"]) == 2


def test_update_all_stocks_skips_non_trading_day():
    with (
        patch.object(market_data, "is_trading_day", return_value=False),
        patch.object(market_data, "get_connection") as get_connection,
    ):
        result = market_data.update_all_stocks("5d", symbols=["BBCA"])

    assert result["skipped"] is True
    assert result["requested"] == 0
    assert result["success"] == 0
    assert result["failed"] == 0
    get_connection.assert_not_called()
