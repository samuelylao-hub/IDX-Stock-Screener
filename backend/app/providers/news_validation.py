from dataclasses import dataclass

from backend.app.providers.news import NewsEvent, NewsSource
from backend.app.providers.news_relationship import (
    SOURCE_ROLE_INDEPENDENT,
    SOURCE_ROLE_OFFICIAL,
    SOURCE_ROLE_PRIMARY,
    create_source_relationship,
)


VALIDATION_NEW = "NEW"
VALIDATION_REPORTED = "REPORTED"
VALIDATION_UNDER_VERIFICATION = "UNDER_VERIFICATION"
VALIDATION_CORROBORATED = "CORROBORATED"
VALIDATION_OFFICIALLY_CONFIRMED = "OFFICIALLY_CONFIRMED"
VALIDATION_CONTRADICTED = "CONTRADICTED"
VALIDATION_UNVERIFIED = "UNVERIFIED"
VALIDATION_RETRACTED = "RETRACTED"


@dataclass
class ValidationResult:
    status: str
    reason: str
    official_source_count: int
    primary_source_count: int
    independent_source_count: int
    contradicting_source_count: int


def _get_source_relationship(source: NewsSource):
    return create_source_relationship(
        source_name=source.name,
        source_type=source.source_type,
        is_primary=source.is_primary,
        derived_from=source.derived_from,
    )


def validate_news_event(
    event: NewsEvent,
) -> ValidationResult:
    sources = event.sources or []

    if not sources:
        return ValidationResult(
            status=VALIDATION_NEW,
            reason="Belum ada sumber berita.",
            official_source_count=0,
            primary_source_count=0,
            independent_source_count=0,
            contradicting_source_count=0,
        )

    official_source_count = 0
    primary_source_count = 0
    independent_source_names = set()
    contradicting_source_names = set()

    for source in sources:
        relationship = _get_source_relationship(source)

        if relationship.source_role == SOURCE_ROLE_OFFICIAL:
            official_source_count += 1

        if relationship.source_role == SOURCE_ROLE_PRIMARY:
            primary_source_count += 1

        if relationship.source_role in {
            SOURCE_ROLE_INDEPENDENT,
            SOURCE_ROLE_PRIMARY,
        }:
            independent_source_names.add(
                source.name.casefold().strip()
            )

        if source.is_contradicting:
            contradicting_source_names.add(
                source.name.casefold().strip()
            )

    independent_source_count = len(independent_source_names)
    contradicting_source_count = len(contradicting_source_names)

    if official_source_count > 0:
        return ValidationResult(
            status=VALIDATION_OFFICIALLY_CONFIRMED,
            reason=(
                "Terdapat sumber regulator atau perusahaan resmi."
            ),
            official_source_count=official_source_count,
            primary_source_count=primary_source_count,
            independent_source_count=independent_source_count,
            contradicting_source_count=contradicting_source_count,
        )

    if contradicting_source_count > 0:
        return ValidationResult(
            status=VALIDATION_CONTRADICTED,
            reason=(
                "Terdapat sumber yang secara eksplisit "
                "membantah event dan belum ada sumber resmi "
                "yang menyelesaikan konflik."
            ),
            official_source_count=official_source_count,
            primary_source_count=primary_source_count,
            independent_source_count=independent_source_count,
            contradicting_source_count=contradicting_source_count,
        )

    if independent_source_count >= 2:
        return ValidationResult(
            status=VALIDATION_CORROBORATED,
            reason=(
                "Terdapat minimal dua sumber independen."
            ),
            official_source_count=official_source_count,
            primary_source_count=primary_source_count,
            independent_source_count=independent_source_count,
            contradicting_source_count=contradicting_source_count,
        )

    if independent_source_count == 1:
        return ValidationResult(
            status=VALIDATION_REPORTED,
            reason=(
                "Berita memiliki satu sumber independen."
            ),
            official_source_count=official_source_count,
            primary_source_count=primary_source_count,
            independent_source_count=independent_source_count,
            contradicting_source_count=contradicting_source_count,
        )

    return ValidationResult(
        status=VALIDATION_UNVERIFIED,
        reason=(
            "Belum terdapat sumber independen yang dapat "
            "digunakan untuk validasi."
        ),
        official_source_count=official_source_count,
        primary_source_count=primary_source_count,
        independent_source_count=independent_source_count,
        contradicting_source_count=contradicting_source_count,
    )
