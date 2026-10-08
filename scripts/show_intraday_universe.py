import sys; sys.path.insert(0, "."); from backend.app.database import get_connection

conn = get_connection()
cur = conn.cursor()

cur.execute("""
    SELECT
        symbol,
        thematic_group,
        avg_volume_20d,
        liquidity_tier,
        intraday_enabled
    FROM stocks
    WHERE intraday_enabled = TRUE
    ORDER BY liquidity_tier, symbol
""")

for row in cur.fetchall():
    print(row)

cur.close()
conn.close()
