"""Resumo + tradução via Claude API."""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml
from anthropic import AsyncAnthropic
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from pipeline.fetcher import Article

logger = logging.getLogger(__name__)

CATEGORIAS_VALIDAS = {
    "Suécia", "França", "Alemanha", "Espanha", "Itália",
    "Reino Unido", "Europa", "Mundo",
}

# Preços por 1M de tokens (Sonnet 4.6 — ajustar conforme tabela vigente)
PRICE_INPUT_PER_M = 3.00
PRICE_OUTPUT_PER_M = 15.00


class ProcessorError(Exception):
    """Erro permanente no processamento (não retentar)."""


@dataclass(frozen=True)
class ProcessedArticle:
    titulo_pt: str
    resumo_pt: str
    tags: list[str]
    categoria: str
    source_url: str
    source_name: str
    cost_usd: float


def load_config(path: str | Path = "config/prompts.yaml") -> dict[str, Any]:
    return yaml.safe_load(Path(path).read_text(encoding="utf-8"))["processor"]


@retry(
    retry=retry_if_exception_type(Exception),
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=2, min=2, max=32),
    reraise=True,
)
async def _call_claude(client: AsyncAnthropic, *, model, max_tokens, temperature,
                      system, user):
    """Chamada ao Claude com retry exponencial em qualquer exceção transiente."""
    return await client.messages.create(
        model=model,
        max_tokens=max_tokens,
        temperature=temperature,
        system=system,
        messages=[{"role": "user", "content": user}],
    )


def _calcular_custo(input_tokens: int, output_tokens: int) -> float:
    return (input_tokens / 1_000_000) * PRICE_INPUT_PER_M + \
           (output_tokens / 1_000_000) * PRICE_OUTPUT_PER_M


def _validar_parsed(parsed: dict) -> None:
    for chave in ("titulo_pt", "resumo_pt", "tags", "categoria"):
        if chave not in parsed:
            raise ProcessorError(f"Resposta sem chave obrigatória: {chave}")
    if parsed["categoria"] not in CATEGORIAS_VALIDAS:
        raise ProcessorError(f"Categoria inválida: {parsed['categoria']}")
    if not isinstance(parsed["tags"], list) or not parsed["tags"]:
        raise ProcessorError("Tags devem ser lista não vazia")


async def process_article(
    article: Article,
    *,
    client: AsyncAnthropic,
    config: dict,
) -> ProcessedArticle:
    user_prompt = config.get("user_template", "").format(
        language=article.language,
        source=article.source,
        title=article.title,
        content=article.content,
    )

    resp = await _call_claude(
        client,
        model=config.get("model", "claude-sonnet-4-6"),
        max_tokens=config.get("max_tokens", 1500),
        temperature=config.get("temperature", 0.7),
        system=config.get("system_prompt", ""),
        user=user_prompt,
    )

    text = resp.content[0].text.strip()
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError as e:
        raise ProcessorError(f"JSON malformado: {e}") from e

    _validar_parsed(parsed)

    cost = _calcular_custo(resp.usage.input_tokens, resp.usage.output_tokens)

    return ProcessedArticle(
        titulo_pt=parsed["titulo_pt"],
        resumo_pt=parsed["resumo_pt"],
        tags=parsed["tags"],
        categoria=parsed["categoria"],
        source_url=article.url,
        source_name=article.source,
        cost_usd=cost,
    )
