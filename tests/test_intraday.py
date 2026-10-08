from backend.app.analysis.intraday import (
    analyze_intraday,
)


def _rows(closes, volumes=None):
    if volumes is None:
        volumes = [100] * len(closes)

    return [
        {
            "datetime": (
                f"2026-10-08 09:{i:02d}:00"
            ),
            "open": close,
            "high": close,
            "low": close,
            "close": close,
            "volume": volume,
        }
        for i, (close, volume)
        in enumerate(zip(closes, volumes))
    ]


def test_intraday_detects_early_bullish():
    stock = _rows(
        [100] * 9 + [101, 102, 103],
        [100] * 9 + [200, 200, 200],
    )

    market = _rows(
        [100] * 12,
        [100] * 12,
    )

    result = analyze_intraday(
        symbol="BBCA",
        stock_rows=stock,
        market_rows=market,
    )

    assert result.symbol == "BBCA"
    assert result.momentum > 0
    assert result.relative_strength > 0
    assert result.volume_ratio > 1
    assert result.volume_price_state == "ACCUMULATION"
    assert result.score > 0


def test_intraday_detects_weak_stock():
    stock = _rows(
        [100] * 9 + [99, 98, 97],
        [100] * 12,
    )

    market = _rows(
        [100] * 12,
        [100] * 12,
    )

    result = analyze_intraday(
        symbol="BBRI",
        stock_rows=stock,
        market_rows=market,
    )

    assert result.momentum < 0
    assert result.relative_strength < 0
    assert result.score < 0


def test_intraday_detects_distribution():
    stock = _rows(
        [100] * 11 + [99],
        [100] * 11 + [300],
    )

    market = _rows(
        [100] * 12,
        [100] * 12,
    )

    result = analyze_intraday(
        symbol="BBRI",
        stock_rows=stock,
        market_rows=market,
    )

    assert result.volume_ratio > 1.5
    assert (
        result.volume_price_state
        == "DISTRIBUTION"
    )


def test_intraday_detects_accumulation():
    stock = _rows(
        [100] * 11 + [101],
        [100] * 11 + [300],
    )

    market = _rows(
        [100] * 12,
        [100] * 12,
    )

    result = analyze_intraday(
        symbol="BBCA",
        stock_rows=stock,
        market_rows=market,
    )

    assert result.volume_ratio > 1.5
    assert (
        result.volume_price_state
        == "ACCUMULATION"
    )


def test_intraday_requires_enough_data():
    stock = _rows([100] * 5)
    market = _rows([100] * 12)

    try:
        analyze_intraday(
            symbol="BBCA",
            stock_rows=stock,
            market_rows=market,
        )
        assert False
    except ValueError:
        assert True
