from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from backend.app.scheduler.jobs import run_market_data_update_if_trading_day


JAKARTA_TZ = ZoneInfo("Asia/Jakarta")
LOG_PATH = Path(__file__).resolve().parents[3] / "logs" / "daily_runner.log"


def _write_runner_log(message: str) -> None:
    timestamp = datetime.now(JAKARTA_TZ).isoformat(timespec="seconds")
    line = f"{timestamp} WIB | {message}"

    try:
        LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with LOG_PATH.open("a", encoding="utf-8") as log_file:
            log_file.write(line + "\n")
    except OSError as error:
        print(f"WARNING: gagal menulis log runner: {error}")

    print(line)


def main():
    _write_runner_log("START")

    try:
        run_market_data_update_if_trading_day()
    except Exception as error:
        _write_runner_log(f"FAILED: {type(error).__name__}: {error}")
        raise

    _write_runner_log(
        "RETURNED: guard selesai; status screening perlu diverifikasi terpisah"
    )


if __name__ == "__main__":
    main()
