"""Testes do helper da coluna 'Cafezinho & Planeta, Urgente!'."""
from __future__ import annotations

from datetime import datetime, timezone
import json
from unittest.mock import patch

import httpx
import pytest

from pipeline.cronica import (
    CronicaError, _strip_html, md_para_html, proximo_domingo,
    listar_posts, agendar_cronica, carregar_config,
    extrair_titulo_md, _cmd_auto,
)


def test_proximo_domingo_de_uma_quinta():
    # 2026-06-11 é quinta-feira
    agora = datetime(2026, 6, 11, 12, 0, tzinfo=timezone.utc)
    assert proximo_domingo(agora) == datetime(2026, 6, 14, 8, 0, tzinfo=timezone.utc)


def test_proximo_domingo_rodando_num_domingo_vai_para_o_seguinte():
    # regra: rodou num domingo -> agenda o domingo SEGUINTE
    agora = datetime(2026, 6, 14, 7, 0, tzinfo=timezone.utc)
    assert proximo_domingo(agora) == datetime(2026, 6, 21, 8, 0, tzinfo=timezone.utc)


def test_proximo_domingo_de_um_sabado_e_o_dia_seguinte():
    agora = datetime(2026, 6, 13, 23, 30, tzinfo=timezone.utc)
    assert proximo_domingo(agora) == datetime(2026, 6, 14, 8, 0, tzinfo=timezone.utc)


def test_md_para_html_converte_estrutura_da_cronica():
    md = "## As notícias\n\n**O Arretado:** Oxe, isso aí é Brasil com neve."
    html = md_para_html(md)
    assert "<h2>As notícias</h2>" in html
    assert "<strong>O Arretado:</strong>" in html


def test_strip_html_remove_tags_e_decodifica_entidades():
    assert _strip_html("<p>T&iacute;tulo <b>teste</b></p>\n") == "Título teste\n"


def test_listar_posts_parseia_resposta_do_wp():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/wp-json/wp/v2/posts"
        assert request.url.params["per_page"] == "50"
        assert "after" in request.url.params
        return httpx.Response(
            200,
            json=[
                {
                    "id": 123,
                    "date": "2026-06-10T07:15:00",
                    "link": "https://cafezinhoeuropa.com/post-teste/",
                    "title": {"rendered": "T&iacute;tulo <b>teste</b>"},
                    "excerpt": {"rendered": "<p>Resumo do post.</p>\n"},
                    "categories": [2],
                }
            ],
        )

    client = httpx.Client(transport=httpx.MockTransport(handler))
    posts = listar_posts(client, "https://cafezinhoeuropa.com", dias=7)
    assert posts == [
        {
            "id": 123,
            "date": "2026-06-10T07:15:00",
            "link": "https://cafezinhoeuropa.com/post-teste/",
            "titulo": "Título teste",
            "resumo": "Resumo do post.",
        }
    ]


def _client_capturando(captured: dict, status_code: int = 201) -> httpx.Client:
    def handler(request: httpx.Request) -> httpx.Response:
        captured["json"] = json.loads(request.content)
        captured["auth"] = request.headers.get("authorization")
        captured["path"] = request.url.path
        if status_code >= 400:
            return httpx.Response(status_code, json={"message": "proibido"})
        return httpx.Response(
            status_code,
            json={"id": 555, "link": "https://cafezinhoeuropa.com/?p=555", "status": "future"},
        )

    return httpx.Client(transport=httpx.MockTransport(handler))


def test_agendar_cronica_monta_payload_future():
    captured: dict = {}
    quando = datetime(2026, 6, 14, 8, 0, tzinfo=timezone.utc)
    data = agendar_cronica(
        _client_capturando(captured),
        base_url="https://cafezinhoeuropa.com",
        auth_header="Basic abc123",
        titulo="A fika da inflação",
        html="<p>conteúdo</p>",
        categoria_id=12,
        quando=quando,
    )
    assert captured["path"] == "/wp-json/wp/v2/posts"
    assert captured["auth"] == "Basic abc123"
    assert captured["json"]["status"] == "future"
    assert captured["json"]["date_gmt"] == "2026-06-14T08:00:00"
    assert captured["json"]["categories"] == [12]
    assert "featured_media" not in captured["json"]
    assert data["id"] == 555


def test_agendar_cronica_inclui_featured_media_quando_configurada():
    captured: dict = {}
    agendar_cronica(
        _client_capturando(captured),
        base_url="https://cafezinhoeuropa.com",
        auth_header="Basic abc123",
        titulo="A fika da inflação",
        html="<p>conteúdo</p>",
        categoria_id=12,
        quando=datetime(2026, 6, 14, 8, 0, tzinfo=timezone.utc),
        featured_media_id=77,
    )
    assert captured["json"]["featured_media"] == 77


