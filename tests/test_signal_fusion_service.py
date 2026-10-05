from datetime import date
from decimal import Decimal

from backend.app.data.signal_fusion_repository import (
    SignalFusionInput,
)
from backend.app.services.signal_fusion_service import (
    SignalFusionService,
)


class FakeSignalFusionRepository:
    def get_signal_input(
        self,
        symbol,
        trade_date,
        price_lookback=5,
        investor_type="all",
        market_segment="RG",
    ):
        return SignalFusionInput(
            symbol=symbol,
            trade_date=trade_date,
            net_foreign=Decimal("99028035225"),
            broker_net=Decimal("-238477692500"),
            first_close=Decimal("6225"),
            last_close=Decimal("6250"),
        )


def test_service_builds_bbca_signal_from_repository():
    service = SignalFusionService(
        repository=FakeSignalFusionRepository()
    )

    result = service.analyze_symbol(
        symbol="BBCA",
        trade_date=date(2026, 9, 25),
    )

    assert result.symbol == "BBCA"
    assert result.trade_date == date(2026, 9, 25)

    assert result.foreign_state == "ACCUMULATION"
    assert result.broker_state == "DISTRIBUTION"
    assert result.price_volume_state == "UPTREND"

    assert result.alignment == "DIVERGENT"
    assert result.data_completeness == 1.0


def test_service_uses_repository_lookback_configuration():
    class RecordingRepository:
        def __init__(self):
            self.arguments = None

        def get_signal_input(
            self,
            symbol,
            trade_date,
            price_lookback=5,
            investor_type="all",
            market_segment="RG",
        ):
            self.arguments = {
                "symbol": symbol,
                "trade_date": trade_date,
                "price_lookback": price_lookback,
                "investor_type": investor_type,
                "market_segment": market_segment,
            }

            return SignalFusionInput(
                symbol=symbol,
                trade_date=trade_date,
                net_foreign=None,
                broker_net=None,
                first_close=Decimal("5000"),
                last_close=Decimal("5050"),
            )

    repository = RecordingRepository()
    service = SignalFusionService(repository=repository)

    result = service.analyze_symbol(
        symbol="BBRI",
        trade_date=date(2026, 9, 25),
        price_lookback=10,
        investor_type="all",
        market_segment="RG",
    )

    assert result.symbol == "BBRI"
    assert result.price_volume_state == "UPTREND"
    assert result.alignment == "INSUFFICIENT_DATA"

    assert repository.arguments == {
        "symbol": "BBRI",
        "trade_date": date(2026, 9, 25),
        "price_lookback": 10,
        "investor_type": "all",
        "market_segment": "RG",
    }


def test_service_attaches_news_evidence():
    class NewsRepositoryConnection:
        def cursor(self):
            return self

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            pass

        def execute(self, *args, **kwargs):
            return self

        def fetchall(self):
            return [
                (
                    1,
                    "BBRI",
                    "BBRI mendapat sentimen positif",
                    None,
                    None,
                    None,
                    "CORROBORATED",
                    2,
                    1,
                    1,
                    1,
                    0,
                    "MEDIUM_HIGH",
                )
            ]

    class FakeConnection:
        def __enter__(self):
            return NewsRepositoryConnection()

        def __exit__(self, exc_type, exc, tb):
            pass

    class FakeSignalFusionRepository:
        def get_signal_input(
            self,
            symbol,
            trade_date,
            price_lookback=5,
            investor_type="all",
            market_segment="RG",
        ):
            return SignalFusionInput(
                symbol=symbol,
                trade_date=trade_date,
                net_foreign=None,
                broker_net=None,
                first_close=Decimal("5000"),
                last_close=Decimal("5050"),
            )

    import backend.app.services.signal_fusion_service as module

    original_get_connection = module.get_connection
    module.get_connection = lambda: FakeConnection()

    try:
        service = SignalFusionService(
            repository=FakeSignalFusionRepository()
        )

        result = service.analyze_symbol(
            symbol="BBRI",
            trade_date=date(2026, 10, 5),
        )

        news = result.evidence["news"]

        assert news.component == "news"
        assert news.source == "news_events"
        assert news.available is True
        assert news.status == "AVAILABLE"
        assert "CORROBORATED" in news.detail
        assert "MEDIUM_HIGH" in news.detail
    finally:
        module.get_connection = original_get_connection
