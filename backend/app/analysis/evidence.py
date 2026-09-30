from dataclasses import dataclass
from datetime import date
from typing import Optional


@dataclass(frozen=True)
class Evidence:
    """
    Provenance metadata for one data component.

    V1 intentionally describes evidence without persisting
    additional database records.
    """

    component: str
    source: str
    as_of: date
    available: bool
    status: str
    detail: Optional[str] = None


def build_evidence(
    component: str,
    source: str,
    as_of: date,
    available: bool,
    status: str,
    detail: Optional[str] = None,
) -> Evidence:
    return Evidence(
        component=component,
        source=source,
        as_of=as_of,
        available=available,
        status=status,
        detail=detail,
    )


def determine_evidence_status(
    available: bool,
    coverage: float = 1.0,
) -> str:
    if not available:
        return "MISSING"

    if coverage >= 1.0:
        return "COMPLETE"

    if coverage > 0:
        return "PARTIAL"

    return "MISSING"