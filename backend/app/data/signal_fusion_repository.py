from dataclasses import dataclass, field
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
    foreign_windows: dict[int, "FlowWindow"] = field(default_factory=dict)
    broker_windows: dict[int, "FlowWindow"] = field(default_factory=dict)


@dataclass
class HistoricalPricePoint:
    trade_date: date
    close: Decimal


@dataclass
class FlowWindow:
    window_days: int
    available_days: int
    net_value: Optional[Decimal]
    positive_days: int
    negative_days: int
    zero_days: int
    consistency_ratio: Optional[Decimal]
    status: str


class SignalFusionRepository:
    def get_signal_input(
        self,
        symbol: str,
        trade_date: date,
        price_lookback: int = 5,
        investor_type: str = "all",
        market_segment: str = "RG",
        connection=None,
    ) -> SignalFusionInput:
        own_connection = connection is None

        if own_connection:
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
                stock_row = cursor.fetchone()

                if stock_row is None:
                    raise ValueError(f"Stock not found: {symbol}")

                stock_id = stock_row[0]

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
                        SUM(buy_value - sell_value)
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

                historical_prices = self.get_historical_prices(
                    symbol=symbol,
                    trade_date=trade_date,
                    lookback=price_lookback,
                    connection=connection,
                )

                first_close = (
                    historical_prices[0].close
                    if historical_prices
                    else None
                )
                last_close = (
                    historical_prices[-1].close
                    if historical_prices
                    else None
                )

                foreign_windows = self.get_foreign_flow_windows(
                    symbol=symbol,
                    trade_date=trade_date,
                    connection=connection,
                )

                broker_windows = self.get_broker_flow_windows(
                    symbol=symbol,
                    trade_date=trade_date,
                    investor_type=investor_type,
                    market_segment=market_segment,
                    connection=connection,
                )

                return SignalFusionInput(
                    symbol=symbol,
                    trade_date=trade_date,
                    net_foreign=net_foreign,
                    broker_net=broker_net,
                    first_close=first_close,
                    last_close=last_close,
                    foreign_windows=foreign_windows,
                    broker_windows=broker_windows,
                )

        finally:
            if own_connection:
                connection.close()

    def get_foreign_flow_windows(
        self,
        symbol: str,
        trade_date: date,
        windows=(1, 5, 20),
        connection=None,
    ) -> dict[int, FlowWindow]:
        own_connection = connection is None

        if own_connection:
            connection = get_connection()

        try:
            with connection.cursor() as cursor:
                max_window = max(windows)

                cursor.execute(
                    """
                    SELECT
                        f.trade_date,
                        f.foreign_net_value
                    FROM foreign_daily_flow f
                    JOIN stocks s
                      ON s.id = f.stock_id
                    WHERE s.symbol = %s
                      AND f.trade_date <= %s
                      AND f.foreign_net_value IS NOT NULL
                    ORDER BY f.trade_date DESC
                    LIMIT %s
                    """,
                    (
                        symbol,
                        trade_date,
                        max_window,
                    ),
                )

                rows = cursor.fetchall()

                points = [
                    (row[0], row[1])
                    for row in reversed(rows)
                ]

                return {
                    window: self._build_flow_window(
                        window_days=window,
                        values=[value for _, value in points[-window:]],
                    )
                    for window in windows
                }

        finally:
            if own_connection:
                connection.close()

    def get_broker_flow_windows(
        self,
        symbol: str,
        trade_date: date,
        windows=(1, 5, 20),
        investor_type: str = "all",
        market_segment: str = "RG",
        connection=None,
    ) -> dict[int, FlowWindow]:
        own_connection = connection is None

        if own_connection:
            connection = get_connection()

        try:
            with connection.cursor() as cursor:
                max_window = max(windows)

                cursor.execute(
                    """
                    SELECT
                        b.trade_date,
                        SUM(b.buy_value - b.sell_value)
                    FROM broker_stock_flow b
                    JOIN stocks s
                      ON s.id = b.stock_id
                    WHERE s.symbol = %s
                      AND b.trade_date <= %s
                      AND b.investor_type = %s
                      AND b.market_segment = %s
                    GROUP BY b.trade_date
                    ORDER BY b.trade_date DESC
                    LIMIT %s
                    """,
                    (
                        symbol,
                        trade_date,
                        investor_type,
                        market_segment,
                        max_window,
                    ),
                )

                rows = cursor.fetchall()

                points = [
                    (row[0], row[1])
                    for row in reversed(rows)
                ]

                return {
                    window: self._build_flow_window(
                        window_days=window,
                        values=[value for _, value in points[-window:]],
                    )
                    for window in windows
                }

        finally:
            if own_connection:
                connection.close()

    @staticmethod
    def _build_flow_window(
        window_days: int,
        values: list[Decimal],
    ) -> FlowWindow:
        clean_values = [
            value
            for value in values
            if value is not None
        ]

        available_days = len(clean_values)

        if available_days == 0:
            return FlowWindow(
                window_days=window_days,
                available_days=0,
                net_value=None,
                positive_days=0,
                negative_days=0,
                zero_days=0,
                consistency_ratio=None,
                status="INSUFFICIENT_DATA",
            )

        net_value = sum(clean_values)

        positive_days = sum(
            1 for value in clean_values if value > 0
        )
        negative_days = sum(
            1 for value in clean_values if value < 0
        )
        zero_days = sum(
            1 for value in clean_values if value == 0
        )

        dominant_days = max(
            positive_days,
            negative_days,
        )

        consistency_ratio = (
            Decimal(dominant_days)
            / Decimal(available_days)
        )

        status = (
            "AVAILABLE"
            if available_days >= window_days
            else "INSUFFICIENT_DATA"
        )

        return FlowWindow(
            window_days=window_days,
            available_days=available_days,
            net_value=net_value,
            positive_days=positive_days,
            negative_days=negative_days,
            zero_days=zero_days,
            consistency_ratio=consistency_ratio,
            status=status,
        )

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
