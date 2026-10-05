from datetime import date, datetime

from src.db.connection import get_connection


def create_screener_run(trade_date: date, stock_count: int) -> int:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO screener_runs (
                    trade_date,
                    started_at,
                    stock_count
                )
                VALUES (%s, %s, %s)
                RETURNING id
                """,
                (trade_date, datetime.now(), stock_count),
            )
            return cur.fetchone()[0]


def save_screener_result(run_id: int, result) -> None:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO screener_results (
                    screener_run_id,
                    symbol,
                    score,
                    signal,
                    confidence,
                    data_quality_status,
                    alignment,
                    foreign_state,
                    broker_state,
                    price_volume_state,
                    observation
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    run_id,
                    result.symbol,
                    result.score,
                    result.signal,
                    result.confidence,
                    result.data_quality_status,
                    result.alignment,
                    result.foreign_state,
                    result.broker_state,
                    result.price_volume_state,
                    result.observation,
                ),
            )


def finish_screener_run(run_id: int) -> None:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE screener_runs
                SET finished_at = NOW()
                WHERE id = %s
                """,
                (run_id,),
            )
