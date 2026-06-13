"""Testes do helper da coluna 'Cafezinho & Planeta, Urgente!'."""
from __future__ import annotations

from datetime import datetime, timezone

from pipeline.cronica import proximo_domingo


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
