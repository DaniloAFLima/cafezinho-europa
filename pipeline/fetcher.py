"""Busca de artigos em feeds RSS multi-idioma."""
from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import feedparser
import httpx
import yaml

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class Source:
    name: str
    url: str
    language: str
    default_category: str


@dataclass(frozen=True)
class Article:
    url: str
    source: str
    language: str
    title: str
    content: str
    published_at: datetime
    fetched_at: datetime
    default_category: str


def load_sources(path: str | Path = "config/sources.yaml") -> list[Source]:
    data = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    return [Source(**item) for item in data["sources"]]


def parse_feed(xml: str, source: Source) -> list[Article]:
    """Parse defensivo: nunca lança, devolve [] em qualquer erro."""
    try:
        parsed = feedparser.parse(xml)
        if parsed.bozo and not parsed.entries:
            return []
    except Exception as e:
        logger.warning("Falha ao parsear feed de %s: %s", source.name, e)
        return []

    artigos: list[Article] = []
    agora = datetime.now(timezone.utc)
    for entry in parsed.entries:
        url = entry.get("link", "").strip()
        title = entry.get("title", "").strip()
        if not url or not title:
            continue

        content = entry.get("summary", "") or entry.get("description", "")

        published_at = _extract_datetime(entry) or agora

        artigos.append(
            Article(
                url=url,
                source=source.name,
                language=source.language,
                title=title,
                content=content,
                published_at=published_at,
                fetched_at=agora,
                default_category=source.default_category,
            )
        )
    return artigos


def _extract_datetime(entry) -> datetime | None:
    parsed_time = entry.get("published_parsed") or entry.get("updated_parsed")
    if not parsed_time:
        return None
    try:
        return datetime(*parsed_time[:6], tzinfo=timezone.utc)
    except Exception:
        return None


async def _fetch_one(client: httpx.AsyncClient, source: Source) -> list[Article]:
    try:
        response = await client.get(source.url, timeout=10.0)
        if response.status_code != 200:
            logger.warning("Status %d ao buscar %s", response.status_code, source.name)
            return []
        return parse_feed(response.text, source)
    except (httpx.HTTPError, httpx.TimeoutException) as e:
        logger.warning("Erro de rede em %s: %s", source.name, e)
        return []


async def fetch_all(sources: list[Source]) -> list[Article]:
    async with httpx.AsyncClient(follow_redirects=True) as client:
        tasks = [_fetch_one(client, s) for s in sources]
        results = await asyncio.gather(*tasks, return_exceptions=False)
    return [a for grupo in results for a in grupo]
