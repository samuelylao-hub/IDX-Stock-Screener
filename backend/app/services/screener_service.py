from datetime import date

from backend.app.analysis.screener import build_screener_result
from backend.app.services.signal_fusion_service import SignalFusionService
from backend.app.database import get_connection
from src.db.screener import (
    create_screener_run,
    finish_screener_run,
    save_screener_result,
)


class ScreenerService:
    def __init__(self, signal_service=None):
        self.signal_service = signal_service or SignalFusionService()

    def screen_market(
        self,
        trade_date: date,
        price_lookback=5,
        investor_type="all",
        market_segment="RG",
        persist=False,
    ):
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT symbol FROM stocks ORDER BY symbol")
                symbols = [r[0] for r in cur.fetchall()]

        results = []

        for symbol in symbols:
            try:
                signal = self.signal_service.analyze_symbol(
                    symbol,
                    trade_date,
                    price_lookback,
                    investor_type,
                    market_segment,
                )
                results.append(build_screener_result(signal))
            except ValueError:
                pass

        results = sorted(results, key=lambda x: x.score, reverse=True)

        if persist:
            run_id = create_screener_run(trade_date, len(results))

            for result in results:
                save_screener_result(run_id, result)

            finish_screener_run(run_id)

        return results
