from dataclasses import dataclass


@dataclass(frozen=True)
class RankingResult:
    symbol: str
    score: float
    early_bullish_score: float
    ranking_score: float


def calculate_ranking_score(
    score: float,
    early_bullish_score: float,
) -> float:
    value = (
        (score * 0.40)
        + (early_bullish_score * 0.60)
    )

    return round(
        max(-100.0, min(100.0, value)),
        2,
    )


def rank_screener_results(results):
    for result in results:
        result.ranking_score = calculate_ranking_score(
            result.score,
            result.early_bullish_score,
        )

    return sorted(
        results,
        key=lambda item: item.ranking_score,
        reverse=True,
    )
