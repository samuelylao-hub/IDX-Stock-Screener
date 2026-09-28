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


@dataclass
class HistoricalPricePoint:
    trade_date: date
    close: Decimal


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
                    (stock_id, trade_date),
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
                        SUM(buy_value - sell_value),
                        COUNT(*)
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

                broker_net = None

                if broker_row is not None:
                    broker_sum, broker_count = broker_row

                    if broker_count > 0:
                        broker_net = broker_sum

                price_rows = self.get_historical_prices(
                    symbol=symbol,
                    trade_date=trade_date,
                    lookback=price_lookback,
                    connection=connection,
                )

                first_close = (
                    price_rows[0].close
                    if price_rows
                    else None
                )

                last_close = (
                    price_rows[-1].close
                    if price_rows
                    else None
                )

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

    def get_historical_prices(
        self,
        symbol: str,
        trade_date: date,
        lookback: int = 5,
        connection=None,
    ) -> list[HistoricalPricePoint]:
        own_connection = connection is None

        if own_connection:
            connection = get_connection()

        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT
                        p.trade_date,
                        p.close
                    FROM stock_prices p
                    JOIN stocks s
                      ON s.id = p.stock_id
                    WHERE s.symbol = %s
                      AND p.trade_date <= %s
                      AND p.close IS NOT NULL
                    ORDER BY p.trade_date DESC
                    LIMIT %s
                    """,
                    (
                        symbol,
                        trade_date,
                        lookback,
                    ),
                )

                rows = cursor.fetchall()

                return [
                    HistoricalPricePoint(
                        trade_date=row[0],
                        close=row[1],
                    )
                    for row in reversed(rows)
                ]

        finally:
            if own_connection:
                connection.close()