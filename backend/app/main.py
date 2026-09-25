from fastapi import FastAPI

from backend.app.database import get_connection

app = FastAPI(
    title="IDX Stock Screener API",
    description="Backend untuk automated Indonesian stock market screener",
    version="0.1.0",
)


@app.get("/")
def root():
    return {
        "message": "IDX Stock Screener API is running",
        "status": "ok",
    }


@app.get("/health")
def health():
    return {
        "status": "healthy",
    }

@app.get("/db-test")
def db_test():
    conn = get_connection()

    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT 1")
            result = cursor.fetchone()

        return {
            "status": "ok",
            "database": "connected",
            "test": result[0],
        }

    finally:
        conn.close()
