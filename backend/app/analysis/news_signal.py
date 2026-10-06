from dataclasses import dataclass


@dataclass(frozen=True)
class NewsSignal:
    state: str
    evidence_strength: str
    event_count: int
    detail: str


def determine_news_signal(
    event_count: int,
    validation_status: str | None,
    evidence_strength: str | None,
) -> NewsSignal:
    if event_count <= 0:
        return NewsSignal(
            state="NO_NEWS",
            evidence_strength="NONE",
            event_count=0,
            detail="No relevant news event.",
        )

    status = (validation_status or "").upper()
    strength = (evidence_strength or "").upper()

    if status == "CONTRADICTED":
        return NewsSignal(
            state="CONFLICTED",
            evidence_strength="CONFLICTED",
            event_count=event_count,
            detail="News evidence contains contradiction.",
        )

    if status == "OFFICIALLY_CONFIRMED":
        return NewsSignal(
            state="CONFIRMED",
            evidence_strength="HIGH",
            event_count=event_count,
            detail="News event is officially confirmed.",
        )

    if status == "CORROBORATED":
        return NewsSignal(
            state="CORROBORATED",
            evidence_strength="MEDIUM_HIGH",
            event_count=event_count,
            detail="News event is corroborated by independent sources.",
        )

    if status == "REPORTED":
        return NewsSignal(
            state="REPORTED",
            evidence_strength="MEDIUM",
            event_count=event_count,
            detail="News event has one independent report.",
        )

    return NewsSignal(
        state="UNVERIFIED",
        evidence_strength=strength or "LOW",
        event_count=event_count,
        detail="News event exists but is not sufficiently verified.",
    )
