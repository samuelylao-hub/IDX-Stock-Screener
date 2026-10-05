from datetime import date

from backend.app.services.signal_fusion_service import SignalFusionService

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

@app.get("/api/v1/signals/{symbol}")
def signal_fusion(
    symbol: str,
    trade_date: date,
    price_lookback: int = 5,
    investor_type: str = "all",
    market_segment: str = "RG",
):
    service = SignalFusionService()

    result = service.analyze_symbol(
        symbol=symbol,
        trade_date=trade_date,
        price_lookback=price_lookback,
        investor_type=investor_type,
        market_segment=market_segment,
    )

    return {
        "symbol": result.symbol,
        "trade_date": result.trade_date,
        "foreign_state": result.foreign_state,
        "broker_state": result.broker_state,
        "price_volume_state": result.price_volume_state,
        "alignment": result.alignment,
        "data_completeness": result.data_completeness,
        "data_quality_status": result.data_quality_status,
        "foreign_coverage": result.foreign_coverage,
        "broker_coverage": result.broker_coverage,
        "evidence": result.evidence,
    }
from datetime import date
from backend.app.services.screener_service import ScreenerService


@app.get("/api/v1/screener")
def screener(
    trade_date: date,
    price_lookback: int = 5,
    investor_type: str = "all",
    market_segment: str = "RG",
):
    results = ScreenerService().screen_market(
        trade_date, price_lookback,
        investor_type, market_segment
    )

    return {
        "trade_date": trade_date,
        "count": len(results),
        "results": [r.__dict__ for r in results],
    }
