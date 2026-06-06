"""Smoke test: integração com BBC RSS + Claude API real.

NÃO roda em pytest padrão; precisa ser invocado explicitamente:
    pytest tests/test_smoke.py -v -m smoke
"""
import os

import pytest
from anthropic import AsyncAnthropic
from dotenv import load_dotenv

from pipeline.fetcher import Source, fetch_all
from pipeline.processor import process_article, load_config


pytestmark = pytest.mark.smoke


@pytest.fixture(autouse=True)
def carrega_env():
    load_dotenv()
    if not os.getenv("ANTHROPIC_API_KEY"):
        pytest.skip("ANTHROPIC_API_KEY não definido")


@pytest.mark.asyncio
async def test_smoke_bbc_para_claude():
    source = Source(
        name="bbc",
        url="https://feeds.bbci.co.uk/news/world/europe/rss.xml",
        language="en",
        default_category="Europa",
    )
    artigos = await fetch_all([source])
    assert len(artigos) > 0, "BBC não devolveu nenhum artigo"

    primeiro = artigos[0]
    client = AsyncAnthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    config = load_config("config/prompts.yaml")

    processed = await process_article(primeiro, client=client, config=config)

    print(f"\n=== SMOKE TEST OK ===")
    print(f"Original (en): {primeiro.title}")
    print(f"Traduzido (pt): {processed.titulo_pt}")
    print(f"Categoria: {processed.categoria}")
    print(f"Tags: {processed.tags}")
    print(f"Custo: ${processed.cost_usd:.4f}")

    assert processed.titulo_pt
    assert len(processed.resumo_pt.split("\n\n")) >= 2
    assert processed.cost_usd < 0.10  # sanity check
