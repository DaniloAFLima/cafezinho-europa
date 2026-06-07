"""Publicação no WordPress via REST API."""
from __future__ import annotations

import base64
import logging
import mimetypes
import re
from dataclasses import dataclass
from urllib.parse import urlparse

import httpx
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from pipeline.processor import ProcessedArticle

logger = logging.getLogger(__name__)

# Limite defensivo: imagens não devem passar de 5MB (artigos não usam)
MAX_IMAGE_BYTES = 5_000_000


class PublisherError(Exception):
    """Falha ao publicar (após retries)."""


@dataclass(frozen=True)
class PublishResult:
    wp_post_id: int
    wp_url: str
    featured_media_id: int | None = None


def _slugify_filename(url: str) -> str:
    """Devolve um nome de arquivo decente a partir da URL da imagem."""
    path = urlparse(url).path or "/imagem.jpg"
    name = path.rsplit("/", 1)[-1] or "imagem"
    # remove query strings residuais e caracteres estranhos
    name = re.sub(r"[^a-zA-Z0-9._-]+", "-", name).strip("-")
    if not name or "." not in name:
        name = f"{name or 'imagem'}.jpg"
    return name[:120]  # limite de tamanho


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
        paragrafos = article.resumo_pt.split("\n\n")
        html_paragrafos = "\n".join(
            f"<p>{p.strip()}</p>" for p in paragrafos if p.strip()
        )
        tags_txt = ", ".join(article.tags)
        tags_html = f'<p><strong>Tags:</strong> {tags_txt}</p>'
        fonte = (
            f'<p><em>Fonte: '
            f'<a href="{article.source_url}" rel="noopener nofollow" '
            f'target="_blank">{article.source_name.upper()}</a></em></p>'
        )
        return f"{html_paragrafos}\n{tags_html}\n{fonte}"

    async def _upload_featured_image(
        self,
        client: httpx.AsyncClient,
        image_url: str,
        title: str,
    ) -> int | None:
        """Baixa a imagem da URL e faz upload pro WP Media Library.

        Retorna o media_id em caso de sucesso, ou None em qualquer falha
        (não derruba a publicação do post).
        """
        try:
            # 1. baixar imagem
            img_resp = await client.get(
                image_url,
                timeout=15.0,
                follow_redirects=True,
                headers={
                    "User-Agent": (
                        "Mozilla/5.0 (compatible; CafezinhoEuropaBot/1.0; "
                        "+https://cafezinhoeuropa.com)"
                    ),
                },
            )
            if img_resp.status_code != 200:
                logger.warning("Imagem indisponível (%d): %s", img_resp.status_code, image_url)
                return None

            content = img_resp.content
            if len(content) > MAX_IMAGE_BYTES:
                logger.warning("Imagem grande demais (%d bytes): %s", len(content), image_url)
                return None
            if len(content) < 1000:
                logger.warning("Imagem suspeitamente pequena (%d bytes): %s", len(content), image_url)
                return None

            # 2. inferir mime e nome do arquivo
            content_type = (
                img_resp.headers.get("content-type", "").split(";")[0].strip()
                or "image/jpeg"
            )
            ext = mimetypes.guess_extension(content_type) or ".jpg"
            filename = _slugify_filename(image_url)
            if not filename.lower().endswith(ext):
                filename = filename.rsplit(".", 1)[0] + ext

            # 3. upload pro WP /media
            upload_resp = await client.post(
                f"{self.base_url}/wp-json/wp/v2/media",
                headers={
                    "Authorization": self.auth_header,
                    "Content-Type": content_type,
                    "Content-Disposition": f'attachment; filename="{filename}"',
                },
                content=content,
                timeout=30.0,
            )
            if upload_resp.status_code not in (200, 201):
                logger.warning(
                    "Upload de imagem falhou (%d): %s",
                    upload_resp.status_code,
                    upload_resp.text[:200],
                )
                return None

            media_data = upload_resp.json()
            media_id = media_data["id"]

            # 4. (opcional) atualizar alt text com o título do post
            try:
                await client.post(
                    f"{self.base_url}/wp-json/wp/v2/media/{media_id}",
                    headers={
                        "Authorization": self.auth_header,
                        "Content-Type": "application/json",
                    },
                    json={"alt_text": title[:120]},
                    timeout=10.0,
                )
            except Exception:  # noqa: BLE001 — alt_text é nice-to-have, não bloqueia
                pass

            logger.info("Imagem enviada ao WP (media_id=%d): %s", media_id, image_url)
            return media_id

        except (httpx.HTTPError, httpx.TimeoutException) as e:
            logger.warning("Erro de rede baixando/enviando imagem %s: %s", image_url, e)
            return None
        except Exception as e:  # noqa: BLE001
            logger.exception("Erro inesperado processando imagem %s: %s", image_url, e)
            return None

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

        async with httpx.AsyncClient(timeout=30.0) as client:
            # 1. tenta upload da featured image (não bloqueia em caso de falha)
            featured_id: int | None = None
            if article.image_url:
                featured_id = await self._upload_featured_image(
                    client, article.image_url, article.titulo_pt
                )

            # 2. monta payload do post
            payload: dict = {
                "title": article.titulo_pt,
                "content": self._build_html(article),
                "status": "publish",
                "categories": [cat_id],
            }
            if featured_id is not None:
                payload["featured_media"] = featured_id

            # 3. cria o post
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
        return PublishResult(
            wp_post_id=data["id"],
            wp_url=data["link"],
            featured_media_id=featured_id,
        )
