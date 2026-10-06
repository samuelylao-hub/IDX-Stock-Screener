from dataclasses import dataclass


@dataclass(frozen=True)
class MarketRegime:
    state: str
    score: float
    return_5d: float
    return_20d: float
    detail: str


def _pct(first: float, last: float) -> float:
    if first == 0:
        return 0.0
    return ((last - first) / first) * 100.0


def determine_market_regime(closes: list[float]) -> MarketRegime:
    if len(closes) < 5:
        return MarketRegime(
            state="INSUFFICIENT_DATA",
            score=0.0,
            return_5d=0.0,
            return_20d=0.0,
            detail="IHSG data belum cukup.",
        )

    last = closes[-1]
    r5 = _pct(closes[-5], last)

    r20 = (
        _pct(closes[-20], last)
        if len(closes) >= 20
        else r5
    )

    score = 0.0

    if r5 > 0:
        score += 40
    elif r5 < 0:
        score -= 40

    if r20 > 0:
        score += 60
    elif r20 < 0:
        score -= 60

    if score >= 60:
        state = "BULLISH"
    elif score <= -60:
        state = "BEARISH"
    else:
        state = "NEUTRAL"

    return MarketRegime(
        state=state,
        score=score,
        return_5d=round(r5, 2),
        return_20d=round(r20, 2),
        detail=f"IHSG 5D {r5:.2f}%, 20D {r20:.2f}%.",
    )
