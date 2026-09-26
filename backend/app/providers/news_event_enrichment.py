from backend.app.providers.news import NewsEvent
from backend.app.providers.news_evidence import build_evidence_summary
from backend.app.providers.news_validation import validate_news_event


def attach_evidence_summary(
    event: NewsEvent,
) -> NewsEvent:
    validation_result = validate_news_event(event)

    event.evidence_summary = build_evidence_summary(
        validation_result
    )

    event.validation_status = validation_result.status

    return event
