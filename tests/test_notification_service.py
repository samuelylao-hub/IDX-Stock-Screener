from types import SimpleNamespace
from unittest.mock import Mock

from backend.app.analysis.intraday_alert import IntradayAlertEngine
from backend.app.services.notification_service import NotificationService


def test_intraday_news_context_reaches_notification_provider_as_formatted_message():
    result = SimpleNamespace(
        symbol="BBCA",
        state="EARLY_BULLISH",
        score=70.0,
        momentum=1.2,
        relative_strength=0.8,
        volume_ratio=1.8,
        volume_price_state="ACCUMULATION",
        market_state="BULLISH",
        reasons=["momentum_positive", "volume_price_accumulation"],
    )
    news_context = {
        "news_state": "CONFIRMED",
        "impact_state": "IMPACT_ELIGIBLE",
        "detail": "News impact eligible with HIGH evidence.",
    }

    alerts = IntradayAlertEngine().evaluate_all(
        [result],
        news_context_by_symbol={"BBCA": news_context},
    )
    provider = Mock()
    notification = NotificationService(providers=[provider])

    notification.send_alerts(alerts)

    assert len(alerts) == 1
    provider.send.assert_called_once_with(alerts[0].message)
    sent_message = provider.send.call_args.args[0]
    assert "BBCA" in sent_message
    assert "CONFIRMED" in sent_message
    assert "News impact: IMPACT_ELIGIBLE" in sent_message
    assert "News impact eligible with HIGH evidence." in sent_message
    assert "IntradayAlert(" not in sent_message
