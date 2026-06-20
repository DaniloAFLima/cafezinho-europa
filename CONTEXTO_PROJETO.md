# Contexto do Projeto — Cafezinho Europa

> Arquivo de memória do projeto. Registra o que foi construído, decisões tomadas,
> incidentes resolvidos e próximos passos. Atualizar a cada sessão de trabalho.
>
> **Última atualização:** 2026-06-20

---

## O que é o Cafezinho Europa

Site editorial automatizado de notícias da Europa em português do Brasil.
Todo dia às 07h UTC, um pipeline Python busca artigos em fontes europeias,
traduz e resume com Claude (Anthropic), e publica no WordPress automaticamente.

**Site:** https://cafezinhoeuropa.com

---

## Sessão 1 — Scaffolding e Pipeline Python

### O que foi construído

- Scaffolding inicial do projeto (`pyproject.toml`, `.gitignore`, estrutura de pastas)
- Camada SQLite (`pipeline/db.py`) — tabelas `articles` e `runs`, controle de idempotência
- Busca de RSS multi-idioma (`pipeline/fetcher.py`) — suporta fontes em PT, EN, FR, DE, ES, IT
- Deduplicação por URL (`pipeline/dedupe.py`) — evita reprocessar artigos já publicados
- Score de relevância (`pipeline/relevance.py`) — seleciona top-N por critérios configuráveis
- Integração com Claude (`pipeline/processor.py`) — traduz título + resume em 5 parágrafos PT-BR
- Publicação via WordPress REST API (`pipeline/publisher.py`) — com autenticação por App Password
- Extração de `og:image` para imagem de destaque (`pipeline/og_image.py`)
- Orquestrador com dry-run e idempotência (`pipeline/main.py`)
- Suite de testes unitários e smoke test com BBC + Claude real

### Arquivos de configuração

| Arquivo | Conteúdo |
|---------|----------|
| `config/sources.yaml` | Fontes RSS (BBC, Le Monde, Der Spiegel, etc.) |
| `config/relevance.yaml` | Critérios de relevância e pontuação |
| `config/prompts.yaml` | Prompts do Claude (tradução, resumo, categoria) |
| `config/wp_categories.yaml` | Mapa de categorias → IDs no WordPress |

### Decisões técnicas

- **SQLite** em vez de Postgres — simplicidade, zero infraestrutura extra, suficiente para o volume
- **Claude** para tradução/resumo — melhor qualidade que MT automático para contexto editorial
- **WordPress REST API** — permite publicar sem acesso SSH ao servidor, via `WP_APP_PASSWORD`
- **Limite de custo** (`MAX_DAILY_COST_USD=1.00`) — proteção contra runaway de API

---

## Sessão 2 — Infraestrutura WordPress + Deploy

### O que foi construído

- Tema WordPress custom `cafezinho` (`infra/themes/cafezinho/`)
  - Design editorial: masthead com wordmark, banner de data, navegação por países
  - Paleta: caramelo profundo `#2A1812`, tipografia Fraunces + Newsreader
  - Templates: `header.php`, `footer.php`, `index.php`, `single.php`, `archive.php`, `page.php`, `404.php`
