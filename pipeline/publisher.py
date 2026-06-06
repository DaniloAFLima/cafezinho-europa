"""Publicação no WordPress via REST API."""
from __future__ import annotations

import base64
import logging
from dataclasses import dataclass

import httpx
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from pipeline.processor import ProcessedArticle

logger = logging.getLogger(__name__)


class PublisherError(Exception):
    """Falha ao publicar (após retries)."""


@dataclass(frozen=True)
class PublishResult:
    wp_post_id: int
    wp_url: str


class WordPressPublisher:
    def __init__(
        self,
        *,
        base_url: str,
        username: str,
        app_password: str,
        category_id_map: dict[str, int],
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.username = username
        self.app_password = app_password
        self.category_id_map = category_id_map
        token = base64.b64encode(f"{username}:{app_password}".encode()).decode()
        self.auth_header = f"Basic {token}"

    def _build_html(self, article: ProcessedArticle) -> str:
        # parágrafos do resumo
        paragrafos = article.resumo_pt.split("\n\n")
        html_paragrafos = "\n".join(
            f"<p>{p.strip()}</p>" for p in paragrafos if p.strip()
        )
        # tags como texto no rodapé (sem usar WP taxonomy para simplicidade)
        tags_txt = ", ".join(article.tags)
        tags_html = f'<p><strong>Tags:</strong> {tags_txt}</p>'
        # crédito da fonte (obrigatório por direitos autorais)
        fonte = (
            f'<p><em>Fonte: '
            f'<a href="{article.source_url}" rel="noopener nofollow" '
            f'target="_blank">{article.source_name.upper()}</a></em></p>'
        )
        return f"{html_paragrafos}\n{tags_html}\n{fonte}"

    @retry(
        retry=retry_if_exception_type((httpx.HTTPError, httpx.TimeoutException)),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=2, min=2, max=32),
        reraise=True,
    )
    async def publish(self, article: ProcessedArticle) -> PublishResult:
        cat_id = self.category_id_map.get(article.categoria)
        if cat_id is None:
            raise PublisherError(
                f"Categoria '{article.categoria}' não está no category_id_map. "
                f"Disponíveis: {sorted(self.category_id_map.keys())}"
            )

        payload = {
            "title": article.titulo_pt,
            "content": self._build_html(article),
            "status": "publish",
            "categories": [cat_id],
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{self.base_url}/wp-json/wp/v2/posts",
                headers={
                    "Authorization": self.auth_header,
                    "Content-Type": "application/json",
                },
                json=payload,
            )

        if response.status_code not in (200, 201):
            raise PublisherError(
                f"WordPress retornou {response.status_code}: {response.text[:200]}"
            )

        data = response.json()
        return PublishResult(wp_post_id=data["id"], wp_url=data["link"])
