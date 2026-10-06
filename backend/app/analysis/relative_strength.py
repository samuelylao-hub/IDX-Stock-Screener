def calculate_relative_strength(
    stock_return: float,
    market_return: float,
) -> float:
    return round(stock_return - market_return, 2)


def classify_relative_strength(value: float) -> str:
    if value >= 3:
        return "OUTPERFORMING"
    if value <= -3:
        return "UNDERPERFORMING"
    return "INLINE"
