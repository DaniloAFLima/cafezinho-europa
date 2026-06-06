"""Score e seleção dos artigos mais relevantes para brasileiros na Europa."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from pipeline.fetcher import Article


@dataclass
class RelevanceConfig:
    keywords_positivas: list[str]
    keywords_negativas: list[str]
    pesos: dict[str, Any]
    top_n: int


def load_config(path: str | Path = "config/relevance.yaml") -> RelevanceConfig:
    data = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    return RelevanceConfig(
        keywords_positivas=[k.lower() for k in data["keywords_positivas"]],
        keywords_negativas=[k.lower() for k in data["keywords_negativas"]],
        pesos=data["pesos"],
        top_n=data.get("top_n", 10),
    )


def _score_recencia(article: Article, pesos: dict) -> float:
    delta = datetime.now(timezone.utc) - article.published_at
    horas = delta.total_seconds() / 3600
    tabela = pesos.get("recencia_horas", {})
    if horas < 6:
        return tabela.get("<6", 1.0)
    if horas < 12:
        return tabela.get("<12", 0.7)
    if horas < 24:
        return tabela.get("<24", 0.4)
    if horas < 48:
        return tabela.get("<48", 0.1)
    return 0.0


def _score_fonte(article: Article, pesos: dict) -> float:
    return pesos.get("fonte", {}).get(article.source, 0.5)


def _score_keywords(article: Article, config: RelevanceConfig) -> float:
    texto = f"{article.title} {article.content}".lower()
    score = 0.0
    for kw in config.keywords_positivas:
        if kw in texto:
            score += config.pesos.get("keyword_positiva", 0.3)
    for kw in config.keywords_negativas:
        if kw in texto:
            score += config.pesos.get("keyword_negativa", -0.5)
    return score


def score_article(article: Article, config: RelevanceConfig) -> float:
    return (
        _score_recencia(article, config.pesos)
        + _score_fonte(article, config.pesos)
        + _score_keywords(article, config)
    )


def select_top(
    artigos: list[Article],
    config: RelevanceConfig,
    n: int | None = None,
) -> list[Article]:
    n = n if n is not None else config.top_n
    ranked = sorted(artigos, key=lambda a: score_article(a, config), reverse=True)
    return ranked[:n]
