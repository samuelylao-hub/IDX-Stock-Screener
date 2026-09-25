from backend.app.database import get_connection


def save_stock(
    symbol: str,
    company_name: str,
    sector: str | None = None,
    subsector: str | None = None,
):
    conn = get_connection()

    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO stocks (
                    symbol,
                    company_name,
                    sector,
                    subsector
                )
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (symbol)
                DO UPDATE SET
                    company_name = EXCLUDED.company_name,
                    sector = EXCLUDED.sector,
                    subsector = EXCLUDED.subsector,
                    updated_at = NOW()
                """,
                (symbol, company_name, sector, subsector),
            )

        conn.commit()

    finally:
        conn.close()