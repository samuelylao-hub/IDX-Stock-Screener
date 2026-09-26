from backend.app.providers.news import NewsEvent


def save_news_event(connection, event: NewsEvent):
    evidence = event.evidence_summary

    if evidence is None:
        raise ValueError(
            "NewsEvent harus memiliki evidence_summary "
            "sebelum disimpan."
        )

    query = """
        INSERT INTO news_events (
            symbol,
            canonical_title,
            first_published_at,
            first_detected_at,
            importance,
            validation_status,
            source_count,
            official_source_count,
            primary_source_count,
            independent_source_count,
            contradicting_source_count,
            evidence_strength
        )
        VALUES (
            %s,
            %s,
            %s,
            %s,
            %s,
            %s,
            %s,
            %s,
            %s,
            %s,
            %s,
            %s
        )
        RETURNING id
    """

    with connection.cursor() as cursor:
        cursor.execute(
            query,
            (
                event.symbol,
                event.canonical_title,
                event.first_published_at,
                event.first_detected_at,
                event.importance,
                event.validation_status,
                event.source_count,
                evidence.official_source_count,
                evidence.primary_source_count,
                evidence.independent_source_count,
                evidence.contradicting_source_count,
                evidence.evidence_strength,
            ),
        )

        row = cursor.fetchone()

    connection.commit()

    return row[0]
