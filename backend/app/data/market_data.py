import time
import math

import yfinance as yf

from backend.app.database import get_connection
from backend.app.data.market_calendar import is_trading_day


def get_daily_prices(symbol: str, period: str = "5d"):
    ticker = f"{symbol}.JK"
    attempt_errors = []

    for attempt in range(3):
        time.sleep(1 if attempt == 0 else attempt * 2)
        try:
            data = yf.download(
                ticker,
                period=period,
                progress=False,
                auto_adjust=False,
                threads=False,
                timeout=30,
            )
        except Exception as exc:
            detail = f"attempt={attempt + 1}/3 exception={type(exc).__name__}: {exc}"
            attempt_errors.append(detail)
            print(f"[YAHOO_DIAGNOSTIC] {symbol}: {detail}")
            continue

        if data is not None and not data.empty:
            return data

        detail = f"attempt={attempt + 1}/3 empty_response ticker={ticker}"
        attempt_errors.append(detail)
        print(f"[YAHOO_DIAGNOSTIC] {symbol}: {detail}")

    details = " | ".join(attempt_errors)
    raise RuntimeError(
        f"Yahoo Finance gagal mengambil data untuk {symbol} "
        f"setelah 3 percobaan. Detail: {details}"
    )



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


def _validated_price_values(row, symbol: str) -> tuple:
    fields = ("Open", "High", "Low", "Close", "Adj Close", "Volume")
    values = {
        field: _get_price_value(row, field)
        for field in fields
    }

    for field in ("Open", "High", "Low", "Close", "Adj Close"):
        if values[field] <= 0:
            raise ValueError(
                f"{symbol}: nilai {field} harus lebih besar dari nol."
            )

    open_price = values["Open"]
    high_price = values["High"]
    low_price = values["Low"]
    close_price = values["Close"]
    volume = values["Volume"]

    if high_price < max(open_price, low_price, close_price):
        raise ValueError(f"{symbol}: nilai High tidak konsisten dengan OHLC.")

    if low_price > min(open_price, high_price, close_price):
        raise ValueError(f"{symbol}: nilai Low tidak konsisten dengan OHLC.")

    if volume < 0 or not volume.is_integer():
        raise ValueError(
            f"{symbol}: Volume harus bilangan bulat nonnegatif."
        )

    return (
        open_price,
        high_price,
        low_price,
        close_price,
        values["Adj Close"],
        int(volume),
    )


def save_prices_from_yahoo(symbol: str, period: str = "5d") -> int:
    data = get_daily_prices(symbol, period)

    # Validasi seluruh data sebelum membuka koneksi database.
    validated_rows = []
    for trade_date, row in data.iterrows():
        price_values = _validated_price_values(row, symbol)
        validated_rows.append((trade_date.date(), *price_values))

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

            for trade_date, *price_values in validated_rows:
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
                    (stock_id, trade_date, *price_values),
                )

    return len(validated_rows)


def _extract_ticker_frame(batch_data, ticker: str, batch_size: int):
    """Extract one ticker from yfinance's single- or multi-ticker column layout."""
    columns = batch_data.columns

    if not hasattr(columns, "nlevels") or columns.nlevels == 1:
        return batch_data if batch_size == 1 else None

    level_zero = columns.get_level_values(0)
    level_one = columns.get_level_values(1)

    if ticker in level_zero:
        frame = batch_data[ticker]
    elif ticker in level_one:
        frame = batch_data.xs(ticker, axis=1, level=1)
    else:
        return None

    # yfinance may return duplicate/extra levels; normalize to plain price columns.
    if hasattr(frame.columns, "nlevels") and frame.columns.nlevels > 1:
        frame.columns = frame.columns.get_level_values(-1)
    return frame


def _save_price_frame(symbol: str, data) -> int:
    """Validate and save already-downloaded data; does not make another HTTP call."""
    if data is None or data.empty:
        return 0

    validated_rows = []
    for trade_date, row in data.iterrows():
        try:
            values = _validated_price_values(row, symbol)
        except (KeyError, TypeError, ValueError, IndexError) as exc:
            # Ignore incomplete rows, but fail if no usable rows remain.
            print(f"[YAHOO_DIAGNOSTIC] {symbol}: invalid_row date={trade_date}: {exc}")
            continue
        validated_rows.append((trade_date.date(), *values))

    if not validated_rows:
        return 0

    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT id FROM stocks WHERE symbol = %s", (symbol,))
            stock = cursor.fetchone()
            if stock is None:
                raise ValueError(f"Stock {symbol} belum terdaftar di database.")

            stock_id = stock[0]
            for trade_date, *values in validated_rows:
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
                    (stock_id, trade_date, *values),
                )

    return len(validated_rows)


