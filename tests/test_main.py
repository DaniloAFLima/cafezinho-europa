"""Testes do orquestrador main."""
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from pipeline.fetcher import Article
from pipeline.main import run_pipeline


def _make_article(url: str) -> Article:
    return Article(
        url=url,
        source="bbc",
        language="en",
        title="Brazilian immigration to EU rises",
        content="The number of Brazilians moving to the EU has increased...",
        published_at=datetime.now(timezone.utc),
        fetched_at=datetime.now(timezone.utc),
        default_category="Europa",
    )


@pytest.mark.asyncio
async def test_pipeline_dry_run_nao_publica(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "fake")
    artigos = [_make_article(f"https://x/{i}") for i in range(3)]

    with patch("pipeline.main.fetch_all", new=AsyncMock(return_value=artigos)), \
         patch("pipeline.main.load_sources", return_value=[]), \
         patch("pipeline.main.process_article", new=AsyncMock()) as mock_proc, \
         patch("pipeline.main.WordPressPublisher") as mock_pub_cls:

        mock_proc.return_value = MagicMock(
            titulo_pt="t", resumo_pt="a\n\nb\n\nc",
            tags=["x"], categoria="Europa",
            source_url="x", source_name="bbc", cost_usd=0.01,
        )

        summary = await run_pipeline(
            db_path=":memory:",
            dry_run=True,
        )

    mock_pub_cls.assert_not_called()
    assert summary["published"] == 0
    assert summary["processed"] >= 1


@pytest.mark.asyncio
async def test_pipeline_uma_falha_no_processor_nao_derruba_outros(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "fake")
    artigos = [_make_article(f"https://x/{i}") for i in range(3)]

    from pipeline.processor import ProcessorError

    async def fake_process(article, **kwargs):
        if "1" in article.url:
            raise ProcessorError("simulado")
        return MagicMock(
            titulo_pt="t", resumo_pt="a\n\nb\n\nc",
            tags=["x"], categoria="Europa",
            source_url=article.url, source_name="bbc", cost_usd=0.01,
        )

    with patch("pipeline.main.fetch_all", new=AsyncMock(return_value=artigos)), \
         patch("pipeline.main.load_sources", return_value=[]), \
         patch("pipeline.main.process_article", new=fake_process):

        summary = await run_pipeline(
            db_path=":memory:",
            dry_run=True,
        )

    assert summary["failed"] == 1
    assert summary["processed"] >= 2


@pytest.mark.asyncio
async def test_pipeline_dedupe_evita_reprocessar(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "fake")
    from pipeline.db import Database, ArticleStatus

    db = Database(":memory:")
    db.upsert_article(
        url="https://x/repetido",
        source="bbc", language="en", title_orig="t",
        published_at=datetime.now(timezone.utc),
        status=ArticleStatus.PUBLISHED,
    )

    artigos = [_make_article("https://x/repetido"), _make_article("https://x/novo")]

    with patch("pipeline.main.fetch_all", new=AsyncMock(return_value=artigos)), \
         patch("pipeline.main.load_sources", return_value=[]), \
         patch("pipeline.main.process_article", new=AsyncMock()) as mock_proc:
        mock_proc.return_value = MagicMock(
            titulo_pt="t", resumo_pt="a\n\nb\n\nc",
            tags=["x"], categoria="Europa",
            source_url="https://x/novo", source_name="bbc", cost_usd=0.01,
        )

        summary = await run_pipeline(
            db=db,
            dry_run=True,
        )

    # processou apenas 1 (o novo)
    assert mock_proc.call_count == 1
