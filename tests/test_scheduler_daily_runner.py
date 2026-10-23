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
    messages = [call.args[0] for call in write_log.call_args_list]
    assert "START" in messages
    assert "RETURNED: market screening guard selesai" in messages
    assert messages[-1] == "SUCCESS"


def test_daily_runner_logs_and_reraises_failure():
    with (
        patch.object(
            daily_runner,
            "run_market_data_update_if_trading_day",
            side_effect=ValueError("test failure"),
        ),
        patch.object(daily_runner, "_write_runner_log") as write_log,
        pytest.raises(ValueError, match="test failure"),
    ):
        daily_runner.main()

    messages = [call.args[0] for call in write_log.call_args_list]
    assert any(message.startswith("FAILED: ValueError") for message in messages)