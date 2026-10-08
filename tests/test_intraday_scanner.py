from datetime import datetime
from zoneinfo import ZoneInfo

from backend.app.services.intraday_scanner import _regular_session


TZ = ZoneInfo("Asia/Jakarta")


def test_regular_session_removes_post_market():
    rows = [
        {
            "datetime": datetime(2026, 10, 8, 15, 45, tzinfo=TZ),
            "volume": 100,
        },
        {
            "datetime": datetime(2026, 10, 8, 16, 0, tzinfo=TZ),
            "volume": 999,
        },
        {
            "datetime": datetime(2026, 10, 8, 16, 10, tzinfo=TZ),
            "volume": 50,
        },
    ]

    result = _regular_session(rows)

    assert len(result) == 1
    assert result[0]["datetime"].time().strftime("%H:%M") == "15:45"


def test_regular_session_keeps_market_open_candles():
    rows = [
        {
            "datetime": datetime(2026, 10, 8, 9, 0, tzinfo=TZ),
            "volume": 100,
        },
        {
            "datetime": datetime(2026, 10, 8, 13, 30, tzinfo=TZ),
            "volume": 200,
        },
        {
            "datetime": datetime(2026, 10, 8, 15, 45, tzinfo=TZ),
            "volume": 300,
        },
    ]

    result = _regular_session(rows)

    assert len(result) == 3
