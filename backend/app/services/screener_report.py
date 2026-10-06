def format_screener_report(results, trade_date):
    lines = [
        f"IDX MARKET SCAN - {trade_date}",
        "",
    ]

    for i, result in enumerate(results, 1):
        lines.extend([
            f"#{i} {result.symbol}",
            f"Signal      : {result.signal}",
            f"Score       : {result.score}",
            f"Early Bull  : {result.early_bullish} ({result.early_bullish_score})",
            f"Rank Score  : {result.ranking_score}",
            f"Confidence  : {result.confidence}%",
            f"Quality     : {result.data_quality_status}",
            "",
        ])

    return "\n".join(lines)
