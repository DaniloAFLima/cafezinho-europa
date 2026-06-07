"""Testes do módulo og_image."""
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from pipeline.og_image import _extract_og_image, fetch_og_image, fetch_og_images_batch


# ───── _extract_og_image (sync) ─────

def test_extract_og_image_basico():
    html = """
    <html><head>
      <meta property="og:image" content="https://example.com/img.jpg">
    </head></html>
    """
    assert _extract_og_image(html, "https://example.com/article") == "https://example.com/img.jpg"


def test_extract_og_image_relativa_resolvida():
    html = '<meta property="og:image" content="/img/hero.jpg">'
    result = _extract_og_image(html, "https://bbc.com/news/123")
    assert result == "https://bbc.com/img/hero.jpg"


def test_extract_og_image_twitter_fallback():
    """Se og:image não existir, usa twitter:image."""
    html = '<meta name="twitter:image" content="https://x.com/twit.jpg">'
    assert _extract_og_image(html, "http://x") == "https://x.com/twit.jpg"


def test_extract_og_image_sem_meta_devolve_none():
    html = "<html><head><title>sem imagem</title></head></html>"
    assert _extract_og_image(html, "http://x") is None


def test_extract_og_image_html_quebrado_nao_explode():
    # lxml é tolerante, BeautifulSoup também
    assert _extract_og_image("<<broken>>>><html", "http://x") is None


def test_extract_og_image_meta_vazia():
    html = '<meta property="og:image" content="">'
    assert _extract_og_image(html, "http://x") is None


# ───── fetch_og_image (async, com mock de httpx) ─────

@pytest.mark.asyncio
async def test_fetch_og_image_sucesso():
    fake_response = MagicMock()
    fake_response.status_code = 200
    fake_response.text = '<meta property="og:image" content="https://example.com/pic.jpg">'

    client = MagicMock()
    client.get = AsyncMock(return_value=fake_response)

    result = await fetch_og_image(client, "https://example.com/article")
    assert result == "https://example.com/pic.jpg"


@pytest.mark.asyncio
async def test_fetch_og_image_status_404_devolve_none():
    fake_response = MagicMock()
    fake_response.status_code = 404

    client = MagicMock()
    client.get = AsyncMock(return_value=fake_response)

    result = await fetch_og_image(client, "https://example.com/x")
    assert result is None


@pytest.mark.asyncio
async def test_fetch_og_image_timeout_devolve_none():
    client = MagicMock()
    client.get = AsyncMock(side_effect=httpx.TimeoutException("timeout"))

    result = await fetch_og_image(client, "https://example.com/x")
    assert result is None


@pytest.mark.asyncio
async def test_fetch_og_image_http_error_devolve_none():
    client = MagicMock()
    client.get = AsyncMock(side_effect=httpx.HTTPError("conexao recusada"))

    result = await fetch_og_image(client, "https://example.com/x")
    assert result is None


# ───── fetch_og_images_batch (paralelo) ─────

@pytest.mark.asyncio
async def test_fetch_og_images_batch_paralelo():
    """3 URLs, mockando httpx.AsyncClient.get."""
    htmls = {
        "https://a.com/1": '<meta property="og:image" content="https://a.com/img1.jpg">',
        "https://b.com/2": '<meta property="og:image" content="https://b.com/img2.jpg">',
        "https://c.com/3": "<html>no meta tags</html>",
    }

    async def fake_get(self, url, **kwargs):
        r = MagicMock()
        r.status_code = 200
        r.text = htmls.get(url, "")
        return r

    with patch("httpx.AsyncClient.get", new=fake_get):
        result = await fetch_og_images_batch(list(htmls.keys()))

    assert result["https://a.com/1"] == "https://a.com/img1.jpg"
    assert result["https://b.com/2"] == "https://b.com/img2.jpg"
    assert result["https://c.com/3"] is None


@pytest.mark.asyncio
async def test_fetch_og_images_batch_lista_vazia():
    result = await fetch_og_images_batch([])
    assert result == {}
