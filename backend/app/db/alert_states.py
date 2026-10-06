from datetime import date

from backend.app.database import get_connection


def get_alert_state(symbol: str, trade_date: date):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT state, level, ranking_score FROM alert_states WHERE symbol = %s AND trade_date = %s", (symbol, trade_date))
            return cur.fetchone()


def save_alert_state(symbol: str, trade_date: date, state: str, level: str, ranking_score: float):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("INSERT INTO alert_states (symbol, trade_date, state, level, ranking_score) VALUES (%s, %s, %s, %s, %s) ON CONFLICT (symbol, trade_date) DO UPDATE SET state = EXCLUDED.state, level = EXCLUDED.level, ranking_score = EXCLUDED.ranking_score", (symbol, trade_date, state, level, ranking_score))
        conn.commit()
