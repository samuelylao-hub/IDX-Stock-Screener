from src.db.connection import get_connection

def get_news_events(symbol):
    with get_connection() as conn:
        return conn.execute(
            """SELECT id, event_key, symbol, canonical_title,
                      first_published_at, first_detected_at,
                      importance, validation_status,
                      source_count, official_source_count,
                      primary_source_count
               FROM news_events
               WHERE symbol = %s
               ORDER BY first_published_at DESC""",
            (symbol,),
        ).fetchall()
