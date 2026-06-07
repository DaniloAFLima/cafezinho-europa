"""Orquestrador do pipeline diário."""
from __future__ import annotations

import argparse
import asyncio
import logging
import os
import sys
from typing import Any

from anthropic import AsyncAnthropic
from dotenv import load_dotenv

from pipeline.db import Database, ArticleStatus
from pipeline.dedupe import filter_unseen
from pipeline.fetcher import Article, fetch_all, load_sources
from pipeline.og_image import fetch_og_images_batch
from pipeline.processor import (
    ProcessorError,
    ProcessedArticle,
    process_article,
    load_config as load_prompts_config,
)
from pipeline.publisher import WordPressPublisher, PublisherError
from pipeline.relevance import load_config as load_relevance_config, select_top


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("cafezinho")


async def _safe_process(
    article, *, client, prompts_config, max_cost_usd, current_cost
) -> tuple[ProcessedArticle | None, float, Exception | None]:
    """Processa 1 artigo; devolve (resultado, custo_incremental, erro)."""
    if current_cost >= max_cost_usd:
        return None, 0.0, RuntimeError(f"Excedeu limite de custo (${max_cost_usd})")
    try:
        result = await process_article(article, client=client, config=prompts_config)
        return result, result.cost_usd, None
    except ProcessorError as e:
        logger.warning("ProcessorError em %s: %s", article.url, e)
        return None, 0.0, e
    except Exception as e:  # noqa: BLE001
        logger.exception("Erro inesperado processando %s", article.url)
        return None, 0.0, e


async def run_pipeline(
    *,
    db: Database | None = None,
    db_path: str = "data/cafezinho.db",
    dry_run: bool = False,
) -> dict[str, Any]:
    load_dotenv()

    if db is None:
        db = Database(db_path)

    run_id = db.start_run()
    summary = {
        "fetched": 0, "processed": 0, "published": 0,
        "skipped": 0, "failed": 0, "cost_usd": 0.0,
    }

    try:
        # 1. Buscar
        sources = load_sources("config/sources.yaml")
        artigos = await fetch_all(sources)
        summary["fetched"] = len(artigos)
        logger.info("Buscados %d artigos brutos", len(artigos))

        # 2. Dedupe
        novos = filter_unseen(db, artigos)
        logger.info("%d sao novos (apos dedupe)", len(novos))

        # 3. Relevância
        relevance_cfg = load_relevance_config("config/relevance.yaml")
        top = select_top(novos, relevance_cfg)
        logger.info("Selecionados top %d por relevancia", len(top))

        # 3.5. Buscar imagem og:image de cada artigo selecionado (em paralelo)
        og_images = await fetch_og_images_batch([a.url for a in top])
        com_qtd = sum(1 for v in og_images.values() if v)
        logger.info("Imagens og:image encontradas em %d/%d artigos", com_qtd, len(top))
        # substitui cada artigo por uma versão com image_url preenchida
        top = [
            Article(
                url=a.url, source=a.source, language=a.language,
                title=a.title, content=a.content,
                published_at=a.published_at, fetched_at=a.fetched_at,
                default_category=a.default_category,
                image_url=og_images.get(a.url),
            )
            for a in top
        ]

        # 4. Processar
        prompts_cfg = load_prompts_config("config/prompts.yaml")
        max_cost = float(os.getenv("MAX_DAILY_COST_USD", "1.00"))

        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise RuntimeError("ANTHROPIC_API_KEY nao definido em .env")
        client = AsyncAnthropic(api_key=api_key)

        processed: list[ProcessedArticle] = []
        for art in top:
            # marca como 'publishing' ANTES de chamar Claude (para idempotência futura)
            db.upsert_article(
                url=art.url,
                source=art.source,
                language=art.language,
                title_orig=art.title,
                published_at=art.published_at,
                status=ArticleStatus.PUBLISHING,
            )
            result, cost_inc, err = await _safe_process(
                art,
                client=client,
                prompts_config=prompts_cfg,
                max_cost_usd=max_cost,
                current_cost=summary["cost_usd"],
            )
            summary["cost_usd"] += cost_inc

            if err is not None:
                summary["failed"] += 1
                db.update_article_status(
                    url=art.url,
                    status=ArticleStatus.FAILED,
                    error_msg=str(err)[:500],
                )
                continue

            summary["processed"] += 1
            processed.append(result)

        # 5. Publicar (pula em dry-run)
        if dry_run:
            for p in processed:
                print(f"\n--- DRY RUN ---\n[{p.categoria}] {p.titulo_pt}\n{p.resumo_pt}\nFonte: {p.source_url}\n")
            summary["skipped"] = len(processed)
        else:
            import yaml as _yaml
            category_id_map = _yaml.safe_load(
                open("config/wp_categories.yaml", encoding="utf-8")
            )["categories"]
            wp = WordPressPublisher(
                base_url=os.environ["WP_URL"],
                username=os.environ["WP_USERNAME"],
                app_password=os.environ["WP_APP_PASSWORD"],
                category_id_map=category_id_map,
            )
            for p in processed:
                try:
                    pub_result = await wp.publish(p)
                    db.update_article_status(
                        url=p.source_url,
                        status=ArticleStatus.PUBLISHED,
                        wp_post_id=pub_result.wp_post_id,
                    )
                    summary["published"] += 1
                except (PublisherError, Exception) as e:  # noqa: BLE001
                    logger.exception("Falha publicando %s", p.source_url)
                    summary["failed"] += 1
                    db.update_article_status(
                        url=p.source_url,
                        status=ArticleStatus.FAILED,
                        error_msg=str(e)[:500],
                    )

        db.finish_run(
            run_id,
            fetched=summary["fetched"],
            published=summary["published"],
            skipped=summary["skipped"],
            failed=summary["failed"],
            cost_usd=summary["cost_usd"],
        )
        return summary

    except Exception as e:
        logger.exception("Run abortado por erro fatal")
        db.finish_run(
            run_id,
            fetched=summary["fetched"],
            published=summary["published"],
            skipped=summary["skipped"],
            failed=summary["failed"],
            cost_usd=summary["cost_usd"],
            error_log=str(e),
        )
        raise


def main() -> int:
    parser = argparse.ArgumentParser(description="Cafezinho Europa pipeline")
    parser.add_argument("--dry-run", action="store_true", help="Não publica no WP")
    args = parser.parse_args()

    summary = asyncio.run(run_pipeline(dry_run=args.dry_run))
    logger.info("Resumo final: %s", summary)
    return 0


if __name__ == "__main__":
    sys.exit(main())
