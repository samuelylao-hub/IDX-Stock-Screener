from src.db.connection import get_connection

def get_foreign_flow(symbol):
    with get_connection() as conn:
        return conn.execute(
            """SELECT trade_date, foreign_buy_value,
                      foreign_sell_value, foreign_net_value
               FROM foreign_daily_flow
               JOIN stocks ON stocks.id = foreign_daily_flow.stock_id
               WHERE stocks.symbol = %s
               ORDER BY trade_date""",
            (symbol,),
        ).fetchall()
