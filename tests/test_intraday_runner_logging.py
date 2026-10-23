import pytest

from backend.app.scheduler import intraday_runner as runner


def test_main_writes_timestamped_output_to_intraday_log(tmp_path, monkeypatch):
    log_path = tmp_path / "logs" / "intraday_runner.log"
    monkeypatch.setattr(runner, "LOG_PATH", log_path)

    def fake_run():
        print("IDX INTRADAY SCHEDULER STARTED")
        print("Scanning 100 symbols...")

    monkeypatch.setattr(runner, "run", fake_run)

    runner.main()

    contents = log_path.read_text(encoding="utf-8")
    assert "INTRADAY RUNNER PROCESS STARTED" in contents
    assert "IDX INTRADAY SCHEDULER STARTED" in contents
    assert "Scanning 100 symbols..." in contents
    assert "WIB |" in contents


def test_main_logs_fatal_error_and_reraises(tmp_path, monkeypatch):
    log_path = tmp_path / "logs" / "intraday_runner.log"
    monkeypatch.setattr(runner, "LOG_PATH", log_path)

    def failing_run():
        print("last diagnostic")
        raise RuntimeError("test failure")

    monkeypatch.setattr(runner, "run", failing_run)

    with pytest.raises(RuntimeError, match="test failure"):
        runner.main()

    contents = log_path.read_text(encoding="utf-8")
    assert "last diagnostic" in contents
    assert "FATAL: RuntimeError: test failure" in contents
