# Cafezinho Europa — MVP Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Construir o MVP do Cafezinho Europa — pipeline Python automatizado que busca notícias multi-idioma, resume/traduz com Claude e publica em WordPress diariamente.

**Architecture:** Pipeline Python em 6 módulos isolados (fetcher → dedupe → relevance → processor → publisher → main), orquestrado por cron em 1 VPS Hetzner. WordPress no mesmo VPS via Docker. SQLite como state store.

**Tech Stack:** Python 3.12, httpx, feedparser, anthropic SDK, pytest, SQLite, WordPress, Docker, Hetzner VPS, cron, healthchecks.io

**Reference Spec:** `docs/superpowers/specs/2026-06-06-cafezinho-europa-design.md`

---

## Plano de execução

Este plano tem duas partes:

- **Parte A — Pipeline Python (Tasks 1–9)**: tudo que pode ser feito localmente, com TDD.
- **Parte B — Infraestrutura (Tasks 10–14)**: setup do VPS, WordPress, deploy e cron. Requer ações manuais (compra de VPS, domínio, etc.).

A Parte A pode ser implementada antes de comprar qualquer infraestrutura — você desenvolve e testa offline, e só compra VPS/domínio quando o código estiver maduro.

---

# Parte A — Pipeline Python

## Task 1: Scaffolding do projeto

**Files:**
- Create: `requirements.txt`
- Create: `pyproject.toml`
- Create: `.gitignore`
- Create: `.env.example`
- Create: `pipeline/__init__.py`
- Create: `tests/__init__.py`
- Create: `README.md`

- [ ] **Step 1: Criar `requirements.txt`**

```
httpx==0.27.0
feedparser==6.0.11
anthropic==0.40.0
python-dotenv==1.0.1
pyyaml==6.0.2
tenacity==9.0.0
pytest==8.3.4
pytest-asyncio==0.24.0
pytest-mock==3.14.0
ruff==0.7.4
black==24.10.0
```

- [ ] **Step 2: Criar `pyproject.toml`**

```toml
[project]
name = "cafezinho-europa"
version = "0.1.0"
description = "Pipeline de notícias automatizadas para brasileiros na Europa"
requires-python = ">=3.12"

[tool.ruff]
line-length = 100
target-version = "py312"

[tool.black]
line-length = 100
target-version = ["py312"]

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
```

- [ ] **Step 3: Criar `.gitignore`**

```
# Python
__pycache__/
*.py[cod]
*.egg-info/
.pytest_cache/
.ruff_cache/

# Virtual env
.venv/
venv/

# Secrets
.env
config/.env

# Data
data/
*.db
*.db-journal

# Logs
*.log
logs/

# OS
.DS_Store
Thumbs.db
```

- [ ] **Step 4: Criar `.env.example`**

```
# Anthropic / Claude API
ANTHROPIC_API_KEY=sk-ant-...

# WordPress REST API
WP_URL=https://cafezinhoeuropa.com
WP_USERNAME=cafezinho-bot
WP_APP_PASSWORD=xxxx xxxx xxxx xxxx xxxx xxxx

# Healthcheck.io (opcional)
HEALTHCHECK_URL=https://hc-ping.com/uuid-aqui

# Limites de segurança
MAX_DAILY_COST_USD=1.00
```

- [ ] **Step 5: Criar `pipeline/__init__.py` e `tests/__init__.py` vazios**

```bash
# arquivos vazios apenas para marcar como pacote Python
```

- [ ] **Step 6: Criar `README.md`**

```markdown
# Cafezinho Europa

Pipeline automatizado de notícias da Europa em português do Brasil.

## Setup local

```bash
python -m venv .venv
.venv\Scripts\activate    # Windows
source .venv/bin/activate # Linux/macOS

pip install -r requirements.txt
cp .env.example .env
# preencher .env com suas chaves
```

## Rodar pipeline

```bash
python -m pipeline.main           # modo normal (publica)
python -m pipeline.main --dry-run # modo teste (não publica)
```

## Rodar testes

```bash
pytest -v
```

Ver `docs/superpowers/specs/` para design completo e `docs/superpowers/plans/` para plano de implementação.
```

- [ ] **Step 7: Criar venv e instalar dependências**

```bash
cd C:\Users\danil\cafezinho-europa
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

Expected: instalação sem erros, todas as libs disponíveis.

- [ ] **Step 8: Commit**

```bash
git add requirements.txt pyproject.toml .gitignore .env.example pipeline/ tests/ README.md
git commit -m "chore: scaffolding inicial do projeto"
```

---

## Task 2: Camada de banco de dados (SQLite)

**Files:**
- Create: `pipeline/db.py`
- Create: `tests/test_db.py`

- [ ] **Step 1: Escrever testes (falhando) em `tests/test_db.py`**

```python
"""Testes da camada de banco de dados."""
import sqlite3
from datetime import datetime, timezone

import pytest

from pipeline.db import Database, ArticleStatus


@pytest.fixture
def db():
    """Database em memória para isolar testes."""
    return Database(":memory:")


def test_init_cria_tabelas(db):
    cursor = db.conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
    )
    tabelas = [row[0] for row in cursor.fetchall()]
    assert "articles" in tabelas
    assert "runs" in tabelas


def test_insere_e_busca_artigo(db):
    db.upsert_article(
        url="https://exemplo.com/noticia",
        source="bbc",
        language="en",
        title_orig="Test Article",
        published_at=datetime(2026, 6, 6, tzinfo=timezone.utc),
        status=ArticleStatus.PUBLISHING,
    )
    row = db.get_article("https://exemplo.com/noticia")
    assert row is not None
    assert row["source"] == "bbc"
    assert row["status"] == "publishing"


def test_filtra_urls_ja_vistos(db):
    db.upsert_article(
        url="https://a.com",
        source="bbc",
        language="en",
        title_orig="A",
        published_at=datetime(2026, 6, 6, tzinfo=timezone.utc),
        status=ArticleStatus.PUBLISHED,
    )
    novos = db.filter_new_urls(["https://a.com", "https://b.com"])
    assert novos == ["https://b.com"]


def test_atualiza_status(db):
    db.upsert_article(
        url="https://x.com",
        source="bbc",
        language="en",
        title_orig="X",
        published_at=datetime(2026, 6, 6, tzinfo=timezone.utc),
        status=ArticleStatus.PUBLISHING,
    )
    db.update_article_status(
        url="https://x.com",
        status=ArticleStatus.PUBLISHED,
        wp_post_id=42,
    )
    row = db.get_article("https://x.com")
    assert row["status"] == "published"
    assert row["wp_post_id"] == 42


def test_cria_e_finaliza_run(db):
    run_id = db.start_run()
    assert run_id > 0
    db.finish_run(run_id, fetched=10, published=8, skipped=2, failed=0, cost_usd=0.15)
    cursor = db.conn.execute("SELECT * FROM runs WHERE id = ?", (run_id,))
    row = dict(cursor.fetchone())
    assert row["published"] == 8
    assert row["cost_usd"] == 0.15
    assert row["finished_at"] is not None
