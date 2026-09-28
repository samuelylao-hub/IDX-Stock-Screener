from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Optional

from backend.app.database import get_connection


@dataclass
class SignalFusionInput:
    symbol: str
    trade_date: date
    net_foreign: Optional[Decimal]
    broker_net: Optional[Decimal]
    first_close: Optional[Decimal]
    last_close: Optional[Decimal]


class SignalFusionRepository:
    def get_signal_input(
        self,
        symbol: str,
        trade_date: date,
        price_lookback: int = 5,
        investor_type: str = "all",
        market_segment: str = "RG",
    ) -> SignalFusionInput:
        connection = get_connection()

        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT id
                    FROM stocks
                    WHERE symbol = %s
                    """,
                    (symbol,),
                )

                stock = cursor.fetchone()

                if stock is None:
                    raise ValueError(
                        f"Stock {symbol} belum terdaftar di database."
                    )

                stock_id = stock[0]

                cursor.execute(
                    """
                    SELECT foreign_net_value
                    FROM foreign_daily_flow
                    WHERE stock_id = %s
                      AND trade_date = %s
                    """,
                    (
                        stock_id,
                        trade_date,
                    ),
                )

                foreign_row = cursor.fetchone()
                net_foreign = (
                    foreign_row[0]
                    if foreign_row is not None
                    else None
                )

                cursor.execute(
                    """
                    SELECT
                        COALESCE(
                            SUM(buy_value - sell_value),
                            0
                        )
                    FROM broker_stock_flow
                    WHERE stock_id = %s
                      AND trade_date = %s
                      AND investor_type = %s
                      AND market_segment = %s
                    """,
                    (
                        stock_id,
                        trade_date,
                        investor_type,
                        market_segment,
                    ),
                )

                broker_row = cursor.fetchone()
                broker_net = (
                    broker_row[0]
                    if broker_row is not None
                    else None
                )

                cursor.execute(
                    """
                    SELECT
                        close
                    FROM stock_prices
                    WHERE stock_id = %s
                      AND trade_date <= %s
                      AND close IS NOT NULL
                    ORDER BY trade_date DESC
                    LIMIT %s
                    """,
                    (
                        stock_id,
                        trade_date,
                        price_lookback,
                    ),
                )

                price_rows = cursor.fetchall()

                closes = [
                    row[0]
                    for row in reversed(price_rows)
                ]

                first_close = closes[0] if closes else None
                last_close = closes[-1] if closes else None

                return SignalFusionInput(
                    symbol=symbol,
                    trade_date=trade_date,
                    net_foreign=net_foreign,
                    broker_net=broker_net,
                    first_close=first_close,
                    last_close=last_close,
                )

        finally:
            connection.close()
