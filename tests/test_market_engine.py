from backend.app.analysis.market_regime import determine_market_regime
from backend.app.analysis.momentum import (
    calculate_momentum,
    classify_momentum,
)
from backend.app.analysis.relative_strength import (
    calculate_relative_strength,
    classify_relative_strength,
)


def test_market_bullish():
    result = determine_market_regime(
        [100, 101, 102, 103, 105] * 5
    )
    assert result.state == "BULLISH"


def test_market_insufficient():
    result = determine_market_regime([100, 101, 102])
    assert result.state == "INSUFFICIENT_DATA"


def test_momentum():
    assert calculate_momentum([100, 105]) == 5.0
    assert classify_momentum(5) == "STRONG"


def test_relative_strength():
    assert calculate_relative_strength(8, 3) == 5
    assert classify_relative_strength(5) == "OUTPERFORMING"
