from dataclasses import dataclass
from datetime import date

from backend.app.analysis.signal_fusion import SignalFusionResult


@dataclass
class ScreenerResult:
    symbol: str
    trade_date: date
    score: float
    signal: str
    confidence: float
    data_quality_status: str
    alignment: str
    foreign_state: str
    broker_state: str
    price_volume_state: str
    observation: str


def _state_score(state: str) -> float:
    if state == "ACCUMULATION":
        return 1.0

    if state == "DISTRIBUTION":
        return -1.0

    return 0.0


def calculate_signal_score(result: SignalFusionResult) -> float:
    score = 0.0

    score += _state_score(result.foreign_state) * 30
    score += _state_score(result.broker_state) * 30

    if result.price_volume_state == "UPTREND":
        score += 20
    elif result.price_volume_state == "DOWNTREND":
        score -= 20

    if result.alignment == "ALIGNED":
        score += 20
    elif result.alignment == "DIVERGENT":
        score -= 10

    return max(-100.0, min(100.0, score))


def determine_signal(score: float) -> str:
    if score >= 60:
        return "STRONG_BUY"

    if score >= 25:
        return "BUY"

    if score <= -60:
        return "STRONG_SELL"

    if score <= -25:
        return "SELL"

    return "WATCH"


def calculate_confidence(result: SignalFusionResult) -> float:
    base = result.data_completeness

    coverage_values = [
        *result.foreign_coverage.values(),
        *result.broker_coverage.values(),
    ]

    coverage = (
        sum(coverage_values) / len(coverage_values)
        if coverage_values
        else 0.0
    )

    confidence = (
        (base * 0.5) +
        (coverage * 0.5)
    )

    return round(confidence * 100, 2)


def build_screener_result(
    result: SignalFusionResult,
) -> ScreenerResult:
    score = calculate_signal_score(result)

    return ScreenerResult(
        symbol=result.symbol,
        trade_date=result.trade_date,
        score=round(score, 2),
        signal=determine_signal(score),
        confidence=calculate_confidence(result),
        data_quality_status=result.data_quality_status,
        alignment=result.alignment,
        foreign_state=result.foreign_state,
        broker_state=result.broker_state,
        price_volume_state=result.price_volume_state,
        observation=result.observation,
    )
