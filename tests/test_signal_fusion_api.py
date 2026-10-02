from datetime import date

from fastapi.testclient import TestClient

from backend.app.analysis.signal_fusion import SignalFusionResult
from backend.app.main import app

class FakeSignalFusionService:
    def analyze_symbol(
        self,
        symbol,
        trade_date,
        price_lookback=5,
        investor_type="all",
        market_segment="RG",
    ):
        return SignalFusionResult(
            symbol=symbol,
            trade_date=trade_date,
            foreign_state="ACCUMULATION",
            broker_state="DISTRIBUTION",
            price_volume_state="UPTREND",
            foreign_1d_state="INSUFFICIENT_DATA",
            foreign_5d_state="INSUFFICIENT_DATA",
            foreign_20d_state="INSUFFICIENT_DATA",
            broker_1d_state="INSUFFICIENT_DATA",
            broker_5d_state="INSUFFICIENT_DATA",
            broker_20d_state="INSUFFICIENT_DATA",
            foreign_persistence="INSUFFICIENT_DATA",
            broker_persistence="INSUFFICIENT_DATA",
            alignment="DIVERGENT",
            observation="Test observation",
            data_completeness=1.0,
            foreign_coverage={1: 1.0, 5: 1.0, 20: 0.75},
            broker_coverage={1: 1.0, 5: 1.0, 20: 1.0},
            data_quality_status="PARTIAL",
            evidence={},
        )

def test_signal_fusion_api_contract(monkeypatch):
    monkeypatch.setattr(
        "backend.app.main.SignalFusionService",
        lambda: FakeSignalFusionService(),
    )

    client = TestClient(app)

    response = client.get(
        "/api/v1/signals/BBCA",
        params={
            "trade_date": "2026-09-25",
            "price_lookback": 10,
            "investor_type": "all",
            "market_segment": "RG",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["symbol"] == "BBCA"
    assert data["trade_date"] == "2026-09-25"
    assert data["foreign_state"] == "ACCUMULATION"
    assert data["broker_state"] == "DISTRIBUTION"
    assert data["price_volume_state"] == "UPTREND"
    assert data["alignment"] == "DIVERGENT"
    assert data["data_completeness"] == 1.0
    assert data["data_quality_status"] == "PARTIAL"
    assert data["foreign_coverage"]["1"] == 1.0
    assert data["foreign_coverage"]["20"] == 0.75
    assert data["broker_coverage"]["20"] == 1.0
    assert data["evidence"] == {}