def test_agendar_cronica_erro_http_vira_cronica_error():
    with pytest.raises(CronicaError, match="403"):
        agendar_cronica(
            _client_capturando({}, status_code=403),
            base_url="https://cafezinhoeuropa.com",
            auth_header="Basic abc123",
            titulo="A fika da inflação",
            html="<p>conteúdo</p>",
            categoria_id=12,
            quando=datetime(2026, 6, 14, 8, 0, tzinfo=timezone.utc),
        )


def test_carregar_config_resolve_categoria_id(tmp_path):
    cronica_yaml = tmp_path / "cronica.yaml"
    cronica_yaml.write_text(
        'categoria: "Cafezinho & Planeta, Urgente!"\nfeatured_media_id: 77\n',
        encoding="utf-8",
    )
    categorias_yaml = tmp_path / "wp_categories.yaml"
    categorias_yaml.write_text(
        'categories:\n  "Cafezinho & Planeta, Urgente!": 12\n',
        encoding="utf-8",
    )
    cfg = carregar_config(cronica_yaml, categorias_yaml)
    assert cfg == {"categoria_id": 12, "featured_media_id": 77}


def test_carregar_config_categoria_ausente_e_erro(tmp_path):
    cronica_yaml = tmp_path / "cronica.yaml"
    cronica_yaml.write_text('categoria: "Inexistente"\nfeatured_media_id: null\n', encoding="utf-8")
    categorias_yaml = tmp_path / "wp_categories.yaml"
    categorias_yaml.write_text('categories:\n  "Europa": 2\n', encoding="utf-8")
    with pytest.raises(CronicaError, match="Inexistente"):
        carregar_config(cronica_yaml, categorias_yaml)


# ── --auto ────────────────────────────────────────────────────────────────────

def test_extrair_titulo_md_encontra_h1():
    md = "# Fique no Seu Lugar!\n\nTexto da crônica."
    assert extrair_titulo_md(md) == "Fique no Seu Lugar!"


def test_extrair_titulo_md_ignora_h2_e_abaixo():
    md = "## Subtítulo\n\nSem H1 aqui."
    assert extrair_titulo_md(md) is None


def test_extrair_titulo_md_sem_titulo_retorna_none():
    assert extrair_titulo_md("Texto sem nenhum título.") is None


def _setup_auto(tmp_path, monkeypatch):
    """Monta estrutura de arquivos e env para testes de --auto."""
    # Pasta de crônicas com um arquivo pendente
    pasta = tmp_path / "cronicas"
    pasta.mkdir()
    (pasta / ".gitkeep").write_text("")
    md = pasta / "2026-06-15-teste.md"
    md.write_text("# A Grande Fika\n\nConteúdo da crônica.", encoding="utf-8")

    # Config YAML
    cfg_dir = tmp_path / "config"
    cfg_dir.mkdir()
    (cfg_dir / "cronica.yaml").write_text(
        'categoria: "Cafezinho & Planeta, Urgente!"\nfeatured_media_id: null\n',
        encoding="utf-8",
    )
    (cfg_dir / "wp_categories.yaml").write_text(
        'categories:\n  "Cafezinho & Planeta, Urgente!": 42\n',
        encoding="utf-8",
    )

    # Patch de caminhos e env
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("WP_USERNAME", "bot")
    monkeypatch.setenv("WP_APP_PASSWORD", "senha123")
    return pasta, md


def test_auto_agenda_cronica_pendente(tmp_path, monkeypatch):
    pasta, md = _setup_auto(tmp_path, monkeypatch)

    with patch("pipeline.cronica.agendar_cronica") as mock_ag, \
         patch("pipeline.cronica.httpx.Client"):
        mock_ag.return_value = {"id": 99, "link": "https://cafezinhoeuropa.com/?p=99"}
        result = _cmd_auto("https://cafezinhoeuropa.com")

    assert result == 0
    assert mock_ag.called
    _, kwargs = mock_ag.call_args
    assert kwargs["titulo"] == "A Grande Fika"
    assert kwargs["categoria_id"] == 42
    assert (pasta / "2026-06-15-teste.agendado").exists()


def test_auto_pula_cronica_ja_agendada(tmp_path, monkeypatch, capsys):
    pasta, md = _setup_auto(tmp_path, monkeypatch)
    (pasta / "2026-06-15-teste.agendado").write_text("agendado=2026-06-15T08:00:00Z\n")

    with patch("pipeline.cronica.agendar_cronica") as mock_ag, \
         patch("pipeline.cronica.httpx.Client"):
        result = _cmd_auto("https://cafezinhoeuropa.com")

    assert result == 0
    mock_ag.assert_not_called()
    assert "[skip]" in capsys.readouterr().out


def test_auto_pula_arquivo_sem_titulo(tmp_path, monkeypatch, capsys):
    pasta, md = _setup_auto(tmp_path, monkeypatch)
    md.write_text("Sem título H1 aqui.", encoding="utf-8")

    with patch("pipeline.cronica.agendar_cronica") as mock_ag, \
         patch("pipeline.cronica.httpx.Client"):
        result = _cmd_auto("https://cafezinhoeuropa.com")

    assert result == 1
    mock_ag.assert_not_called()
    assert "sem título" in capsys.readouterr().err
