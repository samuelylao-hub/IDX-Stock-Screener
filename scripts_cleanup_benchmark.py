from backend.app.database import get_connection

conn = get_connection()

try:
    with conn.cursor() as cur:
        cur.execute(
            "DELETE FROM stocks WHERE symbol = %s",
            ("^JKSE",),
        )
    conn.commit()
    print("Temporary IHSG stock row removed.")
finally:
    conn.close()
