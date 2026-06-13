"""Testes do helper da coluna 'Cafezinho & Planeta, Urgente!'."""
from __future__ import annotations

from datetime import datetime, timezone

from pipeline.cronica import _strip_html, md_para_html, proximo_domingo


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
