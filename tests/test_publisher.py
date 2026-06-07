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


def _make_processed_com_imagem() -> ProcessedArticle:
    return ProcessedArticle(
        titulo_pt="Com imagem",
        resumo_pt="p1.\n\np2.\n\np3.",
        tags=["t"], categoria="Europa",
        source_url="https://bbc.com/x", source_name="bbc",
        cost_usd=0.01,
        image_url="https://bbc.com/img/hero.jpg",
    )


@pytest.mark.asyncio
async def test_publish_com_imagem_upload_sucesso(publisher):
    """Quando image_url existe, deve baixar, fazer upload e setar featured_media."""
    fake_image_bytes = b"\xff\xd8\xff" + b"x" * 5000  # fake JPEG bytes (>1000)

    chamadas = {"get": [], "post": []}

    async def fake_get(url, **kwargs):
        chamadas["get"].append(url)
        r = MagicMock()
        r.status_code = 200
        r.content = fake_image_bytes
        r.headers = {"content-type": "image/jpeg"}
        return r

    async def fake_post(url, **kwargs):
        chamadas["post"].append(url)
        r = MagicMock()
        r.status_code = 201
        if "/media" in url and url.endswith("/media"):
            r.json = MagicMock(return_value={"id": 99, "source_url": "https://wp/img.jpg"})
        elif "/media/" in url:
            # update alt_text — só responde OK
            r.json = MagicMock(return_value={"id": 99})
        elif "/posts" in url:
            chamadas["payload"] = kwargs.get("json")
            r.json = MagicMock(return_value={"id": 42, "link": "https://wp/post"})
        return r

    client_mock = MagicMock()
    client_mock.__aenter__ = AsyncMock(return_value=client_mock)
    client_mock.__aexit__ = AsyncMock(return_value=False)
    client_mock.get = AsyncMock(side_effect=fake_get)
    client_mock.post = AsyncMock(side_effect=fake_post)

    with patch("httpx.AsyncClient", return_value=client_mock):
        result = await publisher.publish(_make_processed_com_imagem())

    # baixou a imagem
    assert "https://bbc.com/img/hero.jpg" in chamadas["get"]
    # fez upload + criou post (e talvez update de alt_text)
    media_calls = [u for u in chamadas["post"] if "/media" in u and not u.endswith("media")]
    assert any("/wp/v2/media" in u for u in chamadas["post"])
    # post final usa featured_media
    assert chamadas["payload"]["featured_media"] == 99
    assert result.featured_media_id == 99


@pytest.mark.asyncio
async def test_publish_imagem_404_publica_sem_featured(publisher):
    """Se imagem retorna 404, publica post normalmente sem featured_media."""
    async def fake_get(url, **kwargs):
        r = MagicMock()
        r.status_code = 404
        return r

    chamadas_post = []

    async def fake_post(url, **kwargs):
        chamadas_post.append((url, kwargs.get("json")))
        r = MagicMock()
        r.status_code = 201
        r.json = MagicMock(return_value={"id": 1, "link": "x"})
        return r

    client_mock = MagicMock()
    client_mock.__aenter__ = AsyncMock(return_value=client_mock)
    client_mock.__aexit__ = AsyncMock(return_value=False)
    client_mock.get = AsyncMock(side_effect=fake_get)
    client_mock.post = AsyncMock(side_effect=fake_post)

    with patch("httpx.AsyncClient", return_value=client_mock):
        result = await publisher.publish(_make_processed_com_imagem())

    # post foi criado normalmente
    posts = [c for c in chamadas_post if "/wp/v2/posts" in c[0]]
    assert len(posts) == 1
    # mas sem featured_media (imagem falhou)
    assert "featured_media" not in posts[0][1]
    assert result.featured_media_id is None
    assert result.wp_post_id == 1


@pytest.mark.asyncio
async def test_publish_sem_image_url_pula_upload(publisher):
    """Se image_url é None, nem tenta baixar imagem."""
    chamadas_get = []

    async def fake_get(url, **kwargs):
        chamadas_get.append(url)
        r = MagicMock()
        r.status_code = 200
        return r

    async def fake_post(url, **kwargs):
        r = MagicMock()
        r.status_code = 201
        r.json = MagicMock(return_value={"id": 1, "link": "x"})
        return r

    client_mock = MagicMock()
    client_mock.__aenter__ = AsyncMock(return_value=client_mock)
    client_mock.__aexit__ = AsyncMock(return_value=False)
    client_mock.get = AsyncMock(side_effect=fake_get)
    client_mock.post = AsyncMock(side_effect=fake_post)

    with patch("httpx.AsyncClient", return_value=client_mock):
        result = await publisher.publish(_make_processed())  # sem image_url

    # nenhum GET pra baixar imagem
    assert chamadas_get == []
    assert result.featured_media_id is None
