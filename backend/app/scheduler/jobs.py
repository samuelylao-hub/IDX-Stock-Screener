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
from backend.app.focused_universe import FOCUSED_UNIVERSE


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
    notification = _get_notification_service()
    try:
        trade_date = date.today()
        focused_symbols = list(FOCUSED_UNIVERSE)

        price_summary = update_all_stocks("5d", symbols=focused_symbols)

        # Backward-compatible for existing tests/mocks that return None.
        if isinstance(price_summary, dict):
            if price_summary.get("skipped"):
                raise RuntimeError(
                    "Update harga dilewati karena bukan hari bursa; screening dihentikan."
                )

            requested = price_summary.get("requested", 0)
            price_success = price_summary.get("success", 0)
            price_failed = price_summary.get("failed", 0)

            if requested == 0 or price_success == 0:
                details = "; ".join(
                    f"{item.get('symbol', '?')}: {item.get('error', 'gagal')}"
                    for item in price_summary.get("failures", [])[:10]
                )
                raise RuntimeError(
                    "Update harga gagal total; screening dihentikan. "
                    f"Diminta={requested}, berhasil={price_success}, gagal={price_failed}. "
                    f"Detail: {details or 'Tidak ada saham yang berhasil diperbarui.'}"
                )
        else:
            price_success = None
            price_failed = 0
            requested = None


        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT id, symbol
                    FROM stocks
                    WHERE is_active = TRUE
                      AND symbol = ANY(%s)
                    ORDER BY symbol
                    """,
                    (focused_symbols,),
                )
                stocks = cur.fetchall()
        if not stocks:
            raise RuntimeError("Tidak ada saham aktif untuk market screening.")
        foreign_saved = update_foreign_flow_batch(stocks, trade_date)
        broker_saved = update_broker_summary_batch(stocks, trade_date)
        print(f"Foreign flow batch updated: {foreign_saved}/{len(stocks)} saham.")
        print(f"Broker flow batch updated: {broker_saved} rows.")
        results = ScreenerService().screen_market(
            trade_date,
            symbols=[symbol for _, symbol in stocks],
            persist=True,
        )
        report = format_screener_report(results, trade_date)
        print(report)
        notification.send_report(report)
        alerts = AlertEngine().evaluate_all(results, trade_date)
        if alerts:
            print(f"Signal alerts: {len(alerts)}")
            notification.send_alerts(alerts)
        else:
            print("Signal alerts: none")
        if isinstance(price_summary, dict) and price_failed > 0:
            failed_symbols = ", ".join(
                item.get("symbol", "?")
                for item in price_summary.get("failures", [])[:15]
            )
            status_message = (
                f"PARTIAL: screening selesai untuk {len(results)} saham dengan "
                f"{len(alerts)} alerts, tetapi update harga gagal untuk "
                f"{price_failed}/{requested} saham. "
                f"Simbol gagal: {failed_symbols or 'lihat log update harga'}."
            )
            finish_job_run(run_id, "failed", status_message)
            notification.send_report(
                "IDX MARKET SCAN ? HASIL PARSIAL\\n\\n"
                f"Screening selesai: {len(results)} saham; alerts: {len(alerts)}.\\n"
                f"Update harga berhasil: {price_success}/{requested}.\\n"
                f"Update harga gagal: {price_failed}.\\n"
                f"Simbol gagal: {failed_symbols or 'lihat log job'}."
            )
            print(status_message)
        else:
            finish_job_run(
                run_id,
                "success",
                f"Market update + screener berhasil. {len(results)} saham, "
                f"{len(alerts)} alerts.",
            )
        print("Market data update and screener finished.")
    except Exception as error:
        error_message = str(error)
        finish_job_run(run_id, "failed", error_message)
        print(f"Market data update failed: {error_message}")

        if "403" in error_message or "Forbidden" in error_message:
            notification.send_report(
                "?? IDX MARKET SCAN\n\n"
                "Market data update gagal.\n"
                "Index Alpha menolak request (403 / quota).\n"
                "Screening dilewati sampai API tersedia kembali."
            )
        else:
            notification.send_report(
                f"?? IDX MARKET SCAN\n\n"
                f"Market data update gagal:\n{error_message}"
            )

        raise


def run_market_data_update_if_trading_day():
    if not is_trading_day(date.today()):
        print("Non-trading day. Market update skipped.")
        return
    run_market_data_update()
