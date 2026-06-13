# Cafezinho Europa

Pipeline automatizado de notícias da Europa em português do Brasil, com site WordPress editorial.

---

## Arquitetura

```
GitHub (85rqmryjgx-create/cafezinho-europa)
    ↓ git pull (manual ou após push)
Servidor de Produção (167.233.58.224)
    ├── cron 07:00 UTC → run_daily.sh → pipeline Python
    ├── Docker: WordPress + MariaDB + Caddy
    └── Site: https://cafezinhoeuropa.com
```

**Fluxo do pipeline:**
1. Busca RSS de fontes europeias (`config/sources.yaml`)
2. Deduplica por URL no banco SQLite (`data/cafezinho.db`)
3. Seleciona top-N por relevância (`config/relevance.yaml`)
4. Processa com Claude (traduz + resume em PT-BR, `config/prompts.yaml`)
5. Publica no WordPress via REST API com imagem og:image

---

## Servidor de Produção

| Item | Valor |
|------|-------|
| IP | `167.233.58.224` |
| Usuário SSH | `cafezinho` |
| Diretório | `/home/cafezinho/cafezinho-europa` |
| Domínio | `https://cafezinhoeuropa.com` |
| OS | Ubuntu 26.04 LTS |

### Containers Docker (via `infra/docker-compose.yml`)

| Container | Imagem | Função |
|-----------|--------|--------|
| `infra-wordpress-1` | `wordpress:6.7-php8.3-apache` | CMS editorial |
| `infra-db-1` | `mariadb:11` | Banco do WordPress |
| `infra-caddy-1` | `caddy:2-alpine` | Reverse proxy + SSL automático |

### Crontab do servidor

```
0 7 * * *    /home/cafezinho/cafezinho-europa/run_daily.sh
30 7 * * *   backup diário do SQLite (retém 7 dias)
```

---

## Arquivo `infra/.env` (NÃO commitado — criar manualmente no servidor)

```
WP_DB_PASSWORD=<senha do wp_user no MariaDB>
WP_DB_ROOT_PASSWORD=<senha root do MariaDB>
```

> **IMPORTANTE:** Este arquivo precisa existir em `~/cafezinho-europa/infra/.env` no servidor.
> Se sumir, o `docker compose up` sobe com senha em branco e o WordPress não conecta ao banco.
> Ver seção "Recovery do banco" abaixo se isso acontecer.

---

## Arquivo `.env` (raiz do projeto — NÃO commitado)

```
ANTHROPIC_API_KEY=sk-ant-...
WP_URL=https://cafezinhoeuropa.com
WP_USERNAME=cafezinho_pipeline
WP_APP_PASSWORD=xxxx xxxx xxxx xxxx xxxx xxxx
HEALTHCHECK_URL=https://hc-ping.com/<uuid>
MAX_DAILY_COST_USD=1.00
```

### Usuários WordPress

| Login | Role | Uso |
|-------|------|-----|
| `admin` | Administrator | Acesso ao painel |
| `cafezinho_pipeline` | Editor | Publicação automatizada via REST API |

> O `WP_APP_PASSWORD` é gerado em: WordPress Admin → Usuários → cafezinho_pipeline → Senhas de aplicativo

---

## Deploy — atualizar o servidor

```bash
# 1. No Windows local: push das mudanças
git push origin master:main

# 2. No servidor:
ssh cafezinho@167.233.58.224
cd ~/cafezinho-europa
git pull
cd infra
docker compose up -d
```

> Se o `docker-compose.yml` mudou (novos volumes, etc.), fazer `docker compose down && docker compose up -d`

---

## Plugin WordPress — cafezinho-weather

Localização no servidor: montado via bind mount em `infra/docker-compose.yml`:
```yaml
- ../plugins/cafezinho-weather:/var/www/html/wp-content/plugins/cafezinho-weather
```

Após `git pull` no servidor, o plugin já fica disponível. Para ativar se necessário:
```bash
docker exec infra-wordpress-1 php -r "
\$c = new mysqli('db','wp_user','<WP_DB_PASSWORD>','wordpress');
\$plugins = ['cafezinho-weather/cafezinho-weather.php'];
\$c->query(\"UPDATE wp_options SET option_value = '\".serialize(\$plugins).\"' WHERE option_name = 'active_plugins'\");
echo 'OK';
"
```

