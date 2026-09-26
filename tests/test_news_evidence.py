from backend.app.providers.news_evidence import EvidenceSummary


def run_test(name, summary):
    print(
        name,
        "=>",
        "status=",
        summary.status,
        "| strength=",
        summary.evidence_strength,
        "| official=",
        summary.has_official_confirmation,
        "| contradiction=",
        summary.has_contradiction,
    )


if __name__ == "__main__":

    run_test(
        "OFFICIALLY_CONFIRMED",
        EvidenceSummary(
            status="OFFICIALLY_CONFIRMED",
            reason="Official source available.",
            official_source_count=1,
            primary_source_count=1,
            independent_source_count=1,
            contradicting_source_count=0,
        ),
    )

    run_test(
        "CORROBORATED",
        EvidenceSummary(
            status="CORROBORATED",
            reason="Multiple independent sources.",
            official_source_count=0,
            primary_source_count=0,
            independent_source_count=2,
            contradicting_source_count=0,
        ),
    )

    run_test(
        "REPORTED",
        EvidenceSummary(
            status="REPORTED",
            reason="One independent source.",
            official_source_count=0,
            primary_source_count=0,
            independent_source_count=1,
            contradicting_source_count=0,
        ),
    )

    run_test(
        "CONTRADICTED",
        EvidenceSummary(
            status="CONTRADICTED",
            reason="Conflicting sources.",
            official_source_count=0,
            primary_source_count=0,
            independent_source_count=2,
            contradicting_source_count=1,
        ),
    )

    run_test(
        "UNVERIFIED",
        EvidenceSummary(
            status="UNVERIFIED",
            reason="Insufficient evidence.",
            official_source_count=0,
            primary_source_count=0,
            independent_source_count=0,
            contradicting_source_count=0,
        ),
    )
