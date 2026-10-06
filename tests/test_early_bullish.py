from backend.app.analysis.early_bullish import detect_early_bullish


def test_early_bullish():
    result = detect_early_bullish(
        market_regime="BULLISH",
        momentum=2.5,
        momentum_state="POSITIVE",
        relative_strength=4.0,
        relative_strength_state="OUTPERFORMING",
        price_volume_state="NEUTRAL",
        foreign_state="NEUTRAL",
        broker_state="NEUTRAL",
    )

    assert result.state == "EARLY_BULLISH"
    assert result.score >= 40


def test_early_bullish_rejected_in_bear_market():
    result = detect_early_bullish(
        market_regime="BEARISH",
        momentum=5.0,
        momentum_state="STRONG",
        relative_strength=5.0,
        relative_strength_state="OUTPERFORMING",
        price_volume_state="UPTREND",
        foreign_state="ACCUMULATION",
        broker_state="ACCUMULATION",
    )

    assert result.state == "NORMAL"


def test_early_bullish_weak_stock():
    result = detect_early_bullish(
        market_regime="NEUTRAL",
        momentum=-5.0,
        momentum_state="WEAK",
        relative_strength=-4.0,
        relative_strength_state="UNDERPERFORMING",
        price_volume_state="DOWNTREND",
        foreign_state="DISTRIBUTION",
        broker_state="DISTRIBUTION",
    )

    assert result.state == "NORMAL"
