from datetime import date
from unittest.mock import MagicMock

import backend.app.services.screener_service as screener_module
from backend.app.services.screener_service import _is_price_fresh


def test_price_is_fresh_when_date_matches_screening_date():
    trade_date = date(2026, 10, 14)

    assert _is_price_fresh(trade_date, trade_date) is True


def test_price_is_stale_when_latest_date_is_older():
    latest_price_date = date(2026, 10, 13)
    trade_date = date(2026, 10, 14)

    assert _is_price_fresh(latest_price_date, trade_date) is False


def test_price_is_not_fresh_when_no_price_exists():
    assert _is_price_fresh(None, date(2026, 10, 14)) is False


def test_price_date_after_screening_date_is_not_fresh():
    latest_price_date = date(2026, 10, 15)
    trade_date = date(2026, 10, 14)

    assert _is_price_fresh(latest_price_date, trade_date) is False


def test_screen_market_skips_stale_price_before_signal_analysis(monkeypatch):
    trade_date = date(2026, 10, 14)
    stale_price_date = date(2026, 10, 13)

    connection = MagicMock()
    connection.__enter__.return_value = connection

    cursor = MagicMock()
    connection.cursor.return_value.__enter__.return_value = cursor

    cursor.fetchone.side_effect = [
        (1,),
        (0,),
        (0,),
        ("ACTIVE", [], ""),
        (stale_price_date,),
    ]

    monkeypatch.setattr(
        screener_module,
        "get_connection",
        lambda: connection,
    )

    benchmark = MagicMock()
    benchmark.get_history.return_value = []

    signal_service = MagicMock()

    service = screener_module.ScreenerService(
        signal_service=signal_service,
        benchmark_provider=benchmark,
    )

    results = service.screen_market(
        trade_date=trade_date,
        symbols=["BBCA"],
    )

    assert results == []
    signal_service.analyze_symbol.assert_not_called()
