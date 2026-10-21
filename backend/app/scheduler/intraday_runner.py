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


if __name__ == "__main__":
    run()
