Set-Location "C:\Users\Lenovo PC\IDX-Stock-Screener"

& ".\.venv\Scripts\python.exe" -c "from backend.app.scheduler.jobs import run_market_data_update_if_trading_day; run_market_data_update_if_trading_day()"

if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
}
