from unittest.mock import patch

import pytest

from backend.app.scheduler import daily_runner


def test_daily_runner_uses_trading_day_guard():
    with (
        patch.object(
            daily_runner,
            "run_market_data_update_if_trading_day",
        ) as guarded_job,
        patch.object(daily_runner, "_write_runner_log") as write_log,
    ):
        daily_runner.main()

    guarded_job.assert_called_once_with()
    assert [call.args[0] for call in write_log.call_args_list] == [
        "START",
        "RETURNED: guard selesai; status screening perlu diverifikasi terpisah",
    ]


def test_daily_runner_logs_uncaught_exception_and_reraises():
    with (
        patch.object(
            daily_runner,
            "run_market_data_update_if_trading_day",
            side_effect=RuntimeError("test error"),
        ),
        patch.object(daily_runner, "_write_runner_log") as write_log,
        pytest.raises(RuntimeError, match="test error"),
    ):
        daily_runner.main()

    assert write_log.call_args_list[0].args[0] == "START"
    assert write_log.call_args_list[1].args[0] == (
        "FAILED: RuntimeError: test error"
    )