```

- [ ] **Step 2: Rodar para confirmar falha**

Run: `pytest tests/test_db.py -v`
Expected: FAIL com "ModuleNotFoundError: No module named 'pipeline.db'"

- [ ] **Step 3: Implementar `pipeline/db.py`**

```python
"""Camada de acesso a SQLite (artigos e execuções)."""
from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Iterable


class ArticleStatus(str, Enum):
    PUBLISHING = "publishing"
    PUBLISHED = "published"
    SKIPPED = "skipped"
    FAILED = "failed"


SCHEMA = """
CREATE TABLE IF NOT EXISTS articles (
    url           TEXT PRIMARY KEY,
    source        TEXT NOT NULL,
    language      TEXT NOT NULL,
    title_orig    TEXT NOT NULL,
    published_at  TIMESTAMP NOT NULL,
    fetched_at    TIMESTAMP NOT NULL,
    status        TEXT NOT NULL,
    wp_post_id    INTEGER,
    relevance     REAL,
    error_msg     TEXT
);
CREATE INDEX IF NOT EXISTS idx_articles_status ON articles(status);
CREATE INDEX IF NOT EXISTS idx_articles_fetched_at ON articles(fetched_at);

CREATE TABLE IF NOT EXISTS runs (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    started_at   TIMESTAMP NOT NULL,
    finished_at  TIMESTAMP,
    fetched      INTEGER DEFAULT 0,
    published    INTEGER DEFAULT 0,
    skipped      INTEGER DEFAULT 0,
    failed       INTEGER DEFAULT 0,
    cost_usd     REAL DEFAULT 0.0,
    error_log    TEXT
);
"""


