from datetime import date

from backend.app.analysis.evidence import (
    Evidence,
    build_evidence,
    determine_evidence_status,
)
from backend.app.analysis.signal_fusion import build_signal_fusion_result


def test_complete_evidence_status():
    assert determine_evidence_status(True, 1.0) == "COMPLETE"


def test_partial_evidence_status():
    assert determine_evidence_status(True, 0.5) == "PARTIAL"


def test_missing_evidence_status():
    assert determine_evidence_status(False, 0.0) == "MISSING"


def test_build_evidence():
    evidence = build_evidence(
        component="price",
        source="stock_prices",
        as_of=date(2026, 9, 25),
        available=True,
        status="COMPLETE",
    )

    assert isinstance(evidence, Evidence)
    assert evidence.component == "price"
    assert evidence.source == "stock_prices"
    assert evidence.as_of == date(2026, 9, 25)
    assert evidence.available is True
    assert evidence.status == "COMPLETE"


def test_signal_fusion_contains_evidence():
    result = build_signal_fusion_result(
        symbol="BBCA",
        trade_date=date(2026, 9, 25),
        net_foreign=100,
        broker_net=-200,
        first_close=6200,
        last_close=6250,
    )

    assert set(result.evidence.keys()) == {"price", "foreign", "broker"}

    assert result.evidence["price"].source == "stock_prices"
    assert result.evidence["foreign"].source == "foreign_daily_flow"
    assert result.evidence["broker"].source == "broker_stock_flow"

    assert result.evidence["price"].as_of == date(2026, 9, 25)
    assert result.evidence["foreign"].as_of == date(2026, 9, 25)
    assert result.evidence["broker"].as_of == date(2026, 9, 25)

    assert result.evidence["price"].status == "COMPLETE"
    assert result.evidence["foreign"].status == "COMPLETE"
    assert result.evidence["broker"].status == "COMPLETE"


def test_missing_signal_fusion_evidence():
    result = build_signal_fusion_result(
        symbol="BBRI",
        trade_date=date(2026, 9, 25),
        net_foreign=None,
        broker_net=None,
        first_close=5000,
        last_close=5050,
    )

    assert result.evidence["price"].status == "COMPLETE"
    assert result.evidence["foreign"].status == "MISSING"
    assert result.evidence["broker"].status == "MISSING"
