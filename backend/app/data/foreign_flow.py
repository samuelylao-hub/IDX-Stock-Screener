from datetime import date

from backend.app.database import get_connection
from backend.app.providers.index_alpha import (
    ForeignFlow,
    IndexAlphaProvider,
)


def save_foreign_flow(
    flow: ForeignFlow,
    stock_id: int,
):
    connection = get_connection()

    query = """
        INSERT INTO foreign_daily_flow (
            stock_id,
            trade_date,
            foreign_buy_value,
            foreign_sell_value,
            foreign_net_value
        )
        VALUES (
            %s,
            %s,
            %s,
            %s,
            %s
        )
        ON CONFLICT (stock_id, trade_date)
        DO UPDATE SET
            foreign_buy_value = EXCLUDED.foreign_buy_value,
            foreign_sell_value = EXCLUDED.foreign_sell_value,
            foreign_net_value = EXCLUDED.foreign_net_value
    """

    with connection.cursor() as cursor:
        cursor.execute(
            query,
            (
                stock_id,
                flow.trade_date,
                flow.foreign_buy,
                flow.foreign_sell,
                flow.net_foreign,
            ),
        )

    connection.commit()
    connection.close()


def update_foreign_flow(
    symbol: str,
    stock_id: int,
    trade_date: date,
):
    provider = IndexAlphaProvider()

    flow = provider.get_foreign_flow(
        symbol=symbol,
        trade_date=trade_date,
    )

    save_foreign_flow(
        flow=flow,
        stock_id=stock_id,
    )

    return flow