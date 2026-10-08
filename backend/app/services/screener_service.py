from datetime import date

from backend.app.analysis.market_regime import determine_market_regime
from backend.app.analysis.momentum import (
    calculate_momentum,
    classify_momentum,
)
from backend.app.analysis.ranking import rank_screener_results
from backend.app.analysis.relative_strength import (
    calculate_relative_strength,
    classify_relative_strength,
)
from backend.app.analysis.screener import build_screener_result
from backend.app.providers.benchmark import BenchmarkProvider
from backend.app.services.signal_fusion_service import SignalFusionService
from backend.app.database import get_connection
from src.db.screener import (
    create_screener_run,
    finish_screener_run,
    save_screener_result,
)


class ScreenerService:
    def __init__(
        self,
        signal_service=None,
        benchmark_provider=None,
    ):
        self.signal_service = signal_service or SignalFusionService()
        self.benchmark_provider = (
            benchmark_provider or BenchmarkProvider()
        )

    def screen_market(
        self,
        trade_date: date,
        price_lookback=5,
        investor_type="all",
        market_segment="RG",
        symbols=None,
        persist=False,
    ):
        # Flow data wajib tersedia pada trade_date.
        # Jangan pernah mencampur harga terbaru dengan flow stale.
        with get_connection() as conn:
            with conn.cursor() as cur:
                if symbols is None:
                    cur.execute(
                        """
                        SELECT COUNT(*)
                        FROM stocks
                        WHERE is_active = TRUE
                        """
                    )
                else:
                    cur.execute(
                        """
                        SELECT COUNT(*)
                        FROM stocks
                        WHERE is_active = TRUE
                          AND symbol = ANY(%s)
                        """,
                        (list(symbols),),
                    )
                active_count = cur.fetchone()[0]

                if symbols is None:
                    cur.execute(
                        """
                        SELECT COUNT(DISTINCT st.id)
                        FROM stocks st
                        JOIN foreign_daily_flow ff
                            ON ff.stock_id = st.id
                           AND ff.trade_date = %s
                        WHERE st.is_active = TRUE
                        """,
                        (trade_date,),
                    )
                else:
                    cur.execute(
                        """
                        SELECT COUNT(DISTINCT st.id)
                        FROM stocks st
                        JOIN foreign_daily_flow ff
                            ON ff.stock_id = st.id
                           AND ff.trade_date = %s
                        WHERE st.is_active = TRUE
                          AND st.symbol = ANY(%s)
                        """,
                        (trade_date, list(symbols)),
                    )
                foreign_count = cur.fetchone()[0]

                if symbols is None:
                    cur.execute(
                        """
                        SELECT COUNT(DISTINCT st.id)
                        FROM stocks st
                        JOIN broker_stock_flow bf
                            ON bf.stock_id = st.id
                           AND bf.trade_date = %s
                        WHERE st.is_active = TRUE
                        """,
                        (trade_date,),
                    )
                else:
                    cur.execute(
                        """
                        SELECT COUNT(DISTINCT st.id)
                        FROM stocks st
                        JOIN broker_stock_flow bf
                            ON bf.stock_id = st.id
                           AND bf.trade_date = %s
                        WHERE st.is_active = TRUE
                          AND st.symbol = ANY(%s)
                        """,
                        (trade_date, list(symbols)),
                    )
                broker_count = cur.fetchone()[0]

        # Foreign/broker coverage boleh partial.
        # Saham tanpa flow pada trade_date tetap masuk screening.
        if foreign_count < active_count or broker_count < active_count:
            print(
                f"FLOW COVERAGE LIMITED: foreign={foreign_count}/{active_count}, broker={broker_count}/{active_count}, date={trade_date}"
            )
        benchmark = self.benchmark_provider.get_history(30)

        market_closes = [
            float(row["close"])
            for row in benchmark
            if row.get("close") is not None
        ]

        market_regime = determine_market_regime(
            market_closes
        )

        market_return_5d = 0.0

        if len(market_closes) >= 5:
            base = market_closes[-5]

            if base != 0:
                market_return_5d = (
                    (market_closes[-1] - base)
                    / base
                ) * 100

        with get_connection() as conn:
            with conn.cursor() as cur:
                if symbols is None:
                    cur.execute(
                        """
                        SELECT st.symbol
                        FROM stocks st
                        WHERE st.is_active = TRUE
                        ORDER BY st.symbol
                        """,
                    )
                    symbols = [
                        row[0]
                        for row in cur.fetchall()
                    ]
                else:
                    symbols = list(symbols)

                results = []

                for symbol in symbols:
                    try:
                        cur.execute(
                            """
                            SELECT market_status, risk_flags, status_reason
                            FROM stocks
                            WHERE symbol = %s
                            """,
                            (symbol,),
                        )

                        status_row = cur.fetchone()

                        market_status = (
                            status_row[0] if status_row else "UNKNOWN"
                        )

                        if market_status == "SUSPENDED":
                            risk_flags = tuple(
                                status_row[1] or []
                            )
                            status_reason = (
                                status_row[2] or ""
                            )

                            print(
                                f"{symbol} SKIP SUSPENDED"
                            )

                            from backend.app.analysis.screener import ScreenerResult

                            results.append(
                                ScreenerResult(
                                    symbol=symbol,
                                    trade_date=trade_date,
                                    score=0.0,
                                    signal="SKIP",
                                    confidence=0.0,
                                    data_quality_status="LIMITED",
                                    alignment="UNKNOWN",
                                    foreign_state="UNKNOWN",
                                    broker_state="UNKNOWN",
                                    price_volume_state="UNKNOWN",
                                    observation="Market status: SUSPENDED",
                                    market_regime=market_regime.state,
                                    market_status=market_status,
                                    risk_flags=risk_flags,
                                    status_reason=status_reason,
                                )
                            )
                            continue

                        signal = self.signal_service.analyze_symbol(
                            symbol=symbol,
                            trade_date=trade_date,
                            price_lookback=price_lookback,
                            investor_type=investor_type,
                            market_segment=market_segment,
                        )

                        cur.execute(
                            """
                            SELECT sp.close
                            FROM stock_prices sp
                            JOIN stocks st
                                ON st.id = sp.stock_id
                            WHERE st.symbol = %s
                              AND sp.trade_date <= %s
                            ORDER BY sp.trade_date DESC
                            LIMIT 20
                            """,
                            (symbol, trade_date),
                        )

                        stock_rows = cur.fetchall()

                        stock_closes = [
                            float(row[0])
                            for row in reversed(stock_rows)
                            if row[0] is not None
                        ]

                        momentum = calculate_momentum(
                            stock_closes
                        )

                        stock_return_5d = 0.0

                        if len(stock_closes) >= 5:
                            base = stock_closes[-5]

                            if base != 0:
                                stock_return_5d = (
                                    (stock_closes[-1] - base)
                                    / base
                                ) * 100

                        relative_strength = (
                            calculate_relative_strength(
                                stock_return_5d,
                                market_return_5d,
                            )
                        )

                        result = build_screener_result(
                            signal,
                            market_regime=market_regime.state,
                            momentum=momentum,
                            momentum_state=classify_momentum(
                                momentum
                            ),
                            relative_strength=relative_strength,
                            relative_strength_state=(
                                classify_relative_strength(
                                    relative_strength
                                )
                            ),
                        )

                        results.append(result)

                    except ValueError:
                        pass

        results = rank_screener_results(results)

        if persist:
            run_id = create_screener_run(
                trade_date,
                len(results),
            )

            for result in results:
                save_screener_result(
                    run_id,
                    result,
                )

            finish_screener_run(run_id)

        return results



