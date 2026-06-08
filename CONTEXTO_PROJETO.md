# Contexto do Projeto — Cafezinho Europa

> Arquivo de memória do projeto. Registra o que foi construído, decisões tomadas,
> incidentes resolvidos e próximos passos. Atualizar a cada sessão de trabalho.
>
> **Última atualização:** 2026-06-08

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

### Estado final após esta sessão

- `https://cafezinhoeuropa.com` funcionando ✅
- Tema `cafezinho` ativo ✅
- Plugin `cafezinho-weather` ativo, widget ao vivo (Londres 17°, Paris 23°...) ✅
- Pipeline cron 07:00 UTC ativo ✅
- README.md atualizado com guia completo de recovery ✅

### Lição aprendida

O `infra/.env` **não é commitado** (correto, por segurança) mas precisa ser recriado
manualmente no servidor após qualquer rebuild. Guardar as senhas em um password manager.

---

## Arquitetura atual

```
GitHub (85rqmryjgx-create/cafezinho-europa)
    ↓ git push origin master:main  (do Windows local)
    ↓ git pull  (no servidor)

Servidor 167.233.58.224
├── cron 07:00 UTC
│   └── run_daily.sh
│       └── python -m pipeline.main
│           ├── fetcher.py    → RSS europeus
│           ├── dedupe.py     → SQLite
│           ├── relevance.py  → top-N
│           ├── processor.py  → Claude API
│           └── publisher.py  → WordPress REST API
│
└── Docker
    ├── caddy      → cafezinhoeuropa.com (SSL automático)
    ├── wordpress  → tema cafezinho + plugin cafezinho-weather
    └── mariadb    → banco WordPress
```

---

## Próximos passos

- [ ] QA visual completo do site com gstack browse (Node.js já instalado)
- [ ] Verificar se `WP_APP_PASSWORD` do usuário `cafezinho_pipeline` está válido no servidor
- [ ] Guardar senhas do servidor em password manager
- [ ] Phase B do widget de tempo — afinar visual e responsividade
- [ ] Monitorar primeiros runs do pipeline no servidor (ver `logs/pipeline-*.log`)
