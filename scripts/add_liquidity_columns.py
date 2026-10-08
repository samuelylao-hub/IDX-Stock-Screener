import sys; sys.path.insert(0, "."); from backend.app.database import get_connection

conn = get_connection()
cur = conn.cursor()

cur.execute("""
    ALTER TABLE stocks
    ADD COLUMN IF NOT EXISTS liquidity_tier VARCHAR(20) NOT NULL DEFAULT 'UNKNOWN'
""")

cur.execute("""
    ALTER TABLE stocks
    ADD COLUMN IF NOT EXISTS avg_volume_20d BIGINT
""")

conn.commit()
cur.close()
conn.close()

print("LIQUIDITY SCHEMA OK")
