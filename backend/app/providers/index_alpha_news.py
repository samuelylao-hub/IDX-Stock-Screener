import os
import re
from datetime import datetime, timezone

import requests
from dotenv import load_dotenv

from backend.app.providers.news import NewsItem, NewsProvider

load_dotenv()


class IndexAlphaNewsProvider(NewsProvider):
    API_URL = "https://api.indexalpha.id/news"

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or os.getenv("INDEX_ALPHA_API_KEY")
        self._cache: list[NewsItem] | None = None

    @property
    def name(self) -> str:
        return "Index Alpha"

    def is_available(self) -> bool:
        return bool(self.api_key)

    def _fetch_news(self) -> list[NewsItem]:
        if self._cache is not None:
            return self._cache

        if not self.api_key:
            raise RuntimeError(
                "INDEX_ALPHA_API_KEY belum tersedia."
            )

        response = requests.get(
            self.API_URL,
            headers={
                "Authorization": f"Bearer {self.api_key}",
            },
            timeout=15,
        )
        response.raise_for_status()

        payload = response.json()
        data = payload.get("data", {})

        detected_at = datetime.now(timezone.utc)
        items: list[NewsItem] = []

        for source_name, articles in data.items():
            if not isinstance(articles, list):
                continue

            for article in articles:
                title = article.get("title")
                published_date = article.get("published_date")

                if not title or not published_date:
                    continue

                published_at = datetime.fromisoformat(
                    published_date.replace("Z", "+00:00")
                )

                description = article.get("description") or ""

                items.append(
                    NewsItem(
                        symbol=None,
                        title=title,
                        source=source_name,
                        published_at=published_at,
                        detected_at=detected_at,
                        url=article.get("link"),
                        description=description,
                    )
                )

        items.sort(
            key=lambda item: item.published_at,
            reverse=True,
        )

        self._cache = items
        return items

    @staticmethod
    def _matches_symbol(
        item: NewsItem,
        symbol: str,
    ) -> bool:
        pattern = rf"(?<![A-Z0-9]){re.escape(symbol.upper())}(?![A-Z0-9])"

        text = item.title.upper()

        return bool(re.search(pattern, text))

    def get_news(
        self,
        symbol: str | None = None,
        limit: int = 20,
    ) -> list[NewsItem]:
        items = self._fetch_news()

        if symbol:
            items = [
                item
                for item in items
                if self._matches_symbol(item, symbol)
            ]

        return items[:limit]
