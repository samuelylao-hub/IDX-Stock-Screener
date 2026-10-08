import sys; sys.path.insert(0, "."); from backend.app.database import get_connection

conn = get_connection()
cur = conn.cursor()

cur.execute("""
    UPDATE stocks s
    SET avg_volume_20d = q.avg_volume
    FROM (
        SELECT
            stock_id,
            ROUND(AVG(volume))::BIGINT AS avg_volume
        FROM (
            SELECT
                stock_id,
                volume,
                ROW_NUMBER() OVER (
                    PARTITION BY stock_id
                    ORDER BY trade_date DESC
                ) AS rn
            FROM stock_prices
            WHERE volume IS NOT NULL
        ) x
        WHERE rn <= 20
        GROUP BY stock_id
    ) q
    WHERE s.id = q.stock_id
""")

cur.execute("""
    UPDATE stocks
    SET liquidity_tier = CASE
        WHEN avg_volume_20d IS NULL THEN 'UNKNOWN'
        WHEN avg_volume_20d >= 10000000 THEN 'A'
        WHEN avg_volume_20d >= 1000000 THEN 'B'
        ELSE 'C'
    END
""")

conn.commit()
cur.close()
conn.close()

print("LIQUIDITY CALCULATED")
