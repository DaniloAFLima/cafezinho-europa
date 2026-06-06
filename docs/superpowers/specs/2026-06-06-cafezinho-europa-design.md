# Cafezinho Europa — Design Document

**Data**: 2026-06-06
**Status**: Draft para revisão
**Autor**: Danilo Lima (com assistência do Claude Code)

---

## 1. Visão geral

**Cafezinho Europa** é um site automatizado de notícias da Europa em português do Brasil, voltado para brasileiros que vivem no continente. O site agrega notícias de fontes em 6 idiomas (EN, SV, FR, DE, ES, IT), traduz e resume com IA, e publica diariamente, com um tom leve e conversacional — como alguém te contando a notícia tomando café.

### Marca

- **Nome**: Cafezinho Europa
- **Domínio**: `cafezinhoeuropa.com`
- **Tagline**: *"Seu cafezinho diário com as notícias da Europa"*
- **Tom**: rápido, leve, divertido, conversacional (não jornalístico-formal)
- **Público-alvo**: brasileiros vivendo na Europa (~milhões de pessoas)

### Objetivo de negócio

Construir um site com audiência e potencial de monetização (AdSense, parcerias, newsletter paga). Tecnologia é meio, não fim — toda decisão técnica deve favorecer **velocidade até audiência** e **qualidade do conteúdo**, não sofisticação.

### Métricas de sucesso (Fase 1)

- 5–10 artigos publicados/dia consistentemente, sem intervenção manual
- Custo operacional ≤ $25/mês
- Qualidade dos resumos suficiente para parecer escrito por humano (validado em QA semanal)
- Site no ar dentro de ~2 semanas após o início da implementação

---

## 2. Decisões principais

| Decisão | Escolha | Razão |
|---|---|---|
| Abordagem | Híbrida (Python + WordPress) | Python para IA (diferencial competitivo); WordPress para publicação/SEO (resolve trabalho difícil de graça) |
| Hospedagem | 1 VPS Hetzner CX22 | Custo baixo (~€4.50/mês), suficiente para o volume |
| Frontend | Tema WordPress custom | Identidade forte sem dobrar a complexidade; `frontend-design` constrói na implementação |
| Idiomas-fonte | EN, SV, FR, DE, ES, IT | Cobertura ampla → diferenciação vs. concorrentes |
| Volume | 5–10 artigos/dia | Sustenta qualidade + custo + SEO consistente |
| Orquestração | Cron + Python (sem n8n) | Menos dependências, mais controle, mais aprendizado |
| Tradução + resumo | Claude API (única chamada combinada) | Mais coerente e mais barato que separar; mantém tom "cafezinho" |
| Storage | SQLite | Single-file, sem servidor adicional, mais que suficiente para o volume |
| CMS | WordPress (auto-hospedado) | Melhor ecossistema de SEO, AdSense, plugins; padrão de mercado para sites de notícias |

---

## 3. Arquitetura

### 3.1 Visão de alto nível

```
[Cron diário 07:00 UTC]
        ↓
[Python: pipeline.main]
        │
        ├── 1. fetcher       → busca RSS multi-idioma em paralelo
        ├── 2. dedupe        → filtra URLs já vistos (SQLite)
        ├── 3. relevance     → score e top-N seleção
        ├── 4. processor     → Claude API: resumo + tradução em pt-BR
        ├── 5. publisher     → WordPress REST API
        └── 6. main          → loga em SQLite (`runs` table)
                ↓
        [WordPress no mesmo VPS]
                ↓
        [cafezinhoeuropa.com] → leitores
```

### 3.2 Infraestrutura

