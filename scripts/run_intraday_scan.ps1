Set-Location "C:\Users\Lenovo PC\IDX-Stock-Screener"

& ".\.venv\Scripts\python.exe" -c "from backend.app.services.intraday_scanner import IntradayScanner; results = IntradayScanner().scan(['BBCA','BBRI']); [print(f'{r.symbol}: {r.state} | Score {r.score} | Mom {r.momentum}% | RS {r.relative_strength}% | Vol {r.volume_ratio}x | VP {r.volume_price_state} | IHSG {r.market_state}') for r in results]"

if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
}
