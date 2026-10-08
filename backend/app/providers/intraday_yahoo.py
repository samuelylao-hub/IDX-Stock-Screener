from __future__ import annotations

import yfinance as yf


class IntradayYahooProvider:
    def get_5m(self, symbol: str, period: str = "1d"):
        ticker = symbol if symbol.startswith("^") else f"{symbol}.JK"

        data = yf.download(
            ticker,
            period=period,
            interval="5m",
            progress=False,
            auto_adjust=False,
        )

        rows = []

        for dt, row in data.iterrows():
            rows.append(
                {
                    "datetime": dt,
                    "open": float(row["Open"].iloc[0]),
                    "high": float(row["High"].iloc[0]),
                    "low": float(row["Low"].iloc[0]),
                    "close": float(row["Close"].iloc[0]),
                    "volume": int(row["Volume"].iloc[0]),
                }
            )

        return rows