- **VPS**: Hetzner CX22 (4 vCPU shared, 8 GB RAM, 80 GB SSD) — ~€4.50/mês
- **SO**: Ubuntu 24.04 LTS
- **WordPress**: rodando em Docker no VPS (container `wordpress:latest` + MariaDB)
- **Script Python**: rodando no host (Python 3.12 via `apt`) com cron
- **SQLite**: arquivo único em `/opt/cafezinho/data/cafezinho.db`
- **Domínio**: `cafezinhoeuropa.com` (~$12/ano, qualquer registrar)
- **Healthcheck externo**: [healthchecks.io](https://healthchecks.io) — free tier
- **TLS**: Let's Encrypt via Caddy ou Nginx (gratuito)

### 3.3 Custo mensal estimado

| Item | Custo |
|---|---|
| VPS Hetzner CX22 | €4.50 (~$5) |
| Claude API (10 artigos × ~3k tokens/dia × 30 dias) | ~$4.50 |
| Domínio | ~$1 (anualizado) |
| Healthchecks.io | $0 (free tier) |
| **Total** | **~$10–12/mês** |

Margem para crescer até ~30 artigos/dia sem mudar o VPS.

---

## 4. Componentes (módulos Python)

Pipeline dividido em 6 módulos independentes. Cada um tem responsabilidade única, é testável isoladamente, e pode ser ajustado sem afetar os outros.

### 4.1 Estrutura de arquivos

```
cafezinho-europa/
├── pipeline/
│   ├── __init__.py
│   ├── fetcher.py
│   ├── dedupe.py
│   ├── relevance.py
│   ├── processor.py
│   ├── publisher.py
│   ├── main.py
│   └── db.py              # helpers de SQLite
├── config/
│   ├── sources.yaml       # feeds RSS por idioma
│   ├── prompts.yaml       # prompts do Claude
│   ├── relevance.yaml     # keywords e regras
│   └── .env               # API keys (não commitado)
├── data/
│   └── cafezinho.db       # SQLite (não commitado)
├── tests/
│   ├── fixtures/          # XMLs de RSS para testes
│   ├── test_fetcher.py
│   ├── test_dedupe.py
│   ├── test_relevance.py
│   ├── test_processor.py
│   ├── test_publisher.py
│   └── test_main.py
├── theme/                 # tema WordPress custom (Fase 2)
├── docs/
│   └── superpowers/specs/2026-06-06-cafezinho-europa-design.md
├── requirements.txt
└── README.md
```

### 4.2 `fetcher.py`

**Responsabilidade**: buscar artigos de feeds RSS multi-idioma.

- Lê `config/sources.yaml` (lista de feeds com idioma e categoria)
- Busca em paralelo (`asyncio` + `httpx.AsyncClient`)
- Parsing com `feedparser`
- Timeout por feed: 10s
- Devolve `List[Article]`

**Modelo `Article` (dataclass)**:
```python
@dataclass
class Article:
    url: str
    source: str           # ex: 'bbc', 'svt', 'lemonde'
    language: str         # 'en', 'sv', 'fr', 'de', 'es', 'it'
    title: str            # título no idioma original
    content: str          # corpo (do RSS; sem scraping no MVP)
    published_at: datetime
    fetched_at: datetime
```

### 4.3 `dedupe.py`

**Responsabilidade**: filtrar artigos já processados.

- Consulta `SELECT url FROM articles WHERE url IN (...)`
- Remove URLs já vistos (qualquer status: `published`, `skipped`, `failed`)
- Devolve apenas artigos novos

### 4.4 `relevance.py`

**Responsabilidade**: rankear e selecionar top-N artigos.

Score simples no MVP (configurável em `config/relevance.yaml`):
- **Recência**: artigos publicados há <24h pontuam mais
- **Keywords positivas**: termos relevantes para brasileiros na Europa (imigração, vistos, trabalho, brasileiros, Brasil, eleições europeias, etc.)
- **Keywords negativas**: esportes locais sem interesse internacional, fofocas de celebridades regionais
- **Fonte**: pesos diferentes (BBC > tabloide local)

Devolve top **10** (configurável).

### 4.5 `processor.py`

**Responsabilidade**: usar Claude para resumir + traduzir em uma chamada.

- Cliente: `anthropic.Anthropic` (SDK oficial)
- Modelo: `claude-sonnet-4-6` (custo/qualidade balanceados)
- Chamadas em paralelo (10 simultâneas via `asyncio`)
- Cada chamada: ~2k tokens input + ~1k output ≈ $0.015
- **Prompt** (em `config/prompts.yaml`, sem hardcode):

> Você está escrevendo para "Cafezinho Europa", um site descontraído de notícias para brasileiros vivendo na Europa.
>
> Sua tarefa: receber um artigo no idioma original e devolver um post em português do Brasil, com **tom leve e conversacional** — como se você estivesse contando a notícia para um amigo tomando café. Não use jargão jornalístico-formal.
>
> Mantenha os fatos rigorosamente precisos. Não invente nada. Se algo não estiver claro no original, omita.
>
> **Formato de saída (JSON estrito)**:
> ```json
> {
>   "titulo_pt": "...",
>   "resumo_pt": "Parágrafo 1...\n\nParágrafo 2...\n\nParágrafo 3...",
>   "tags": ["tag1", "tag2", "tag3"],
>   "categoria": "Suécia | França | Alemanha | Espanha | Itália | Europa | Mundo"
> }
> ```
>
> O `resumo_pt` deve ter exatamente 3 parágrafos curtos. Tags em minúsculas. Categoria deve ser uma das listadas.

Saída por artigo:
```python
@dataclass
class ProcessedArticle:
    titulo_pt: str
    resumo_pt: str
    tags: list[str]
    categoria: str
    source_url: str
    source_name: str
```

### 4.6 `publisher.py`

**Responsabilidade**: publicar no WordPress via REST API.

- Endpoint: `POST /wp-json/wp/v2/posts`
- Autenticação: Application Password (mais seguro que basic auth)
- Payload: título traduzido + corpo (3 parágrafos + rodapé com link da fonte) + categoria + tags
- Rodapé obrigatório (direitos autorais): *"Fonte: [Nome da fonte](URL original)"*

**Idempotência**:
1. Antes de chamar WP: marca artigo como `status='publishing'` no SQLite
2. Chama WP REST API
3. Em sucesso: atualiza para `status='published'` com `wp_post_id`
4. Em falha pós-publicação: próxima run vê `publishing`, consulta WP por título, reconcilia

### 4.7 `main.py`

**Responsabilidade**: orquestrar a pipeline.

- Cria entrada na tabela `runs`
- Encadeia: fetcher → dedupe → relevance → processor → publisher
- Loga totais (fetched, published, skipped, failed, cost_usd)
- Suporta flag `--dry-run`: roda tudo exceto o publisher (imprime na stdout)

---

## 5. Modelo de dados (SQLite)

```sql
-- Artigos processados (publicados, descartados ou falhados)
CREATE TABLE articles (
    url           TEXT PRIMARY KEY,
    source        TEXT NOT NULL,
    language      TEXT NOT NULL,
    title_orig    TEXT NOT NULL,
    published_at  TIMESTAMP NOT NULL,
    fetched_at    TIMESTAMP NOT NULL,
    status        TEXT NOT NULL,           -- 'publishing' | 'published' | 'skipped' | 'failed'
    wp_post_id    INTEGER,
    relevance     REAL,
    error_msg     TEXT
);
CREATE INDEX idx_articles_status ON articles(status);
CREATE INDEX idx_articles_fetched_at ON articles(fetched_at);

-- Execuções do pipeline (1 linha por dia)
CREATE TABLE runs (
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
```

---

## 6. Tratamento de erros

**Princípio**: uma falha individual nunca derruba a run inteira.

| Falha | Estratégia |
|---|---|
| RSS feed off / timeout / malformado | try/except por feed; loga e segue |
| Claude API rate limit (429) | Retry com backoff exponencial (3x: 2s → 8s → 32s) via `tenacity` |
| Claude erro de rede | Mesmo retry; marca `failed` se persistir |
| Claude JSON malformado | 1 retry com "responda apenas JSON válido"; marca `failed` se persistir |
| Claude recusa por política | Marca `skipped`, loga motivo, segue |
| WordPress API down | Retry 3x; mantém `status='publishing'`, próxima run reconcilia |
| WordPress auth falha (401) | Falha fatal da run + alerta (config errada, requer intervenção) |
| SQLite locked / disk full | Falha fatal + alerta |
| Cron não rodou | Healthcheck externo (healthchecks.io) detecta após 2h |

**Observabilidade**:
- Logs estruturados em `/var/log/cafezinho/pipeline-YYYY-MM-DD.log` (rotação 30 dias)
- Tabela `runs` com totais diários
- Healthcheck.io: ping ao terminar com sucesso; alerta se ausente >2h

---

## 7. Testes

**Filosofia**: testes proporcionais ao tamanho do projeto. Cobrir parsing de fontes externas, lógica de filtro, e caminho feliz fim-a-fim.

### 7.1 Unitários (pytest, ~25–30 testes)

| Módulo | O que testar |
|---|---|
| `fetcher.py` | Parsing de 3+ formatos RSS reais (fixtures em `tests/fixtures/`) |
| `dedupe.py` | Filtragem correta usando SQLite `:memory:` |
| `relevance.py` | Score e top-N com artigos sintéticos |
| `processor.py` | Mock do Anthropic SDK; parse de JSON válido/inválido/refusal |
| `publisher.py` | Mock `httpx.Client`; valida payload com categoria/tags/fonte |
| `main.py` | Integração com tudo mockado: 10→10, idempotência, 1 falha não derruba 9 |

Roda em <5 segundos. Sem rede.

### 7.2 Smoke test (1 teste com rede real)

- Busca 1 feed real (BBC)
- Chama Claude com 1 artigo real
- Valida JSON parseável em pt-BR
- **Não publica** (dry-run)
- Roda manualmente antes de cada deploy. Custo ~$0.02 por execução.

### 7.3 QA manual semanal

A cada 7 dias, ~5 minutos:
- Lê 3–5 posts da semana
- Checa: tradução natural, tom mantido, fatos corretos, links funcionando
- Se qualidade caiu: ajusta `prompts.yaml` (sem mexer em código)

### 7.4 Não-objetivos no MVP

- Testes de performance/carga
- Testes de browser/UI do tema (delegado ao trabalho da `frontend-design` na implementação)

---

## 8. Direção visual (tema WordPress custom)

### Conceito central

O site é o **cafezinho da manhã**: ritual rápido, caloroso, que prepara você pra encarar o dia.

### Princípios

1. **Calor sobre frio**: paleta com tons de café, não azuis frios típicos de news sites
2. **Tipografia com personalidade**: serifa moderna nos títulos (credibilidade jornalística), sans-serif super legível no corpo
3. **Leve, não bagunçado**: muito espaço em branco; post nunca parece longo
4. **Identidade por país**: cada artigo destaca o país de origem (bandeira elegante, não emoji genérico) — único e funcional para multi-país
5. **"Servido às 07h"**: timestamp como "fornada" do dia, reforçando o ritual diário

### Paleta sugerida (refinada pelo `frontend-design` na implementação)

- **Primária (expresso)**: `#3E2723`
- **Acento (caramelo)**: `#D7822F`
- **Fundo (creme)**: `#FAF6F0`
- **Texto (café escuro)**: `#1F1A17`

### Layout do MVP

- **Home**: grid de cards (3 colunas desktop, 1 mobile) com bandeira + título + resumo de 1 linha + tempo de leitura
- **Header**: categorias por país (Suécia, França, Alemanha, Espanha, Itália, Reino Unido, Europa, Mundo)
- **Single post**: leitura confortável; fonte original em destaque no topo
- **Newsletter signup** no rodapé de cada post (essencial para retenção/monetização)

### O que NÃO fazer

- Pop-ups agressivos
- Carrosséis na home
- Auto-play de vídeo
- Sidebars cheias de "trending"

---

## 9. Roadmap

### Fase 1 — MVP funcionando (semanas 1–2)
- VPS provisionado, Docker + WordPress + DB rodando
- Domínio comprado e apontado
- 6 módulos Python escritos e testados
- Cron diário ativo
- Tema WordPress básico (placeholder; visual refinado na Fase 2)
- Healthcheck externo configurado

### Fase 2 — Tema custom + AdSense (semanas 3–4)
- `frontend-design` cria tema WordPress refinado seguindo a direção visual
- Inscrição no Google AdSense
- Configuração de SEO (Yoast, schema.org)
- Página "Sobre" + "Contato" + "Política de Privacidade"

### Fase 3 — Crescimento (mês 2+)
- Newsletter automatizada (digesto semanal via Substack ou similar)
- Bot Telegram/X que publica resumos
- Análise de engajamento; ajuste de keywords e fontes
- Possível expansão de idiomas (PL, NL)

---

## 10. Decisões adiadas (fora do MVP)

- **Web scraping** para fontes sem RSS bom (Fase 2 se necessário)
- **DeepL como fallback de tradução** (Fase 2 se sueco com Claude sair ruim)
- **Multi-VPS / CDN** (só quando tráfego justificar)
- **Frontend headless (Next.js)** (revisitar se WordPress virar gargalo de UX)
- **Newsletter paga** (depende de audiência de Fase 3)

---

## 11. Riscos e mitigações

| Risco | Impacto | Mitigação |
|---|---|---|
| Qualidade de tradução cair em algum idioma | Alta — afeta retenção | QA manual semanal; prompt ajustável sem código; DeepL como fallback se necessário |
| Google penalizar conteúdo "agregado/AI" | Alta — afeta tráfego | Resumos com tom único + crédito da fonte + 3 parágrafos (não cópia); foco em valor para o leitor brasileiro |
| Custo de Claude API escalar inesperado | Média | Limite hard-coded no `main.py` (`MAX_DAILY_COST=$1`); aborta se exceder |
| Direitos autorais (DMCA) | Alta — pode tirar o site do ar | Resumos curtos (3 parágrafos), nunca artigo completo, sempre link para fonte original |
| VPS cair sem aviso | Baixa | Healthcheck externo notifica; backups diários do SQLite para storage externo |

---

## 12. Convenções de código

- **Linguagem**: Python 3.12
- **Style**: PEP 8 + `black` + `ruff`
- **Type hints**: obrigatórios em todas as funções públicas
- **Comentários**: em português (preferência do autor)
- **Random seed (onde aplicável)**: `12345`
- **Logs**: estruturados via `logging` stdlib + formato JSON
- **Configuração**: YAML files + `.env` para secrets (`python-dotenv`)
