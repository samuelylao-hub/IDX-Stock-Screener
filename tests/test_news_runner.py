from unittest.mock import MagicMock, patch

import pytest

from backend.app.scheduler import news_runner


@patch("backend.app.scheduler.news_runner.write_log")
@patch("backend.app.scheduler.news_runner.finish_job_run")
@patch("backend.app.scheduler.news_runner.start_job_run", return_value=23)
@patch("backend.app.scheduler.news_runner.get_or_create_job", return_value=7)
@patch("backend.app.scheduler.news_runner.get_connection")
@patch("backend.app.scheduler.news_runner.NewsIngestionService")
@patch("backend.app.scheduler.news_runner.IndexAlphaNewsProvider")
def test_news_runner_success(
    provider_class,
    service_class,
    get_connection_mock,
    get_or_create_job_mock,
    start_job_run_mock,
    finish_job_run_mock,
    write_log_mock,
):
    provider = provider_class.return_value
    provider.is_available.return_value = True

    connection = MagicMock()
    get_connection_mock.return_value = connection

    service = service_class.return_value
    service.ingest.return_value = 4

    result = news_runner.main()

    assert result == 4
    service_class.assert_called_once_with(
        provider=provider,
        connection=connection,
    )
    service.ingest.assert_called_once_with(
        limit=100,
        items=provider.get_news.return_value,
    )
    connection.close.assert_called_once_with()
    finish_job_run_mock.assert_called_once_with(
        23,
        status="success",
        message="News ingestion selesai. Event relevan tersimpan: 4",
    )


@patch("backend.app.scheduler.news_runner.write_log")
@patch("backend.app.scheduler.news_runner.IndexAlphaNewsProvider")
def test_news_runner_stops_when_api_key_missing(
    provider_class,
    write_log_mock,
):
    provider_class.return_value.is_available.return_value = False

    with patch(
        "backend.app.scheduler.news_runner.get_connection"
    ) as get_connection_mock:
        with pytest.raises(
            RuntimeError,
            match="INDEX_ALPHA_API_KEY belum tersedia",
        ):
            news_runner.main()

    get_connection_mock.assert_not_called()


@patch("backend.app.scheduler.news_runner.write_log")
@patch("backend.app.scheduler.news_runner.finish_job_run")
@patch("backend.app.scheduler.news_runner.start_job_run", return_value=23)
@patch("backend.app.scheduler.news_runner.get_or_create_job", return_value=7)
@patch("backend.app.scheduler.news_runner.get_connection")
@patch("backend.app.scheduler.news_runner.NewsIngestionService")
@patch("backend.app.scheduler.news_runner.IndexAlphaNewsProvider")
def test_news_runner_records_failure(
    provider_class,
    service_class,
    get_connection_mock,
    get_or_create_job_mock,
    start_job_run_mock,
    finish_job_run_mock,
    write_log_mock,
):
    provider_class.return_value.is_available.return_value = True

    connection = MagicMock()
    get_connection_mock.return_value = connection

    service_class.return_value.ingest.side_effect = ValueError(
        "simulated ingestion failure"
    )

    with pytest.raises(
        ValueError,
        match="simulated ingestion failure",
    ):
        news_runner.main()

    connection.close.assert_called_once_with()
    finish_job_run_mock.assert_called_once_with(
        23,
        status="failed",
        message="ValueError: simulated ingestion failure",
    )


@patch("backend.app.scheduler.news_runner.write_log")
@patch("backend.app.scheduler.news_runner.is_trading_day", return_value=False)
@patch("backend.app.scheduler.news_runner.IndexAlphaNewsProvider")
def test_news_runner_skips_non_trading_day(
    provider_class,
    trading_day_mock,
    write_log_mock,
):
    result = news_runner.main()

    assert result == 0
    trading_day_mock.assert_called_once()
    provider_class.assert_not_called()


