from apscheduler.schedulers.blocking import BlockingScheduler

from backend.app.scheduler.jobs import run_market_data_update


scheduler = BlockingScheduler(
    timezone="Asia/Jakarta"
)


def start_scheduler():
    scheduler.add_job(
        run_market_data_update,
        "cron",
        day_of_week="mon-fri",
        hour=18,
        minute=0,
        id="market_data_update",
        replace_existing=True,
    )

    print("Scheduler started.")
    print("Market data update dijadwalkan setiap Senin-Jumat pukul 18:00 WIB.")

    scheduler.start()


if __name__ == "__main__":
    start_scheduler()