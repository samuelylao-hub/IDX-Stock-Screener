from src.db.connection import get_connection

def get_market_calendar():
    with get_connection() as conn:
        return conn.execute(
            """SELECT calendar_date, is_trading_day
               FROM market_calendar
               ORDER BY calendar_date"""
        ).fetchall()
