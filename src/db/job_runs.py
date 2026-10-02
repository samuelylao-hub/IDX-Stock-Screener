from src.db.connection import get_connection

def get_job_runs(job_id):
    with get_connection() as conn:
        return conn.execute(
            """SELECT id, job_id, started_at, finished_at, status
               FROM job_runs
               WHERE job_id = %s
               ORDER BY started_at DESC""",
            (job_id,),
        ).fetchall()
