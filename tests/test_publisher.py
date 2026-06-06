"""Testes do publisher de WordPress."""
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from pipeline.processor import ProcessedArticle
from pipeline.publisher import WordPressPublisher, PublishResult


def _make_processed() -> ProcessedArticle:
    return ProcessedArticle(
        titulo_pt="Brasil e UE assinam acordo",
        resumo_pt="Parágrafo 1.\n\nParágrafo 2.\n\nParágrafo 3.",
        tags=["brasil", "ue"],
        categoria="Europa",
        source_url="https://bbc.com/x",
        source_name="bbc",
        cost_usd=0.015,
    )


CATEGORY_MAP = {
    "Suécia": 2, "França": 3, "Alemanha": 4, "Espanha": 5,
    "Itália": 6, "Reino Unido": 7, "Europa": 8, "Mundo": 9,
}


@pytest.fixture
def publisher():
    return WordPressPublisher(
        base_url="https://cafezinhoeuropa.com",
        username="cafezinho-bot",
        app_password="xxxx xxxx xxxx xxxx xxxx xxxx",
        category_id_map=CATEGORY_MAP,
    )


@pytest.mark.asyncio
async def test_publish_sucesso(publisher):
    fake_response = MagicMock()
    fake_response.status_code = 201
    fake_response.json = MagicMock(return_value={"id": 42, "link": "https://x/post"})

    client_mock = MagicMock()
    client_mock.__aenter__ = AsyncMock(return_value=client_mock)
    client_mock.__aexit__ = AsyncMock(return_value=False)
    client_mock.post = AsyncMock(return_value=fake_response)

    with patch("httpx.AsyncClient", return_value=client_mock):
        result = await publisher.publish(_make_processed())

    assert isinstance(result, PublishResult)
    assert result.wp_post_id == 42
    assert result.wp_url == "https://x/post"


@pytest.mark.asyncio
async def test_publish_payload_inclui_fonte_e_categoria(publisher):
    fake_response = MagicMock()
    fake_response.status_code = 201
    fake_response.json = MagicMock(return_value={"id": 1, "link": "x"})

    captured = {}

    async def fake_post(url, **kwargs):
        captured["url"] = url
        captured["json"] = kwargs.get("json")
        return fake_response

    client_mock = MagicMock()
    client_mock.__aenter__ = AsyncMock(return_value=client_mock)
    client_mock.__aexit__ = AsyncMock(return_value=False)
    client_mock.post = AsyncMock(side_effect=fake_post)

    with patch("httpx.AsyncClient", return_value=client_mock):
        await publisher.publish(_make_processed())

    assert "wp-json/wp/v2/posts" in captured["url"]
    assert "Fonte:" in captured["json"]["content"]
    assert "https://bbc.com/x" in captured["json"]["content"]
    assert captured["json"]["categories"] == [8]


@pytest.mark.asyncio
async def test_publish_categoria_desconhecida_levanta(publisher):
    artigo = ProcessedArticle(
        titulo_pt="x", resumo_pt="a\n\nb\n\nc",
        tags=["x"], categoria="Categoria Que Não Existe",
        source_url="x", source_name="bbc", cost_usd=0.01,
    )
    from pipeline.publisher import PublisherError
    with pytest.raises(PublisherError, match="Categoria"):
        await publisher.publish(artigo)


@pytest.mark.asyncio
async def test_publish_erro_401_levanta(publisher):
    fake_response = MagicMock()
    fake_response.status_code = 401
    fake_response.text = "Unauthorized"

    client_mock = MagicMock()
    client_mock.__aenter__ = AsyncMock(return_value=client_mock)
    client_mock.__aexit__ = AsyncMock(return_value=False)
    client_mock.post = AsyncMock(return_value=fake_response)

    with patch("httpx.AsyncClient", return_value=client_mock):
        with pytest.raises(Exception, match="401"):
            await publisher.publish(_make_processed())
