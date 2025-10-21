from __future__ import annotations
import feedparser
from datetime import datetime, timezone

DEFAULT_FEEDS = [
    "https://feeds.reuters.com/reuters/businessNews",
    "https://www.ft.com/?format=rss",
]

def get_headlines(max_items: int = 6, feeds: list[str] | None = None):
    feeds = feeds or DEFAULT_FEEDS
    items = []
    for url in feeds:
        try:
            d = feedparser.parse(url)
            for e in d.entries[: max_items // len(feeds) + 1]:
                items.append({
                    "title": e.get("title", "n/a"),
                    "source": d.feed.get("title", "RSS"),
                    "url": e.get("link", ""),
                    "published": e.get("published", datetime.now(timezone.utc).isoformat()),
                })
        except Exception:
            continue
    seen, deduped = set(), []
    for it in items:
        if it["title"] in seen:
            continue
        seen.add(it["title"])
        deduped.append(it)
    return deduped[:max_items]
