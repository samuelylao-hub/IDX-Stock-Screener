import math

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

    if data is None or data.empty:
        raise ValueError(
            f"Yahoo Finance tidak mengembalikan data untuk {symbol}."
        )

    return data


def _get_price_value(row, field: str) -> float:
    value = row[field]

    if hasattr(value, "iloc"):
        value = value.iloc[0]

    result = float(value)
    if not math.isfinite(result):
        raise ValueError(f"Nilai {field} tidak valid: {result}")

    return result


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
                    stock_id, trade_date, open, high, low,
                    close, adjusted_close, volume
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
                    stock_id, trade_date, open_price, high_price,
                    low_price, close_price, adjusted_close, volume,
                ),
            )


def save_prices_from_yahoo(symbol: str, period: str = "5d") -> int:
    data = get_daily_prices(symbol, period)

    with get_connection() as conn:
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
            saved = 0

            for trade_date, row in data.iterrows():
                values = (
                    stock_id,
                    trade_date.date(),
                    _get_price_value(row, "Open"),
                    _get_price_value(row, "High"),
                    _get_price_value(row, "Low"),
                    _get_price_value(row, "Close"),
                    _get_price_value(row, "Adj Close"),
                    int(_get_price_value(row, "Volume")),
                )

                cursor.execute(
                    """
                    INSERT INTO stock_prices (
                        stock_id, trade_date, open, high, low,
                        close, adjusted_close, volume
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
                    values,
                )
                saved += 1

    return saved


def update_all_stocks(period: str = "5d", symbols=None):
    from datetime import date

    today = date.today()
    if not is_trading_day(today):
        print(f"{today} bukan hari Bursa. Update dilewati.")
        return {
            "requested": 0,
            "success": 0,
            "failed": 0,
            "rows_saved": 0,
            "skipped": True,
            "failures": [],
        }

    with get_connection() as conn:
        with conn.cursor() as cursor:
            if symbols is None:
                cursor.execute("""
                    SELECT symbol
                    FROM stocks
                    WHERE is_active = TRUE
                    ORDER BY symbol
                """)
            else:
                cursor.execute("""
                    SELECT symbol
                    FROM stocks
                    WHERE is_active = TRUE
                      AND symbol = ANY(%s)
                    ORDER BY symbol
                """, (list(symbols),))
            stocks = cursor.fetchall()

    success = 0
    failed = 0
    rows_saved = 0
    failures = []

    for (symbol,) in stocks:
        try:
            saved = save_prices_from_yahoo(symbol, period)
            if saved <= 0:
                failed += 1
                failures.append({
                    "symbol": symbol,
                    "error": "Tidak ada baris harga yang tersimpan",
                })
                print(f"{symbol}: GAGAL ? tidak ada baris harga tersimpan.")
                continue

            success += 1
            rows_saved += saved
            print(f"{symbol}: berhasil, {saved} baris harga tersimpan.")
        except Exception as error:
            failed += 1
            failures.append({"symbol": symbol, "error": str(error)})
            print(f"{symbol}: GAGAL ? {error}")

    summary = {
        "requested": len(stocks),
        "success": success,
        "failed": failed,
        "rows_saved": rows_saved,
        "skipped": False,
        "failures": failures,
    }

    print(
        f"Update harga selesai: {success}/{len(stocks)} saham berhasil, "
        f"{failed} gagal; {rows_saved} baris harga tersimpan."
    )
    return summary
