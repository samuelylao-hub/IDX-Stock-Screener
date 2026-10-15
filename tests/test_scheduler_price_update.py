from unittest.mock import patch

import pytest

from backend.app.scheduler.jobs import run_market_data_update


def test_scheduler_stops_when_all_price_updates_fail():
    summary = {
        "requested": 100,
        "success": 0,
        "failed": 100,
        "rows_saved": 0,
        "skipped": False,
        "failures": [{"symbol": "BBCA", "error": "Yahoo unavailable"}],
    }

    with (
        patch("backend.app.scheduler.jobs.update_all_stocks", return_value=summary),
        patch("backend.app.scheduler.jobs.update_foreign_flow_batch") as foreign,
        patch("backend.app.scheduler.jobs.NotificationService") as notification_cls,
        patch("backend.app.scheduler.jobs.get_or_create_job", return_value=1),
        patch("backend.app.scheduler.jobs.start_job_run", return_value=7),
        patch("backend.app.scheduler.jobs.finish_job_run") as finish,
    ):
        with pytest.raises(RuntimeError, match="gagal total"):
            run_market_data_update()

    finish.assert_called_once()
    assert finish.call_args.args[1] == "failed"
    foreign.assert_not_called()
    notification_cls.return_value.send_report.assert_called_once()


def test_scheduler_marks_partial_price_update_as_failed():
    summary = {
        "requested": 2,
        "success": 1,
        "failed": 1,
        "rows_saved": 5,
        "skipped": False,
        "failures": [{"symbol": "BBRI", "error": "Yahoo unavailable"}],
    }

    with (
        patch("backend.app.scheduler.jobs.update_all_stocks", return_value=summary),
        patch("backend.app.scheduler.jobs.update_foreign_flow_batch", return_value=2),
        patch("backend.app.scheduler.jobs.update_broker_summary_batch", return_value=2),
        patch("backend.app.scheduler.jobs.get_or_create_job", return_value=1),
        patch("backend.app.scheduler.jobs.start_job_run", return_value=7),
        patch("backend.app.scheduler.jobs.finish_job_run") as finish,
        patch("backend.app.scheduler.jobs.NotificationService") as notification_cls,
        patch("backend.app.scheduler.jobs.get_connection") as get_connection,
        patch("backend.app.scheduler.jobs.ScreenerService") as screener_cls,
        patch("backend.app.scheduler.jobs.format_screener_report", return_value="Test report"),
        patch("backend.app.scheduler.jobs.AlertEngine") as alert_cls,
    ):
        conn = get_connection.return_value.__enter__.return_value
        cursor = conn.cursor.return_value.__enter__.return_value
        cursor.fetchall.return_value = [(1, "BBCA"), (2, "BBRI")]
        screener_cls.return_value.screen_market.return_value = []
        alert_cls.return_value.evaluate_all.return_value = []

        run_market_data_update()

    assert finish.call_args.args[1] == "failed"
    assert "PARTIAL" in finish.call_args.args[2]
    assert "BBRI" in finish.call_args.args[2]
    reports = [
        call.args[0]
        for call in notification_cls.return_value.send_report.call_args_list
    ]
    assert len(reports) == 1
    partial_report = reports[0]
    assert "HASIL PARSIAL" in partial_report
    assert "\n\n" in partial_report
    assert "\\n" not in partial_report
    assert "Update harga berhasil: 1/2." in partial_report
    assert "Update harga gagal: 1." in partial_report
