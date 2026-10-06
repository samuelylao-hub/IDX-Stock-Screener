from backend.app.analysis.news_signal import determine_news_signal


def test_no_news():
    result = determine_news_signal(0, None, None)
    assert result.state == "NO_NEWS"
    assert result.evidence_strength == "NONE"


def test_confirmed_news():
    result = determine_news_signal(
        1,
        "OFFICIALLY_CONFIRMED",
        "HIGH",
    )
    assert result.state == "CONFIRMED"
    assert result.evidence_strength == "HIGH"


def test_corroborated_news():
    result = determine_news_signal(
        2,
        "CORROBORATED",
        "MEDIUM_HIGH",
    )
    assert result.state == "CORROBORATED"
    assert result.evidence_strength == "MEDIUM_HIGH"


def test_reported_news():
    result = determine_news_signal(
        1,
        "REPORTED",
        "MEDIUM",
    )
    assert result.state == "REPORTED"
    assert result.evidence_strength == "MEDIUM"


def test_contradicted_news():
    result = determine_news_signal(
        2,
        "CONTRADICTED",
        "CONFLICTED",
    )
    assert result.state == "CONFLICTED"
    assert result.evidence_strength == "CONFLICTED"


def test_unverified_news():
    result = determine_news_signal(
        1,
        "UNVERIFIED",
        "LOW",
    )
    assert result.state == "UNVERIFIED"
    assert result.evidence_strength == "LOW"
