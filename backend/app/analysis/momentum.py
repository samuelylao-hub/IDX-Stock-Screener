def calculate_momentum(closes: list[float]) -> float:
    if len(closes) < 2 or closes[0] == 0:
        return 0.0

    return round(
        ((closes[-1] - closes[0]) / closes[0]) * 100,
        2,
    )


def classify_momentum(momentum: float) -> str:
    if momentum >= 5:
        return "STRONG"
    if momentum >= 2:
        return "POSITIVE"
    if momentum <= -5:
        return "WEAK"
    if momentum <= -2:
        return "NEGATIVE"
    return "NEUTRAL"
