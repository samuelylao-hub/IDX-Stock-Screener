import pandas as pd

from backend.app.data.market_data import _extract_ticker_frame


FIELDS = ["Open", "High", "Low", "Close", "Adj Close", "Volume"]


def _frame(columns):
    values = [[1, 2, 0.5, 1.5, 1.5, 100] for _ in range(2)]
    return pd.DataFrame(values, index=pd.date_range("2026-10-20", periods=2), columns=columns)


def test_extract_ticker_frame_grouped_by_ticker():
    tickers = ["BBCA.JK", "BBRI.JK"]
    columns = pd.MultiIndex.from_product([tickers, FIELDS])
    data = _frame(columns)

    result = _extract_ticker_frame(data, "BBRI.JK", 2)

    assert list(result.columns) == FIELDS
    assert len(result) == 2


def test_extract_ticker_frame_grouped_by_field():
    tickers = ["BBCA.JK", "BBRI.JK"]
    columns = pd.MultiIndex.from_product([FIELDS, tickers])
    data = _frame(columns)

    result = _extract_ticker_frame(data, "BBRI.JK", 2)

    assert list(result.columns) == FIELDS
    assert len(result) == 2


def test_extract_ticker_frame_returns_none_for_missing_ticker():
    columns = pd.MultiIndex.from_product([["BBCA.JK"], FIELDS])
    data = _frame(columns)

    assert _extract_ticker_frame(data, "BBRI.JK", 2) is None


def test_extract_ticker_frame_single_ticker_flat_columns():
    data = _frame(FIELDS)

    result = _extract_ticker_frame(data, "BBCA.JK", 1)

    assert result is data
