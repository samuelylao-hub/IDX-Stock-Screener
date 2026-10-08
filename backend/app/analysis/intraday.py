from __future__ import annotations

from dataclasses import dataclass

from backend.app.analysis.relative_strength import (
    calculate_relative_strength,
    classify_relative_strength,
)


@dataclass(frozen=True)
class IntradayResult:
    symbol: str
    price: float
    momentum: float
    market_return: float
    relative_strength: float
    volume_ratio: float
    market_state: str
    momentum_state: str
    relative_strength_state: str
    volume_state: str
    volume_price_state: str
    score: float
    state: str
    reasons: list[str]


def _return(first: float, last: float) -> float:
    if first == 0:
        return 0.0
    return ((last - first) / first) * 100.0


def _momentum_state(value: float) -> str:
    if value >= 1.0:
        return "STRONG"
    if value >= 0.3:
        return "POSITIVE"
    if value <= -1.0:
        return "WEAK"
    if value <= -0.3:
        return "NEGATIVE"
    return "NEUTRAL"


def _market_state(value: float) -> str:
    if value >= 0.5:
        return "BULLISH"
    if value <= -0.5:
        return "BEARISH"
    return "NEUTRAL"


def _volume_state(ratio: float) -> str:
    if ratio >= 1.5:
        return "ACCELERATING"
    if ratio >= 1.1:
        return "ABOVE_AVERAGE"
    if ratio <= 0.7:
        return "WEAK"
    return "NORMAL"


def _get_time(value) -> str | None:
    if value is None:
        return None

    if hasattr(value, "strftime"):
        return value.strftime("%H:%M")

    if isinstance(value, str) and len(value) >= 16:
        return value[11:16]

    return None


def _calculate_volume_ratio(
    stock_rows: list[dict],
) -> float:
    if len(stock_rows) < 2:
        return 0.0

    latest = stock_rows[-1]

    latest_volume = float(
        latest.get("volume", 0)
    )

    latest_time = _get_time(
        latest.get("datetime")
    )

    historical_same_slot = []

    if latest_time is not None:
        for row in stock_rows[:-1]:
            row_time = _get_time(
                row.get("datetime")
            )

            if row_time == latest_time:
                historical_same_slot.append(
                    float(row.get("volume", 0))
                )

    if historical_same_slot:
        baseline_volume = (
            sum(historical_same_slot)
            / len(historical_same_slot)
        )
    else:
        previous_rows = stock_rows[-12:-1]

        if not previous_rows:
            return 0.0

        baseline_volume = (
            sum(
                float(row.get("volume", 0))
                for row in previous_rows
            )
            / len(previous_rows)
        )

    if baseline_volume <= 0:
        return 0.0

    return round(
        latest_volume / baseline_volume,
        2,
    )


def _volume_price_state(
    previous_close: float,
    latest_close: float,
    volume_ratio: float,
) -> str:
    if previous_close == 0:
        return "NEUTRAL"

    price_change = _return(
        previous_close,
        latest_close,
    )

    high_volume = volume_ratio >= 1.5

    if high_volume and price_change > 0:
        return "ACCUMULATION"

    if high_volume and price_change < 0:
        return "DISTRIBUTION"

    if volume_ratio < 1.1 and price_change > 0:
        return "WEAK_UPTREND"

    if volume_ratio < 1.1 and price_change < 0:
        return "WEAK_DOWNTREND"

    return "NEUTRAL"


def analyze_intraday(
    symbol: str,
    stock_rows: list[dict],
    market_rows: list[dict],
) -> IntradayResult:
    if len(stock_rows) < 12:
        raise ValueError(
            f"{symbol}: intraday data insufficient."
        )

    if len(market_rows) < 12:
        raise ValueError(
            "IHSG: intraday data insufficient."
        )

    stock_closes = [
        float(row["close"])
        for row in stock_rows
    ]

    market_closes = [
        float(row["close"])
        for row in market_rows
    ]

    momentum = _return(
        stock_closes[-12],
        stock_closes[-1],
    )

    market_return = _return(
        market_closes[-12],
        market_closes[-1],
    )

    relative_strength = calculate_relative_strength(
        momentum,
        market_return,
    )

    volume_ratio = _calculate_volume_ratio(
        stock_rows
    )

    volume_price_state = _volume_price_state(
        previous_close=stock_closes[-2],
        latest_close=stock_closes[-1],
        volume_ratio=volume_ratio,
    )

    market_state = _market_state(
        market_return
    )

    momentum_state = _momentum_state(
        momentum
    )

    relative_strength_state = (
        classify_relative_strength(
            relative_strength
        )
    )

    volume_state = _volume_state(
        volume_ratio
    )

    score = 0.0
    reasons = []

    if market_state == "BULLISH":
        score += 20
        reasons.append("ihsg_bullish")
    elif market_state == "BEARISH":
        score -= 20

    if momentum_state in {"POSITIVE", "STRONG"}:
        score += 30
        reasons.append("momentum_positive")
    elif momentum_state in {"NEGATIVE", "WEAK"}:
        score -= 30

    if relative_strength_state == "OUTPERFORMING":
        score += 30
        reasons.append(
            "relative_strength_outperforming"
        )
    elif relative_strength_state == "UNDERPERFORMING":
        score -= 30

    if volume_price_state == "ACCUMULATION":
        score += 20
        reasons.append(
            "volume_price_accumulation"
        )
    elif volume_price_state == "DISTRIBUTION":
        score -= 20
        reasons.append(
            "volume_price_distribution"
        )
    elif volume_state == "ABOVE_AVERAGE":
        score += 5
        reasons.append(
            "volume_above_average"
        )
    elif volume_state == "WEAK":
        score -= 10

    score = round(
        max(
            -100.0,
            min(100.0, score),
        ),
        2,
    )

    if (
        market_state != "BEARISH"
        and volume_price_state != "DISTRIBUTION"
        and score >= 60
        and len(reasons) >= 3
    ):
        state = "EARLY_BULLISH"
    elif score >= 35:
        state = "WATCH"
    else:
        state = "NORMAL"

    return IntradayResult(
        symbol=symbol,
        price=stock_closes[-1],
        momentum=round(momentum, 2),
        market_return=round(
            market_return,
            2,
        ),
        relative_strength=relative_strength,
        volume_ratio=volume_ratio,
        market_state=market_state,
        momentum_state=momentum_state,
        relative_strength_state=(
            relative_strength_state
        ),
        volume_state=volume_state,
        volume_price_state=(
            volume_price_state
        ),
        score=score,
        state=state,
        reasons=reasons,
    )