- Infraestrutura Docker (`infra/docker-compose.yml`)
  - WordPress 6.7 + PHP 8.3
  - MariaDB 11
  - Caddy 2 (reverse proxy + SSL automático via Let's Encrypt)
- Caddyfile configurado para `cafezinhoeuropa.com` + `www.cafezinhoeuropa.com`
- Script do cron (`run_daily.sh`) — ativa venv, roda pipeline, pinga healthcheck.io
- Crontab no servidor: `0 7 * * *` (07:00 UTC)
- Backup diário do SQLite: `30 7 * * *` (retém 7 dias)

### Servidor de produção

- **IP:** `167.233.58.224`
- **Usuário SSH:** `cafezinho`
- **Diretório do projeto:** `/home/cafezinho/cafezinho-europa`
- **OS:** Ubuntu 26.04 LTS
- **Domínio:** `cafezinhoeuropa.com` (DNS apontando para o IP acima)

---

## Sessão 3 — Plugin de Previsão do Tempo

### O que foi construído

Plugin WordPress `cafezinho-weather` (`plugins/cafezinho-weather/`):

| Arquivo | Função |
|---------|--------|
| `cafezinho-weather.php` | Bootstrap: registra cron, assets, hooks |
| `includes/class-weather-fetcher.php` | Busca paralela na Open-Meteo API (6 cidades) |
| `includes/class-weather-cache.php` | Cache em transient WordPress (TTL 3h, graceful fallback por cidade) |
| `includes/class-weather-cron.php` | WP-Cron a cada 2h com lock anti-duplicação |
| `includes/class-weather-widget.php` | Renderiza barra editorial com 6 tabs + painel dropdown |
| `includes/wmo-codes.php` | Mapa WMO code → ícone + descrição PT-BR |
| `assets/weather.css` | CSS editorial com gradientes de bandeiras, responsivo |
| `assets/weather.js` | Vanilla JS: tab switching, painel, teclado, click-outside |
| `config/cities.php` | 6 capitais: Lisboa, Londres, Paris, Berlim, Madrid, Roma |

**API:** Open-Meteo (gratuita, sem chave de API)

**Integração com o tema:** `header.php` chama `cafezinho_render_weather_bar()` no banner.

**Testes PHPUnit:** 16 testes passando (WeatherCache, WeatherFetcher, WmoCodes)

### Decisões técnicas

- Open-Meteo em vez de OpenWeatherMap — gratuita, sem rate limit, sem chave
- Transient WordPress (3h TTL) — evita requisições a cada pageview
- Fallback por cidade — se uma cidade falhar, as outras continuam aparecendo
- WP-Cron disparado a cada 2h — mais frequente que o TTL para garantir dados frescos

---

## Sessão 4 — Deploy do Plugin + Recovery do Servidor

### Problema descoberto

O repositório local (`master`) estava **20 commits à frente** do servidor (`origin/main`).
Todo o pipeline, publisher, og_image e weather plugin nunca tinham chegado ao servidor.

### O que foi feito

1. **Push do histórico completo:** `git push origin master:main`
2. **Pull + restart no servidor:** `git pull && docker compose down && docker compose up -d`
3. **Incidente — banco inacessível:** o arquivo `infra/.env` havia sumido do servidor.
   Com senha em branco, o WordPress não conseguia conectar ao MariaDB.
4. **Recovery do MariaDB:**
   - Subiu container temporário com `--skip-grant-tables`
   - Resetou senhas de `root` e `wp_user`
   - Recriou `infra/.env` com novas senhas
5. **Ativação do tema e plugin** via atualização direta no banco WordPress
6. **Cache do tempo populado** via `wp-cron.php`

### Lição aprendida

O `infra/.env` **não é commitado** (correto, por segurança) mas precisa ser recriado
manualmente no servidor após qualquer rebuild. Guardar as senhas em um password manager.

---

## Sessão 5 — Página de contato + experimentos de logo

### O que foi feito

- **Página de contato** (`/contato`) criada e deployada:
  - Template `infra/themes/cafezinho/page-contato.php` — 4 seções editoriais
  - E-mail `cafezinhoeuropa@gmail.com` com link `mailto:`
  - CSS dedicado em `main.css` com estilo editorial consistente
  - Página criada no banco WordPress via SQL (ID 100, slug `contato`)
- **WP_APP_PASSWORD** confirmado inválido — usuário `cafezinho-bot` sem permissão para criar páginas via REST API

### Experimentos de logo (todos revertidos)

Tentativas de adicionar elemento gráfico ao wordmark, todas revertidas ao original:
1. Fumaça substituindo ponto do "i" — difícil de posicionar sem ver ao vivo
2. Xícara como marca d'água atrás do wordmark — problema de z-index/posicionamento

**Lição:** Para iterações visuais, criar arquivo em `design/` e validar no browser antes de deployar.

---

## Sessão 6 — Coluna "Cafezinho & Planeta, Urgente!"

### Conceito

Coluna satírica semanal inspirada no "Casseta & Planeta". Nome final evita marca registrada.
Uma **fika da tarde multicultural** — os personagens fixos comentam 2-3 notícias reais
através das lentes das suas culturas. As falas dramatizam as **opiniões do editor** (Danilo).

### Elenco fixo (5 personagens)

| Personagem | Origem | Marca registrada |
|---|---|---|
| 🌶️ **Pedrinho do Mundo** | Brasil — paulista que viveu na Bahia | Fala alto, tapinha nas costas, piada em inglês que só ele entende, home office tático |
| 🇮🇳 **Raj das Planilhas** | Índia (Bangalore) | Nunca tira o fone — ninguém sabe com quem fala (trabalho? mãe? vozes do além?) |
| 🇸🇪 **Lars Lagom** | Suécia | Nunca levanta a voz, espanto silencioso com o volume dos brasileiros |
| 🇵🇱 **Zbig** | Polônia (Cracóvia) | Nunca saiu da guerra, usa a mesma camisa o verão inteiro |
| 🤖 **Cafeteira 3000** | — | Reinicia no meio da melhor piada, 12 estatísticas sem noção de contexto |

### Componentes entregues

| Arquivo | Função |
|---------|--------|
| `config/cronica_prompt.md` | Prompt mestre com 5 fichas completas, estrutura, regras editoriais |
| `config/cronica.yaml` | Categoria WP + featured_media_id da coluna |
| `config/wp_categories.yaml` | Mapa categorias→IDs, inclui `"Cafezinho & Planeta, Urgente!": 11` |
| `pipeline/cronica.py` | CLI: `--listar`, `--agendar`, `--auto` |
| `tests/test_cronica.py` | 17 testes unitários, todos passando |
| `run_cronica.sh` | Script do cron de sábado (ativa venv, roda `--auto`, loga) |
| `cronicas/` | Histórico de edições (`AAAA-MM-DD-slug.md`) |
| `design/cafezinho-e-planeta-icone.html` | Ícone SVG vetorial (3 variantes: 400px, 200px, 80px) |

### Edições publicadas

| Arquivo | Publicação | Tema | WP ID |
|---------|-----------|------|-------|
| `cronicas/2026-06-15-fique-no-seu-lugar.md` | 2026-06-15 | Europa e suas cercas (Suíça, Suécia, Ryanair) | 166 |
| `cronicas/2026-06-22-primeira-semana-de-copa.md` | 2026-06-22 | Copa do Mundo — primeira semana | (agendado pelo cron) |

### Decisões técnicas

- Agendamento nativo do WP: `status=future` + `date_gmt` → sem cron novo
- `--listar` usa endpoint público (`GET /wp-json/wp/v2/posts`) — sem credenciais
- `--agendar` exige `WP_USERNAME` + `WP_APP_PASSWORD` no `.env`
- `--auto`: detecta `.md` sem `.agendado` correspondente → agenda e cria marcador
- `proximo_domingo`: se rodar num domingo, agenda para o seguinte
- Markdown→HTML: biblioteca `markdown==3.7` (instalada no servidor)
- Fix para post "preso em future": incluir `date_gmt` atual junto com `status=publish` no PATCH

### Ritual semanal de produção da crônica

1. **Sexta-feira** — sessão Claude Code:
   - `python -m pipeline.cronica --listar` no servidor para ver notícias da semana
   - Busca complementar via WP REST API: `/wp-json/wp/v2/posts?search=TERMO` para cobertura total
   - Danilo dá **opiniões brutas** sobre cada notícia (1-3 frases, informal)
   - Claude transforma as opiniões em **diálogos entre personagens** — não escrever as falas direto
   - Salvar em `cronicas/AAAA-MM-DD-slug.md` + `git push`
2. **Sábado 10:00 UTC** — cron no servidor:
   - `run_cronica.sh` → `git pull` + `python -m pipeline.cronica --auto`
   - Detecta o `.md` novo, agenda para domingo 08:00 UTC, cria `.agendado`
3. **Domingo 08:00 UTC** — WordPress publica automaticamente

---

## Sessão 7 — Home sidebar + correção de bandeiras

### Widget lateral na home

Adicionado em `index.php` + `main.css`:

- Layout dois colunas na home: `.main-feed` (flex: 1) + `.home-sidebar` (280px fixo)
- Sidebar com `position: sticky; top: 20px` — acompanha scroll em desktop
- Em mobile (< 900px) empilha abaixo do feed, centralizado
- Widget `.sidebar-cronica` busca o último post publicado da categoria "Cafezinho & Planeta, Urgente!"
- Enquanto a categoria não existir no WP, exibe placeholder: *"A fika ainda não começou…"*
- Elenco de emojis dos personagens no rodapé do widget

### Correção de bandeiras CSS

As bandeiras são elementos `18×12px` gerados via CSS em `assets/main.css`.
Função PHP `cafezinho_country_flag_class()` em `functions.php` mapeia categoria → classe CSS.

| Bandeira | Problema | Correção |
|----------|----------|----------|
| 🇸🇪 Suécia (`.flag.se`) | Só listras horizontais — faltava barra vertical | Cruz nórdica: 2 gradientes empilhados (horizontal + vertical amarelos) |
| 🇬🇧 Reino Unido (`.flag.uk`) | Azul sólido `#012169` | Union Jack: 6 gradientes (fundo azul + X branco diagonal + cruz branca + cruz vermelha) |
| 🇪🇺 EU (`.flag.eu`) | 1 estrela centralizada | 12 pontos amarelos em círculo via `box-shadow` no `::after` |
| 🇫🇷 🇩🇪 🇪🇸 🇮🇹 | Corretas | Sem alteração |

### Cache bust

Bumped `style.css`: `Version: 1.0.0` → `1.1.0`
WordPress usa a versão como querystring (`main.css?ver=1.1.0`), invalidando o cache do browser.

### Deploy desta sessão

Para mudanças de PHP/CSS/config, **não é necessário reiniciar Docker** — basta `git pull`.
O WordPress serve os arquivos montados em volume diretamente.

```bash
# Do Windows:
git push origin master:main

# No servidor (SSH cafezinho@167.233.58.224):
cd /home/cafezinho/cafezinho-europa && git pull
```

---

## Sessão 8 — Automação da crônica + Edições 001 e 002

### O que foi construído

**`pipeline/cronica.py --auto`**
- Escaneia `cronicas/*.md` (ignora `.gitkeep`)
- Pula arquivos com `.agendado` correspondente (idempotência)
- Extrai título via `extrair_titulo_md()` — busca primeira linha `# H1`
- Converte para HTML, chama `agendar_cronica()`, grava marcador `filename.agendado`
- Retorna 0 se sem erros, 1 se algum arquivo falhou

**`run_cronica.sh`** — script do cron, instala em `/home/cafezinho/cafezinho-europa/`

**Crontab no servidor:** `0 10 * * 6` (sábados 10:00 UTC)

**WordPress configurado:**
- Categoria "Cafezinho & Planeta, Urgente!": ID = 11
- Usuário `cafezinho-bot` com App Password para o pipeline
- Credenciais em `/home/cafezinho/cafezinho-europa/.env`

**Fix publicação imediata:** ao publicar post `future` via PATCH, incluir `date_gmt` atual junto com `status=publish`, caso contrário o WP mantém status `future`.

**Edição 001 — "Fique no Seu Lugar!"** (WP ID 166):
- Publicada imediatamente via PATCH direto na API (o `--auto` rodou no domingo, quando `proximo_domingo` agendaria para daqui 7 dias)
- Tema: cercas da Europa — imigração Suíça, lei penal Suécia, Ryanair separando famílias

**Edição 002 — "Primeira Semana de Copa"** (agendado para 2026-06-22):
- `cronicas/2026-06-22-primeira-semana-de-copa.md`
- Tema: Copa do Mundo — Brasil empata e vence, Suécia goleia, Zbig e Giuseppe sem time
- Giuseppe: engenheiro italiano, **personagem convidado** desta edição (não fixo)
  - Argumento cômico recorrente: "Ancelotti é italiano, portanto tecnicamente…"
  - Zbig interrompe toda vez com "Não."
- Cafeteira 3000 sofisticada: análise preditiva que chega à definição de vitória depois de 3 dias

### Lições do processo editorial

- Danilo dá **opiniões brutas** (1-3 frases, informal) — Claude converte em diálogos
- Edição 001 foi considerada "pobre" por ter pouco bate-bola entre personagens
- Edição 002: mais texto, mais réplicas, Lars fez um discurso, Giuseppe e Zbig formaram dupla cômica
- Para buscar notícias da semana: `--listar` + busca extra via REST API por palavra-chave

---

## Arquitetura atual (v1.2.0)

```
GitHub (85rqmryjgx-create/cafezinho-europa)
    ↓ git push origin master  (do Windows local)
    ↓ git pull  (no servidor — /home/cafezinho/cafezinho-europa)

Servidor 167.233.58.224
├── cron 07:00 UTC diário
│   └── run_daily.sh → python -m pipeline.main
│       ├── fetcher.py    → RSS europeus
│       ├── dedupe.py     → SQLite
│       ├── relevance.py  → top-N
│       ├── processor.py  → Claude API
│       └── publisher.py  → WordPress REST API
│
├── cron 10:00 UTC sábados
│   └── run_cronica.sh → python -m pipeline.cronica --auto
│       ├── detecta cronicas/*.md sem .agendado
│       ├── extrai título H1
│       ├── POST /wp-json/wp/v2/posts (status=future, próximo domingo 08:00 UTC)
│       └── cria cronicas/arquivo.agendado (marcador de idempotência)
│
└── Docker
    ├── caddy      → cafezinhoeuropa.com (SSL automático)
    ├── wordpress  → tema cafezinho v1.1.0 + plugin cafezinho-weather
    │   ├── home: hero + grid + sidebar (última crônica da categoria 11)
    │   └── bandeiras: FR ✅ SE ✅ DE ✅ ES ✅ IT ✅ UK ✅ EU ✅
    └── mariadb    → banco WordPress
```

---

## Próximos passos

### Fluxo semanal em curso (automático)
- Toda sexta: sessão Claude Code → escreve crônica → `git push`
- Sábado 10:00 UTC: cron agenda automaticamente para domingo
- Domingo 08:00 UTC: WordPress publica

### Backlog técnico
- [ ] Phase B do widget de tempo — afinar visual e responsividade
- [ ] Monitorar runs do pipeline no servidor (`logs/cronica-*.log`, `logs/pipeline-*.log`)
- [ ] Guardar senhas do servidor em password manager
- [ ] Ícone/imagem de capa para a categoria "Cafezinho & Planeta, Urgente!" (featured_media_id em `config/cronica.yaml`)

### Personagens convidados a explorar
- **Giuseppe** (italiano, engenheiro) — funcionou bem na edição 002, pode retornar quando o tema justificar
- Outros convidados eventuais: decidir a cada semana conforme a pauta
