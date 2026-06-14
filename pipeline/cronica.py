"""Coluna semanal 'Cafezinho & Planeta, Urgente!' — listar notícias e agendar a crônica."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import argparse
import base64
import os
import sys
from pathlib import Path

import httpx
import markdown as _markdown
import yaml
from bs4 import BeautifulSoup
from dotenv import load_dotenv

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


def carregar_config(
    cronica_yaml: str | Path = "config/cronica.yaml",
    categorias_yaml: str | Path = "config/wp_categories.yaml",
) -> dict:
    """Resolve a categoria da coluna para o ID do WP. Erro claro se não mapeada."""
    with open(cronica_yaml, encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    with open(categorias_yaml, encoding="utf-8") as f:
        categorias = yaml.safe_load(f)["categories"]

    categoria_id = categorias.get(cfg["categoria"])
    if categoria_id is None:
        raise CronicaError(
            f"Categoria '{cfg['categoria']}' não está em {categorias_yaml}. "
            "Crie a categoria no WordPress e adicione o ID lá (ver README)."
        )
    return {"categoria_id": categoria_id, "featured_media_id": cfg.get("featured_media_id")}


def extrair_titulo_md(texto: str) -> str | None:
    """Extrai o primeiro H1 (# Título) do Markdown. Retorna None se não encontrar."""
    for line in texto.splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return None


def _auth_header(username: str, app_password: str) -> str:
    token = base64.b64encode(f"{username}:{app_password}".encode()).decode()
    return f"Basic {token}"


def _cmd_listar(base_url: str, dias: int) -> int:
    with httpx.Client() as client:
        posts = listar_posts(client, base_url, dias=dias)
    if not posts:
        print(f"Nenhum post publicado nos últimos {dias} dias.")
        return 0
    for i, p in enumerate(posts, 1):
        print(f"{i}. {p['titulo']}  ({p['date'][:10]})")
        print(f"   {p['resumo']}")
        print(f"   {p['link']}\n")
    return 0


def _cmd_agendar(base_url: str, arquivo_md: str, titulo: str | None) -> int:
    if not titulo:
        print("--agendar exige --titulo", file=sys.stderr)
        return 1
    arquivo = Path(arquivo_md)
    if not arquivo.exists():
        print(f"Arquivo não encontrado: {arquivo}", file=sys.stderr)
        return 1

    cfg = carregar_config()
    username = os.getenv("WP_USERNAME")
    app_password = os.getenv("WP_APP_PASSWORD")
    if not username or not app_password:
        print("WP_USERNAME/WP_APP_PASSWORD não definidos no .env", file=sys.stderr)
        return 1

    html = md_para_html(arquivo.read_text(encoding="utf-8"))
    quando = proximo_domingo(datetime.now(timezone.utc))
    with httpx.Client() as client:
        data = agendar_cronica(
            client,
            base_url=base_url,
            auth_header=_auth_header(username, app_password),
            titulo=titulo,
            html=html,
            categoria_id=cfg["categoria_id"],
            quando=quando,
            featured_media_id=cfg["featured_media_id"],
        )
    print(f"Agendado para {quando:%Y-%m-%d %H:%M} UTC — post {data['id']}: {data.get('link')}")
    return 0


def _cmd_auto(base_url: str) -> int:
    """Detecta crônicas em cronicas/*.md sem marcador .agendado e agenda cada uma."""
    pasta = Path("cronicas")
    candidatos = sorted(p for p in pasta.glob("*.md") if p.name != ".gitkeep")
    if not candidatos:
        print("Nenhuma crônica encontrada em cronicas/")
        return 0

    cfg = carregar_config()
    username = os.getenv("WP_USERNAME")
    app_password = os.getenv("WP_APP_PASSWORD")
    if not username or not app_password:
        print("WP_USERNAME/WP_APP_PASSWORD não definidos no .env", file=sys.stderr)
        return 1

    agendadas = erros = 0
    for md in candidatos:
        marcador = md.with_suffix(".agendado")
        if marcador.exists():
            print(f"[skip] {md.name} — já agendada")
            continue

        texto = md.read_text(encoding="utf-8")
        titulo = extrair_titulo_md(texto)
        if not titulo:
            print(f"[erro] {md.name} — sem título H1, pulando", file=sys.stderr)
            erros += 1
            continue

        html = md_para_html(texto)
        quando = proximo_domingo(datetime.now(timezone.utc))
        try:
            with httpx.Client() as client:
                data = agendar_cronica(
                    client,
                    base_url=base_url,
                    auth_header=_auth_header(username, app_password),
                    titulo=titulo,
                    html=html,
                    categoria_id=cfg["categoria_id"],
                    quando=quando,
                    featured_media_id=cfg["featured_media_id"],
                )
            marcador.write_text(
                f"agendado={quando:%Y-%m-%dT%H:%M:%S}Z\npost_id={data['id']}\n",
                encoding="utf-8",
            )
            print(f"[ok] {md.name} → post {data['id']} agendado para {quando:%Y-%m-%d %H:%M} UTC")
            agendadas += 1
        except CronicaError as exc:
            print(f"[erro] {md.name} — {exc}", file=sys.stderr)
            erros += 1

    print(f"\n{agendadas} agendada(s), {erros} erro(s).")
    return 1 if erros else 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Coluna 'Cafezinho & Planeta, Urgente!'")
    grupo = parser.add_mutually_exclusive_group(required=True)
    grupo.add_argument("--listar", action="store_true", help="Lista os posts da semana")
    grupo.add_argument("--agendar", metavar="ARQUIVO_MD", help="Agenda a crônica para domingo")
    grupo.add_argument("--auto", action="store_true", help="Detecta e agenda crônicas pendentes em cronicas/")
    parser.add_argument("--dias", type=int, default=7, help="Janela de busca (--listar)")
    parser.add_argument("--titulo", help="Título do post (obrigatório com --agendar)")
    args = parser.parse_args()

    load_dotenv()
    base_url = os.getenv("WP_URL", "https://cafezinhoeuropa.com")

    if args.listar:
        return _cmd_listar(base_url, args.dias)
    if args.auto:
        return _cmd_auto(base_url)
    return _cmd_agendar(base_url, args.agendar, args.titulo)


if __name__ == "__main__":
    sys.exit(main())
