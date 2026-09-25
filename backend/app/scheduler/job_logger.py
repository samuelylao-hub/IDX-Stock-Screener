from datetime import datetime, timezone

from backend.app.database import get_connection


def get_or_create_job(
    job_name: str,
    description: str | None = None,
):
    conn = get_connection()

    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO scheduled_jobs (
                    job_name,
                    description
                )
                VALUES (%s, %s)
                ON CONFLICT (job_name)
                DO UPDATE SET
                    description = EXCLUDED.description,
                    updated_at = NOW()
                RETURNING id
                """,
                (job_name, description),
            )

            job_id = cursor.fetchone()[0]

        conn.commit()

        return job_id

    finally:
        conn.close()


def start_job_run(job_id: int):
    conn = get_connection()

    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO job_runs (
                    job_id,
                    started_at,
                    status
                )
                VALUES (%s, %s, %s)
                RETURNING id
                """,
                (
                    job_id,
                    datetime.now(timezone.utc),
                    "running",
                ),
            )

            run_id = cursor.fetchone()[0]

        conn.commit()

        return run_id

    finally:
        conn.close()


def finish_job_run(
    run_id: int,
    status: str,
    message: str | None = None,
):
    conn = get_connection()

    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                UPDATE job_runs
                SET
                    finished_at = %s,
                    status = %s,
                    message = %s
                WHERE id = %s
                """,
                (
                    datetime.now(timezone.utc),
                    status,
                    message,
                    run_id,
                ),
            )

        conn.commit()

    finally:
        conn.close()