from unittest.mock import patch

import pandas as pd

from backend.app.data import market_data


FIELDS = ["Open", "High", "Low", "Close", "Adj Close", "Volume"]


def _mock_stock_query(mock_connection, symbols):
    conn = mock_connection.return_value.__enter__.return_value
    cursor = conn.cursor.return_value.__enter__.return_value
    cursor.fetchall.return_value = [(symbol,) for symbol in symbols]


def _mock_batch_data(symbols):
    tickers = [f"{symbol}.JK" for symbol in symbols]
    columns = pd.MultiIndex.from_product([tickers, FIELDS])
    values = [[10, 12, 9, 11, 11, 1000] * len(tickers) for _ in range(2)]
    return pd.DataFrame(
        values,
        index=pd.date_range("2026-10-20", periods=2),
        columns=columns,
    )


def _common_patches(symbols):
    return (
        patch.object(market_data, "is_trading_day", return_value=True),
        patch.object(market_data, "get_connection"),
        patch.object(market_data.yf, "download", return_value=_mock_batch_data(symbols)),
        patch.object(market_data.time, "sleep"),
    )


def test_update_all_stocks_returns_full_success_summary():
    symbols = ["BBCA", "BBRI"]
    with (
        patch.object(market_data, "is_trading_day", return_value=True),
        patch.object(market_data, "get_connection") as get_connection,
        patch.object(market_data.yf, "download", return_value=_mock_batch_data(symbols)),
        patch.object(market_data, "_save_price_frame", side_effect=[5, 3]) as save_frame,
        patch.object(market_data.time, "sleep"),
    ):
        _mock_stock_query(get_connection, symbols)
        result = market_data.update_all_stocks("5d", symbols=symbols)

    assert result["requested"] == 2
    assert result["success"] == 2
    assert result["failed"] == 0
    assert result["rows_saved"] == 8
    assert result["skipped"] is False
    assert result["failures"] == []
    assert save_frame.call_count == 2


def test_update_all_stocks_reports_partial_failure():
    symbols = ["BBCA", "BBRI", "BMRI"]
    with (
        patch.object(market_data, "is_trading_day", return_value=True),
        patch.object(market_data, "get_connection") as get_connection,
        patch.object(market_data.yf, "download", return_value=_mock_batch_data(symbols)),
        patch.object(
            market_data, "_save_price_frame",
            side_effect=[5, RuntimeError("Database unavailable"), 3],
        ),
        patch.object(market_data.time, "sleep"),
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
        patch.object(market_data.yf, "download", return_value=_mock_batch_data(symbols)),
        patch.object(
            market_data, "_save_price_frame",
            side_effect=RuntimeError("Database unavailable"),
        ),
        patch.object(market_data.time, "sleep"),
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
