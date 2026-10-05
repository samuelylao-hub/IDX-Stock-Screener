from backend.app.providers.news import (
    NewsEvent,
    NewsItem,
    build_event_key,
    create_news_event,
)
from backend.app.providers.news_entity_matcher import (
    find_matching_symbols,
)
from backend.app.providers.news_event_enrichment import (
    attach_evidence_summary,
)
from backend.app.providers.news_relationship import (
    apply_source_relationship,
    create_source_relationship,
)
from backend.app.providers.news_repository import (
    save_news_event,
    save_news_event_source,
)
from src.db.stocks import get_all_stocks


class NewsIngestionService:
    def __init__(
        self,
        provider,
        stocks=None,
        connection=None,
    ):
        self.provider = provider
        self.stocks = (
            stocks
            if stocks is not None
            else get_all_stocks()
        )
        self.connection = connection

    def ingest(
        self,
        limit: int = 100,
    ) -> int:
        items = self.provider.get_news(
            limit=limit,
        )

        events: dict[str, NewsEvent] = {}

        for item in items:
            match_text = " ".join(
                part
                for part in (
                    item.title,
                    item.description,
                )
                if part
            )

            matches = find_matching_symbols(
                match_text,
                self.stocks,
            )

            for symbol in matches:
                symbol_item = NewsItem(
                    symbol=symbol,
                    title=item.title,
                    source=item.source,
                    published_at=item.published_at,
                    detected_at=item.detected_at,
                    url=item.url,
                    category=item.category,
                    importance=item.importance,
                    source_tier=item.source_tier,
                    validation_status=item.validation_status,
                    description=item.description,
                )

                event_key = (
                    f"{symbol.casefold()}|"
                    f"{symbol_item.title.casefold().strip()}"
                )

                if event_key not in events:
                    events[event_key] = create_news_event(
                        symbol_item
                    )
                    continue

                existing_event = events[event_key]

                if existing_event.sources is None:
                    existing_event.sources = []

                source = create_news_event(
                    symbol_item
                ).sources[0]

                existing_event.sources.append(source)
                existing_event.source_count = len(
                    existing_event.sources
                )

        if self.connection is None:
            return len(events)

        saved_count = 0

        for event in events.values():
            for source in event.sources or []:
                relationship = create_source_relationship(
                    source_name=source.name,
                    source_type=source.source_type,
                    is_primary=source.is_primary,
                    derived_from=source.derived_from,
                )

                apply_source_relationship(
                    source,
                    relationship,
                )

            attach_evidence_summary(event)

            event_id = save_news_event(
                self.connection,
                event,
            )

            for source in event.sources or []:
                save_news_event_source(
                    self.connection,
                    event_id,
                    source,
                )

            saved_count += 1

        return saved_count
