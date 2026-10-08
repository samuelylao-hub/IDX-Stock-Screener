from backend.app.database import get_connection
from backend.app.providers.idx_universe import IDXUniverseProvider


def sync():
    provider = IDXUniverseProvider()
    rows = provider.fetch()

    conn = get_connection()

    try:
        with conn.cursor() as cur:
            for row in rows:
                cur.execute(
                    """
                    INSERT INTO stocks (
                        symbol,
                        company_name,
                        sector,
                        subsector,
                        is_active
                    )
                    VALUES (%s, %s, %s, %s, TRUE)
                    ON CONFLICT (symbol)
                    DO UPDATE SET
                        company_name = EXCLUDED.company_name,
                        sector = EXCLUDED.sector,
                        subsector = EXCLUDED.subsector,
                        is_active = TRUE,
                        updated_at = NOW()
                    """,
                    (
                        row["symbol"],
                        row["company_name"],
                        row["sector"],
                        row["subsector"],
                    ),
                )

        conn.commit()

    finally:
        conn.close()

    return len(rows)


if __name__ == "__main__":
    count = sync()
    print(f"IDX UNIVERSE SYNCED: {count}")
