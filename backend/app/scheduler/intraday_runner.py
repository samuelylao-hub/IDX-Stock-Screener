import time
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from backend.app.analysis.intraday_alert import IntradayAlertEngine
from backend.app.analysis.news_signal import determine_news_signal
from backend.app.analysis.news_impact import determine_news_impact
from backend.app.database import get_connection
from backend.app.providers.news_repository import get_news_events_for_symbol
from backend.app.data.intraday_universe import get_intraday_symbols
from backend.app.data.market_calendar import is_trading_day
from backend.app.notifications.telegram import TelegramNotificationProvider
from backend.app.scheduler.intraday_session import is_intraday_session, session_name
from backend.app.services.intraday_scanner import IntradayScanner
from backend.app.services.notification_service import NotificationService

JAKARTA_TZ = ZoneInfo("Asia/Jakarta")
INTERVAL_SECONDS = 300


def load_intraday_news_context(symbols, trade_date):
    """Fetch news context only for eligible intraday candidates."""
    contexts = {}
    if not symbols:
        return contexts

    try:
        with get_connection() as connection:
            for symbol in symbols:
                try:
                    events = get_news_events_for_symbol(
                        connection=connection,
                        symbol=symbol,
                        start_date=trade_date - timedelta(days=3),
                        end_date=trade_date + timedelta(days=1),
                    )

                    if events:
                        latest = events[0]
                        signal = determine_news_signal(
                            event_count=len(events),
                            validation_status=latest[6],
                            evidence_strength=latest[12],
                        )
                    else:
                        signal = determine_news_signal(
                            event_count=0,
                            validation_status=None,
                            evidence_strength=None,
                        )

                    impact = determine_news_impact(
                        signal.state,
                        signal.evidence_strength,
                    )
                    contexts[symbol] = {
                        "news_state": signal.state,
                        "impact_state": impact.state,
                        "detail": impact.detail,
                    }
                except Exception as error:
                    print(f"  News lookup failed for {symbol}: {error}")
                    contexts[symbol] = {
                        "news_state": "UNAVAILABLE",
                        "impact_state": "NO_IMPACT",
                        "detail": "News lookup unavailable; no impact applied.",
                    }
    except Exception as error:
        print(f"  News database unavailable: {error}")
        for symbol in symbols:
            contexts.setdefault(symbol, {
                "news_state": "UNAVAILABLE",
                "impact_state": "NO_IMPACT",
                "detail": "News lookup unavailable; no impact applied.",
            })

    return contexts


def build_notification():
    import os
    from dotenv import load_dotenv

    load_dotenv(override=True)

    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")

    if not token or not chat_id:
        return None

    return NotificationService([
        TelegramNotificationProvider(token, chat_id)
    ])


def run():
    scanner = IntradayScanner()
    alert_engine = IntradayAlertEngine(persistent=True)
    notification = build_notification()

    print("IDX INTRADAY SCHEDULER STARTED")
    print("Interval: 5 minutes")
    print("Timezone: Asia/Jakarta")
    print("")

    while True:
        now = datetime.now(JAKARTA_TZ)

        if not is_trading_day(datetime.now(JAKARTA_TZ).date()):
            print(f"[{now:%Y-%m-%d %H:%M:%S}] Non-trading day. Waiting...")
            time.sleep(INTERVAL_SECONDS)
            continue

        if not is_intraday_session(now):
            print(
                f"[{now:%Y-%m-%d %H:%M:%S}] "
                f"Market closed ({session_name(now)}). Waiting..."
            )
            time.sleep(INTERVAL_SECONDS)
            continue

        try:
            symbols = get_intraday_symbols()

            if not symbols:
                print("No intraday symbols configured.")
                time.sleep(INTERVAL_SECONDS)
                continue

            print(
                f"[{now:%Y-%m-%d %H:%M:%S}] "
                f"Scanning {len(symbols)} symbols..."
            )

            results = scanner.scan(symbols)

            for result in results:
                print(
                    f"  {result.symbol}: {result.state} | "
                    f"Score {result.score} | "
                    f"Mom {result.momentum}% | "
                    f"RS {result.relative_strength}% | "
                    f"Vol {result.volume_ratio}x | "
                    f"VP {result.volume_price_state}"
                )

            trade_date = now.date()
            eligible_news_symbols = [
                result.symbol
                for result in results
                if result.state == "EARLY_BULLISH"
                and result.score >= alert_engine.EARLY_THRESHOLD
                and result.volume_price_state != "DISTRIBUTION"
            ]
            news_context_by_symbol = load_intraday_news_context(
                eligible_news_symbols,
                trade_date,
            )
            alerts = alert_engine.evaluate_all(
                results,
                trade_date=trade_date,
                news_context_by_symbol=news_context_by_symbol,
            )

            print(f"  Intraday alerts: {len(alerts)}")

            if alerts and notification:
                notification.send_alerts(alerts)
                print("  Telegram alert sent.")

        except Exception as error:
            print(f"  Intraday scan failed: {error}")

        time.sleep(INTERVAL_SECONDS)


# Persist runner/scanner output because Task Scheduler does not retain a
# useful console transcript for a long-running background process.
import sys
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

LOG_PATH = Path(__file__).resolve().parents[3] / "logs" / "intraday_runner.log"


class _TimestampedTee:
    def __init__(self, *streams):
        self.streams = streams
        self.buffer = ""

    def write(self, value):
        if not isinstance(value, str):
            value = str(value)
        self.buffer += value
        while "\n" in self.buffer:
            line, self.buffer = self.buffer.split("\n", 1)
            self._write_line(line)
        return len(value)

    def _write_line(self, line):
        timestamp = datetime.now(JAKARTA_TZ).isoformat(timespec="seconds")
        rendered = f"{timestamp} WIB | {line}\n"
        for stream in self.streams:
            stream.write(rendered)
            stream.flush()

    def flush(self):
        for stream in self.streams:
            stream.flush()

    def flush_partial(self):
        if self.buffer:
            self._write_line(self.buffer)
            self.buffer = ""


def main():
    try:
        LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with LOG_PATH.open("a", encoding="utf-8", buffering=1) as log_file:
            stdout = _TimestampedTee(*([sys.__stdout__] if sys.__stdout__ else []), log_file)
            stderr = _TimestampedTee(*([sys.__stderr__] if sys.__stderr__ else []), log_file)
            with redirect_stdout(stdout), redirect_stderr(stderr):
                print("INTRADAY RUNNER PROCESS STARTED")
                try:
                    run()
                except Exception as error:
                    print(
                        f"FATAL: {type(error).__name__}: {error}",
                        file=sys.stderr,
                    )
                    raise
                finally:
                    stdout.flush_partial()
                    stderr.flush_partial()
    except OSError as error:
        print(
            f"WARNING: intraday log unavailable ({error}); "
            "continuing without file logging.",
            file=sys.stderr,
        )
        run()


if __name__ == "__main__":
    main()
