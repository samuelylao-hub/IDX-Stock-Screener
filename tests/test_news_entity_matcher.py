
from backend.app.providers.news_entity_matcher import (
    find_matching_symbols,
    matches_stock_entity,
)

def test_matches_symbol_with_market_context():
    assert matches_stock_entity("BBCA mencatat kenaikan laba", "BBCA", "Bank Central Asia Tbk")

def test_matches_company_name_with_market_context():
    assert matches_stock_entity("Bank Central Asia mencatat kenaikan laba", "BBCA", "Bank Central Asia Tbk")

def test_rejects_entity_mention_without_market_context():
    assert not matches_stock_entity("BBCA hadir dalam acara hiburan", "BBCA", "Bank Central Asia Tbk")

def test_rejects_unrelated_social_article():
    assert not matches_stock_entity("Bahaya YouTube bagi anak-anak", "BBCA", "Bank Central Asia Tbk")

def test_does_not_match_partial_symbol():
    assert not matches_stock_entity("ABCBBCAXYZ mencatat kenaikan laba", "BBCA", "Bank Central Asia Tbk")

def test_find_matching_symbols():
    stocks = [
        (1, "BBCA", "Bank Central Asia Tbk"),
        (2, "BBRI", "Bank Rakyat Indonesia (Persero) Tbk"),
    ]
    assert find_matching_symbols("Bank Central Asia mencatat kinerja positif", stocks) == ["BBCA"]
