from src.db.connection import get_connection

def get_all_stocks():
    with get_connection() as conn:
        return conn.execute(
            "SELECT id, symbol, company_name FROM stocks ORDER BY symbol"
        ).fetchall()