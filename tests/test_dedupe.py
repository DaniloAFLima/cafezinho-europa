"""Testes do filtro de duplicação."""
from datetime import datetime, timezone

import pytest

from pipeline.db import Database, ArticleStatus
from pipeline.dedupe import filter_unseen
from pipeline.fetcher import Article


def _artigo(url: str) -> Article:
    return Article(
        url=url,
        source="bbc",
        language="en",
        title="t",
        content="c",
        published_at=datetime(2026, 6, 6, tzinfo=timezone.utc),
        fetched_at=datetime(2026, 6, 6, tzinfo=timezone.utc),
        default_category="Europa",
    )


@pytest.fixture
def db():
    return Database(":memory:")


def test_filter_unseen_lista_vazia(db):
    assert filter_unseen(db, []) == []


def test_filter_unseen_todos_novos(db):
    artigos = [_artigo("https://a.com"), _artigo("https://b.com")]
    resultado = filter_unseen(db, artigos)
    assert len(resultado) == 2


def test_filter_unseen_remove_ja_vistos(db):
    db.upsert_article(
        url="https://a.com",
        source="bbc",
        language="en",
        title_orig="A",
        published_at=datetime(2026, 6, 6, tzinfo=timezone.utc),
        status=ArticleStatus.PUBLISHED,
    )
    artigos = [_artigo("https://a.com"), _artigo("https://b.com")]
    resultado = filter_unseen(db, artigos)
    assert len(resultado) == 1
    assert resultado[0].url == "https://b.com"
