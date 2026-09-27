from datetime import date

from backend.app.database import get_connection
from backend.app.providers.index_alpha import (
    BrokerSummary,
    IndexAlphaProvider,
)


def save_broker_summary(
    summaries: list[BrokerSummary],
    stock_id: int,
    investor_type: str = "all",
    market_segment: str = "RG",
):
    if not summaries:
        return 0

    connection = get_connection()

    query = """
        INSERT INTO broker_stock_flow (
            stock_id,
            trade_date,
            broker_code,
            investor_type,
            market_segment,
            buy_freq,
            buy_volume,
            buy_value,
            sell_freq,
            sell_volume,
            sell_value,
            buy_avg,
            sell_avg
        )
        VALUES (
            %s,
            %s,
            %s,
            %s,
            %s,
            %s,
            %s,
            %s,
            %s,
            %s,
            %s,
            %s,
            %s
        )
        ON CONFLICT (
            stock_id,
            trade_date,
            broker_code,
            investor_type,
            market_segment
        )
        DO UPDATE SET
            buy_freq = EXCLUDED.buy_freq,
            buy_volume = EXCLUDED.buy_volume,
            buy_value = EXCLUDED.buy_value,
            sell_freq = EXCLUDED.sell_freq,
            sell_volume = EXCLUDED.sell_volume,
            sell_value = EXCLUDED.sell_value,
            buy_avg = EXCLUDED.buy_avg,
            sell_avg = EXCLUDED.sell_avg,
            updated_at = NOW()
    """

    saved_count = 0

    try:
        with connection.cursor() as cursor:
            for summary in summaries:
                cursor.execute(
                    query,
                    (
                        stock_id,
                        summary.trade_date,
                        summary.broker_code,
                        investor_type,
                        market_segment,
                        summary.buy_freq,
                        summary.buy_volume,
                        summary.buy_value,
                        summary.sell_freq,
                        summary.sell_volume,
                        summary.sell_value,
                        summary.buy_avg,
                        summary.sell_avg,
                    ),
                )

                saved_count += 1

        connection.commit()

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()

    return saved_count


def update_broker_summary(
    symbol: str,
    stock_id: int,
    trade_date: date,
    investor_type: str = "all",
    market_segment: str = "RG",
):
    provider = IndexAlphaProvider()

    summaries = provider.get_broker_summary(
        symbol=symbol,
        trade_date=trade_date,
        investor=investor_type,
        market=market_segment,
    )

    saved_count = save_broker_summary(
        summaries=summaries,
        stock_id=stock_id,
        investor_type=investor_type,
        market_segment=market_segment,
    )

    return saved_count