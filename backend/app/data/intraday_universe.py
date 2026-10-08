from backend.app.database import get_connection


def get_intraday_symbols():
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT symbol
                FROM stocks
                WHERE is_active = TRUE
                  AND (
                      liquidity_tier IN ('A', 'B')
                      OR thematic_group IS NOT NULL
                  )
                ORDER BY symbol
            """)
            return [row[0] for row in cur.fetchall()]
