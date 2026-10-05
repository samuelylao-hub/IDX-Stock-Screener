from datetime import date

from backend.app.data.market_calendar import is_trading_day
from backend.app.data.market_data import update_all_stocks
from backend.app.scheduler.job_logger import (
    finish_job_run,
    get_or_create_job,
    start_job_run,
)
from backend.app.services.notification_service import NotificationService
from backend.app.services.screener_report import format_screener_report
from backend.app.services.screener_service import ScreenerService


def run_market_data_update():
    print("Starting market data update...")

    job_id = get_or_create_job(
        "market_data_update",
        "Update market data harian",
    )

    run_id = start_job_run(job_id)

    try:
        update_all_stocks("5d")

        results = ScreenerService().screen_market(
            date.today(),
            persist=True,
        )

        report = format_screener_report(results, date.today())
        print(report)

        NotificationService().send_report(report)

        finish_job_run(
            run_id,
            "success",
            f"Market update + screener berhasil. {len(results)} saham.",
        )

        print("Market data update and screener finished.")

    except Exception as error:
        finish_job_run(
            run_id,
            "failed",
            str(error),
        )

        print(f"Market data update failed: {error}")

        raise


def run_market_data_update_if_trading_day():
    if not is_trading_day(date.today()):
        print("Non-trading day. Market update skipped.")
        return

    run_market_data_update()
