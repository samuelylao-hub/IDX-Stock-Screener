from backend.app.database import get_connection


def get_latest_intraday_state(symbol: str, trade_date):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT state, score
                FROM intraday_alert_states
                WHERE symbol = %s
                  AND trade_date = %s
                """,
                (symbol, trade_date),
            )
            return cur.fetchone()


def save_intraday_state(
    symbol: str,
    trade_date,
    state: str,
    score: float,
):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO intraday_alert_states
                    (symbol, trade_date, state, score)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (symbol, trade_date)
                DO UPDATE SET
                    state = EXCLUDED.state,
                    score = EXCLUDED.score,
                    updated_at = CURRENT_TIMESTAMP
                """,
                (
                    symbol,
                    trade_date,
                    state,
                    score,
                ),
            )
        conn.commit()