Para popular o cache de tempo manualmente:
```bash
curl -s "https://cafezinhoeuropa.com/wp-cron.php?doing_wp_cron"
```

---

## Recovery do banco MariaDB (senha perdida)

Se o `infra/.env` sumir e os containers forem reiniciados com senha em branco:

```bash
# 1. Para os containers dependentes
docker stop infra-wordpress-1 infra-db-1

# 2. Sobe o banco em modo de recuperação
docker run -d --name db-recovery \
  --volumes-from infra-db-1 \
  mariadb:11 \
  --skip-grant-tables --skip-networking=0
sleep 5

# 3. Reseta as senhas (escolha senhas fortes)
docker exec db-recovery mariadb -u root --connect-timeout=10 -e "
FLUSH PRIVILEGES;
ALTER USER 'root'@'localhost' IDENTIFIED BY '<nova-senha-root>';
ALTER USER 'wp_user'@'%' IDENTIFIED BY '<nova-senha-wp>';
FLUSH PRIVILEGES;
"

# 4. Remove container de recovery
docker stop db-recovery && docker rm db-recovery

# 5. Recria infra/.env com as novas senhas
cat > ~/cafezinho-europa/infra/.env << EOF
WP_DB_PASSWORD=<nova-senha-wp>
WP_DB_ROOT_PASSWORD=<nova-senha-root>
EOF

# 6. Sobe tudo
cd ~/cafezinho-europa/infra
docker compose up -d
```

---

## Setup local (desenvolvimento no Windows)

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# preencher .env com suas chaves
```

Subir o WordPress local:
```bash
cd infra
# Criar infra/.env com senhas de dev:
echo "WP_DB_PASSWORD=local-dev-password" > .env
echo "WP_DB_ROOT_PASSWORD=local-dev-root-password" >> .env
docker compose up -d
```

Site local: `http://localhost:8080/`
Admin local: `http://localhost:8080/wp-admin/` (login: `admin`)

### Rodar pipeline

```bash
python -m pipeline.main           # modo normal (publica)
python -m pipeline.main --dry-run # modo teste (não publica)
```

### Rodar testes

```bash
pytest -v
# Testes do plugin PHP (dentro do container):
docker exec infra-wordpress-1 bash -c "cd /var/www/html/wp-content/plugins/cafezinho-weather && vendor/bin/phpunit"
```

---

## Coluna semanal — "Cafezinho & Planeta, Urgente!"

Crônica satírica publicada todo domingo 08:00 UTC. O ritual semanal roda em
sessão Claude Code (skill `cronica-da-semana`); as opiniões do editor viram as
falas dos personagens (fichas em `config/cronica_prompt.md`).

```bash
python -m pipeline.cronica --listar                # notícias dos últimos 7 dias
python -m pipeline.cronica --agendar cronicas/2026-06-15-exemplo.md --titulo "Título"
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

---

## Estrutura do projeto

```
cafezinho-europa/
├── pipeline/          # Código Python do pipeline
│   ├── main.py        # Orquestrador
│   ├── fetcher.py     # Busca RSS
│   ├── dedupe.py      # Deduplicação
│   ├── relevance.py   # Score de relevância
│   ├── processor.py   # Integração Claude (tradução/resumo)
│   ├── publisher.py   # Publicação WordPress REST API
│   └── og_image.py    # Busca og:image
├── plugins/
│   └── cafezinho-weather/   # Plugin WordPress de previsão do tempo
├── infra/
│   ├── docker-compose.yml
│   ├── Caddyfile
│   └── themes/cafezinho/    # Tema editorial custom
├── config/
│   ├── sources.yaml         # Fontes RSS
│   ├── relevance.yaml       # Critérios de relevância
│   ├── prompts.yaml         # Prompts Claude
│   └── wp_categories.yaml   # Mapa categoria → ID no WP
├── data/
│   └── cafezinho.db         # SQLite (artigos processados)
├── run_daily.sh             # Script do cron
└── .env                     # Credenciais (não commitado)
```

---

Ver `docs/superpowers/specs/` para design completo e `docs/superpowers/plans/` para plano de implementação.
