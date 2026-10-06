import os
from datetime import date

from dotenv import load_dotenv

load_dotenv()

from backend.app.analysis.alert_engine import AlertEngine
from backend.app.data.market_calendar import is_trading_day
from backend.app.data.market_data import update_all_stocks
from backend.app.data.foreign_flow import update_foreign_flow_batch
from backend.app.data.broker_flow import update_broker_summary_batch
from backend.app.database import get_connection
from backend.app.notifications.telegram import TelegramNotificationProvider
from backend.app.scheduler.job_logger import (
    finish_job_run,
    get_or_create_job,
    start_job_run,
)
from backend.app.services.notification_service import NotificationService
from backend.app.services.screener_report import format_screener_report
from backend.app.services.screener_service import ScreenerService


def _get_notification_service():
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    if token and chat_id:
        return NotificationService([TelegramNotificationProvider(token, chat_id)])
    return NotificationService()


def run_market_data_update():
    print("Starting market data update...")
    job_id = get_or_create_job("market_data_update", "Update market data harian")
    run_id = start_job_run(job_id)
    try:
        trade_date = date.today()
        update_all_stocks("5d")
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT id, symbol FROM stocks WHERE is_active = TRUE ORDER BY symbol")
                stocks = cur.fetchall()
        if not stocks:
            raise RuntimeError("Tidak ada saham aktif untuk market screening.")
        foreign_saved = update_foreign_flow_batch(stocks, trade_date)
        broker_saved = update_broker_summary_batch(stocks, trade_date)
        print(f"Foreign flow batch updated: {foreign_saved}/{len(stocks)} saham.")
        print(f"Broker flow batch updated: {broker_saved} rows.")
        results = ScreenerService().screen_market(trade_date, persist=True)
        report = format_screener_report(results, trade_date)
        print(report)
        notification = _get_notification_service()
        notification.send_report(report)
        alerts = AlertEngine().evaluate_all(results, trade_date)
        if alerts:
            print(f"Signal alerts: {len(alerts)}")
            notification.send_alerts(alerts)
        else:
            print("Signal alerts: none")
        finish_job_run(run_id, "success", f"Market update + screener berhasil. {len(results)} saham, {len(alerts)} alerts.")
        print("Market data update and screener finished.")
    except Exception as error:
        finish_job_run(run_id, "failed", str(error))
        print(f"Market data update failed: {error}")
        raise


def run_market_data_update_if_trading_day():
    if not is_trading_day(date.today()):
        print("Non-trading day. Market update skipped.")
        return
    run_market_data_update()
