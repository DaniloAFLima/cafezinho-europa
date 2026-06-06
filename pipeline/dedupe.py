"""Filtragem de artigos já processados."""
from __future__ import annotations

from pipeline.db import Database
from pipeline.fetcher import Article


def filter_unseen(db: Database, artigos: list[Article]) -> list[Article]:
    """Devolve apenas artigos cujos URLs nunca foram processados."""
    urls = [a.url for a in artigos]
    novos = set(db.filter_new_urls(urls))
    return [a for a in artigos if a.url in novos]
