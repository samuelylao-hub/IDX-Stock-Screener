Set-Location "C:\Users\Lenovo PC\IDX-Stock-Screener"

& ".\.venv\Scripts\python.exe" -m backend.app.scheduler.intraday_runner

if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
}
