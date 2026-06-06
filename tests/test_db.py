"""Testes da camada de banco de dados."""
import sqlite3
from datetime import datetime, timezone

import pytest

from pipeline.db import Database, ArticleStatus


@pytest.fixture
def db():
    """Database em memória para isolar testes."""
    return Database(":memory:")


def test_init_cria_tabelas(db):
    cursor = db.conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
    )
    tabelas = [row[0] for row in cursor.fetchall()]
    assert "articles" in tabelas
    assert "runs" in tabelas


def test_insere_e_busca_artigo(db):
    db.upsert_article(
        url="https://exemplo.com/noticia",
        source="bbc",
        language="en",
        title_orig="Test Article",
        published_at=datetime(2026, 6, 6, tzinfo=timezone.utc),
        status=ArticleStatus.PUBLISHING,
    )
    row = db.get_article("https://exemplo.com/noticia")
    assert row is not None
    assert row["source"] == "bbc"
    assert row["status"] == "publishing"


def test_filtra_urls_ja_vistos(db):
    db.upsert_article(
        url="https://a.com",
        source="bbc",
        language="en",
        title_orig="A",
        published_at=datetime(2026, 6, 6, tzinfo=timezone.utc),
        status=ArticleStatus.PUBLISHED,
    )
    novos = db.filter_new_urls(["https://a.com", "https://b.com"])
    assert novos == ["https://b.com"]


def test_atualiza_status(db):
    db.upsert_article(
        url="https://x.com",
        source="bbc",
        language="en",
        title_orig="X",
        published_at=datetime(2026, 6, 6, tzinfo=timezone.utc),
        status=ArticleStatus.PUBLISHING,
    )
    db.update_article_status(
        url="https://x.com",
        status=ArticleStatus.PUBLISHED,
        wp_post_id=42,
    )
    row = db.get_article("https://x.com")
    assert row["status"] == "published"
    assert row["wp_post_id"] == 42


def test_cria_e_finaliza_run(db):
    run_id = db.start_run()
    assert run_id > 0
    db.finish_run(run_id, fetched=10, published=8, skipped=2, failed=0, cost_usd=0.15)
    cursor = db.conn.execute("SELECT * FROM runs WHERE id = ?", (run_id,))
    row = dict(cursor.fetchone())
    assert row["published"] == 8
    assert row["cost_usd"] == 0.15
    assert row["finished_at"] is not None
