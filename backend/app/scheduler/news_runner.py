import os
from collections import Counter
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from dotenv import load_dotenv
from backend.app.notifications.telegram import TelegramNotificationProvider
from backend.app.services.notification_service import NotificationService

from backend.app.database import get_connection
from backend.app.data.market_calendar import is_trading_day
from backend.app.providers.index_alpha_news import IndexAlphaNewsProvider
from backend.app.scheduler.job_logger import (
    finish_job_run,
    get_or_create_job,
    start_job_run,
)
from backend.app.services.news_ingestion_service import (
    NewsIngestionService,
)


JAKARTA_TZ = ZoneInfo("Asia/Jakarta")
LOG_PATH = Path(__file__).resolve().parents[3] / "logs" / "news_runner.log"


def write_log(message: str) -> None:
    timestamp = datetime.now(JAKARTA_TZ).isoformat(timespec="seconds")
    line = f"{timestamp} WIB | {message}"

    try:
        LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with LOG_PATH.open("a", encoding="utf-8") as log_file:
            log_file.write(line + "\n")
    except OSError as error:
        print(f"WARNING: gagal menulis log berita: {error}")

    print(line)


def main() -> int:
    write_log("START")

    run_id = None

    try:
        now = datetime.now(JAKARTA_TZ)
        if not is_trading_day(now.date()):
            write_log(f"SKIPPED: non-trading day ({now.date()})")
            return 0
    except Exception as error:
        write_log(f"FAILED: {type(error).__name__}: {error}")
        raise

    try:
        provider = IndexAlphaNewsProvider()

        if not provider.is_available():
            raise RuntimeError(
                "INDEX_ALPHA_API_KEY belum tersedia. Ingestion dibatalkan."
            )

        job_id = get_or_create_job(
            job_name="news_ingestion",
            description="Mengambil dan menyimpan berita untuk intraday scanner.",
        )
        run_id = start_job_run(job_id)

        connection = get_connection()
        try:
            # Ambil berita sekali; provider menggunakan cache untuk ingestion.
            items = provider.get_news(limit=100)
            service = NewsIngestionService(
                provider=provider,
                connection=connection,
            )
            saved_count = service.ingest(limit=100, items=items)
        finally:
            connection.close()

        finish_job_run(
            run_id,
            status="success",
            message=f"News ingestion selesai. Event tersimpan/diproses: {saved_count}",
        )

        write_log(f"SUCCESS: events_saved={saved_count}")

        # Notifikasi terpisah: kegagalan Telegram tidak membatalkan ingestion.
        try:
            load_dotenv(override=True)
            token = os.getenv("TELEGRAM_BOT_TOKEN")
            chat_id = os.getenv("TELEGRAM_CHAT_ID")

            if not token or not chat_id:
                write_log("TELEGRAM_SKIPPED: TELEGRAM_BOT_TOKEN/TELEGRAM_CHAT_ID belum tersedia")
            else:
                source_counts = Counter(
                    str(getattr(item, "source", None) or "Sumber tidak diketahui")
                    for item in items
                )
                report_time = datetime.now(JAKARTA_TZ).strftime("%Y-%m-%d %H:%M:%S WIB")
                source_lines = [
                    f"- {source}: {count}"
                    for source, count in source_counts.most_common(10)
                ]
                message = (
                    "IDX STOCK SCREENER | LAPORAN INGESTION BERITA\n"
                    f"Waktu: {report_time}\n"
                    f"Artikel diterima: {len(items)}\n"
                    f"Sumber berita: {len(source_counts)}\n"
                    f"Event tersimpan/diproses: {saved_count}\n"
                    "\nRincian sumber:\n"
                    + ("\n".join(source_lines) if source_lines else "- Tidak ada artikel")
                )
                notification = NotificationService([
                    TelegramNotificationProvider(token, chat_id)
                ])
                notification.send_report(message)
                write_log("TELEGRAM_SENT: laporan ingestion dikirim")
        except Exception as notify_error:
            write_log(
                f"TELEGRAM_FAILED: {type(notify_error).__name__}: {notify_error}"
            )

        return saved_count

    except Exception as error:
        write_log(f"FAILED: {type(error).__name__}: {error}")

        if run_id is not None:
            try:
                finish_job_run(
                    run_id,
                    status="failed",
                    message=f"{type(error).__name__}: {error}"[:1000],
                )
            except Exception as log_error:
                write_log(
                    f"FAILED TO UPDATE JOB STATUS: "
                    f"{type(log_error).__name__}: {log_error}"
                )

        raise


if __name__ == "__main__":
    main()
