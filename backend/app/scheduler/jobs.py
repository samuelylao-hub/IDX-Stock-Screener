from backend.app.data.market_data import update_all_stocks
from backend.app.scheduler.job_logger import (
    finish_job_run,
    get_or_create_job,
    start_job_run,
)


def run_market_data_update():
    print("Starting market data update...")

    job_id = get_or_create_job(
        "market_data_update",
        "Update market data harian",
    )

    run_id = start_job_run(job_id)

    try:
        update_all_stocks("5d")

        finish_job_run(
            run_id,
            "success",
            "Market data update berhasil.",
        )

        print("Market data update finished.")

    except Exception as error:
        finish_job_run(
            run_id,
            "failed",
            str(error),
        )

        print(f"Market data update failed: {error}")

        raise