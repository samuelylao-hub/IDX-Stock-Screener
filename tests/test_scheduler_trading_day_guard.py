from datetime import date, datetime
from unittest.mock import patch
from zoneinfo import ZoneInfo

from backend.app.scheduler import jobs


JAKARTA_TZ = ZoneInfo("Asia/Jakarta")
FIXED_NOW = datetime(2026, 10, 16, 10, 0, tzinfo=JAKARTA_TZ)
EXPECTED_DATE = date(2026, 10, 16)


def test_scheduler_skips_job_on_non_trading_day():
    with (
        patch.object(jobs, "datetime") as mocked_datetime,
        patch.object(jobs, "is_trading_day", return_value=False) as calendar_check,
        patch.object(jobs, "run_market_data_update") as run_update,
    ):
        mocked_datetime.now.return_value = FIXED_NOW
        result = jobs.run_market_data_update_if_trading_day()

    assert result == "SKIPPED"
    mocked_datetime.now.assert_called_once_with(JAKARTA_TZ)
    calendar_check.assert_called_once_with(EXPECTED_DATE)
    run_update.assert_not_called()


def test_scheduler_runs_job_on_trading_day():
    with (
        patch.object(jobs, "datetime") as mocked_datetime,
        patch.object(jobs, "is_trading_day", return_value=True) as calendar_check,
        patch.object(jobs, "run_market_data_update") as run_update,
    ):
        mocked_datetime.now.return_value = FIXED_NOW
        result = jobs.run_market_data_update_if_trading_day()

    assert result == "SUCCESS"
    mocked_datetime.now.assert_called_once_with(JAKARTA_TZ)
    calendar_check.assert_called_once_with(EXPECTED_DATE)
    run_update.assert_called_once_with()
