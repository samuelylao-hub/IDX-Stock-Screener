from __future__ import annotations

from datetime import date, timedelta
import requests
import yfinance as yf


class BenchmarkProvider:
    IDX_URL = "https://www.idx.co.id/primary/TradingSummary/GetIndexSummary"

    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "X-Requested-With": "XMLHttpRequest",
        "Referer": "https://www.idx.co.id/",
        "Origin": "https://www.idx.co.id",
    }

    def _idx_day(self, trade_date: date):
        response = requests.get(
            self.IDX_URL,
            params={
                "lang": "id",
                "date": trade_date.strftime("%Y%m%d"),
                "start": 0,
                "length": 9999,
            },
            headers=self.HEADERS,
            timeout=15,
        )
        response.raise_for_status()
        payload = response.json()

        for row in payload.get("data", []):
            if row.get("IndexCode") in {"COMPOSITE", "IHSG"}:
                return {
                    "date": trade_date,
                    "open": row.get("Previous"),
                    "high": row.get("Highest"),
                    "low": row.get("Lowest"),
                    "close": row.get("Close"),
                    "volume": row.get("Volume"),
                    "value": row.get("Value"),
                    "frequency": row.get("Frequency"),
                    "source": "IDX",
                }

        return None

    def _yahoo(self, period: str = "3mo"):
        data = yf.download(
            "^JKSE",
            period=period,
            progress=False,
            auto_adjust=False,
        )

        rows = []

        for dt, row in data.iterrows():
            rows.append({
                "date": dt.date(),
                "open": float(row["Open"].iloc[0]),
                "high": float(row["High"].iloc[0]),
                "low": float(row["Low"].iloc[0]),
                "close": float(row["Close"].iloc[0]),
                "volume": int(row["Volume"].iloc[0]),
                "value": None,
                "frequency": None,
                "source": "YAHOO",
            })

        return rows

    def get_history(self, days: int = 30):
        # Primary: Yahoo Finance direct IHSG ticker.
        try:
            yahoo_rows = self._yahoo("3mo")
            if len(yahoo_rows) >= min(days, 5):
                return yahoo_rows[-days:]
        except Exception:
            pass

        # Fallback: IDX official endpoint.
        end = date.today()
        start_date = end - timedelta(days=max(days * 2, 45))
        idx_rows = []

        current = start_date
        while current <= end:
            if current.weekday() < 5:
                try:
                    row = self._idx_day(current)
                    if row:
                        idx_rows.append(row)
                except Exception:
                    pass
            current += timedelta(days=1)

        if len(idx_rows) >= min(days, 5):
            return idx_rows[-days:]

        raise RuntimeError(
            "IHSG benchmark unavailable from Yahoo and IDX."
        )