def update_all_stocks(period: str = "5d", symbols=None, batch_size: int = 10):
    """Fetch prices in small batches to reduce Yahoo request pressure.

    Each batch gets at most two attempts. If a whole batch returns no data or
    raises, stop further requests instead of hammering Yahoo; remaining symbols
    are reported as failed and existing database prices are left untouched.
    """
    from datetime import datetime
    from zoneinfo import ZoneInfo

    today = datetime.now(ZoneInfo("Asia/Jakarta")).date()
    if not is_trading_day(today):
        print(f"{today} bukan hari Bursa. Update dilewati.")
        return {
            "requested": 0, "success": 0, "failed": 0,
            "rows_saved": 0, "skipped": True, "failures": [],
        }

    with get_connection() as conn:
        with conn.cursor() as cursor:
            if symbols is None:
                cursor.execute("""
                    SELECT symbol FROM stocks
                    WHERE is_active = TRUE
                    ORDER BY symbol
                """)
            else:
                cursor.execute("""
                    SELECT symbol FROM stocks
                    WHERE is_active = TRUE AND symbol = ANY(%s)
                    ORDER BY symbol
                """, (list(symbols),))
            stocks = [row[0] for row in cursor.fetchall()]

    if batch_size < 1:
        raise ValueError("batch_size harus minimal 1")

    success = failed = rows_saved = 0
    failures = []
    total = len(stocks)

    for start_index in range(0, total, batch_size):
        batch = stocks[start_index:start_index + batch_size]
        tickers = [f"{symbol}.JK" for symbol in batch]
        batch_data = None
        batch_error = None

        for attempt in range(2):
            if attempt:
                print(f"[YAHOO_DIAGNOSTIC] batch={start_index + 1}-{start_index + len(batch)} retry=2/2")
                time.sleep(5)
            else:
                time.sleep(1)

            try:
                batch_data = yf.download(
                    tickers,
                    period=period,
                    progress=False,
                    auto_adjust=False,
                    threads=False,
                    group_by="ticker",
                    timeout=30,
                )
                if batch_data is not None and not batch_data.empty:
                    batch_error = None
                    break
                batch_error = "empty_response"
            except Exception as exc:
                batch_error = f"{type(exc).__name__}: {exc}"

            print(
                f"[YAHOO_DIAGNOSTIC] batch={start_index + 1}-{start_index + len(batch)} "
                f"attempt={attempt + 1}/2 error={batch_error}"
            )

        if batch_data is None or batch_data.empty:
            # Do not continue issuing requests if Yahoo fails for an entire batch.
            remaining = stocks[start_index:]
            for symbol in remaining:
                failures.append({"symbol": symbol, "error": f"batch_fetch_failed: {batch_error}"})
            failed += len(remaining)
            print(
                f"[YAHOO_DIAGNOSTIC] STOP: batch gagal; tidak mengirim batch berikutnya. "
                f"remaining={len(remaining)} reason={batch_error}"
            )
            break

        for symbol in batch:
            ticker = f"{symbol}.JK"
            frame = _extract_ticker_frame(batch_data, ticker, len(batch))
            if frame is None or frame.empty:
                failed += 1
                failures.append({"symbol": symbol, "error": "ticker_missing_from_batch_response"})
                print(f"{symbol}: GAGAL - ticker tidak ada dalam respons batch.")
                continue
            try:
                saved = _save_price_frame(symbol, frame)
                if saved <= 0:
                    raise ValueError("Tidak ada baris harga valid yang tersimpan.")
                success += 1
                rows_saved += saved
                print(f"{symbol}: berhasil, {saved} baris harga tersimpan.")
            except Exception as exc:
                failed += 1
                failures.append({"symbol": symbol, "error": str(exc)})
                print(f"{symbol}: GAGAL - {exc}")

        if start_index + batch_size < total:
            time.sleep(2)

    summary = {
        "requested": total,
        "success": success,
        "failed": failed,
        "rows_saved": rows_saved,
        "skipped": False,
        "failures": failures,
    }
    print(
        f"Update harga selesai: {success}/{total} saham berhasil, "
        f"{failed} gagal; {rows_saved} baris harga tersimpan."
    )
    return summary
