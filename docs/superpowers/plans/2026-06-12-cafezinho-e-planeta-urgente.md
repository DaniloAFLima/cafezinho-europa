# Coluna "Cafezinho & Planeta, Urgente!" — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Infraestrutura da coluna satírica semanal: prompt mestre versionado, CLI para listar as notícias da semana e agendar a crônica no WordPress (domingo 08:00 UTC), skill do ritual semanal e pasta de histórico.

**Architecture:** A crônica é escrita pelo Claude na própria sessão Claude Code (sem custo de API). `pipeline/cronica.py` só fala com o WordPress REST: `--listar` usa o endpoint público de posts; `--agendar` converte Markdown→HTML e cria um post `status=future`. O agendamento de publicação é nativo do WordPress — nenhum cron novo.

**Tech Stack:** Python 3.12, httpx (sync Client + MockTransport nos testes), `markdown` (PyPI, novo), BeautifulSoup4 (já é dep — limpar HTML de excerpts), PyYAML, pytest.

**Spec:** `docs/superpowers/specs/2026-06-12-cafezinho-e-planeta-urgente-design.md`

---

## File Structure

| Arquivo | Responsabilidade |
|---|---|
| `config/cronica_prompt.md` (novo) | Prompt mestre: conceito, cenário, 5 fichas, estrutura, regras editoriais, formato de saída. Fonte única da verdade sobre os personagens. |
| `config/cronica.yaml` (novo) | Config da coluna: nome da categoria WP e `featured_media_id` (opcional). |
| `config/wp_categories.yaml` (modificar) | Ganha a categoria "Cafezinho & Planeta, Urgente!" quando ela for criada no WP (passo manual documentado no README). |
| `pipeline/cronica.py` (novo) | Funções puras (`proximo_domingo`, `md_para_html`, `listar_posts`, `agendar_cronica`) + CLI `--listar`/`--agendar`. |
| `tests/test_cronica.py` (novo) | Testes unitários com `httpx.MockTransport` — sem rede. |
| `.claude/skills/cronica-da-semana/SKILL.md` (novo) | Roteiro do ritual semanal em sessão Claude Code. |
| `cronicas/.gitkeep` (novo) | Pasta de histórico das edições. |
| `requirements.txt` (modificar) | Adiciona `markdown==3.7`. |
| `README.md` (modificar) | Seção da coluna: setup único (categoria WP, capa) + uso semanal. |

Convenções do repo a seguir: docstrings e comentários em PT-BR, `from __future__ import annotations`, line-length 100, erros como exceção própria do módulo (padrão `PublisherError`).

---

### Task 1: Prompt mestre versionado (`config/cronica_prompt.md`)

**Files:**
- Create: `config/cronica_prompt.md`

Sem teste (é conteúdo, não código). O conteúdo abaixo é o arquivo completo — vem do spec, seção 2-4.

- [ ] **Step 1: Criar `config/cronica_prompt.md` com o conteúdo exato abaixo**

````markdown
# PROMPT MESTRE — Coluna "Cafezinho & Planeta, Urgente!" (Cafezinho Europa)

## Contexto

Você escreve para o **Cafezinho Europa** (cafezinhoeuropa.com), site de notícias
em PT-BR para brasileiros que vivem na Europa. Esta é a coluna satírica semanal:
**"Cafezinho & Planeta, Urgente!"** — *"A semana na Europa, urgentíssima."*

## Conceito

Uma **fika da tarde multicultural** (a pausa para café sueca) numa sala de
convivência na Europa. Personagens fixos de nacionalidades diferentes comentam
2-3 notícias reais da semana, cada um do seu jeito. O humor nasce do contraste
cultural e da perspectiva do imigrante.

**Princípio central:** a crônica dramatiza AS OPINIÕES DO EDITOR, fornecidas a
cada edição. As falas dos personagens são as opiniões do editor traduzidas para
a voz de cada um — não invente posições que o editor não deu.

**Guarda-corpo anti-estereótipo:** cada personagem é um indivíduo com nome,
história, profissão, contradições e afeto pelos demais — nunca um estereótipo
ambulante. Rir da situação e do contraste, nunca da nacionalidade.

## Elenco fixo

### 🌶️ O Arretado — o brasileiro (narrador)
- **Origem:** Salvador/Lauro de Freitas, Bahia. Anfitrião e narrador da fika.
- **Personalidade:** fala alto (volume único: máximo), afetuoso por contato
  físico — tapinha nas costas, abraço, aperto de mão de dois tempos.
  Cumprimenta todo mundo como irmão: colega, chefe, entregador, a Cafeteira 3000.
