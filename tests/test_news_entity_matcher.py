from backend.app.providers.news_entity_matcher import (
    find_matching_symbols,
    matches_stock_entity,
)


def test_matches_symbol():
    assert matches_stock_entity(
        "BBCA mencatat kenaikan laba",
        "BBCA",
        "Bank Central Asia Tbk",
    )


def test_matches_company_name():
    assert matches_stock_entity(
        "Bank Central Asia mencatat kenaikan laba",
        "BBCA",
        "Bank Central Asia Tbk",
    )


def test_does_not_match_partial_symbol():
    assert not matches_stock_entity(
        "ABCBBCAXYZ mencatat kenaikan",
        "BBCA",
        "Bank Central Asia Tbk",
    )


def test_find_matching_symbols():
    stocks = [
        (1, "BBCA", "Bank Central Asia Tbk"),
        (2, "BBRI", "Bank Rakyat Indonesia (Persero) Tbk"),
    ]

    result = find_matching_symbols(
        "Bank Central Asia mencatat kinerja positif",
        stocks,
    )

    assert result == ["BBCA"]
