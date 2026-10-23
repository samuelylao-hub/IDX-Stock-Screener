from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from backend.app.scheduler.jobs import run_market_data_update_if_trading_day
from backend.app.scheduler.news_runner import main as run_news_ingestion


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
    failures = []

    # Run news independently first, so a market-data failure does not suppress
    # the news report and a news failure does not suppress stock screening.
    try:
        result = run_news_ingestion()
        _write_runner_log(f"NEWS_RETURNED: events_saved={result}")
    except Exception as error:
        failures.append(("news ingestion", error))
        _write_runner_log(f"NEWS_FAILED: {type(error).__name__}: {error}")

    try:
        run_market_data_update_if_trading_day()
        _write_runner_log("MARKET_DATA_RETURNED")
    except Exception as error:
        failures.append(("market screening", error))
        _write_runner_log(f"MARKET_DATA_FAILED: {type(error).__name__}: {error}")

    if failures:
        summary = "; ".join(
            f"{name}: {type(error).__name__}: {error}"
            for name, error in failures
        )
        _write_runner_log(f"FAILED: {summary}")
        raise RuntimeError(summary) from failures[0][1]

    _write_runner_log("SUCCESS: news ingestion and market screening returned")


if __name__ == "__main__":
    main()
