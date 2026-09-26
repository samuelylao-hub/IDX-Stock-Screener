from backend.app.providers.news import NewsEvent, NewsSource


def save_news_event(connection, event: NewsEvent):
    evidence = event.evidence_summary

    if evidence is None:
        raise ValueError(
            "NewsEvent harus memiliki evidence_summary "
            "sebelum disimpan."
        )

    if event.event_key is None:
        raise ValueError(
            "NewsEvent harus memiliki event_key "
            "sebelum disimpan."
        )

    query = """
        INSERT INTO news_events (
            event_key,
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
            %s,
            %s
        )
        ON CONFLICT (event_key)
        DO UPDATE SET
            validation_status = EXCLUDED.validation_status,
            source_count = EXCLUDED.source_count,
            official_source_count = EXCLUDED.official_source_count,
            primary_source_count = EXCLUDED.primary_source_count,
            independent_source_count = EXCLUDED.independent_source_count,
            contradicting_source_count = EXCLUDED.contradicting_source_count,
            evidence_strength = EXCLUDED.evidence_strength,
            updated_at = NOW()
        RETURNING id
    """

    with connection.cursor() as cursor:
        cursor.execute(
            query,
            (
                event.event_key,
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


def save_news_event_source(
    connection,
    news_event_id: int,
    source: NewsSource,
):
    query = """
        INSERT INTO news_event_sources (
            news_event_id,
            source_name,
            source_type,
            source_tier,
            country,
            url,
            published_at,
            detected_at,
            is_primary,
            is_contradicting,
            source_role,
            derived_from,
            relationship_note
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
            %s,
            %s
        )
        ON CONFLICT (
            news_event_id,
            source_name,
            url
        )
        DO UPDATE SET
            source_type = EXCLUDED.source_type,
            source_tier = EXCLUDED.source_tier,
            country = EXCLUDED.country,
            published_at = EXCLUDED.published_at,
            detected_at = EXCLUDED.detected_at,
            is_primary = EXCLUDED.is_primary,
            is_contradicting = EXCLUDED.is_contradicting,
            source_role = EXCLUDED.source_role,
            derived_from = EXCLUDED.derived_from,
            relationship_note = EXCLUDED.relationship_note
        RETURNING id
    """

    with connection.cursor() as cursor:
        cursor.execute(
            query,
            (
                news_event_id,
                source.name,
                source.source_type,
                source.source_tier,
                source.country,
                source.url,
                source.published_at,
                source.detected_at,
                source.is_primary,
                source.is_contradicting,
                source.source_role,
                source.derived_from,
                source.relationship_note,
            ),
        )

        row = cursor.fetchone()

    connection.commit()

    return row[0]