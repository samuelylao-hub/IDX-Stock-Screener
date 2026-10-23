from datetime import datetime
from zoneinfo import ZoneInfo

import pandas as pd

from backend.app.providers.intraday_yahoo import IntradayYahooProvider


def test_get_5m_uses_timeout_and_disables_threads(monkeypatch):
    calls = {}

    class FakeFrame:
        def iterrows(self):
            row = {
                "Open": pd.Series([100.0]),
                "High": pd.Series([102.0]),
                "Low": pd.Series([99.0]),
                "Close": pd.Series([101.0]),
                "Volume": pd.Series([1234]),
            }
            return iter([
                (datetime(2026, 10, 23, 10, 0, tzinfo=ZoneInfo("Asia/Jakarta")), row)
            ])

    def fake_download(ticker, **kwargs):
        calls["ticker"] = ticker
        calls.update(kwargs)
        return FakeFrame()

    monkeypatch.setattr(
        "backend.app.providers.intraday_yahoo.yf.download",
        fake_download,
    )

    rows = IntradayYahooProvider().get_5m("BBCA")

    assert calls["ticker"] == "BBCA.JK"
    assert calls["timeout"] == 15
    assert calls["threads"] is False
    assert rows[0]["close"] == 101.0
    assert rows[0]["volume"] == 1234
