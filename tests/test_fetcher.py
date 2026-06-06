"""Testes do fetcher de RSS."""
from pathlib import Path
from unittest.mock import patch

import pytest

from pipeline.fetcher import Article, Source, parse_feed, fetch_all


FIXTURES = Path(__file__).parent / "fixtures"


def test_parse_feed_bbc():
    xml = (FIXTURES / "bbc_sample.xml").read_text(encoding="utf-8")
    source = Source(name="bbc", url="http://x", language="en", default_category="Europa")
    artigos = parse_feed(xml, source)
    assert len(artigos) >= 1
    assert all(isinstance(a, Article) for a in artigos)
    assert all(a.source == "bbc" for a in artigos)
    assert all(a.language == "en" for a in artigos)
    assert all(a.url.startswith("http") for a in artigos)


def test_parse_feed_svt():
    xml = (FIXTURES / "svt_sample.xml").read_text(encoding="utf-8")
    source = Source(name="svt", url="http://x", language="sv", default_category="Suécia")
    artigos = parse_feed(xml, source)
    assert len(artigos) >= 1
    assert artigos[0].language == "sv"


def test_parse_feed_lemonde():
    xml = (FIXTURES / "lemonde_sample.xml").read_text(encoding="utf-8")
    source = Source(name="lemonde", url="http://x", language="fr", default_category="França")
    artigos = parse_feed(xml, source)
    assert len(artigos) >= 1
    assert artigos[0].language == "fr"


def test_parse_feed_xml_malformado():
    source = Source(name="x", url="http://x", language="en", default_category="X")
    artigos = parse_feed("<xml>quebrado", source)
    assert artigos == []  # silenciosamente devolve lista vazia


@pytest.mark.asyncio
async def test_fetch_all_agrupa_resultados():
    """Mock de httpx para evitar rede real."""
    bbc_xml = (FIXTURES / "bbc_sample.xml").read_text(encoding="utf-8")
    svt_xml = (FIXTURES / "svt_sample.xml").read_text(encoding="utf-8")

    sources = [
        Source(name="bbc", url="http://bbc.test", language="en", default_category="Europa"),
        Source(name="svt", url="http://svt.test", language="sv", default_category="Suécia"),
    ]

    async def fake_get(self, url, **kwargs):
        class FakeResponse:
            status_code = 200
            text = bbc_xml if "bbc" in url else svt_xml
        return FakeResponse()

    with patch("httpx.AsyncClient.get", new=fake_get):
        artigos = await fetch_all(sources)

    assert len(artigos) >= 2
    fontes = {a.source for a in artigos}
    assert "bbc" in fontes
    assert "svt" in fontes
