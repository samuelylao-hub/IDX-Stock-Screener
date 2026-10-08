from datetime import datetime
from zoneinfo import ZoneInfo

from backend.app.scheduler.intraday_session import (
    is_intraday_session,
    session_name,
)


JAKARTA_TZ = ZoneInfo("Asia/Jakarta")


def _dt(
    year,
    month,
    day,
    hour,
    minute,
):
    return datetime(
        year,
        month,
        day,
        hour,
        minute,
        tzinfo=JAKARTA_TZ,
    )


def test_weekend_closed():
    saturday = _dt(
        2026,
        10,
        10,
        10,
        0,
    )

    sunday = _dt(
        2026,
        10,
        11,
        10,
        0,
    )

    assert not is_intraday_session(
        saturday
    )

    assert not is_intraday_session(
        sunday
    )

    assert session_name(
        saturday
    ) == "CLOSED"


def test_monday_morning_open():
    dt = _dt(
        2026,
        10,
        12,
        9,
        0,
    )

    assert is_intraday_session(dt)
    assert session_name(dt) == "MORNING"


def test_monday_before_open():
    dt = _dt(
        2026,
        10,
        12,
        8,
        59,
    )

    assert not is_intraday_session(dt)


def test_monday_lunch_break():
    dt = _dt(
        2026,
        10,
        12,
        12,
        30,
    )

    assert not is_intraday_session(dt)
    assert session_name(dt) == "CLOSED"


def test_monday_afternoon_open():
    dt = _dt(
        2026,
        10,
        12,
        13,
        30,
    )

    assert is_intraday_session(dt)
    assert session_name(dt) == "AFTERNOON"


def test_monday_after_close():
    dt = _dt(
        2026,
        10,
        12,
        16,
        0,
    )

    assert not is_intraday_session(dt)


def test_friday_morning_session():
    dt = _dt(
        2026,
        10,
        9,
        11,
        29,
    )

    assert is_intraday_session(dt)
    assert session_name(dt) == "FRIDAY_MORNING"


def test_friday_lunch_break():
    dt = _dt(
        2026,
        10,
        9,
        11,
        31,
    )

    assert not is_intraday_session(dt)


def test_friday_afternoon_session():
    dt = _dt(
        2026,
        10,
        9,
        14,
        0,
    )

    assert is_intraday_session(dt)
    assert session_name(dt) == "FRIDAY_AFTERNOON"


def test_friday_after_close():
    dt = _dt(
        2026,
        10,
        9,
        15,
        50,
    )

    assert not is_intraday_session(dt)
