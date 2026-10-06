from backend.app.analysis.news_impact import determine_news_impact


def test_no_news_has_no_impact():
    result = determine_news_impact("NO_NEWS", "NONE")
    assert result.state == "NO_IMPACT"
    assert result.eligible is False


def test_unverified_news_has_no_impact():
    result = determine_news_impact("UNVERIFIED", "LOW")
    assert result.state == "NO_IMPACT"
    assert result.eligible is False


def test_reported_news_is_context_only():
    result = determine_news_impact("REPORTED", "MEDIUM")
    assert result.state == "CONTEXT_ONLY"
    assert result.eligible is False


def test_corroborated_news_is_impact_eligible():
    result = determine_news_impact("CORROBORATED", "MEDIUM_HIGH")
    assert result.state == "IMPACT_ELIGIBLE"
    assert result.eligible is True


def test_confirmed_news_is_impact_eligible():
    result = determine_news_impact("CONFIRMED", "HIGH")
    assert result.state == "IMPACT_ELIGIBLE"
    assert result.eligible is True


def test_conflicted_news_is_not_impact_eligible():
    result = determine_news_impact("CONFLICTED", "CONFLICTED")
    assert result.state == "CONFLICTED"
    assert result.eligible is False


def test_unknown_news_state_is_disabled():
    result = determine_news_impact("SOMETHING_NEW", "HIGH")
    assert result.state == "NO_IMPACT"
    assert result.eligible is False
