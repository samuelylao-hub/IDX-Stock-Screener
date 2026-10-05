from datetime import date, timedelta
from backend.app.database import get_connection
from backend.app.providers.index_alpha import ForeignFlow, IndexAlphaProvider


def save_foreign_flow(flow, stock_id):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO foreign_daily_flow
                (stock_id, trade_date, foreign_buy_value,
                 foreign_sell_value, foreign_net_value)
                VALUES (%s,%s,%s,%s,%s)
                ON CONFLICT (stock_id, trade_date) DO UPDATE SET
                foreign_buy_value=EXCLUDED.foreign_buy_value,
                foreign_sell_value=EXCLUDED.foreign_sell_value,
                foreign_net_value=EXCLUDED.foreign_net_value
            """, (
                stock_id, flow.trade_date, flow.foreign_buy,
                flow.foreign_sell, flow.net_foreign
            ))


def update_foreign_flow(symbol, stock_id, trade_date):
    flow = IndexAlphaProvider().get_foreign_flow(symbol, trade_date)
    save_foreign_flow(flow, stock_id)
    return flow


def update_foreign_history(symbol, stock_id, end_date, days=20):
    provider = IndexAlphaProvider()
    current = end_date - timedelta(days=days - 1)
    saved = 0

    while current <= end_date:
        try:
            flow = provider.get_foreign_flow(symbol, current)
            save_foreign_flow(flow, stock_id)
            saved += 1
        except Exception:
            pass
        current += timedelta(days=1)

    return saved
