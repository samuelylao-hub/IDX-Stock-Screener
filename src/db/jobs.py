from src.db.connection import get_connection

def get_scheduled_jobs():
    with get_connection() as conn:
        return conn.execute(
            """SELECT id, job_name
               FROM scheduled_jobs
               ORDER BY job_name"""
        ).fetchall()
