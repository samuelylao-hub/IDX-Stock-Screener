import sys; sys.path.insert(0, "."); from backend.app.database import get_connection

conn = get_connection()
cur = conn.cursor()

cur.execute("""
    UPDATE stocks
    SET intraday_enabled = TRUE
    WHERE symbol IN ('BBCA', 'BBRI')
""")

conn.commit()
cur.close()
conn.close()

print("BASE INTRADAY CANDIDATES: OK")
