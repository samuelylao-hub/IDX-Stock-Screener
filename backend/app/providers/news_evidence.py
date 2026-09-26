from dataclasses import dataclass


@dataclass
class EvidenceSummary:
    status: str
    reason: str
    official_source_count: int
    primary_source_count: int
    independent_source_count: int
    contradicting_source_count: int

    @property
    def has_official_confirmation(self) -> bool:
        return self.official_source_count > 0

    @property
    def has_contradiction(self) -> bool:
        return self.contradicting_source_count > 0

    @property
    def evidence_strength(self) -> str:
        if self.status == "OFFICIALLY_CONFIRMED":
            return "HIGH"

        if self.status == "CORROBORATED":
            return "MEDIUM_HIGH"

        if self.status == "REPORTED":
            return "MEDIUM"

        if self.status == "CONTRADICTED":
            return "CONFLICTED"

        return "LOW"


def build_evidence_summary(validation_result) -> EvidenceSummary:
    return EvidenceSummary(
        status=validation_result.status,
        reason=validation_result.reason,
        official_source_count=validation_result.official_source_count,
        primary_source_count=validation_result.primary_source_count,
        independent_source_count=validation_result.independent_source_count,
        contradicting_source_count=validation_result.contradicting_source_count,
    )
