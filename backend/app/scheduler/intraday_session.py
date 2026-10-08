from __future__ import annotations

from datetime import datetime, time
from zoneinfo import ZoneInfo


JAKARTA_TZ = ZoneInfo("Asia/Jakarta")


def is_intraday_session(dt: datetime | None = None) -> bool:
    """
    Cek apakah waktu saat ini berada di sesi perdagangan intraday BEI.

    Senin-Kamis:
        09:00 - 12:00
        13:30 - 15:49

    Jumat:
        09:00 - 11:30
        14:00 - 15:49

    Sabtu/Minggu:
        Tidak aktif.
    """

    if dt is None:
        dt = datetime.now(JAKARTA_TZ)

    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=JAKARTA_TZ)

    weekday = dt.weekday()
    current = dt.time()

    if weekday >= 5:
        return False

    morning_start = time(9, 0)

    if weekday == 4:
        morning_end = time(11, 30)
        afternoon_start = time(14, 0)
    else:
        morning_end = time(12, 0)
        afternoon_start = time(13, 30)

    afternoon_end = time(15, 49, 59)

    morning_session = (
        morning_start
        <= current
        <= morning_end
    )

    afternoon_session = (
        afternoon_start
        <= current
        <= afternoon_end
    )

    return (
        morning_session
        or afternoon_session
    )


def session_name(dt: datetime | None = None) -> str:
    if dt is None:
        dt = datetime.now(JAKARTA_TZ)

    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=JAKARTA_TZ)

    if not is_intraday_session(dt):
        return "CLOSED"

    if dt.weekday() == 4:
        if dt.time() <= time(11, 30):
            return "FRIDAY_MORNING"
        return "FRIDAY_AFTERNOON"

    if dt.time() <= time(12, 0):
        return "MORNING"

    return "AFTERNOON"
