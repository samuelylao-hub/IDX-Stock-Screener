from datetime import date


DAILY_LIMIT = 5
ENDPOINT_LIMITS = {
    "foreign_flow": 3,
    "broker_summary": 2,
}


def reserve_daily_index_alpha_symbols(
    connection_factory,
    stocks,
    trade_date: date,
    endpoint: str,
    limit: int,
    daily_limit: int = DAILY_LIMIT,
):
    """Reserve quota units persistently before calling Index Alpha."""
    if endpoint not in ENDPOINT_LIMITS:
        raise ValueError(f"Endpoint kuota tidak dikenal: {endpoint}")
    if not stocks or limit <= 0:
        return []

    with connection_factory() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS index_alpha_daily_usage (
                    trade_date DATE NOT NULL,
                    endpoint TEXT NOT NULL,
                    symbol TEXT NOT NULL,
                    reserved_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    PRIMARY KEY (trade_date, endpoint, symbol)
                )
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS index_alpha_daily_batches (
                    trade_date DATE NOT NULL,
                    endpoint TEXT NOT NULL,
                    reserved_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    PRIMARY KEY (trade_date, endpoint)
                )
            """)
            cur.execute("SELECT pg_advisory_xact_lock(728194, 501)")
            cur.execute("""
                SELECT 1 FROM index_alpha_daily_batches
                WHERE trade_date = %s AND endpoint = %s
            """, (trade_date, endpoint))
            if cur.fetchone():
                return []

            cur.execute("""
                SELECT COUNT(*) FROM index_alpha_daily_usage
                WHERE trade_date = %s
            """, (trade_date,))
            used = cur.fetchone()[0]
            remaining = max(0, daily_limit - used)

            count = min(limit, ENDPOINT_LIMITS[endpoint], remaining)
            if count == 0:
                return []

            cur.execute("""
                INSERT INTO index_alpha_daily_batches (trade_date, endpoint)
                VALUES (%s, %s)
                ON CONFLICT DO NOTHING
            """, (trade_date, endpoint))

            # Rotate symbols by date so the same first tickers are not
            # permanently favored. A reservation counts per ticker/endpoint.
            offset = trade_date.toordinal() % len(stocks)
            rotated = stocks[offset:] + stocks[:offset]
            selected = rotated[:count]

            for _, symbol in selected:
                cur.execute("""
                    INSERT INTO index_alpha_daily_usage
                        (trade_date, endpoint, symbol)
                    VALUES (%s, %s, %s)
                    ON CONFLICT DO NOTHING
                """, (trade_date, endpoint, symbol))

            return selected
