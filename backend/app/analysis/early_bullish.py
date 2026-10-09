from dataclasses import dataclass


@dataclass(frozen=True)
class EarlyBullishResult:
    state: str
    score: float
    reasons: list[str]


def detect_early_bullish(
    market_regime: str,
    momentum: float,
    momentum_state: str,
    relative_strength: float,
    relative_strength_state: str,
    price_volume_state: str,
    foreign_state: str,
    broker_state: str,
) -> EarlyBullishResult:

    score = 0.0
    reasons = []

    if market_regime == "BULLISH":
        score += 20
        reasons.append("market_bullish")
    elif market_regime == "BEARISH":
        score -= 20

    if momentum_state in {"POSITIVE", "STRONG"}:
        score += 25
        reasons.append("momentum_positive")
    elif momentum_state in {"NEGATIVE", "WEAK"}:
        score -= 25

    if relative_strength_state == "OUTPERFORMING":
        score += 25
        reasons.append("relative_strength_outperforming")
    elif relative_strength_state == "UNDERPERFORMING":
        score -= 25

    if price_volume_state == "UPTREND":
        score += 15
        reasons.append("price_volume_uptrend")
    elif price_volume_state == "DOWNTREND":
        score -= 15

    if foreign_state == "ACCUMULATION":
        score += 7.5
        reasons.append("foreign_accumulation")
    elif foreign_state == "DISTRIBUTION":
        score -= 7.5

    if broker_state == "ACCUMULATION":
        score += 7.5
        reasons.append("broker_accumulation")
    elif broker_state == "DISTRIBUTION":
        score -= 7.5

    # Add bounded numeric contributions within each category.
    score += max(-5.0, min(5.0, momentum))
    score += max(-5.0, min(5.0, relative_strength))
    score = max(-100.0, min(100.0, score))

    bullish_confirmations = sum(
        [
            momentum_state in {"POSITIVE", "STRONG"},
            relative_strength_state == "OUTPERFORMING",
            price_volume_state == "UPTREND",
            foreign_state == "ACCUMULATION",
            broker_state == "ACCUMULATION",
        ]
    )

    if (
        market_regime != "BEARISH"
        and bullish_confirmations >= 3
        and score >= 60
    ):
        state = "CONFIRMED_BULLISH"
    elif (
        market_regime != "BEARISH"
        and bullish_confirmations >= 2
        and score >= 35
    ):
        state = "EARLY_BULLISH"
    else:
        state = "NORMAL"

    return EarlyBullishResult(
        state=state,
        score=round(score, 2),
        reasons=reasons,
    )
