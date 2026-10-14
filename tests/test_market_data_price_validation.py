from unittest.mock import patch

import pandas as pd
import pytest

from backend.app.data import market_data


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("Open", float("nan")),
        ("High", float("inf")),
        ("Low", -1),
        ("Close", 0),
        ("Adj Close", float("-inf")),
        ("Volume", -1),
    ],
)
def test_save_prices_from_yahoo_rejects_invalid_values_before_database_write(
    field, value
):
    row = {
        "Open": 10.0,
        "High": 12.0,
        "Low": 9.0,
        "Close": 11.0,
        "Adj Close": 11.0,
        "Volume": 1000,
    }
    row[field] = value
    data = pd.DataFrame([row], index=pd.to_datetime(["2026-10-13"]))

    with (
        patch.object(market_data, "get_daily_prices", return_value=data),
        patch.object(market_data, "get_connection") as get_connection,
    ):
        with pytest.raises((ValueError, TypeError, OverflowError)):
            market_data.save_prices_from_yahoo("BBCA")

    get_connection.assert_not_called()


def test_save_prices_from_yahoo_rejects_missing_required_column():
    data = pd.DataFrame(
        {
            "Open": [10.0],
            "High": [12.0],
            "Low": [9.0],
            "Close": [11.0],
            "Volume": [1000],
        },
        index=pd.to_datetime(["2026-10-13"]),
    )

    with (
        patch.object(market_data, "get_daily_prices", return_value=data),
        patch.object(market_data, "get_connection") as get_connection,
    ):
        with pytest.raises((ValueError, KeyError)):
            market_data.save_prices_from_yahoo("BBCA")

    get_connection.assert_not_called()
