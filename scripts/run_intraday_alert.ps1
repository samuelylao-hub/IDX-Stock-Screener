Set-Location "C:\Users\Lenovo PC\IDX-Stock-Screener"

& ".\.venv\Scripts\python.exe" -c "import os; from dotenv import load_dotenv; load_dotenv(override=True); from backend.app.services.intraday_scanner import IntradayScanner; from backend.app.analysis.intraday_alert import IntradayAlertEngine; from backend.app.services.notification_service import NotificationService; from backend.app.notifications.telegram import TelegramNotificationProvider; results = IntradayScanner().scan(['BBCA','BBRI']); [print(f'{r.symbol}: {r.state} | Score {r.score} | Mom {r.momentum}% | RS {r.relative_strength}% | Vol {r.volume_ratio}x | VP {r.volume_price_state} | IHSG {r.market_state}') for r in results]; alerts = IntradayAlertEngine().evaluate_all(results); print(f'Intraday alerts: {len(alerts)}'); notification = NotificationService([TelegramNotificationProvider(os.getenv('TELEGRAM_BOT_TOKEN'), os.getenv('TELEGRAM_CHAT_ID'))]) if alerts else None; notification.send_alerts(alerts) if notification else None"

if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
}
