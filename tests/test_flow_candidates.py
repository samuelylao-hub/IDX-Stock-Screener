from types import SimpleNamespace

from backend.app.scheduler.flow_candidates import select_flow_candidate_stocks


def test_selects_top_ranked_eligible_symbols_in_rank_order():
    stocks = [(1, "BBCA"), (2, "BBRI"), (3, "BMRI"), (4, "WSKT")]
    ranked = [
        SimpleNamespace(symbol="WSKT", signal="SKIP", market_status="SUSPENDED"),
        SimpleNamespace(symbol="BBRI", signal="BUY", market_status="ACTIVE"),
        SimpleNamespace(symbol="BMRI", signal="WATCH", market_status="ACTIVE"),
        SimpleNamespace(symbol="BBCA", signal="BUY", market_status="ACTIVE"),
    ]

    assert select_flow_candidate_stocks(stocks, ranked, limit=2) == [
        (2, "BBRI"),
        (3, "BMRI"),
    ]


def test_empty_or_zero_limit_returns_no_candidates():
    assert select_flow_candidate_stocks([], [], limit=5) == []
    assert select_flow_candidate_stocks([(1, "BBCA")], [], limit=5) == []
    assert select_flow_candidate_stocks(
        [(1, "BBCA")],
        [SimpleNamespace(symbol="BBCA", signal="BUY")],
        limit=0,
    ) == []


def test_ignores_unknown_and_duplicate_symbols():
    stocks = [(1, "BBCA"), (2, "BBRI")]
    ranked = [
        SimpleNamespace(symbol="UNKNOWN", signal="BUY"),
        SimpleNamespace(symbol="BBRI", signal="BUY"),
        SimpleNamespace(symbol="BBRI", signal="BUY"),
        SimpleNamespace(symbol="BBCA", signal="BUY"),
    ]

    assert select_flow_candidate_stocks(stocks, ranked, limit=5) == [
        (2, "BBRI"),
        (1, "BBCA"),
    ]
