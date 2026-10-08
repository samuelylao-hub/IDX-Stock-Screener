from datetime import date

import yfinance as yf

from backend.app.database import get_connection
from backend.app.data.market_calendar import is_trading_day


def get_daily_prices(symbol: str, period: str = "5d"):
    return yf.download(
        f"{symbol}.JK",
        period=period,
        progress=False,
        auto_adjust=False,
        threads=False,
    )


def save_daily_price(
    stock_id: int,
    trade_date,
    open_price,
    high_price,
    low_price,
    close_price,
    adjusted_close,
    volume,
):
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO stock_prices (
                    stock_id, trade_date, open, high, low, close,
                    adjusted_close, volume
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (stock_id, trade_date)
                DO UPDATE SET
                    open = EXCLUDED.open,
                    high = EXCLUDED.high,
                    low = EXCLUDED.low,
                    close = EXCLUDED.close,
                    adjusted_close = EXCLUDED.adjusted_close,
                    volume = EXCLUDED.volume
                """,
                (
                    stock_id,
                    trade_date,
                    open_price,
                    high_price,
                    low_price,
                    close_price,
                    adjusted_close,
                    volume,
                ),
            )


def save_prices_from_yahoo(symbol: str, period: str = "5d"):
    data = get_daily_prices(symbol, period)

    if data.empty:
        return 0

    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT id FROM stocks WHERE symbol = %s",
                (symbol,),
            )
            stock = cursor.fetchone()

            if stock is None:
                raise ValueError(f"Stock {symbol} belum terdaftar di database.")

            stock_id = stock[0]
            saved = 0

            for trade_date, row in data.iterrows():
                cursor.execute(
                    """
                    INSERT INTO stock_prices (
                        stock_id, trade_date, open, high, low, close,
                        adjusted_close, volume
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (stock_id, trade_date)
                    DO UPDATE SET
                        open = EXCLUDED.open,
                        high = EXCLUDED.high,
                        low = EXCLUDED.low,
                        close = EXCLUDED.close,
                        adjusted_close = EXCLUDED.adjusted_close,
                        volume = EXCLUDED.volume
                    """,
                    (
                        stock_id,
                        trade_date.date(),
                        float(row["Open"].iloc[0]),
                        float(row["High"].iloc[0]),
                        float(row["Low"].iloc[0]),
                        float(row["Close"].iloc[0]),
                        float(row["Adj Close"].iloc[0]),
                        int(row["Volume"].iloc[0]),
                    ),
                )
                saved += 1

            return saved


def update_all_stocks(period: str = "5d", batch_size: int = 50):
    today = date.today()

    if not is_trading_day(today):
        print(f"{today} bukan hari Bursa. Update dilewati.")
        return

    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT id, symbol
                FROM stocks
                WHERE is_active = TRUE
                ORDER BY symbol
                """
            )
            stocks = cursor.fetchall()

    total = len(stocks)
    success = 0
    failed = 0
    rows_saved = 0

    for start in range(0, total, batch_size):
        batch = stocks[start:start + batch_size]
        symbols = [symbol for _, symbol in batch]
        tickers = [f"{symbol}.JK" for symbol in symbols]

        print(
            f"PRICE BATCH {start + 1}-{min(start + batch_size, total)}/{total}"
        )

        try:
            data = yf.download(
                tickers,
                period=period,
                progress=False,
                auto_adjust=False,
                threads=True,
                group_by="ticker",
            )

            if data.empty:
                failed += len(batch)
                print("  NO DATA")
                continue

            with get_connection() as conn:
                with conn.cursor() as cursor:
                    for stock_id, symbol in batch:
                        ticker = f"{symbol}.JK"

                        try:
                            if ticker not in data.columns.get_level_values(0):
                                failed += 1
                                continue

                            ticker_data = data[ticker].dropna(
                                subset=["Close"]
                            )

                            if ticker_data.empty:
                                failed += 1
                                continue

                            for trade_date, row in ticker_data.iterrows():
                                cursor.execute(
                                    """
                                    INSERT INTO stock_prices (
                                        stock_id, trade_date, open, high,
                                        low, close, adjusted_close, volume
                                    )
                                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                                    ON CONFLICT (stock_id, trade_date)
                                    DO UPDATE SET
                                        open = EXCLUDED.open,
                                        high = EXCLUDED.high,
                                        low = EXCLUDED.low,
                                        close = EXCLUDED.close,
                                        adjusted_close = EXCLUDED.adjusted_close,
                                        volume = EXCLUDED.volume
                                    """,
                                    (
                                        stock_id,
                                        trade_date.date(),
                                        float(row["Open"]),
                                        float(row["High"]),
                                        float(row["Low"]),
                                        float(row["Close"]),
                                        float(row["Adj Close"]),
                                        int(row["Volume"]),
                                    ),
                                )
                                rows_saved += 1

                            success += 1

                        except Exception as error:
                            failed += 1
                            print(f"  {symbol}: {error}")

            print(f"  OK={success} FAILED={failed}")

        except Exception as error:
            failed += len(batch)
            print(f"  BATCH FAILED: {error}")

    print(
        f"PRICE UPDATE DONE: total={total}, "
        f"success={success}, failed={failed}, rows={rows_saved}"
    )