class Database:
    """Wrapper fino sobre SQLite com os métodos que o pipeline precisa."""

    def __init__(self, path: str | Path = "data/cafezinho.db") -> None:
        self.path = str(path)
        self.conn = sqlite3.connect(self.path)
        self.conn.row_factory = sqlite3.Row
        self.conn.executescript(SCHEMA)
        self.conn.commit()

    def upsert_article(
        self,
        *,
        url: str,
        source: str,
        language: str,
        title_orig: str,
        published_at: datetime,
        status: ArticleStatus,
        relevance: float | None = None,
    ) -> None:
        # mantém a primeira ocorrência do URL (não sobrescreve status)
        self.conn.execute(
            """
            INSERT OR IGNORE INTO articles
                (url, source, language, title_orig, published_at, fetched_at, status, relevance)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                url,
                source,
                language,
                title_orig,
                published_at.isoformat(),
                datetime.now(timezone.utc).isoformat(),
                status.value,
                relevance,
            ),
        )
        self.conn.commit()

    def get_article(self, url: str) -> dict | None:
        cursor = self.conn.execute("SELECT * FROM articles WHERE url = ?", (url,))
        row = cursor.fetchone()
        return dict(row) if row else None

    def filter_new_urls(self, urls: Iterable[str]) -> list[str]:
        urls = list(urls)
        if not urls:
            return []
        placeholders = ",".join("?" * len(urls))
        cursor = self.conn.execute(
            f"SELECT url FROM articles WHERE url IN ({placeholders})", urls
        )
        ja_vistos = {row[0] for row in cursor.fetchall()}
        return [u for u in urls if u not in ja_vistos]

    def update_article_status(
        self,
        *,
        url: str,
        status: ArticleStatus,
        wp_post_id: int | None = None,
        error_msg: str | None = None,
    ) -> None:
        self.conn.execute(
            """
            UPDATE articles
            SET status = ?, wp_post_id = COALESCE(?, wp_post_id), error_msg = ?
            WHERE url = ?
            """,
            (status.value, wp_post_id, error_msg, url),
        )
        self.conn.commit()

    def start_run(self) -> int:
        cursor = self.conn.execute(
            "INSERT INTO runs (started_at) VALUES (?)",
            (datetime.now(timezone.utc).isoformat(),),
        )
        self.conn.commit()
        return cursor.lastrowid

    def finish_run(
        self,
        run_id: int,
        *,
        fetched: int,
        published: int,
        skipped: int,
        failed: int,
        cost_usd: float,
        error_log: str | None = None,
    ) -> None:
        self.conn.execute(
            """
            UPDATE runs SET
                finished_at = ?,
                fetched = ?, published = ?, skipped = ?, failed = ?,
                cost_usd = ?, error_log = ?
            WHERE id = ?
            """,
            (
                datetime.now(timezone.utc).isoformat(),
                fetched,
                published,
                skipped,
                failed,
                cost_usd,
                error_log,
                run_id,
            ),
        )
        self.conn.commit()

    def close(self) -> None:
        self.conn.close()
```

- [ ] **Step 4: Rodar testes para confirmar PASS**

Run: `pytest tests/test_db.py -v`
Expected: 5 passed.

- [ ] **Step 5: Commit**

```bash
git add pipeline/db.py tests/test_db.py
git commit -m "feat(db): camada SQLite com articles e runs"
```

---

## Task 3: Fetcher (busca de RSS)

**Files:**
- Create: `pipeline/fetcher.py`
- Create: `config/sources.yaml`
- Create: `tests/test_fetcher.py`
- Create: `tests/fixtures/bbc_sample.xml`
- Create: `tests/fixtures/svt_sample.xml`
- Create: `tests/fixtures/lemonde_sample.xml`

- [ ] **Step 1: Criar fixtures de RSS reais**

Salvar 3 amostras de RSS feeds reais (truncados para 2-3 itens cada) em:
- `tests/fixtures/bbc_sample.xml` (feed RSS da BBC, ex.: https://feeds.bbci.co.uk/news/rss.xml)
- `tests/fixtures/svt_sample.xml` (SVT Nyheter, ex.: https://www.svt.se/nyheter/rss.xml)
- `tests/fixtures/lemonde_sample.xml` (Le Monde, ex.: https://www.lemonde.fr/rss/une.xml)

Para cada um, baixar manualmente o XML do feed e truncar para 2-3 `<item>` para acelerar testes. Comando para baixar:

```bash
curl https://feeds.bbci.co.uk/news/rss.xml -o tests/fixtures/bbc_sample.xml
curl https://www.svt.se/nyheter/rss.xml -o tests/fixtures/svt_sample.xml
curl https://www.lemonde.fr/rss/une.xml -o tests/fixtures/lemonde_sample.xml
```

Depois truncar manualmente cada arquivo para deixar apenas 2-3 itens (para o teste rodar rápido).

- [ ] **Step 2: Criar `config/sources.yaml`**

```yaml
# Cada fonte tem: url, language, name, default_category
sources:
  - name: bbc
    url: https://feeds.bbci.co.uk/news/world/europe/rss.xml
    language: en
    default_category: Europa

  - name: reuters_europe
    url: https://www.reutersagency.com/feed/?best-regions=europe&post_type=best
    language: en
    default_category: Europa

  - name: guardian_europe
    url: https://www.theguardian.com/world/europe-news/rss
    language: en
    default_category: Europa

  - name: svt_nyheter
    url: https://www.svt.se/nyheter/rss.xml
    language: sv
    default_category: Suécia

  - name: dn_se
    url: https://www.dn.se/rss
    language: sv
    default_category: Suécia

  - name: lemonde
    url: https://www.lemonde.fr/rss/une.xml
    language: fr
    default_category: França

  - name: spiegel
    url: https://www.spiegel.de/international/index.rss
    language: de
    default_category: Alemanha

  - name: elpais
    url: https://feeds.elpais.com/mrss-s/pages/ep/site/elpais.com/portada
    language: es
    default_category: Espanha

  - name: corriere
    url: https://www.corriere.it/rss/homepage.xml
    language: it
    default_category: Itália
```

- [ ] **Step 3: Escrever testes (falhando) em `tests/test_fetcher.py`**

```python
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
```

- [ ] **Step 4: Rodar para confirmar falha**

Run: `pytest tests/test_fetcher.py -v`
Expected: FAIL com "ModuleNotFoundError: No module named 'pipeline.fetcher'"

- [ ] **Step 5: Implementar `pipeline/fetcher.py`**

```python
"""Busca de artigos em feeds RSS multi-idioma."""
from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import feedparser
import httpx
import yaml

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class Source:
    name: str
    url: str
    language: str
    default_category: str


@dataclass(frozen=True)
class Article:
    url: str
    source: str
    language: str
    title: str
    content: str
    published_at: datetime
    fetched_at: datetime
    default_category: str


def load_sources(path: str | Path = "config/sources.yaml") -> list[Source]:
    data = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    return [Source(**item) for item in data["sources"]]


def parse_feed(xml: str, source: Source) -> list[Article]:
    """Parse defensivo: nunca lança, devolve [] em qualquer erro."""
    try:
        parsed = feedparser.parse(xml)
        if parsed.bozo and not parsed.entries:
            return []
    except Exception as e:
        logger.warning("Falha ao parsear feed de %s: %s", source.name, e)
        return []

    artigos: list[Article] = []
    agora = datetime.now(timezone.utc)
    for entry in parsed.entries:
        url = entry.get("link", "").strip()
        title = entry.get("title", "").strip()
        if not url or not title:
            continue

        content = entry.get("summary", "") or entry.get("description", "")

        published_at = _extract_datetime(entry) or agora

        artigos.append(
            Article(
                url=url,
                source=source.name,
                language=source.language,
                title=title,
                content=content,
                published_at=published_at,
                fetched_at=agora,
                default_category=source.default_category,
            )
        )
    return artigos


def _extract_datetime(entry) -> datetime | None:
    parsed_time = entry.get("published_parsed") or entry.get("updated_parsed")
    if not parsed_time:
        return None
    try:
        return datetime(*parsed_time[:6], tzinfo=timezone.utc)
    except Exception:
        return None


async def _fetch_one(client: httpx.AsyncClient, source: Source) -> list[Article]:
    try:
        response = await client.get(source.url, timeout=10.0)
        if response.status_code != 200:
            logger.warning("Status %d ao buscar %s", response.status_code, source.name)
            return []
        return parse_feed(response.text, source)
    except (httpx.HTTPError, httpx.TimeoutException) as e:
        logger.warning("Erro de rede em %s: %s", source.name, e)
        return []


async def fetch_all(sources: list[Source]) -> list[Article]:
    async with httpx.AsyncClient(follow_redirects=True) as client:
        tasks = [_fetch_one(client, s) for s in sources]
        results = await asyncio.gather(*tasks, return_exceptions=False)
    return [a for grupo in results for a in grupo]
```

- [ ] **Step 6: Rodar testes**

Run: `pytest tests/test_fetcher.py -v`
Expected: 5 passed.

- [ ] **Step 7: Commit**

```bash
git add pipeline/fetcher.py config/sources.yaml tests/test_fetcher.py tests/fixtures/
git commit -m "feat(fetcher): busca de RSS multi-idioma com fixtures"
```

---

## Task 4: Dedupe

**Files:**
- Create: `pipeline/dedupe.py`
- Create: `tests/test_dedupe.py`

- [ ] **Step 1: Escrever testes (falhando) em `tests/test_dedupe.py`**

```python
"""Testes do filtro de duplicação."""
from datetime import datetime, timezone

import pytest

from pipeline.db import Database, ArticleStatus
from pipeline.dedupe import filter_unseen
from pipeline.fetcher import Article


def _artigo(url: str) -> Article:
    return Article(
        url=url,
        source="bbc",
        language="en",
        title="t",
        content="c",
        published_at=datetime(2026, 6, 6, tzinfo=timezone.utc),
        fetched_at=datetime(2026, 6, 6, tzinfo=timezone.utc),
        default_category="Europa",
    )


@pytest.fixture
def db():
    return Database(":memory:")


def test_filter_unseen_lista_vazia(db):
    assert filter_unseen(db, []) == []


def test_filter_unseen_todos_novos(db):
    artigos = [_artigo("https://a.com"), _artigo("https://b.com")]
    resultado = filter_unseen(db, artigos)
    assert len(resultado) == 2


def test_filter_unseen_remove_ja_vistos(db):
    db.upsert_article(
        url="https://a.com",
        source="bbc",
        language="en",
        title_orig="A",
        published_at=datetime(2026, 6, 6, tzinfo=timezone.utc),
        status=ArticleStatus.PUBLISHED,
    )
    artigos = [_artigo("https://a.com"), _artigo("https://b.com")]
    resultado = filter_unseen(db, artigos)
    assert len(resultado) == 1
    assert resultado[0].url == "https://b.com"
```

- [ ] **Step 2: Rodar para confirmar falha**

Run: `pytest tests/test_dedupe.py -v`
Expected: FAIL com "ModuleNotFoundError: No module named 'pipeline.dedupe'"

- [ ] **Step 3: Implementar `pipeline/dedupe.py`**

```python
"""Filtragem de artigos já processados."""
from __future__ import annotations

from pipeline.db import Database
from pipeline.fetcher import Article


def filter_unseen(db: Database, artigos: list[Article]) -> list[Article]:
    """Devolve apenas artigos cujos URLs nunca foram processados."""
    urls = [a.url for a in artigos]
    novos = set(db.filter_new_urls(urls))
    return [a for a in artigos if a.url in novos]
```

- [ ] **Step 4: Rodar testes**

Run: `pytest tests/test_dedupe.py -v`
Expected: 3 passed.

- [ ] **Step 5: Commit**

```bash
git add pipeline/dedupe.py tests/test_dedupe.py
git commit -m "feat(dedupe): filtro de URLs já processados"
```

---

## Task 5: Relevance

**Files:**
- Create: `pipeline/relevance.py`
- Create: `config/relevance.yaml`
- Create: `tests/test_relevance.py`

- [ ] **Step 1: Criar `config/relevance.yaml`**

```yaml
# Configuração de score de relevância para brasileiros na Europa

keywords_positivas:
  # Imigração e vida na Europa
  - brasileiro
  - brasileira
  - brasileiros
  - brasil
  - imigração
  - imigrante
  - visto
  - cidadania
  - residência
  - schengen
  # Trabalho/economia
  - emprego
  - mercado de trabalho
  - salário
  - inflação
  - eurozona
  # Política europeia
  - união europeia
  - parlamento europeu
  - eleições europeias
  # Inglês
  - brazilian
  - immigration
  - visa
  - citizenship
  - eu citizenship
  - schengen visa

keywords_negativas:
  # Esportes locais sem apelo internacional
  - bundesliga
  - serie a
  - premier league
  - allsvenskan
  - ligue 1
  # Celebridades regionais
  - eurovision
  - bachelorette

pesos:
  recencia_horas:        # mais recente = melhor
    "<6": 1.0
    "<12": 0.7
    "<24": 0.4
    "<48": 0.1
  fonte:
    bbc: 1.0
    reuters_europe: 1.0
    guardian_europe: 0.9
    svt_nyheter: 0.8
    dn_se: 0.8
    lemonde: 0.8
    spiegel: 0.8
    elpais: 0.8
    corriere: 0.7
  keyword_positiva: 0.3   # cada keyword positiva soma
  keyword_negativa: -0.5  # keyword negativa subtrai bastante

top_n: 10
```

- [ ] **Step 2: Escrever testes (falhando) em `tests/test_relevance.py`**

```python
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
    # o de maior score deve vir primeiro
    assert "brazilian" in top[0].title or "visa" in top[0].title
```

- [ ] **Step 3: Rodar para confirmar falha**

Run: `pytest tests/test_relevance.py -v`
Expected: FAIL com "ModuleNotFoundError: No module named 'pipeline.relevance'"

- [ ] **Step 4: Implementar `pipeline/relevance.py`**

```python
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
```

- [ ] **Step 5: Rodar testes**

Run: `pytest tests/test_relevance.py -v`
Expected: 6 passed.

- [ ] **Step 6: Commit**

```bash
git add pipeline/relevance.py config/relevance.yaml tests/test_relevance.py
git commit -m "feat(relevance): score e seleção top-N"
```

---

## Task 6: Processor (Claude API)

**Files:**
- Create: `pipeline/processor.py`
- Create: `config/prompts.yaml`
- Create: `tests/test_processor.py`

- [ ] **Step 1: Criar `config/prompts.yaml`**

```yaml
processor:
  model: claude-sonnet-4-6
  max_tokens: 1500
  temperature: 0.7
  system_prompt: |
    Você é o redator do "Cafezinho Europa", um site descontraído de notícias para brasileiros vivendo na Europa.

    Sua tarefa: receber um artigo no idioma original e devolver um post em português do Brasil, com tom leve e conversacional — como se você estivesse contando a notícia para um amigo tomando café. Não use jargão jornalístico-formal.

    Mantenha os fatos rigorosamente precisos. Não invente nada. Se algo não estiver claro no original, omita.

    Devolva APENAS JSON estrito, sem markdown, sem comentários, sem texto antes ou depois.

    Formato:
    {
      "titulo_pt": "string",
      "resumo_pt": "Parágrafo 1.\n\nParágrafo 2.\n\nParágrafo 3.",
      "tags": ["tag1", "tag2", "tag3"],
      "categoria": "Suécia | França | Alemanha | Espanha | Itália | Reino Unido | Europa | Mundo"
    }

    O resumo_pt deve ter exatamente 3 parágrafos curtos. Tags em minúsculas (3 a 5).

  user_template: |
    Artigo original ({language}, fonte: {source}):

    Título: {title}

    Conteúdo:
    {content}
```

- [ ] **Step 2: Escrever testes (falhando) em `tests/test_processor.py`**

```python
"""Testes do processor (Claude API)."""
import json
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest

from pipeline.fetcher import Article
from pipeline.processor import (
    ProcessedArticle,
    process_article,
    ProcessorError,
)


def _make_article() -> Article:
    return Article(
        url="https://bbc.com/x",
        source="bbc",
        language="en",
        title="Brazil and EU sign new trade deal",
        content="The new agreement covers...",
        published_at=datetime(2026, 6, 6, tzinfo=timezone.utc),
        fetched_at=datetime(2026, 6, 6, tzinfo=timezone.utc),
        default_category="Europa",
    )


def _fake_claude_response(content_json: dict, usage_input=2000, usage_output=800):
    """Constrói uma resposta fake do Claude SDK."""
    msg = MagicMock()
    msg.content = [MagicMock(text=json.dumps(content_json))]
    msg.usage = MagicMock(input_tokens=usage_input, output_tokens=usage_output)
    return msg


@pytest.mark.asyncio
async def test_process_article_sucesso():
    artigo = _make_article()
    fake_resp = _fake_claude_response({
        "titulo_pt": "Brasil e UE assinam novo acordo comercial",
        "resumo_pt": "Saiu fresquinho hoje...\n\nO acordo cobre...\n\nO impacto pra brasileiros...",
        "tags": ["brasil", "ue", "comércio"],
        "categoria": "Europa",
    })

    with patch("pipeline.processor._call_claude", return_value=fake_resp):
        result = await process_article(artigo, client=MagicMock(), config={})

    assert isinstance(result, ProcessedArticle)
    assert result.titulo_pt == "Brasil e UE assinam novo acordo comercial"
    assert result.categoria == "Europa"
    assert "brasil" in result.tags
    assert result.source_url == "https://bbc.com/x"
    assert result.source_name == "bbc"
    assert result.cost_usd > 0


@pytest.mark.asyncio
async def test_process_article_json_malformado_levanta():
    artigo = _make_article()
    fake_resp = MagicMock()
    fake_resp.content = [MagicMock(text="isso não é JSON")]
    fake_resp.usage = MagicMock(input_tokens=2000, output_tokens=10)

    with patch("pipeline.processor._call_claude", return_value=fake_resp):
        with pytest.raises(ProcessorError):
            await process_article(artigo, client=MagicMock(), config={})


@pytest.mark.asyncio
async def test_process_article_categoria_invalida_levanta():
    artigo = _make_article()
    fake_resp = _fake_claude_response({
        "titulo_pt": "x",
        "resumo_pt": "a\n\nb\n\nc",
        "tags": ["x"],
        "categoria": "Categoria Inexistente",
    })

    with patch("pipeline.processor._call_claude", return_value=fake_resp):
        with pytest.raises(ProcessorError):
            await process_article(artigo, client=MagicMock(), config={})
```

- [ ] **Step 3: Rodar para confirmar falha**

Run: `pytest tests/test_processor.py -v`
Expected: FAIL com "ModuleNotFoundError: No module named 'pipeline.processor'"

- [ ] **Step 4: Implementar `pipeline/processor.py`**

```python
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
```

- [ ] **Step 5: Rodar testes**

Run: `pytest tests/test_processor.py -v`
Expected: 3 passed.

- [ ] **Step 6: Commit**

```bash
git add pipeline/processor.py config/prompts.yaml tests/test_processor.py
git commit -m "feat(processor): integração com Claude para resumo+tradução"
```

---

## Task 7: Publisher (WordPress)

**Files:**
- Create: `pipeline/publisher.py`
- Create: `tests/test_publisher.py`

- [ ] **Step 1: Escrever testes (falhando) em `tests/test_publisher.py`**

```python
"""Testes do publisher de WordPress."""
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from pipeline.processor import ProcessedArticle
from pipeline.publisher import WordPressPublisher, PublishResult


def _make_processed() -> ProcessedArticle:
    return ProcessedArticle(
        titulo_pt="Brasil e UE assinam acordo",
        resumo_pt="Parágrafo 1.\n\nParágrafo 2.\n\nParágrafo 3.",
        tags=["brasil", "ue"],
        categoria="Europa",
        source_url="https://bbc.com/x",
        source_name="bbc",
        cost_usd=0.015,
    )


CATEGORY_MAP = {
    "Suécia": 2, "França": 3, "Alemanha": 4, "Espanha": 5,
    "Itália": 6, "Reino Unido": 7, "Europa": 8, "Mundo": 9,
}


@pytest.fixture
def publisher():
    return WordPressPublisher(
        base_url="https://cafezinhoeuropa.com",
        username="cafezinho-bot",
        app_password="xxxx xxxx xxxx xxxx xxxx xxxx",
        category_id_map=CATEGORY_MAP,
    )


@pytest.mark.asyncio
async def test_publish_sucesso(publisher):
    fake_response = MagicMock()
    fake_response.status_code = 201
    fake_response.json = MagicMock(return_value={"id": 42, "link": "https://x/post"})

    client_mock = MagicMock()
    client_mock.__aenter__ = AsyncMock(return_value=client_mock)
    client_mock.__aexit__ = AsyncMock(return_value=False)
    client_mock.post = AsyncMock(return_value=fake_response)

    with patch("httpx.AsyncClient", return_value=client_mock):
        result = await publisher.publish(_make_processed())

    assert isinstance(result, PublishResult)
    assert result.wp_post_id == 42
    assert result.wp_url == "https://x/post"


@pytest.mark.asyncio
async def test_publish_payload_inclui_fonte_e_categoria(publisher):
    fake_response = MagicMock()
    fake_response.status_code = 201
    fake_response.json = MagicMock(return_value={"id": 1, "link": "x"})

    captured = {}

    async def fake_post(url, **kwargs):
        captured["url"] = url
        captured["json"] = kwargs.get("json")
        return fake_response

    client_mock = MagicMock()
    client_mock.__aenter__ = AsyncMock(return_value=client_mock)
    client_mock.__aexit__ = AsyncMock(return_value=False)
    client_mock.post = AsyncMock(side_effect=fake_post)

    with patch("httpx.AsyncClient", return_value=client_mock):
        await publisher.publish(_make_processed())

    assert "wp-json/wp/v2/posts" in captured["url"]
    assert "Fonte:" in captured["json"]["content"]
    assert "https://bbc.com/x" in captured["json"]["content"]
    # categoria 'Europa' deve virar id 8 no payload
    assert captured["json"]["categories"] == [8]


@pytest.mark.asyncio
async def test_publish_categoria_desconhecida_levanta(publisher):
    artigo = ProcessedArticle(
        titulo_pt="x", resumo_pt="a\n\nb\n\nc",
        tags=["x"], categoria="Categoria Que Não Existe",
        source_url="x", source_name="bbc", cost_usd=0.01,
    )
    from pipeline.publisher import PublisherError
    with pytest.raises(PublisherError, match="Categoria"):
        await publisher.publish(artigo)


@pytest.mark.asyncio
async def test_publish_erro_401_levanta(publisher):
    fake_response = MagicMock()
    fake_response.status_code = 401
    fake_response.text = "Unauthorized"

    client_mock = MagicMock()
    client_mock.__aenter__ = AsyncMock(return_value=client_mock)
    client_mock.__aexit__ = AsyncMock(return_value=False)
    client_mock.post = AsyncMock(return_value=fake_response)

    with patch("httpx.AsyncClient", return_value=client_mock):
        with pytest.raises(Exception, match="401"):
            await publisher.publish(_make_processed())
```

- [ ] **Step 2: Rodar para confirmar falha**

Run: `pytest tests/test_publisher.py -v`
Expected: FAIL com "ModuleNotFoundError: No module named 'pipeline.publisher'"

- [ ] **Step 3: Implementar `pipeline/publisher.py`**

```python
"""Publicação no WordPress via REST API."""
from __future__ import annotations

import base64
import logging
from dataclasses import dataclass

import httpx
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from pipeline.processor import ProcessedArticle

logger = logging.getLogger(__name__)


class PublisherError(Exception):
    """Falha ao publicar (após retries)."""


@dataclass(frozen=True)
class PublishResult:
    wp_post_id: int
    wp_url: str


class WordPressPublisher:
    def __init__(
        self,
        *,
        base_url: str,
        username: str,
        app_password: str,
        category_id_map: dict[str, int],
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.username = username
        self.app_password = app_password
        self.category_id_map = category_id_map
        token = base64.b64encode(f"{username}:{app_password}".encode()).decode()
        self.auth_header = f"Basic {token}"

    def _build_html(self, article: ProcessedArticle) -> str:
        # parágrafos do resumo
        paragrafos = article.resumo_pt.split("\n\n")
        html_paragrafos = "\n".join(
            f"<p>{p.strip()}</p>" for p in paragrafos if p.strip()
        )
        # tags como texto no rodapé (sem usar WP taxonomy para simplicidade)
        tags_txt = ", ".join(article.tags)
        tags_html = f'<p><strong>Tags:</strong> {tags_txt}</p>'
        # crédito da fonte (obrigatório por direitos autorais)
        fonte = (
            f'<p><em>Fonte original: '
            f'<a href="{article.source_url}" rel="noopener nofollow" '
            f'target="_blank">{article.source_name.upper()}</a></em></p>'
        )
        return f"{html_paragrafos}\n{tags_html}\n{fonte}"

    @retry(
        retry=retry_if_exception_type((httpx.HTTPError, httpx.TimeoutException)),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=2, min=2, max=32),
        reraise=True,
    )
    async def publish(self, article: ProcessedArticle) -> PublishResult:
        cat_id = self.category_id_map.get(article.categoria)
        if cat_id is None:
            raise PublisherError(
                f"Categoria '{article.categoria}' não está no category_id_map. "
                f"Disponíveis: {sorted(self.category_id_map.keys())}"
            )

        payload = {
            "title": article.titulo_pt,
            "content": self._build_html(article),
            "status": "publish",
            "categories": [cat_id],
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{self.base_url}/wp-json/wp/v2/posts",
                headers={
                    "Authorization": self.auth_header,
                    "Content-Type": "application/json",
                },
                json=payload,
            )

        if response.status_code not in (200, 201):
            raise PublisherError(
                f"WordPress retornou {response.status_code}: {response.text[:200]}"
            )

        data = response.json()
        return PublishResult(wp_post_id=data["id"], wp_url=data["link"])
```

- [ ] **Step 4: Rodar testes**

Run: `pytest tests/test_publisher.py -v`
Expected: 3 passed.

- [ ] **Step 5: Commit**

```bash
git add pipeline/publisher.py tests/test_publisher.py
git commit -m "feat(publisher): publicação via WordPress REST API"
```

---

## Task 8: Main orchestrator + dry-run

**Files:**
- Create: `pipeline/main.py`
- Create: `tests/test_main.py`

- [ ] **Step 1: Escrever testes (falhando) em `tests/test_main.py`**

```python
"""Testes do orquestrador main."""
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from pipeline.fetcher import Article
from pipeline.main import run_pipeline


def _make_article(url: str) -> Article:
    return Article(
        url=url,
        source="bbc",
        language="en",
        title="Brazilian immigration to EU rises",
        content="The number of Brazilians moving to the EU has increased...",
        published_at=datetime.now(timezone.utc),
        fetched_at=datetime.now(timezone.utc),
        default_category="Europa",
    )


@pytest.mark.asyncio
async def test_pipeline_dry_run_nao_publica():
    artigos = [_make_article(f"https://x/{i}") for i in range(3)]

    with patch("pipeline.main.fetch_all", new=AsyncMock(return_value=artigos)), \
         patch("pipeline.main.load_sources", return_value=[]), \
         patch("pipeline.main.process_article", new=AsyncMock()) as mock_proc, \
         patch("pipeline.main.WordPressPublisher") as mock_pub_cls:

        mock_proc.return_value = MagicMock(
            titulo_pt="t", resumo_pt="a\n\nb\n\nc",
            tags=["x"], categoria="Europa",
            source_url="x", source_name="bbc", cost_usd=0.01,
        )

        summary = await run_pipeline(
            db_path=":memory:",
            dry_run=True,
        )

    mock_pub_cls.assert_not_called()
    assert summary["published"] == 0
    assert summary["processed"] >= 1


@pytest.mark.asyncio
async def test_pipeline_uma_falha_no_processor_nao_derruba_outros():
    artigos = [_make_article(f"https://x/{i}") for i in range(3)]

    from pipeline.processor import ProcessorError

    async def fake_process(article, **kwargs):
        if "1" in article.url:
            raise ProcessorError("simulado")
        return MagicMock(
            titulo_pt="t", resumo_pt="a\n\nb\n\nc",
            tags=["x"], categoria="Europa",
            source_url=article.url, source_name="bbc", cost_usd=0.01,
        )

    with patch("pipeline.main.fetch_all", new=AsyncMock(return_value=artigos)), \
         patch("pipeline.main.load_sources", return_value=[]), \
         patch("pipeline.main.process_article", new=fake_process):

        summary = await run_pipeline(
            db_path=":memory:",
            dry_run=True,
        )

    assert summary["failed"] == 1
    assert summary["processed"] >= 2


@pytest.mark.asyncio
async def test_pipeline_dedupe_evita_reprocessar():
    from pipeline.db import Database, ArticleStatus

    db = Database(":memory:")
    db.upsert_article(
        url="https://x/repetido",
        source="bbc", language="en", title_orig="t",
        published_at=datetime.now(timezone.utc),
        status=ArticleStatus.PUBLISHED,
    )

    artigos = [_make_article("https://x/repetido"), _make_article("https://x/novo")]

    with patch("pipeline.main.fetch_all", new=AsyncMock(return_value=artigos)), \
         patch("pipeline.main.load_sources", return_value=[]), \
         patch("pipeline.main.process_article", new=AsyncMock()) as mock_proc:
        mock_proc.return_value = MagicMock(
            titulo_pt="t", resumo_pt="a\n\nb\n\nc",
            tags=["x"], categoria="Europa",
            source_url="https://x/novo", source_name="bbc", cost_usd=0.01,
        )

        summary = await run_pipeline(
            db=db,
            dry_run=True,
        )

    # processou apenas 1 (o novo)
    assert mock_proc.call_count == 1
```

- [ ] **Step 2: Rodar para confirmar falha**

Run: `pytest tests/test_main.py -v`
Expected: FAIL com "ModuleNotFoundError: No module named 'pipeline.main'"

- [ ] **Step 3: Implementar `pipeline/main.py`**

```python
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
from pipeline.fetcher import fetch_all, load_sources
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
        logger.info("%d são novos (após dedupe)", len(novos))

        # 3. Relevância
        relevance_cfg = load_relevance_config("config/relevance.yaml")
        top = select_top(novos, relevance_cfg)
        logger.info("Selecionados top %d por relevância", len(top))

        # 4. Processar
        prompts_cfg = load_prompts_config("config/prompts.yaml")
        max_cost = float(os.getenv("MAX_DAILY_COST_USD", "1.00"))

        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise RuntimeError("ANTHROPIC_API_KEY não definido em .env")
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
```

- [ ] **Step 4: Rodar testes**

Run: `pytest tests/test_main.py -v`
Expected: 3 passed.

- [ ] **Step 5: Rodar suite completa**

Run: `pytest -v`
Expected: ~25–30 testes passando, todos em <5s.

- [ ] **Step 6: Commit**

```bash
git add pipeline/main.py tests/test_main.py
git commit -m "feat(main): orquestrador com dry-run e idempotência"
```

---

## Task 9: Smoke test com APIs reais

**Files:**
- Create: `tests/test_smoke.py`

- [ ] **Step 1: Implementar smoke test**

```python
"""Smoke test: integração com BBC RSS + Claude API real.

NÃO roda em pytest padrão; precisa ser invocado explicitamente:
    pytest tests/test_smoke.py -v -m smoke
"""
import os
from datetime import datetime, timezone

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
```

- [ ] **Step 2: Atualizar `pyproject.toml` com marker `smoke`**

Adicionar dentro de `[tool.pytest.ini_options]`:
```toml
markers = [
    "smoke: testes com APIs reais (não roda no CI padrão)",
]
```

- [ ] **Step 3: Configurar `.env` localmente com sua chave Anthropic**

```bash
cp .env.example .env
# editar .env e preencher ANTHROPIC_API_KEY
```

- [ ] **Step 4: Rodar smoke test**

Run: `pytest tests/test_smoke.py -v -m smoke`
Expected: PASS, com output mostrando título traduzido em pt-BR. Custo deve ser ~$0.01-0.03.

- [ ] **Step 5: Verificar que pytest padrão NÃO roda smoke por padrão**

Run: `pytest -v --ignore=tests/test_smoke.py`
Expected: todos os testes unitários passam, smoke não roda.

- [ ] **Step 6: Commit**

```bash
git add tests/test_smoke.py pyproject.toml
git commit -m "test(smoke): integração real com BBC + Claude"
```

---

# Parte B — Infraestrutura

Esta parte exige ações manuais (compra de serviços) e não tem TDD. Cada task é uma checklist operacional.

## Task 10: Comprar e configurar VPS Hetzner

**Files:**
- Create: `infra/setup-vps.md` (documentação dos passos)

- [ ] **Step 1: Criar conta na Hetzner Cloud**

Acessar https://www.hetzner.com/cloud → "Sign Up" → confirmar email.

- [ ] **Step 2: Provisionar VPS CX22**

Criar novo projeto "Cafezinho Europa" → adicionar servidor:
- Image: Ubuntu 24.04
- Type: CX22 (4 vCPU shared, 8 GB RAM)
- Location: Falkenstein, Alemanha (mais perto da Europa = melhor latência para leitores)
- SSH key: gerar localmente com `ssh-keygen -t ed25519 -C "cafezinho"` e adicionar a chave pública
- Name: `cafezinho-prod`

- [ ] **Step 3: Acessar VPS via SSH**

```bash
ssh root@<IP_DO_VPS>
```

- [ ] **Step 4: Atualizar sistema e criar usuário não-root**

```bash
apt update && apt upgrade -y
adduser cafezinho
usermod -aG sudo cafezinho
mkdir -p /home/cafezinho/.ssh
cp ~/.ssh/authorized_keys /home/cafezinho/.ssh/
chown -R cafezinho:cafezinho /home/cafezinho/.ssh
chmod 700 /home/cafezinho/.ssh
chmod 600 /home/cafezinho/.ssh/authorized_keys
```

- [ ] **Step 5: Desabilitar login root via SSH**

Editar `/etc/ssh/sshd_config`:
```
PermitRootLogin no
PasswordAuthentication no
```
Restart: `systemctl restart ssh`

Validar em outro terminal: `ssh cafezinho@<IP>` (deve funcionar) e `ssh root@<IP>` (deve falhar).

- [ ] **Step 6: Instalar Docker + Python**

```bash
ssh cafezinho@<IP>
sudo apt install -y docker.io docker-compose-v2 python3.12 python3.12-venv python3-pip git ufw fail2ban
sudo usermod -aG docker cafezinho
# logout/login para o grupo entrar em efeito
exit
ssh cafezinho@<IP>
docker --version  # confirmar instalação
```

- [ ] **Step 7: Configurar firewall (ufw)**

```bash
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow http
sudo ufw allow https
sudo ufw enable
```

- [ ] **Step 8: Documentar tudo em `infra/setup-vps.md`**

Salvar comandos e IP do VPS em arquivo local (NÃO commitar IP nem credenciais sensíveis no git).

- [ ] **Step 9: Commit**

```bash
git add infra/setup-vps.md
git commit -m "docs(infra): passos de setup do VPS Hetzner"
```

---

## Task 11: Comprar domínio e configurar DNS

- [ ] **Step 1: Verificar disponibilidade**

Checar `cafezinhoeuropa.com` em https://www.namecheap.com ou https://porkbun.com.

- [ ] **Step 2: Comprar domínio**

~$10–15/ano. Habilitar privacy WHOIS (geralmente grátis).

- [ ] **Step 3: Apontar DNS para o VPS**

No painel do registrar, criar records:
- `A` record: `@` → `<IP_DO_VPS>`
- `A` record: `www` → `<IP_DO_VPS>`

- [ ] **Step 4: Validar propagação**

Esperar 10–30 min e testar:
```bash
nslookup cafezinhoeuropa.com
# deve devolver o IP do VPS
```

- [ ] **Step 5: Documentar em `infra/setup-vps.md`**

Adicionar seção "Domínio" com registrar usado e configuração de DNS.

---

## Task 12: WordPress + Caddy via Docker

**Files:**
- Create: `infra/docker-compose.yml`
- Create: `infra/Caddyfile`

- [ ] **Step 1: Criar `infra/docker-compose.yml` localmente**

```yaml
services:
  wordpress:
    image: wordpress:6.7-php8.3-apache
    restart: unless-stopped
    environment:
      WORDPRESS_DB_HOST: db
      WORDPRESS_DB_USER: wp_user
      WORDPRESS_DB_PASSWORD: ${WP_DB_PASSWORD}
      WORDPRESS_DB_NAME: wordpress
    volumes:
      - wp_data:/var/www/html
    depends_on:
      - db

  db:
    image: mariadb:11
    restart: unless-stopped
    environment:
      MARIADB_DATABASE: wordpress
      MARIADB_USER: wp_user
      MARIADB_PASSWORD: ${WP_DB_PASSWORD}
      MARIADB_ROOT_PASSWORD: ${WP_DB_ROOT_PASSWORD}
    volumes:
      - db_data:/var/lib/mysql

  caddy:
    image: caddy:2-alpine
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./Caddyfile:/etc/caddy/Caddyfile
      - caddy_data:/data
      - caddy_config:/config
    depends_on:
      - wordpress

volumes:
  wp_data:
  db_data:
  caddy_data:
  caddy_config:
```

- [ ] **Step 2: Criar `infra/Caddyfile`**

```caddy
cafezinhoeuropa.com, www.cafezinhoeuropa.com {
    reverse_proxy wordpress:80
    encode gzip
    header {
        Strict-Transport-Security "max-age=31536000;"
        X-Content-Type-Options "nosniff"
        Referrer-Policy "strict-origin-when-cross-origin"
    }
}
```

- [ ] **Step 3: Copiar arquivos para o VPS e iniciar**

```bash
scp -r infra cafezinho@<IP>:/home/cafezinho/cafezinho/
ssh cafezinho@<IP>
cd /home/cafezinho/cafezinho/infra
echo "WP_DB_PASSWORD=$(openssl rand -hex 24)" > .env
echo "WP_DB_ROOT_PASSWORD=$(openssl rand -hex 24)" >> .env
docker compose up -d
docker compose ps   # confirmar 3 containers UP
```

- [ ] **Step 4: Completar setup do WordPress no browser**

Abrir https://cafezinhoeuropa.com no navegador. Caddy obtém TLS automaticamente (Let's Encrypt). Completar wizard do WordPress: nome do site, admin user, senha forte.

- [ ] **Step 5: Criar usuário `cafezinho-bot` no WordPress**

No painel WP: Users → Add New → role `Editor` (não Admin — princípio do menor privilégio).

- [ ] **Step 6: Gerar Application Password para o bot**

WP painel → Users → cafezinho-bot → "Application Passwords" → criar com nome "pipeline" → copiar valor (formato `xxxx xxxx xxxx xxxx xxxx xxxx`).

- [ ] **Step 7: Criar categorias no WordPress e capturar IDs**

Painel WP → Posts → Categories. Criar exatamente estas 8: **Suécia, França, Alemanha, Espanha, Itália, Reino Unido, Europa, Mundo**.

Após criar, capturar o ID de cada categoria (visível na URL ao editar a categoria, ex.: `?taxonomy=category&tag_ID=8` → id 8). Criar `config/wp_categories.yaml` no repositório local:

```yaml
# Mapa nome→ID das categorias do WordPress.
# Capturado manualmente após criar as categorias no painel WP.
categories:
  Suécia: 2
  França: 3
  Alemanha: 4
  Espanha: 5
  Itália: 6
  Reino Unido: 7
  Europa: 8
  Mundo: 9
```

(Os IDs reais vão depender da ordem de criação e do que já existe no WP — substitua pelos valores corretos do seu ambiente.)

- [ ] **Step 8: Commit dos arquivos infra**

```bash
git add infra/docker-compose.yml infra/Caddyfile config/wp_categories.yaml
git commit -m "infra: WordPress + Caddy + mapa de categorias"
```

---

## Task 13: Deploy do pipeline Python no VPS

- [ ] **Step 1: Clonar repositório no VPS**

```bash
ssh cafezinho@<IP>
git clone <URL_DO_REPO> ~/cafezinho-app
cd ~/cafezinho-app
```

Se ainda não tiver remoto: criar repo privado no GitHub e fazer `git push`.

- [ ] **Step 2: Criar venv e instalar dependências**

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

- [ ] **Step 3: Configurar `.env` no servidor**

```bash
cp .env.example .env
nano .env
# preencher:
# ANTHROPIC_API_KEY=sk-ant-... (chave real)
# WP_URL=https://cafezinhoeuropa.com
# WP_USERNAME=cafezinho-bot
# WP_APP_PASSWORD=<senha gerada no Task 12 step 6>
# HEALTHCHECK_URL=... (preencher após Task 14)
chmod 600 .env
```

- [ ] **Step 4: Rodar smoke test no VPS**

```bash
pytest tests/test_smoke.py -v -m smoke
```

Expected: PASS, mostrando 1 artigo traduzido em pt-BR.

- [ ] **Step 5: Rodar 1 vez em dry-run**

```bash
python -m pipeline.main --dry-run
```

Expected: imprime 10 artigos no console, sem publicar.

- [ ] **Step 6: Rodar 1 vez real (publicação verdadeira)**

```bash
python -m pipeline.main
```

Verificar no browser que ~10 posts apareceram no site. Revisar qualidade — se algo estiver ruim, ajustar `config/prompts.yaml` e rodar de novo.

---

## Task 14: Cron diário + healthcheck

- [ ] **Step 1: Criar conta em healthchecks.io**

Acessar https://healthchecks.io → criar conta gratuita → criar 1 check "Cafezinho diário":
- Schedule: cron `0 7 * * *`
- Grace time: 30 minutes
- Copiar URL do ping (formato `https://hc-ping.com/uuid-aqui`)

- [ ] **Step 2: Atualizar `.env` no VPS com `HEALTHCHECK_URL`**

```bash
ssh cafezinho@<IP>
nano ~/cafezinho-app/.env
# adicionar HEALTHCHECK_URL=https://hc-ping.com/uuid-aqui
```

- [ ] **Step 3: Adicionar ping no final de `pipeline/main.py`**

Modificar a função `main()` localmente:

```python
def main() -> int:
    parser = argparse.ArgumentParser(description="Cafezinho Europa pipeline")
    parser.add_argument("--dry-run", action="store_true", help="Não publica no WP")
    args = parser.parse_args()

    try:
        summary = asyncio.run(run_pipeline(dry_run=args.dry_run))
        logger.info("Resumo final: %s", summary)
        # ping healthcheck só em modo produção
        if not args.dry_run:
            hc_url = os.getenv("HEALTHCHECK_URL")
            if hc_url:
                try:
                    import httpx
                    httpx.get(hc_url, timeout=10.0)
                except Exception:
                    logger.warning("Falha ao pingar healthcheck")
        return 0
    except Exception:
        logger.exception("Pipeline falhou")
        # ping de fail (sufixo /fail)
        hc_url = os.getenv("HEALTHCHECK_URL")
        if hc_url:
            try:
                import httpx
                httpx.get(f"{hc_url}/fail", timeout=10.0)
            except Exception:
                pass
        return 1
```

- [ ] **Step 4: Commit e fazer pull no VPS**

```bash
# local:
git add pipeline/main.py
git commit -m "feat(main): integração com healthchecks.io"
git push

# no VPS:
cd ~/cafezinho-app
git pull
```

- [ ] **Step 5: Criar script wrapper para o cron**

No VPS, criar `~/cafezinho-app/run_daily.sh`:

```bash
#!/usr/bin/env bash
set -e
cd /home/cafezinho/cafezinho-app
source .venv/bin/activate
mkdir -p logs
python -m pipeline.main >> "logs/pipeline-$(date +%Y-%m-%d).log" 2>&1
```

```bash
chmod +x ~/cafezinho-app/run_daily.sh
```

- [ ] **Step 6: Configurar cron**

```bash
crontab -e
# adicionar linha:
0 7 * * * /home/cafezinho/cafezinho-app/run_daily.sh
```

- [ ] **Step 7: Validar cron**

Esperar até 07:00 UTC do dia seguinte. Após executar:
- Conferir https://healthchecks.io → check deve estar verde
- Conferir site → ~10 novos posts publicados
- Conferir `~/cafezinho-app/logs/pipeline-YYYY-MM-DD.log`

- [ ] **Step 8: Configurar rotação de logs**

Criar `/etc/logrotate.d/cafezinho` (com sudo):
```
/home/cafezinho/cafezinho-app/logs/*.log {
    daily
    rotate 30
    compress
    missingok
    notifempty
    copytruncate
}
```

- [ ] **Step 9: Backup diário do SQLite**

Adicionar segunda linha no crontab:
```
30 7 * * * cp /home/cafezinho/cafezinho-app/data/cafezinho.db /home/cafezinho/cafezinho-app/data/backup-$(date +\%Y\%m\%d).db && find /home/cafezinho/cafezinho-app/data/backup-*.db -mtime +7 -delete
```

Mantém backups dos últimos 7 dias.

- [ ] **Step 10: Documentar tudo em `infra/setup-vps.md`** e commit final

```bash
# local:
git add infra/setup-vps.md
git commit -m "docs(infra): documentação completa de deploy"
```

---

# Critérios de pronto (MVP)

O MVP está pronto quando todos abaixo forem verdadeiros:

- [ ] Todos os testes unitários passam (`pytest -v`)
- [ ] Smoke test passa com APIs reais
- [ ] VPS rodando com WordPress acessível em https://cafezinhoeuropa.com
- [ ] Cron diário publica ~10 posts por dia automaticamente
- [ ] Healthcheck verde em healthchecks.io
- [ ] Backup diário do SQLite funcionando
- [ ] QA manual da primeira semana valida qualidade dos resumos
- [ ] Categorias e tags aparecem corretamente nos posts

# Próximos passos (fora do MVP)

Após o MVP rodar estável por ~2 semanas, criar plano separado para Fase 2:
- Tema WordPress custom (usando skill `frontend-design`)
- Inscrição AdSense
- Yoast SEO
- Newsletter automatizada
- Páginas estáticas (Sobre, Contato, Política de Privacidade)
