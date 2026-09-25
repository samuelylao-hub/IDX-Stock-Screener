import yfinance as yf

from backend.app.database import get_connection
from backend.app.data.market_calendar import is_trading_day


def get_daily_prices(symbol: str, period: str = "5d"):
    ticker = f"{symbol}.JK"

    data = yf.download(
        ticker,
        period=period,
        progress=False,
        auto_adjust=False,
    )

    return data


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
    conn = get_connection()

    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO stock_prices (
                    stock_id,
                    trade_date,
                    open,
                    high,
                    low,
                    close,
                    adjusted_close,
                    volume
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

        conn.commit()

    finally:
        conn.close()


def save_prices_from_yahoo(symbol: str, period: str = "5d"):
    data = get_daily_prices(symbol, period)

    conn = get_connection()

    try:
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT id FROM stocks WHERE symbol = %s",
                (symbol,),
            )

            stock = cursor.fetchone()

            if stock is None:
                raise ValueError(
                    f"Stock {symbol} belum terdaftar di database."
                )

            stock_id = stock[0]

            for date, row in data.iterrows():
                cursor.execute(
                    """
                    INSERT INTO stock_prices (
                        stock_id,
                        trade_date,
                        open,
                        high,
                        low,
                        close,
                        adjusted_close,
                        volume
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
                        date.date(),
                        float(row["Open"].iloc[0]),
                        float(row["High"].iloc[0]),
                        float(row["Low"].iloc[0]),
                        float(row["Close"].iloc[0]),
                        float(row["Adj Close"].iloc[0]),
                        int(row["Volume"].iloc[0]),
                    ),
                )

        conn.commit()

    finally:
        conn.close()


def update_all_stocks(period: str = "5d"):
    from datetime import date

    today = date.today()

    if not is_trading_day(today):
        print(f"{today} bukan hari Bursa. Update dilewati.")
        return

    conn = get_connection()

    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT symbol
                FROM stocks
                WHERE is_active = TRUE
                ORDER BY symbol
                """
            )

            stocks = cursor.fetchall()

    finally:
        conn.close()

    for (symbol,) in stocks:
        print(f"Updating {symbol}...")

        try:
            save_prices_from_yahoo(symbol, period)
            print(f"{symbol} updated successfully.")
        except Exception as error:
            print(f"Failed to update {symbol}: {error}")