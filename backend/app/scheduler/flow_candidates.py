"""Select ranked, price-fresh stocks for the limited flow-data quota."""

def select_flow_candidate_stocks(stocks, ranked_results, limit=5):
    """Return stock tuples in screener rank order, excluding skipped symbols."""
    if not stocks or not ranked_results or limit <= 0:
        return []

    stock_by_symbol = {symbol: (stock_id, symbol) for stock_id, symbol in stocks}
    selected = []
    seen = set()

    for result in ranked_results:
        symbol = getattr(result, "symbol", None)
        if not symbol or symbol in seen or symbol not in stock_by_symbol:
            continue
        if getattr(result, "signal", None) == "SKIP":
            continue
        if getattr(result, "market_status", "UNKNOWN") == "SUSPENDED":
            continue

        selected.append(stock_by_symbol[symbol])
        seen.add(symbol)
        if len(selected) >= limit:
            break

    return selected
