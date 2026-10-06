from unittest.mock import patch

import pytest

from backend.app.scheduler.jobs import run_market_data_update


@patch("backend.app.scheduler.jobs.update_foreign_flow_batch")
@patch("backend.app.scheduler.jobs.update_all_stocks")
@patch("backend.app.scheduler.jobs.NotificationService")
@patch("backend.app.scheduler.jobs.start_job_run", return_value=1)
@patch("backend.app.scheduler.jobs.get_or_create_job", return_value=1)
@patch("backend.app.scheduler.jobs.finish_job_run")
def test_scheduler_handles_index_alpha_failure(
    finish_job_run,
    get_or_create_job,
    start_job_run,
    notification_service,
    update_all_stocks,
    update_foreign_flow_batch,
):
    notification = notification_service.return_value

    update_foreign_flow_batch.side_effect = RuntimeError(
        "403 Client Error: Forbidden for url: https://api.indexalpha.id/foreign-flow/batch"
    )

    with patch(
        "backend.app.scheduler.jobs.get_connection"
    ) as get_connection:
        conn = get_connection.return_value.__enter__.return_value
        cur = conn.cursor.return_value.__enter__.return_value
        cur.fetchall.return_value = [(1, "BBCA"), (2, "BBRI")]

        with pytest.raises(RuntimeError, match="403"):
            run_market_data_update()

    finish_job_run.assert_called_once()
    assert finish_job_run.call_args.args[1] == "failed"

    notification.send_report.assert_called_once()
    message = notification.send_report.call_args.args[0]

    assert "Index Alpha" in message
    assert "403" in message
    assert "Screening dilewati" in message
