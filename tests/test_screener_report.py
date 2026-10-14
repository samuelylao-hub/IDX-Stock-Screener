from datetime import date
from types import SimpleNamespace

from backend.app.services.screener_report import format_screener_report


def test_empty_screener_report_explains_no_results():
    report = format_screener_report([], date(2026, 10, 14))

    assert "IDX MARKET SCAN - 2026-10-14" in report
    assert "Tidak ada hasil screening untuk tanggal ini." in report


def test_screener_report_includes_stock_details():
    result = SimpleNamespace(
        symbol="BBCA",
        signal="BULLISH",
        score=75,
        early_bullish="EARLY_BULLISH",
        early_bullish_score=60,
        ranking_score=80,
        confidence=90,
        data_quality_status="GOOD",
    )

    report = format_screener_report([result], date(2026, 10, 14))

    assert "#1 BBCA" in report
    assert "Rank Score  : 80" in report
    assert "Quality     : GOOD" in report
