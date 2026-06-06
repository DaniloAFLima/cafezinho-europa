"""Testes do filtro de relevância."""
from datetime import datetime, timedelta, timezone

import pytest

from pipeline.fetcher import Article
from pipeline.relevance import score_article, select_top, load_config


@pytest.fixture
def config():
    return load_config("config/relevance.yaml")


def _make_article(
    title: str = "test",
    content: str = "",
    source: str = "bbc",
    horas_atras: float = 1.0,
) -> Article:
    published_at = datetime.now(timezone.utc) - timedelta(hours=horas_atras)
    return Article(
        url=f"https://x.com/{title}",
        source=source,
        language="en",
        title=title,
        content=content,
        published_at=published_at,
        fetched_at=datetime.now(timezone.utc),
        default_category="Europa",
    )


def test_score_recente_vale_mais_que_antigo(config):
    recente = _make_article(title="t1", horas_atras=2)
    antigo = _make_article(title="t2", horas_atras=40)
    assert score_article(recente, config) > score_article(antigo, config)


def test_score_keyword_positiva_aumenta(config):
    com_kw = _make_article(title="Brazilian immigration to Europe", horas_atras=2)
    sem_kw = _make_article(title="Random news about cats", horas_atras=2)
    assert score_article(com_kw, config) > score_article(sem_kw, config)


def test_score_keyword_negativa_diminui(config):
    com_neg = _make_article(title="Bundesliga match results", horas_atras=2)
    neutro = _make_article(title="Some news", horas_atras=2)
    assert score_article(com_neg, config) < score_article(neutro, config)


def test_score_fonte_bbc_maior_que_corriere(config):
    bbc = _make_article(title="t", source="bbc", horas_atras=2)
    corriere = _make_article(title="t", source="corriere", horas_atras=2)
    assert score_article(bbc, config) >= score_article(corriere, config)


def test_select_top_pega_n_artigos(config):
    artigos = [_make_article(title=f"t{i}", horas_atras=2) for i in range(20)]
    top = select_top(artigos, config, n=5)
    assert len(top) == 5


def test_select_top_ordem_decrescente(config):
    artigos = [
        _make_article(title="brazilian immigration", horas_atras=2),
        _make_article(title="random", horas_atras=40),
        _make_article(title="visa news", horas_atras=2),
    ]
    top = select_top(artigos, config, n=3)
    assert "brazilian" in top[0].title or "visa" in top[0].title
