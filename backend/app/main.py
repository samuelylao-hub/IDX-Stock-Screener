from fastapi import FastAPI

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