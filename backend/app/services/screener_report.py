def format_screener_report(results, trade_date, news_by_symbol=None, alerts=None):
    lines = [
        f"IDX MARKET SCAN - {trade_date}",
        "",
    ]
    news_by_symbol = news_by_symbol or {}
    alerts = alerts or []
    alert_by_symbol = {alert.symbol: alert for alert in alerts}

    if not results:
        lines.append("Tidak ada hasil screening untuk tanggal ini.")
        return "\\n".join(lines)

    for i, result in enumerate(results, 1):
        lines.extend([
            f"#{i} {result.symbol}",
            f"Signal      : {result.signal}",
            f"Score       : {result.score}",
            f"Early Bull  : {result.early_bullish} ({result.early_bullish_score})",
            f"Rank Score  : {result.ranking_score}",
            f"Confidence  : {result.confidence}%",
            f"Quality     : {result.data_quality_status}",
            f"Foreign     : {getattr(result, 'foreign_state', 'UNKNOWN')}",
            f"Broker      : {getattr(result, 'broker_state', 'UNKNOWN')}",
            f"Price/Vol   : {getattr(result, 'price_volume_state', 'UNKNOWN')}",
        ])
        news = news_by_symbol.get(result.symbol)
        if news:
            lines.extend([
                f"News        : {news.get('title', 'Judul tidak tersedia')}",
                f"News time   : {news.get('published_at', 'Waktu tidak tersedia')}",
                f"News source : {news.get('source', 'Sumber tidak tersedia')}",
                f"News status : {news.get('validation_status', 'UNKNOWN')}",
                f"News impact : {news.get('evidence_strength', 'UNKNOWN')}",
                f"News link   : {news.get('url', 'Tidak tersedia')}",
            ])
        else:
            lines.append("News        : Tidak ada berita relevan terverifikasi dalam 3 hari terakhir.")
        alert = alert_by_symbol.get(result.symbol)
        if alert:
            lines.append(f"Alert       : {alert.level} / {alert.state}")
        lines.append("")

    return "\\n".join(lines)
