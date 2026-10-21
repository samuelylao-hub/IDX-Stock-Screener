from datetime import date, datetime
from unittest.mock import patch
from zoneinfo import ZoneInfo

from backend.app.data import market_calendar
from backend.app.providers import yahoo


def test_unknown_weekday_is_not_assumed_to_be_trading_day():
    day = date(2026, 10, 16)
    with patch.object(
        market_calendar, "get_market_calendar", return_value=None
    ) as lookup:
        assert market_calendar.is_trading_day(day) is False
    lookup.assert_called_once_with(day)


def test_calendar_trading_day_override_is_respected():
    day = date(2026, 10, 16)
    with patch.object(
        market_calendar,
        "get_market_calendar",
        return_value=(day, True, None),
    ):
        assert market_calendar.is_trading_day(day) is True


def test_calendar_holiday_override_is_respected():
    day = date(2026, 10, 16)
    with patch.object(
        market_calendar,
        "get_market_calendar",
        return_value=(day, False, "Hari libur"),
    ):
        assert market_calendar.is_trading_day(day) is False


def test_weekend_returns_false_without_database_lookup():
    day = date(2026, 10, 17)
    with patch.object(market_calendar, "get_market_calendar") as lookup:
        assert market_calendar.is_trading_day(day) is False
    lookup.assert_not_called()


def test_yahoo_update_uses_jakarta_date():
    class FixedDateTime:
        @staticmethod
        def now(tz):
            assert tz == ZoneInfo("Asia/Jakarta")
            return datetime(2026, 10, 16, 10, 0, tzinfo=tz)

    with (
        patch.object(yahoo, "datetime", FixedDateTime, create=True),
        patch.object(yahoo, "is_trading_day", return_value=False) as guard,
    ):
        yahoo.update_all_stocks()

    guard.assert_called_once_with(date(2026, 10, 16))
