from dataclasses import dataclass


@dataclass(frozen=True)
class NewsImpact:
    state: str
    eligible: bool
    detail: str


def determine_news_impact(
    news_state: str,
    evidence_strength: str,
) -> NewsImpact:
    state = (news_state or "").upper()
    strength = (evidence_strength or "").upper()

    if state == "NO_NEWS":
        return NewsImpact(
            state="NO_IMPACT",
            eligible=False,
            detail="No relevant news event.",
        )

    if state == "UNVERIFIED":
        return NewsImpact(
            state="NO_IMPACT",
            eligible=False,
            detail="News evidence is not sufficiently verified.",
        )

    if state == "REPORTED":
        return NewsImpact(
            state="CONTEXT_ONLY",
            eligible=False,
            detail="Reported news is context only.",
        )

    if state in {"CORROBORATED", "CONFIRMED"}:
        return NewsImpact(
            state="IMPACT_ELIGIBLE",
            eligible=True,
            detail=(
                f"News impact eligible with "
                f"{strength or 'UNKNOWN'} evidence."
            ),
        )

    if state == "CONFLICTED":
        return NewsImpact(
            state="CONFLICTED",
            eligible=False,
            detail="Conflicting news evidence requires caution.",
        )

    return NewsImpact(
        state="NO_IMPACT",
        eligible=False,
        detail="Unknown news state; impact disabled.",
    )
