import time
from datetime import date, datetime
from zoneinfo import ZoneInfo

from backend.app.analysis.intraday_alert import IntradayAlertEngine
from backend.app.data.intraday_universe import get_intraday_symbols
from backend.app.data.market_calendar import is_trading_day
from backend.app.notifications.telegram import TelegramNotificationProvider
from backend.app.scheduler.intraday_session import is_intraday_session, session_name
from backend.app.services.intraday_scanner import IntradayScanner
from backend.app.services.notification_service import NotificationService

JAKARTA_TZ = ZoneInfo("Asia/Jakarta")
INTERVAL_SECONDS = 300


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

        if not is_trading_day(date.today()):
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

            alerts = alert_engine.evaluate_all(results)

            print(f"  Intraday alerts: {len(alerts)}")

            if alerts and notification:
                notification.send_alerts(alerts)
                print("  Telegram alert sent.")

        except Exception as error:
            print(f"  Intraday scan failed: {error}")

        time.sleep(INTERVAL_SECONDS)


if __name__ == "__main__":
    run()
