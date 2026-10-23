from unittest.mock import patch

import pytest

from backend.app.scheduler import daily_runner


def test_daily_runner_runs_news_and_market_jobs():
    with (
        patch.object(daily_runner, "run_news_ingestion", return_value=3) as news_job,
        patch.object(daily_runner, "run_market_data_update_if_trading_day") as market_job,
        patch.object(daily_runner, "_write_runner_log") as write_log,
    ):
        daily_runner.main()

    news_job.assert_called_once_with()
    market_job.assert_called_once_with()
    messages = [call.args[0] for call in write_log.call_args_list]
    assert "NEWS_RETURNED: events_saved=3" in messages
    assert "MARKET_DATA_RETURNED" in messages
    assert messages[-1] == "SUCCESS: news ingestion and market screening returned"


def test_daily_runner_runs_market_even_if_news_fails():
    with (
        patch.object(
            daily_runner,
            "run_news_ingestion",
            side_effect=ValueError("news error"),
        ),
        patch.object(daily_runner, "run_market_data_update_if_trading_day") as market_job,
        patch.object(daily_runner, "_write_runner_log"),
        pytest.raises(RuntimeError, match="news ingestion: ValueError: news error"),
    ):
        daily_runner.main()

    market_job.assert_called_once_with()


def test_daily_runner_runs_news_even_if_market_fails():
    with (
        patch.object(daily_runner, "run_news_ingestion", return_value=0) as news_job,
        patch.object(
            daily_runner,
            "run_market_data_update_if_trading_day",
            side_effect=ValueError("market error"),
        ),
        patch.object(daily_runner, "_write_runner_log"),
        pytest.raises(RuntimeError, match="market screening: ValueError: market error"),
    ):
        daily_runner.main()

    news_job.assert_called_once_with()
