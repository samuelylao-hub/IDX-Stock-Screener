from datetime import time

from backend.app.analysis.intraday import analyze_intraday
from backend.app.providers.intraday_yahoo import IntradayYahooProvider


def _regular_session(rows):
    filtered = []

    for row in rows:
        dt = row["datetime"]

        if hasattr(dt, "time"):
            current_time = dt.time()
        else:
            current_time = time(
                dt.hour,
                dt.minute,
                dt.second,
            )

        if time(9, 0) <= current_time <= time(15, 45):
            filtered.append(row)

    return filtered


class IntradayScanner:
    def __init__(self, provider=None):
        self.provider = provider or IntradayYahooProvider()

    def scan(self, symbols: list[str]):
        market_rows = _regular_session(
            self.provider.get_5m("^JKSE")
        )

        results = []

        for symbol in symbols:
            try:
                stock_rows = _regular_session(
                    self.provider.get_5m(symbol)
                )

                if not stock_rows:
                    print(f"  {symbol}: NO_DATA - skipped")
                    continue

                result = analyze_intraday(
                    symbol=symbol,
                    stock_rows=stock_rows,
                    market_rows=market_rows,
                )

                results.append(result)

            except Exception as error:
                print(f"  {symbol}: ERROR - skipped ({error})")

        return sorted(
            results,
            key=lambda item: item.score,
            reverse=True,
        )