@patch("backend.app.scheduler.news_runner.write_log")
@patch("backend.app.scheduler.news_runner.is_trading_day", return_value=True)
@patch("backend.app.scheduler.news_runner.finish_job_run")
@patch("backend.app.scheduler.news_runner.start_job_run", return_value=23)
@patch("backend.app.scheduler.news_runner.get_or_create_job", return_value=7)
@patch("backend.app.scheduler.news_runner.get_connection")
@patch("backend.app.scheduler.news_runner.NewsIngestionService")
@patch("backend.app.scheduler.news_runner.IndexAlphaNewsProvider")
def test_news_runner_continues_on_trading_day(
    provider_class,
    service_class,
    get_connection_mock,
    get_or_create_job_mock,
    start_job_run_mock,
    finish_job_run_mock,
    trading_day_mock,
    write_log_mock,
):
    provider_class.return_value.is_available.return_value = True
    connection = MagicMock()
    get_connection_mock.return_value = connection
    service_class.return_value.ingest.return_value = 2

    assert news_runner.main() == 2
    service_class.return_value.ingest.assert_called_once_with(
        limit=100,
        items=provider_class.return_value.get_news.return_value,
    )
    connection.close.assert_called_once_with()
from unittest.mock import patch

import pytest

from backend.app.scheduler import news_runner


@patch("backend.app.scheduler.news_runner.write_log")
@patch("backend.app.scheduler.news_runner.IndexAlphaNewsProvider")
@patch(
    "backend.app.scheduler.news_runner.is_trading_day",
    side_effect=RuntimeError("simulated calendar failure"),
)
def test_news_runner_logs_calendar_failure(
    trading_day_mock,
    provider_class,
    write_log_mock,
):
    with pytest.raises(RuntimeError, match="simulated calendar failure"):
        news_runner.main()

    write_log_mock.assert_any_call(
        "FAILED: RuntimeError: simulated calendar failure"
    )
    provider_class.assert_not_called()


def test_news_runner_logs_start_job_failure():
    with (
        patch("backend.app.scheduler.news_runner.write_log") as write_log,
        patch(
            "backend.app.scheduler.news_runner.is_trading_day",
            return_value=True,
        ),
        patch(
            "backend.app.scheduler.news_runner.IndexAlphaNewsProvider"
        ) as provider_class,
        patch(
            "backend.app.scheduler.news_runner.get_or_create_job",
            return_value=7,
        ),
        patch(
            "backend.app.scheduler.news_runner.start_job_run",
            side_effect=RuntimeError("simulated start failure"),
        ),
        patch(
            "backend.app.scheduler.news_runner.get_connection"
        ) as get_connection,
        patch(
            "backend.app.scheduler.news_runner.finish_job_run"
        ) as finish_job_run,
    ):
        provider_class.return_value.is_available.return_value = True

        with pytest.raises(RuntimeError, match="simulated start failure"):
            news_runner.main()

    write_log.assert_any_call(
        "FAILED: RuntimeError: simulated start failure"
    )
    get_connection.assert_not_called()
    finish_job_run.assert_not_called()


def test_news_runner_preserves_ingestion_error_if_failure_status_update_fails():
    with (
        patch("backend.app.scheduler.news_runner.write_log") as write_log,
        patch(
            "backend.app.scheduler.news_runner.is_trading_day",
            return_value=True,
        ),
        patch(
            "backend.app.scheduler.news_runner.IndexAlphaNewsProvider"
        ) as provider_class,
        patch(
            "backend.app.scheduler.news_runner.get_or_create_job",
            return_value=7,
        ),
        patch(
            "backend.app.scheduler.news_runner.start_job_run",
            return_value=23,
        ),
        patch(
            "backend.app.scheduler.news_runner.get_connection"
        ) as get_connection,
        patch(
            "backend.app.scheduler.news_runner.NewsIngestionService"
        ) as service_class,
        patch(
            "backend.app.scheduler.news_runner.finish_job_run",
            side_effect=RuntimeError("simulated status update failure"),
        ) as finish_job_run,
    ):
        provider_class.return_value.is_available.return_value = True
        connection = MagicMock()
        get_connection.return_value = connection
        service_class.return_value.ingest.side_effect = ValueError(
            "simulated ingestion failure"
        )

        with pytest.raises(ValueError, match="simulated ingestion failure"):
            news_runner.main()

    connection.close.assert_called_once_with()
    finish_job_run.assert_called_once_with(
        23,
        status="failed",
        message="ValueError: simulated ingestion failure",
    )
    write_log.assert_any_call(
        "FAILED TO UPDATE JOB STATUS: RuntimeError: simulated status update failure"
    )




def test_news_runner_does_not_expose_separate_raw_news_report():
    assert not hasattr(news_runner, "format_news_ingestion_report")
