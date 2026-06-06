"""Testes do processor (Claude API)."""
import json
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest

from pipeline.fetcher import Article
from pipeline.processor import (
    ProcessedArticle,
    process_article,
    ProcessorError,
)


def _make_article() -> Article:
    return Article(
        url="https://bbc.com/x",
        source="bbc",
        language="en",
        title="Brazil and EU sign new trade deal",
        content="The new agreement covers...",
        published_at=datetime(2026, 6, 6, tzinfo=timezone.utc),
        fetched_at=datetime(2026, 6, 6, tzinfo=timezone.utc),
        default_category="Europa",
    )


def _fake_claude_response(content_json: dict, usage_input=2000, usage_output=800):
    """Constrói uma resposta fake do Claude SDK."""
    msg = MagicMock()
    msg.content = [MagicMock(text=json.dumps(content_json))]
    msg.usage = MagicMock(input_tokens=usage_input, output_tokens=usage_output)
    return msg


@pytest.mark.asyncio
async def test_process_article_sucesso():
    artigo = _make_article()
    fake_resp = _fake_claude_response({
        "titulo_pt": "Brasil e UE assinam novo acordo comercial",
        "resumo_pt": "Saiu fresquinho hoje...\n\nO acordo cobre...\n\nO impacto pra brasileiros...",
        "tags": ["brasil", "ue", "comércio"],
        "categoria": "Europa",
    })

    with patch("pipeline.processor._call_claude", return_value=fake_resp):
        result = await process_article(artigo, client=MagicMock(), config={})

    assert isinstance(result, ProcessedArticle)
    assert result.titulo_pt == "Brasil e UE assinam novo acordo comercial"
    assert result.categoria == "Europa"
    assert "brasil" in result.tags
    assert result.source_url == "https://bbc.com/x"
    assert result.source_name == "bbc"
    assert result.cost_usd > 0


@pytest.mark.asyncio
async def test_process_article_json_malformado_levanta():
    artigo = _make_article()
    fake_resp = MagicMock()
    fake_resp.content = [MagicMock(text="isso não é JSON")]
    fake_resp.usage = MagicMock(input_tokens=2000, output_tokens=10)

    with patch("pipeline.processor._call_claude", return_value=fake_resp):
        with pytest.raises(ProcessorError):
            await process_article(artigo, client=MagicMock(), config={})


@pytest.mark.asyncio
async def test_process_article_categoria_invalida_levanta():
    artigo = _make_article()
    fake_resp = _fake_claude_response({
        "titulo_pt": "x",
        "resumo_pt": "a\n\nb\n\nc",
        "tags": ["x"],
        "categoria": "Categoria Inexistente",
    })

    with patch("pipeline.processor._call_claude", return_value=fake_resp):
        with pytest.raises(ProcessorError):
            await process_article(artigo, client=MagicMock(), config={})
