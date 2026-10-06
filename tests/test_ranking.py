from backend.app.analysis.ranking import calculate_ranking_score


def test_ranking_favors_early_bullish():
    score = calculate_ranking_score(
        score=20,
        early_bullish_score=80,
    )

    assert score == 56.0


def test_ranking_favors_confirmed_signal():
    score = calculate_ranking_score(
        score=80,
        early_bullish_score=20,
    )

    assert score == 44.0


def test_ranking_clamped():
    assert calculate_ranking_score(100, 100) == 100.0
    assert calculate_ranking_score(-100, -100) == -100.0
