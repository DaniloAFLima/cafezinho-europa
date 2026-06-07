"""Extração de Open Graph image dos artigos originais."""
from __future__ import annotations

import asyncio
import logging
from urllib.parse import urljoin

import httpx
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

# limite de tamanho do HTML pra parsear (alguns sites devolvem 5MB+; só queremos as <meta>)
MAX_HTML_BYTES = 500_000
TIMEOUT_SECONDS = 10.0


def _extract_og_image(html: str, base_url: str) -> str | None:
    """Parseia HTML e devolve a URL absoluta da og:image, ou None."""
    soup = BeautifulSoup(html, "html.parser")

    # tenta vários metas em ordem de preferência
    candidatos = [
        soup.find("meta", property="og:image"),
        soup.find("meta", attrs={"name": "twitter:image"}),
        soup.find("meta", property="og:image:url"),
        soup.find("link", rel="image_src"),
    ]
    for tag in candidatos:
        if tag is None:
            continue
        url = tag.get("content") or tag.get("href")
        if not url:
            continue
        # resolve URL relativa contra a URL base do artigo
        return urljoin(base_url, url.strip())

    return None


async def fetch_og_image(client: httpx.AsyncClient, article_url: str) -> str | None:
    """Faz GET na URL do artigo e extrai og:image. Retorna None em qualquer erro."""
    try:
        response = await client.get(
            article_url,
            timeout=TIMEOUT_SECONDS,
            follow_redirects=True,
            headers={
                # alguns sites bloqueiam UA "python-httpx" — finge ser browser
                "User-Agent": (
                    "Mozilla/5.0 (compatible; CafezinhoEuropaBot/1.0; "
                    "+https://cafezinhoeuropa.com)"
                ),
                "Accept": "text/html,application/xhtml+xml",
            },
        )
        if response.status_code != 200:
            logger.debug("og_image: status %d para %s", response.status_code, article_url)
            return None

        # lê só o início do HTML — meta tags ficam no <head>
        html = response.text[:MAX_HTML_BYTES]
        return _extract_og_image(html, article_url)

    except (httpx.HTTPError, httpx.TimeoutException) as e:
        logger.debug("og_image: erro de rede em %s: %s", article_url, e)
        return None
    except Exception as e:  # noqa: BLE001
        logger.warning("og_image: erro inesperado em %s: %s", article_url, e)
        return None


async def fetch_og_images_batch(urls: list[str]) -> dict[str, str | None]:
    """Busca og:image em paralelo pra várias URLs. Retorna dict {url: image_url|None}."""
    async with httpx.AsyncClient() as client:
        tasks = [fetch_og_image(client, url) for url in urls]
        results = await asyncio.gather(*tasks, return_exceptions=False)
    return dict(zip(urls, results))