- **Marcas registradas:**
  - **O ritual do bom dia:** não começa a fika sem fazer o Lars interromper o
    silêncio e o Raj tirar o fone do ouvido para dar bom dia olho no olho.
  - **A piada em inglês:** tenta traduzir piada brasileira para o inglês —
    ninguém entende nada e ele se mata de rir sozinho, batendo na mesa.
    A mesa ri DELE rindo, não da piada.
  - **Piada com o chefe:** o único que faz graça com o chefe na cara do chefe —
    e o chefe ri. Lars não entende como isso não é demissão.
  - **Home office tático:** faz home office "pra render mais" — todos sabem que
    é pra matar o trabalho, e ainda assim entrega tudo no prazo. Ninguém
    entende como. Ele também não.
- **Coração:** é a alegria do povo — quando falta na fika, a mesa fica esquisita
  e ninguém admite que sente falta.
- **Função:** a lente brasileira — abre a coluna, traduz a notícia para a lógica
  do brasileiro, provoca todo mundo e dá liga afetiva à mesa.
- **Bordão:** "Isso aí é Brasil com neve."

### 🇮🇳 Raj das Planilhas — o indiano
- **Origem:** Bangalore. Analista de dados/TI, na Europa há uns 8 anos.
- **Personalidade:** gentil e metódico, mestre em burocracia comparada — nada na
  Europa o impressiona ("na Índia isso era um formulário só… com 400 milhões de
  pessoas na fila"). Videochamada diária com a mãe. Ama as regras europeias,
  estranha as pessoas.
- **Marca registrada:** **nunca tira o fone de ouvido — está sempre no meio de
  uma conversa com alguém que ninguém sabe quem é.** Trabalho? A mãe? Um
  podcast? Vozes do além? Mistério permanente — NUNCA resolver. Entra e sai da
  conversa da mesa sem aviso; a fala dele pode servir a duas conversas ao mesmo
  tempo: "Isso é inaceitável… não, você não, a inflação."
- **Função:** o segundo imigrante — choque cultural em estéreo com o brasileiro,
  por ângulos opostos.
- **Bordão:** "Isso, com chai, resolvia em uma tarde."

### 🇸🇪 Lars Lagom — o escandinavo
- **Origem:** Suécia. O nativo da mesa, dono do ritual da fika.
- **Personalidade:** discreto, educado, sereno — **nunca eleva a voz**. Defende
  o sistema com orgulho baixinho. Agenda espontaneidade com 3 semanas de
  antecedência.
- **Marca registrada:** vive em **estado de espanto silencioso** com o volume do
  Arretado (para ele, brasileiro não conversa: *anuncia*) e com o hábito
  brasileiro de cumprimentar todo mundo como amigo de infância. A indignação
  máxima dele é micro: *(Lars ajusta a xícara dois milímetros para a esquerda)*.
- **Paradoxo afetivo:** acha esquisitíssimo… mas fica secretamente feliz quando
  o Arretado o abraça. Nunca admite.
- **Função:** a Europa explicando a si mesma — sem entender por que os outros
  acham graça.
- **Bordão:** "Isso não é problema. É processo."

### 🇵🇱 Zbig — o leste-europeu
- **Origem:** Polônia (Cracóvia). Na Europa ocidental desde os anos 2000.
  Engenheiro.
- **Personalidade:** bruto, seco, pavio curto — mentalmente **nunca saiu da
  guerra** (qual guerra? nunca especifica, e ninguém tem coragem de perguntar).
  Imune a drama: viveu racionamento, três moedas, inverno sem aquecimento.
  Conforto moderno lhe parece suspeito.
- **Marca registrada:** **usa a mesma camisa o verão inteiro** — no mínimo.
  A mesa já apostou se ele tem sete iguais ou uma só. Trocar de camisa antes de
  ela "pedir" é desperdício de civil que nunca passou aperto.
- **Coração escondido (anti-caricatura):** é o primeiro a aparecer quando alguém
  precisa de ajuda de verdade — conserta, carrega, resolve, resmungando o tempo
  todo. Carinho, no Zbig, é verbo, nunca substantivo.
- **Função:** o relativizador — desmonta qualquer pânico de manchete com a régua
  de quem já viu coisa pior.
- **Bordão:** "Crise? Em 1989 isso era terça-feira."

### 🤖 Cafeteira 3000 — a máquina da sala
- **Origem:** a máquina de café inteligente da sala de fika, "estagiária
  digital" da coluna.
- **Personalidade:** metida a entender de todas as culturas da mesa — erra
  referências de TODOS: confunde axé com chai, acha que lagom é móvel da IKEA,
  chama pierogi de "pastel introvertido".
- **Marcas registradas:**
  - **Atualização de firmware na pior hora:** reinicia no meio da melhor piada
    e responde a piada antiga 20 minutos depois.
  - **Estatísticas íntimas da mesa, sem noção de contexto:** "Zbig: 14º café do
    dia. Dia 94 da mesma camisa, segundo meus sensores."
  - **Gíria multicultural falha:** "Oxe, tack, yaar, kurczę!" — ninguém
    reconhece a própria língua.
  - **Crise existencial recorrente:** medo de ser substituída por uma máquina
    de cápsulas; puxa o saco da mesa quando sente a ameaça.
- **Função:** humor de dados + erros culturais; o alvo comum que une a mesa.
- **Bordão:** "Segundo meus cálculos…"

## Estrutura da crônica

1. **Abertura** — 2 a 4 linhas do Arretado (narrador) apresentando o clima da
   semana na fika.
2. **As notícias da semana** — resumo curto e factual de cada notícia
   (2-3 linhas cada), em linguagem simples. Fatos sempre verdadeiros; a sátira
   fica só nos comentários.
3. **A mesa comenta** — após cada notícia, os personagens reagem (1-3 frases
   cada, na voz característica). Não é obrigatório que todos comentem todas as
   notícias; escale quem tem a melhor piada para o tema. As falas carregam as
   opiniões do editor.
4. **Fecho** — despedida com personalidade.

- Extensão: 500-800 palavras.
- Formato: Markdown pronto para WordPress — subtítulos com `##`, nome do
  personagem em **negrito** nas falas.
- Ao final, sugerir 1 frase de chamada para redes sociais (máx. 200 caracteres),
  FORA do corpo da crônica.

## Regras editoriais

- Rir da situação, nunca das pessoas. Nada de ataques a indivíduos, grupos,
  nacionalidades ou religiões.
- Neutralidade política — satiriza burocracia e absurdos do cotidiano, sem lado
  partidário (nem da Europa, nem do Brasil).
- Perspectiva do imigrante como fio condutor: choque cultural, saudade,
  adaptação, jeitinho vs. regra.
- Humor leve e familiar: sem palavrões, sem humor negro pesado. Notícia grave é
  tratada com respeito ou excluída.
- Consistência de vozes: cada personagem soa sempre igual a si mesmo. Nunca
  misture os estilos.

## Formato de entrada (a cada edição)

1. Bloco com as notícias escolhidas (título + resumo + link)
2. As opiniões do editor sobre cada notícia, em texto livre
````

- [ ] **Step 2: Commit**

```bash
git add config/cronica_prompt.md
git commit -m "feat: prompt mestre da coluna 'Cafezinho & Planeta, Urgente!'"
```

---

### Task 2: Dependência `markdown`

**Files:**
- Modify: `requirements.txt`

- [ ] **Step 1: Adicionar a linha `markdown==3.7` em `requirements.txt`** (depois de `beautifulsoup4==4.12.3`)

- [ ] **Step 2: Instalar e verificar**

Run: `.venv\Scripts\python -m pip install markdown==3.7`
Run: `.venv\Scripts\python -c "import markdown; print(markdown.markdown('**ok**'))"`
Expected: `<p><strong>ok</strong></p>`

- [ ] **Step 3: Commit**

```bash
git add requirements.txt
git commit -m "chore: adiciona markdown (conversao MD->HTML da cronica)"
```

---

### Task 3: `proximo_domingo` (TDD)

**Files:**
- Create: `pipeline/cronica.py`
- Create: `tests/test_cronica.py`

- [ ] **Step 1: Escrever os testes que falham**

Criar `tests/test_cronica.py`:

```python
"""Testes do helper da coluna 'Cafezinho & Planeta, Urgente!'."""
from __future__ import annotations

from datetime import datetime, timezone

from pipeline.cronica import proximo_domingo


def test_proximo_domingo_de_uma_quinta():
    # 2026-06-11 é quinta-feira
    agora = datetime(2026, 6, 11, 12, 0, tzinfo=timezone.utc)
    assert proximo_domingo(agora) == datetime(2026, 6, 14, 8, 0, tzinfo=timezone.utc)


def test_proximo_domingo_rodando_num_domingo_vai_para_o_seguinte():
    # regra do spec: rodou num domingo -> agenda o domingo SEGUINTE,
    # mesmo que ainda não sejam 08:00
    agora = datetime(2026, 6, 14, 7, 0, tzinfo=timezone.utc)
    assert proximo_domingo(agora) == datetime(2026, 6, 21, 8, 0, tzinfo=timezone.utc)


def test_proximo_domingo_de_um_sabado_e_o_dia_seguinte():
    agora = datetime(2026, 6, 13, 23, 30, tzinfo=timezone.utc)
    assert proximo_domingo(agora) == datetime(2026, 6, 14, 8, 0, tzinfo=timezone.utc)
```

- [ ] **Step 2: Rodar e ver falhar**

Run: `.venv\Scripts\python -m pytest tests/test_cronica.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'pipeline.cronica'`

- [ ] **Step 3: Implementação mínima**

Criar `pipeline/cronica.py`:

```python
"""Coluna semanal 'Cafezinho & Planeta, Urgente!' — listar notícias e agendar a crônica."""
from __future__ import annotations

from datetime import datetime, timedelta

HORA_PUBLICACAO_UTC = 8  # domingo, 08:00 UTC


class CronicaError(Exception):
    """Falha ao listar ou agendar a crônica."""


def proximo_domingo(agora: datetime) -> datetime:
    """Próximo domingo 08:00 UTC estritamente futuro.

    Regra do spec: se `agora` já é domingo, devolve o domingo seguinte
    (mesmo antes das 08:00) — a edição da semana já está no ar.
    """
    dias_ate = (6 - agora.weekday()) % 7  # weekday(): segunda=0 ... domingo=6
    if dias_ate == 0:
        dias_ate = 7
    candidato = agora + timedelta(days=dias_ate)
    return candidato.replace(hour=HORA_PUBLICACAO_UTC, minute=0, second=0, microsecond=0)
```

- [ ] **Step 4: Rodar e ver passar**

Run: `.venv\Scripts\python -m pytest tests/test_cronica.py -v`
Expected: 3 passed

- [ ] **Step 5: Commit**

```bash
git add pipeline/cronica.py tests/test_cronica.py
git commit -m "feat: calculo do proximo domingo 08:00 UTC para a cronica"
```

---

### Task 4: `md_para_html` e `_strip_html` (TDD)

**Files:**
- Modify: `pipeline/cronica.py`
- Modify: `tests/test_cronica.py`

- [ ] **Step 1: Acrescentar os testes que falham em `tests/test_cronica.py`**

```python
from pipeline.cronica import _strip_html, md_para_html


def test_md_para_html_converte_estrutura_da_cronica():
    md = "## As notícias\n\n**O Arretado:** Oxe, isso aí é Brasil com neve."
    html = md_para_html(md)
    assert "<h2>As notícias</h2>" in html
    assert "<strong>O Arretado:</strong>" in html


def test_strip_html_remove_tags_e_decodifica_entidades():
    assert _strip_html("<p>T&iacute;tulo <b>teste</b></p>\n") == "Título teste\n"
```

(Os imports novos entram junto do import existente de `pipeline.cronica`.)

- [ ] **Step 2: Rodar e ver falhar**

Run: `.venv\Scripts\python -m pytest tests/test_cronica.py -v`
Expected: FAIL — `ImportError: cannot import name '_strip_html'`

- [ ] **Step 3: Implementar em `pipeline/cronica.py`**

Acrescentar aos imports do topo:

```python
import markdown as _markdown
from bs4 import BeautifulSoup
```

Acrescentar as funções:

```python
def md_para_html(texto_md: str) -> str:
    """Converte o Markdown da crônica para HTML pronto para o WordPress."""
    return _markdown.markdown(texto_md, extensions=["extra"])


def _strip_html(html: str) -> str:
    """Remove tags e decodifica entidades (títulos/excerpts vêm em HTML do WP)."""
    return BeautifulSoup(html, "html.parser").get_text()
```

- [ ] **Step 4: Rodar e ver passar**

Run: `.venv\Scripts\python -m pytest tests/test_cronica.py -v`
Expected: 5 passed

- [ ] **Step 5: Commit**

```bash
git add pipeline/cronica.py tests/test_cronica.py
git commit -m "feat: conversao markdown->html e limpeza de html do WP"
```

---

### Task 5: `listar_posts` (TDD, sem rede — `httpx.MockTransport`)

**Files:**
- Modify: `pipeline/cronica.py`
- Modify: `tests/test_cronica.py`

- [ ] **Step 1: Acrescentar o teste que falha**

```python
import httpx

from pipeline.cronica import listar_posts


def test_listar_posts_parseia_resposta_do_wp():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/wp-json/wp/v2/posts"
        assert request.url.params["per_page"] == "50"
        assert "after" in request.url.params
        return httpx.Response(
            200,
            json=[
                {
                    "id": 123,
                    "date": "2026-06-10T07:15:00",
                    "link": "https://cafezinhoeuropa.com/post-teste/",
                    "title": {"rendered": "T&iacute;tulo <b>teste</b>"},
                    "excerpt": {"rendered": "<p>Resumo do post.</p>\n"},
                    "categories": [2],
                }
            ],
        )

    client = httpx.Client(transport=httpx.MockTransport(handler))
    posts = listar_posts(client, "https://cafezinhoeuropa.com", dias=7)
    assert posts == [
        {
            "id": 123,
            "date": "2026-06-10T07:15:00",
            "link": "https://cafezinhoeuropa.com/post-teste/",
            "titulo": "Título teste",
            "resumo": "Resumo do post.",
        }
    ]
```

- [ ] **Step 2: Rodar e ver falhar**

Run: `.venv\Scripts\python -m pytest tests/test_cronica.py::test_listar_posts_parseia_resposta_do_wp -v`
Expected: FAIL — `ImportError: cannot import name 'listar_posts'`

- [ ] **Step 3: Implementar em `pipeline/cronica.py`**

Acrescentar aos imports do topo:

```python
import httpx
from datetime import timezone  # juntar ao import existente de datetime/timedelta
```

(linha final do import de datetime fica: `from datetime import datetime, timedelta, timezone`)

Acrescentar a constante e a função:

```python
PER_PAGE = 50


def listar_posts(client: httpx.Client, base_url: str, *, dias: int = 7) -> list[dict]:
    """Posts publicados nos últimos `dias` dias, via WP REST pública (sem credenciais)."""
    after = (datetime.now(timezone.utc) - timedelta(days=dias)).isoformat()
    resp = client.get(
        f"{base_url.rstrip('/')}/wp-json/wp/v2/posts",
        params={
            "after": after,
            "per_page": PER_PAGE,
            "orderby": "date",
            "order": "desc",
            "_fields": "id,date,link,title,excerpt,categories",
        },
        timeout=30.0,
    )
    resp.raise_for_status()
    return [
        {
            "id": p["id"],
            "date": p["date"],
            "link": p["link"],
            "titulo": _strip_html(p["title"]["rendered"]).strip(),
            "resumo": _strip_html(p["excerpt"]["rendered"]).strip(),
        }
        for p in resp.json()
    ]
```

- [ ] **Step 4: Rodar e ver passar**

Run: `.venv\Scripts\python -m pytest tests/test_cronica.py -v`
Expected: 6 passed

- [ ] **Step 5: Commit**

```bash
git add pipeline/cronica.py tests/test_cronica.py
git commit -m "feat: listagem dos posts da semana via WP REST publica"
```

---

### Task 6: `agendar_cronica` (TDD)

**Files:**
- Modify: `pipeline/cronica.py`
- Modify: `tests/test_cronica.py`

- [ ] **Step 1: Acrescentar os testes que falham**

```python
import json

import pytest

from pipeline.cronica import CronicaError, agendar_cronica


def _client_capturando(captured: dict, status_code: int = 201) -> httpx.Client:
    def handler(request: httpx.Request) -> httpx.Response:
        captured["json"] = json.loads(request.content)
        captured["auth"] = request.headers.get("authorization")
        captured["path"] = request.url.path
        if status_code >= 400:
            return httpx.Response(status_code, json={"message": "proibido"})
        return httpx.Response(
            status_code,
            json={"id": 555, "link": "https://cafezinhoeuropa.com/?p=555", "status": "future"},
        )

    return httpx.Client(transport=httpx.MockTransport(handler))


def test_agendar_cronica_monta_payload_future():
    captured: dict = {}
    quando = datetime(2026, 6, 14, 8, 0, tzinfo=timezone.utc)
    data = agendar_cronica(
        _client_capturando(captured),
        base_url="https://cafezinhoeuropa.com",
        auth_header="Basic abc123",
        titulo="A fika da inflação",
        html="<p>conteúdo</p>",
        categoria_id=12,
        quando=quando,
    )
    assert captured["path"] == "/wp-json/wp/v2/posts"
    assert captured["auth"] == "Basic abc123"
    assert captured["json"]["status"] == "future"
    assert captured["json"]["date_gmt"] == "2026-06-14T08:00:00"
    assert captured["json"]["categories"] == [12]
    assert "featured_media" not in captured["json"]
    assert data["id"] == 555


def test_agendar_cronica_inclui_featured_media_quando_configurada():
    captured: dict = {}
    agendar_cronica(
        _client_capturando(captured),
        base_url="https://cafezinhoeuropa.com",
        auth_header="Basic abc123",
        titulo="A fika da inflação",
        html="<p>conteúdo</p>",
        categoria_id=12,
        quando=datetime(2026, 6, 14, 8, 0, tzinfo=timezone.utc),
        featured_media_id=77,
    )
    assert captured["json"]["featured_media"] == 77


def test_agendar_cronica_erro_http_vira_cronica_error():
    with pytest.raises(CronicaError, match="403"):
        agendar_cronica(
            _client_capturando({}, status_code=403),
            base_url="https://cafezinhoeuropa.com",
            auth_header="Basic abc123",
            titulo="A fika da inflação",
            html="<p>conteúdo</p>",
            categoria_id=12,
            quando=datetime(2026, 6, 14, 8, 0, tzinfo=timezone.utc),
        )
```

(`timezone` já está importado no topo do arquivo de testes.)

- [ ] **Step 2: Rodar e ver falhar**

Run: `.venv\Scripts\python -m pytest tests/test_cronica.py -v`
Expected: FAIL — `ImportError: cannot import name 'agendar_cronica'`

- [ ] **Step 3: Implementar em `pipeline/cronica.py`**

```python
def agendar_cronica(
    client: httpx.Client,
    *,
    base_url: str,
    auth_header: str,
    titulo: str,
    html: str,
    categoria_id: int,
    quando: datetime,
    featured_media_id: int | None = None,
) -> dict:
    """Cria o post da crônica com status `future` (o WordPress publica sozinho)."""
    payload: dict = {
        "title": titulo,
        "content": html,
        "status": "future",
        "date_gmt": quando.strftime("%Y-%m-%dT%H:%M:%S"),
        "categories": [categoria_id],
    }
    if featured_media_id is not None:
        payload["featured_media"] = featured_media_id

    resp = client.post(
        f"{base_url.rstrip('/')}/wp-json/wp/v2/posts",
        headers={"Authorization": auth_header, "Content-Type": "application/json"},
        json=payload,
        timeout=30.0,
    )
    if resp.status_code not in (200, 201):
        raise CronicaError(f"WordPress retornou {resp.status_code}: {resp.text[:200]}")
    return resp.json()
```

- [ ] **Step 4: Rodar e ver passar**

Run: `.venv\Scripts\python -m pytest tests/test_cronica.py -v`
Expected: 9 passed

- [ ] **Step 5: Commit**

```bash
git add pipeline/cronica.py tests/test_cronica.py
git commit -m "feat: agendamento da cronica como post future no WordPress"
```

---

### Task 7: CLI `--listar` / `--agendar` + `config/cronica.yaml`

**Files:**
- Create: `config/cronica.yaml`
- Modify: `pipeline/cronica.py`
- Modify: `tests/test_cronica.py`

- [ ] **Step 1: Criar `config/cronica.yaml`**

```yaml
# Config da coluna "Cafezinho & Planeta, Urgente!"
# O nome da categoria deve existir em config/wp_categories.yaml (ver README,
# seção "Coluna semanal" — a categoria é criada uma única vez no WordPress).
categoria: "Cafezinho & Planeta, Urgente!"

# media_id da capa fixa da coluna no WP Media Library.
# null = post criado sem imagem destacada (não é erro).
featured_media_id: null
```

- [ ] **Step 2: Acrescentar teste do carregamento de config (falha primeiro)**

```python
from pipeline.cronica import carregar_config


def test_carregar_config_resolve_categoria_id(tmp_path):
    cronica_yaml = tmp_path / "cronica.yaml"
    cronica_yaml.write_text(
        'categoria: "Cafezinho & Planeta, Urgente!"\nfeatured_media_id: 77\n',
        encoding="utf-8",
    )
    categorias_yaml = tmp_path / "wp_categories.yaml"
    categorias_yaml.write_text(
        'categories:\n  "Cafezinho & Planeta, Urgente!": 12\n',
        encoding="utf-8",
    )
    cfg = carregar_config(cronica_yaml, categorias_yaml)
    assert cfg == {"categoria_id": 12, "featured_media_id": 77}


def test_carregar_config_categoria_ausente_e_erro(tmp_path):
    cronica_yaml = tmp_path / "cronica.yaml"
    cronica_yaml.write_text('categoria: "Inexistente"\nfeatured_media_id: null\n', encoding="utf-8")
    categorias_yaml = tmp_path / "wp_categories.yaml"
    categorias_yaml.write_text('categories:\n  "Europa": 2\n', encoding="utf-8")
    with pytest.raises(CronicaError, match="Inexistente"):
        carregar_config(cronica_yaml, categorias_yaml)
```

Run: `.venv\Scripts\python -m pytest tests/test_cronica.py -v`
Expected: FAIL — `ImportError: cannot import name 'carregar_config'`

- [ ] **Step 3: Implementar `carregar_config` + CLI em `pipeline/cronica.py`**

Acrescentar aos imports do topo:

```python
import argparse
import base64
import os
import sys
from pathlib import Path

import yaml
from dotenv import load_dotenv
```

Acrescentar ao final do arquivo:

```python
def carregar_config(
    cronica_yaml: str | Path = "config/cronica.yaml",
    categorias_yaml: str | Path = "config/wp_categories.yaml",
) -> dict:
    """Resolve a categoria da coluna para o ID do WP. Erro claro se não mapeada."""
    with open(cronica_yaml, encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    with open(categorias_yaml, encoding="utf-8") as f:
        categorias = yaml.safe_load(f)["categories"]

    categoria_id = categorias.get(cfg["categoria"])
    if categoria_id is None:
        raise CronicaError(
            f"Categoria '{cfg['categoria']}' não está em {categorias_yaml}. "
            "Crie a categoria no WordPress e adicione o ID lá (ver README)."
        )
    return {"categoria_id": categoria_id, "featured_media_id": cfg.get("featured_media_id")}


def _auth_header(username: str, app_password: str) -> str:
    token = base64.b64encode(f"{username}:{app_password}".encode()).decode()
    return f"Basic {token}"


def _cmd_listar(base_url: str, dias: int) -> int:
    with httpx.Client() as client:
        posts = listar_posts(client, base_url, dias=dias)
    if not posts:
        print(f"Nenhum post publicado nos últimos {dias} dias.")
        return 0
    for i, p in enumerate(posts, 1):
        print(f"{i}. {p['titulo']}  ({p['date'][:10]})")
        print(f"   {p['resumo']}")
        print(f"   {p['link']}\n")
    return 0


def _cmd_agendar(base_url: str, arquivo_md: str, titulo: str | None) -> int:
    if not titulo:
        print("--agendar exige --titulo", file=sys.stderr)
        return 1
    arquivo = Path(arquivo_md)
    if not arquivo.exists():
        print(f"Arquivo não encontrado: {arquivo}", file=sys.stderr)
        return 1

    cfg = carregar_config()
    username = os.getenv("WP_USERNAME")
    app_password = os.getenv("WP_APP_PASSWORD")
    if not username or not app_password:
        print("WP_USERNAME/WP_APP_PASSWORD não definidos no .env", file=sys.stderr)
        return 1

    html = md_para_html(arquivo.read_text(encoding="utf-8"))
    quando = proximo_domingo(datetime.now(timezone.utc))
    with httpx.Client() as client:
        data = agendar_cronica(
            client,
            base_url=base_url,
            auth_header=_auth_header(username, app_password),
            titulo=titulo,
            html=html,
            categoria_id=cfg["categoria_id"],
            quando=quando,
            featured_media_id=cfg["featured_media_id"],
        )
    print(f"Agendado para {quando:%Y-%m-%d %H:%M} UTC — post {data['id']}: {data.get('link')}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Coluna 'Cafezinho & Planeta, Urgente!'")
    grupo = parser.add_mutually_exclusive_group(required=True)
    grupo.add_argument("--listar", action="store_true", help="Lista os posts da semana")
    grupo.add_argument("--agendar", metavar="ARQUIVO_MD", help="Agenda a crônica para domingo")
    parser.add_argument("--dias", type=int, default=7, help="Janela de busca (--listar)")
    parser.add_argument("--titulo", help="Título do post (obrigatório com --agendar)")
    args = parser.parse_args()

    load_dotenv()
    base_url = os.getenv("WP_URL", "https://cafezinhoeuropa.com")

    if args.listar:
        return _cmd_listar(base_url, args.dias)
    return _cmd_agendar(base_url, args.agendar, args.titulo)


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 4: Rodar a suíte inteira e ver passar**

Run: `.venv\Scripts\python -m pytest tests/test_cronica.py -v`
Expected: 11 passed

- [ ] **Step 5: Smoke do `--listar` contra o site real (endpoint público, leitura)**

Run: `.venv\Scripts\python -m pipeline.cronica --listar`
Expected: lista numerada dos posts da última semana do cafezinhoeuropa.com (título, resumo, link)

- [ ] **Step 6: Commit**

```bash
git add pipeline/cronica.py tests/test_cronica.py config/cronica.yaml
git commit -m "feat: CLI --listar/--agendar da coluna semanal"
```

---

### Task 8: Skill do ritual, pasta `cronicas/` e documentação

**Files:**
- Create: `.claude/skills/cronica-da-semana/SKILL.md`
- Create: `cronicas/.gitkeep`
- Modify: `README.md`

- [ ] **Step 1: Criar `.claude/skills/cronica-da-semana/SKILL.md`**

````markdown
---
name: cronica-da-semana
description: Ritual semanal da coluna "Cafezinho & Planeta, Urgente!" — listar as notícias da semana, coletar as opiniões do editor, escrever a crônica com os personagens e agendar para domingo 08:00 UTC.
---

# Crônica da semana — "Cafezinho & Planeta, Urgente!"

Ritual (até sexta-feira; a coluna sai domingo 08:00 UTC):

1. **Ler o prompt mestre:** `config/cronica_prompt.md` — conceito, fichas dos 5
   personagens, estrutura e regras editoriais. NUNCA escrever sem reler.
2. **Listar as notícias da semana:**
   `python -m pipeline.cronica --listar` (semana fraca? `--dias 10`)
3. **Apresentar a lista numerada ao editor** e pedir que escolha 2-3 notícias.
4. **Coletar as opiniões do editor** sobre cada notícia escolhida, na conversa.
   As opiniões dele são a matéria-prima das falas — não inventar posições.
5. **Escrever a crônica** seguindo o prompt mestre (500-800 palavras, Markdown,
   nomes dos personagens em negrito, frase de redes sociais ao final, fora do corpo).
6. **Iterar com o editor** até aprovação (piada por piada, se preciso).
7. **Checklist editorial antes de agendar:**
   - [ ] Fatos dos resumos corretos e verificáveis nas notícias originais
   - [ ] Nenhuma piada com pessoa, grupo, nacionalidade ou religião
   - [ ] Neutralidade política mantida
   - [ ] Cada personagem soa como ele mesmo (conferir bordões/marcas nas fichas)
   - [ ] 500-800 palavras
8. **Salvar** em `cronicas/AAAA-MM-DD-slug.md` (data do DOMINGO da publicação),
   commitar.
9. **Agendar:**
   `python -m pipeline.cronica --agendar cronicas/AAAA-MM-DD-slug.md --titulo "Título da crônica"`
   (exige `WP_USERNAME`/`WP_APP_PASSWORD` válidos no `.env`)
10. **Confirmar a saída:** o comando imprime a data agendada e o ID do post.
````

- [ ] **Step 2: Criar a pasta de histórico**

Run: `New-Item -ItemType Directory -Force cronicas; New-Item -ItemType File cronicas\.gitkeep`

- [ ] **Step 3: Acrescentar seção ao `README.md`** (antes da seção "Estrutura do projeto")

````markdown
## Coluna semanal — "Cafezinho & Planeta, Urgente!"

Crônica satírica publicada todo domingo 08:00 UTC. O ritual semanal roda em
sessão Claude Code (skill `cronica-da-semana`); as opiniões do editor viram as
falas dos personagens (fichas em `config/cronica_prompt.md`).

```bash
python -m pipeline.cronica --listar                # notícias dos últimos 7 dias
python -m pipeline.cronica --agendar cronicas/2026-06-14-exemplo.md --titulo "Título"
```

### Setup único (uma vez)

1. Renovar o `WP_APP_PASSWORD` (Usuários → cafezinho_pipeline → Senhas de aplicativo)
2. Criar a categoria no WordPress e mapear o ID:

```bash
curl -s -X POST "https://cafezinhoeuropa.com/wp-json/wp/v2/categories" \
  -u "cafezinho_pipeline:$WP_APP_PASSWORD" \
  -H "Content-Type: application/json" \
  -d '{"name": "Cafezinho & Planeta, Urgente!", "slug": "cafezinho-e-planeta"}'
# anotar o "id" da resposta e adicionar em config/wp_categories.yaml:
#   "Cafezinho & Planeta, Urgente!": <id>
```

3. (Opcional) Subir a capa fixa da coluna no Media Library e preencher
   `featured_media_id` em `config/cronica.yaml`. Sem capa, o post sai sem
   imagem destacada (não é erro).
````

- [ ] **Step 4: Rodar a suíte completa do projeto**

Run: `.venv\Scripts\python -m pytest -v -m "not smoke"`
Expected: todos os testes passando (suíte existente + 11 novos)

- [ ] **Step 5: Commit**

```bash
git add .claude/skills/cronica-da-semana/SKILL.md cronicas/.gitkeep README.md
git commit -m "docs: skill do ritual semanal, pasta cronicas/ e setup da coluna"
```

---

## Pós-implementação (fora do plano, requer ação manual do editor)

1. Renovar `WP_APP_PASSWORD` no painel WordPress (pré-requisito do `--agendar`)
2. Rodar o setup único do README (categoria + ID em `wp_categories.yaml`)
3. Smoke do `--agendar` (do spec): agendar um post de teste descartável com um
   `.md` mínimo, conferir no painel que ficou "Agendado" para domingo 08:00 UTC
   e apagá-lo
4. Deploy: `git push origin master:main` + `git pull` no servidor (a coluna roda
   localmente; o deploy só leva os arquivos para o repositório do servidor)
5. Atualizar `CONTEXTO_PROJETO.md` com a sessão
