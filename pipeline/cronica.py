"""Coluna semanal 'Cafezinho & Planeta, Urgente!' — listar notícias e agendar a crônica."""
from __future__ import annotations

from datetime import datetime, timedelta

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
