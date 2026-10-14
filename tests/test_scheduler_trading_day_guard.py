from datetime import date
from unittest.mock import patch

from backend.app.scheduler import jobs


def test_scheduler_skips_job_on_non_trading_day():
    with (
        patch.object(jobs, "is_trading_day", return_value=False) as calendar_check,
        patch.object(jobs, "run_market_data_update") as run_update,
    ):
        jobs.run_market_data_update_if_trading_day()

    calendar_check.assert_called_once_with(date.today())
    run_update.assert_not_called()


def test_scheduler_runs_job_on_trading_day():
    with (
        patch.object(jobs, "is_trading_day", return_value=True) as calendar_check,
        patch.object(jobs, "run_market_data_update") as run_update,
    ):
        jobs.run_market_data_update_if_trading_day()

    calendar_check.assert_called_once_with(date.today())
    run_update.assert_called_once_with()
