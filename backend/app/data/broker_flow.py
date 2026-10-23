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

def update_broker_summary_batch(
    stocks,
    trade_date,
    investor_type="all",
    market_segment="RG",
):
    from pathlib import Path
    from datetime import datetime
    from zoneinfo import ZoneInfo

    log_path = Path("logs/broker_flow.log")
    log_path.parent.mkdir(parents=True, exist_ok=True)

    def diagnostic(message):
        timestamp = datetime.now(ZoneInfo("Asia/Jakarta")).isoformat(timespec="seconds")
        with log_path.open("a", encoding="utf-8") as log:
            log.write(f"{timestamp} WIB | BROKER_BATCH_DIAGNOSTIC | {message}\n")

    provider = IndexAlphaProvider()
    symbols = [symbol for _, symbol in stocks]

    if not symbols:
        diagnostic(f"NO_SYMBOLS trade_date={trade_date}")
        return 0

    data = {}
    for i in range(0, len(symbols), 50):
        batch = symbols[i:i + 50]
        try:
            batch_data = provider.get_broker_summary_batch(
                batch,
                trade_date,
                investor=investor_type,
                market=market_segment,
            )
        except Exception as exc:
            diagnostic(
                f"API_ERROR trade_date={trade_date} ticker_count={len(batch)} "
                f"error_type={type(exc).__name__} error={str(exc)[:500]}"
            )
            raise

        if not isinstance(batch_data, dict):
            diagnostic(
                f"INVALID_RESPONSE trade_date={trade_date} "
                f"response_type={type(batch_data).__name__}"
            )
            raise RuntimeError("Respons batch broker summary bukan objek mapping.")

        data.update(batch_data)
        diagnostic(
            f"API_RESPONSE trade_date={trade_date} requested={len(batch)} "
            f"returned_symbols={len(batch_data)}"
        )

    missing_symbols = [symbol for symbol in symbols if symbol not in data]
    if missing_symbols:
        diagnostic(
            f"MISSING_SYMBOLS trade_date={trade_date} "
            f"symbols={','.join(missing_symbols)}"
        )
        print(
            "PERINGATAN broker flow: simbol tidak ada dalam respons API: "
            + ", ".join(missing_symbols)
        )

    saved = 0
    row_counts = {symbol: len(data.get(symbol, [])) for _, symbol in stocks}
    diagnostic(
        f"ROW_COUNTS trade_date={trade_date} "
        + ",".join(f"{symbol}:{count}" for symbol, count in row_counts.items())
    )
    empty_symbols = [symbol for symbol, count in row_counts.items() if count == 0]
    if empty_symbols:
        diagnostic(
            f"EMPTY_ROWS trade_date={trade_date} "
            f"symbols={",".join(empty_symbols)}"
        )
    for stock_id, symbol in stocks:
        rows = data.get(symbol, [])
        summaries = [
            BrokerSummary(
                symbol=symbol,
                trade_date=trade_date,
                broker_code=row["code"],
                buy_freq=int(row["buy_freq"]),
                buy_volume=int(row["buy_volume"]),
                buy_value=int(row["buy_value"]),
                sell_freq=int(row["sell_freq"]),
                sell_volume=int(row["sell_volume"]),
                sell_value=int(row["sell_value"]),
                buy_avg=float(row["buy_avg"]),
                sell_avg=float(row["sell_avg"]),
            )
            for row in rows
        ]
        saved += save_broker_summary(
            summaries=summaries,
            stock_id=stock_id,
            investor_type=investor_type,
            market_segment=market_segment,
        )

    diagnostic(
        f"SAVE_COMPLETE trade_date={trade_date} requested={len(stocks)} "
        f"returned_symbols={len(data)} saved_rows={saved}"
    )
    return saved
