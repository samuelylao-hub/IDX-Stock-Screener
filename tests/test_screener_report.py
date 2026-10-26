from datetime import date
from types import SimpleNamespace

from backend.app.services.screener_report import format_screener_report


def _result():
    return SimpleNamespace(
        symbol="BBCA",
        signal="BULLISH",
        score=75,
        early_bullish="EARLY_BULLISH",
        early_bullish_score=60,
        ranking_score=80,
        confidence=90,
        data_quality_status="GOOD",
    )


def test_empty_screener_report_explains_no_results():
    report = format_screener_report([], date(2026, 10, 14))
    assert "IDX MARKET SCAN - 2026-10-14" in report
    assert "Tidak ada hasil screening untuk tanggal ini." in report


def test_screener_report_includes_stock_details():
    report = format_screener_report([_result()], date(2026, 10, 14))
    assert "#1 BBCA" in report
    assert "Rank Score  : 80" in report
    assert "Quality     : GOOD" in report


def test_screener_report_includes_news_and_alert_in_same_message():
    alert = SimpleNamespace(symbol="BBCA", level="HIGH", state="NEW")
    report = format_screener_report(
        [_result()],
        date(2026, 10, 14),
        news_by_symbol={
            "BBCA": {
                "title": "BBCA mencatat kenaikan laba",
                "published_at": "2026-10-14 10:00",
                "source": "CNBC Indonesia",
                "validation_status": "VALIDATED",
                "evidence_strength": "STRONG",
                "url": "https://example.com/news",
            }
        },
        alerts=[alert],
    )
    assert "BBCA mencatat kenaikan laba" in report
    assert "News source : CNBC Indonesia" in report
    assert "News link   : https://example.com/news" in report
    assert "Alert       : HIGH / NEW" in report


def test_screener_report_marks_missing_relevant_news():
    report = format_screener_report([_result()], date(2026, 10, 14))
    assert "Tidak ada berita relevan terverifikasi" in report
