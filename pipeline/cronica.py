"""Coluna semanal 'Cafezinho & Planeta, Urgente!' — listar notícias e agendar a crônica."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import httpx
import markdown as _markdown
from bs4 import BeautifulSoup

HORA_PUBLICACAO_UTC = 8  # domingo, 08:00 UTC


class CronicaError(Exception):
    """Falha ao listar ou agendar a crônica."""


def proximo_domingo(agora: datetime) -> datetime:
    """Próximo domingo 08:00 UTC estritamente futuro.

    Se `agora` já é domingo, devolve o domingo seguinte — a edição da semana
    já está no ar.
    """
    dias_ate = (6 - agora.weekday()) % 7  # weekday(): segunda=0 ... domingo=6
    if dias_ate == 0:
        dias_ate = 7
    candidato = agora + timedelta(days=dias_ate)
    return candidato.replace(hour=HORA_PUBLICACAO_UTC, minute=0, second=0, microsecond=0)


def md_para_html(texto_md: str) -> str:
    """Converte o Markdown da crônica para HTML pronto para o WordPress."""
    return _markdown.markdown(texto_md, extensions=["extra"])


def _strip_html(html: str) -> str:
    """Remove tags e decodifica entidades (títulos/excerpts vêm em HTML do WP)."""
    return BeautifulSoup(html, "html.parser").get_text()


PER_PAGE = 50


def listar_posts(client: httpx.Client, base_url: str, *, dias: int = 7) -> list[dict]:
    """Posts publicados nos últimos `dias` dias, via WP REST pública (sem credenciais)."""
    after = (datetime.now(timezone.utc) - timedelta(days=dias)).isoformat()
    resp = client.get(
        f"{base_url.rstrip('/')}/wp-json/wp/v2/posts",
        params={
            "after": after,
            "per_page": PER_PAGE,
            "orderby": "date",
            "order": "desc",
            "_fields": "id,date,link,title,excerpt,categories",
        },
        timeout=30.0,
    )
    resp.raise_for_status()
    return [
        {
            "id": p["id"],
            "date": p["date"],
            "link": p["link"],
            "titulo": _strip_html(p["title"]["rendered"]).strip(),
            "resumo": _strip_html(p["excerpt"]["rendered"]).strip(),
        }
        for p in resp.json()
    ]


def agendar_cronica(
    client: httpx.Client,
    *,
    base_url: str,
    auth_header: str,
    titulo: str,
    html: str,
    categoria_id: int,
    quando: datetime,
    featured_media_id: int | None = None,
) -> dict:
    """Cria o post da crônica com status `future` (o WordPress publica sozinho)."""
    payload: dict = {
        "title": titulo,
        "content": html,
        "status": "future",
        "date_gmt": quando.strftime("%Y-%m-%dT%H:%M:%S"),
        "categories": [categoria_id],
    }
    if featured_media_id is not None:
        payload["featured_media"] = featured_media_id

    resp = client.post(
        f"{base_url.rstrip('/')}/wp-json/wp/v2/posts",
        headers={"Authorization": auth_header, "Content-Type": "application/json"},
        json=payload,
        timeout=30.0,
    )
    if resp.status_code not in (200, 201):
        raise CronicaError(f"WordPress retornou {resp.status_code}: {resp.text[:200]}")
    return resp.json()
