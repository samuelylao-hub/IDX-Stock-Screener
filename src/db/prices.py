from src.db.connection import get_connection

def get_prices(symbol):
    with get_connection() as conn:
        return conn.execute(
            """SELECT trade_date, open, high, low, close, volume
               FROM stock_prices
               JOIN stocks ON stocks.id = stock_prices.stock_id
               WHERE stocks.symbol = %s
               ORDER BY trade_date""",
            (symbol,),
        ).fetchall()