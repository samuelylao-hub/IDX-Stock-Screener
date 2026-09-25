from datetime import date

from backend.app.database import get_connection


def save_market_calendar(
    calendar_date: date,
    is_trading_day: bool,
    holiday_name: str | None = None,
):
    conn = get_connection()

    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO market_calendar (
                    calendar_date,
                    is_trading_day,
                    holiday_name
                )
                VALUES (%s, %s, %s)
                ON CONFLICT (calendar_date)
                DO UPDATE SET
                    is_trading_day = EXCLUDED.is_trading_day,
                    holiday_name = EXCLUDED.holiday_name
                """,
                (
                    calendar_date,
                    is_trading_day,
                    holiday_name,
                ),
            )

        conn.commit()

    finally:
        conn.close()


def get_market_calendar(calendar_date: date):
    conn = get_connection()

    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    calendar_date,
                    is_trading_day,
                    holiday_name
                FROM market_calendar
                WHERE calendar_date = %s
                """,
                (calendar_date,),
            )

            return cursor.fetchone()

    finally:
        conn.close()


def is_trading_day(calendar_date: date):
    # Sabtu dan Minggu selalu libur Bursa
    if calendar_date.weekday() >= 5:
        return False

    # Cek apakah ada holiday override di database
    result = get_market_calendar(calendar_date)

    if result is not None:
        return result[1]

    # Senin-Jumat dianggap hari Bursa
    # kecuali ada override libur di database
    return True