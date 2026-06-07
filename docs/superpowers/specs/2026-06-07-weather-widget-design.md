# Widget de Previsão do Tempo — Design Document

**Data**: 2026-06-07
**Status**: Draft para revisão
**Autor**: Danilo Lima (com assistência do Claude Code)
**Relacionado**: `2026-06-06-cafezinho-europa-design.md` (Fase 2 do roadmap principal)

---

## 1. Visão geral

Adicionar ao **Cafezinho Europa** uma barra fina no topo do header com previsão do tempo para os 6 países cobertos pelo site. Reforça a identidade "cafezinho da manhã" — informação útil e cálida para começar o dia, sem competir com a manchete.

### Objetivo

- Aumentar utilidade e tempo de retenção: o leitor brasileiro na Europa olha o tempo do país onde mora antes/depois de ler a notícia.
- Reforçar o conceito "ritual da manhã" do site.
- Manter custo operacional ≈ $0 e complexidade baixa (plugin isolado, sem nova dependência paga).

### Países e cidades cobertos

Mesma lista das categorias de país do site, com a capital como cidade representativa:

| País | Cidade | Lat / Lon |
|---|---|---|
| Reino Unido | Londres | 51.5074, -0.1278 |
| França | Paris | 48.8566, 2.3522 |
| Alemanha | Berlim | 52.5200, 13.4050 |
| Espanha | Madri | 40.4168, -3.7038 |
| Itália | Roma | 41.9028, 12.4964 |
| Suécia | Estocolmo | 59.3293, 18.0686 |

### Métricas de sucesso

- Widget visível em 100% das pageviews do desktop e mobile.
- Cache acerta ≥99% das requisições (transient quase nunca vazio).
- Custo adicional: $0/mês (Open-Meteo é gratuito sem chave).
- Zero quebra do site se a API estiver indisponível.

---

## 2. Decisões principais

| Decisão | Escolha | Razão |
|---|---|---|
| Onde aparece | Barra fina no topo do header, abas por país | Sempre visível, discreto, não compete com manchete |
| Cidades | Uma capital por país (6 no total) | Simples, previsível, alinha com categorias existentes |
| Detalhe | Hoje + 2 dias (máx/mín + ícone WMO) | Útil para planejar; não inflar widget |
| Fonte de dados | Open-Meteo | Gratuita, sem chave, sem rate limit prático, dados ECMWF |
| Atualização | WP-Cron a cada 2h + transient cache | Rápido para o leitor, ~12 chamadas/dia para a API |
| Tipo de entrega | Plugin WordPress isolado (`cafezinho-weather`) | Desacopla do tema; reutilizável; testável; ativável/desativável |
| Front-end | HTML + CSS + ~30 linhas de vanilla JS | Sem framework; troca de aba puramente DOM |
| Idiomas do widget | Apenas pt-BR | Site é pt-BR; sem necessidade de i18n |

---

## 3. Arquitetura

### 3.1 Visão de alto nível

```
[WP-Cron a cada 2h]
        ↓
[Plugin cafezinho-weather (PHP)]
        │
        ├── Weather_Fetcher::fetch_all()
        │     └─→ Open-Meteo (6 chamadas paralelas via Requests::request_multiple)
        ├── Weather_Cache::merge_and_store()
        │     └─→ set_transient('cafezinho_weather', $data, 3h)
        └── Logs (cidades OK, cidades em fallback, latência)
                ↓
        [Header do tema chama cafezinho_render_weather_bar()]
                ↓
        Lê transient, gera HTML com todas as 6 cidades inline
                ↓
        [weather.js: troca de aba puramente DOM]
```

### 3.2 Por que plugin separado, não código no tema?

- O tema custom (Fase 2) ainda não existe quando o widget for desenvolvido.
- Plugin pode ser ativado já com o WordPress vanilla.
- Permite desativar widget sem mexer no tema (toggle de feature).
- Testes unitários (PHPUnit) ficam isolados em `wp-content/plugins/cafezinho-weather/tests/`.

### 3.3 Endpoint da API

Open-Meteo — uma chamada por cidade:

```
GET https://api.open-meteo.com/v1/forecast
  ?latitude={lat}
  &longitude={lon}
  &daily=temperature_2m_max,temperature_2m_min,weather_code
  &timezone=auto
  &forecast_days=3
```

Resposta de exemplo (campos relevantes):

```json
{
  "daily": {
    "time": ["2026-06-07", "2026-06-08", "2026-06-09"],
    "temperature_2m_max": [18.4, 19.1, 17.2],
    "temperature_2m_min": [11.0, 12.3, 10.5],
    "weather_code": [3, 61, 80]
  }
}
```

Sem chave, sem header de auth, sem cota nominal para nosso volume (~12 chamadas × 6 cidades = 72/dia).

### 3.4 Custo

| Item | Custo |
|---|---|
| Open-Meteo | $0 (gratuito) |
| WP-Cron | $0 (já incluso no WordPress) |
| Storage extra (transient = ~5 KB) | desprezível |
| **Total** | **$0/mês** |

---

## 4. Componentes (plugin PHP)

### 4.1 Estrutura de arquivos

```
wp-content/plugins/cafezinho-weather/
├── cafezinho-weather.php           # bootstrap + hooks
├── includes/
│   ├── class-weather-fetcher.php   # cliente Open-Meteo
│   ├── class-weather-cache.php     # leitura/escrita do transient
│   ├── class-weather-cron.php      # agendamento e handler WP-Cron
│   ├── class-weather-widget.php    # render do HTML da barra
│   ├── class-weather-admin.php     # página admin de status
│   └── wmo-codes.php               # mapa código WMO → ícone + descrição pt-BR
├── assets/
│   ├── weather.css
│   ├── weather.js                  # troca de aba vanilla
│   └── flags/                      # SVGs das 6 bandeiras
├── config/
│   └── cities.php                  # lat/lon + nomes
├── tests/
│   ├── test-weather-fetcher.php
│   ├── test-weather-cache.php
│   ├── test-wmo-codes.php
│   └── fixtures/
│       └── open-meteo-paris.json
└── bin/
    └── smoke-weather.php           # chama API real, dry-run de validação
```

### 4.2 `Weather_Fetcher`

Responsabilidade: buscar dados crus de cada cidade na Open-Meteo.

- `fetch_all(array $cities): array` — chama as 6 cidades em paralelo via `Requests::request_multiple` (já incluso no WordPress).
- `parse_response(array $raw): array` — extrai e valida os campos esperados; lança exceção se faltar chave.
- Timeout por chamada: **5 segundos**.
- Não escreve em cache nem em log diretamente; devolve estrutura normalizada.

### 4.3 `Weather_Cache`

Responsabilidade: gerenciar o transient `cafezinho_weather`.

- `get(): ?array` — devolve cache atual ou null.
- `merge_and_store(array $fresh): void` — para cada cidade no `$fresh`, atualiza; cidades ausentes mantêm a leitura anterior (degradação graciosa).
- TTL do transient: **3 horas** (margem em cima do cron de 2h).

### 4.4 `Weather_Cron`

Responsabilidade: agendar e executar o refresh periódico.

- Na ativação do plugin: `wp_schedule_event(time(), 'cafezinho_2h', 'cafezinho_weather_refresh')`.
- Registra intervalo custom `cafezinho_2h` = 7200s via filtro `cron_schedules`.
- Handler do hook: chama `Weather_Fetcher::fetch_all()` → `Weather_Cache::merge_and_store()`.
- Lock anti-stampede: `set_transient('cafezinho_weather_lock', 1, 60)` no início; libera no final.
- Na desativação do plugin: `wp_clear_scheduled_hook('cafezinho_weather_refresh')`.

### 4.5 `Weather_Widget`

Responsabilidade: renderizar o HTML da barra + painéis.

- Função pública `cafezinho_render_weather_bar(): void` (echo direto, sem return).
- Lê cache; se vazio, renderiza placeholder "Tempo carregando…" e dispara `wp_schedule_single_event` para refresh imediato.
- Gera 6 botões de aba (bandeira + label oculto para SR) + 6 painéis (um aberto por padrão, cinco com `hidden`).
- Determina aba ativa padrão:
  1. Se a página atual for categoria de país → abre nesse país.
  2. Caso contrário → abre em Paris (configurável via filter `cafezinho_weather_default_city`).
- Enfileira `weather.css` e `weather.js` apenas quando a função é chamada (não em toda página).

### 4.6 `Weather_Admin`

Página em `Configurações → Cafezinho Weather`:

- Última atualização (timestamp + "há X horas").
- Status por cidade: OK / em fallback (com timestamp da última leitura válida).
- Botão "Atualizar agora" (dispara o handler manualmente).
- Botão "Limpar cache".

### 4.7 `wmo-codes.php`

Mapa estático dos códigos WMO usados pela Open-Meteo para os 12 cenários que cobrimos:

| Códigos | Ícone | Descrição pt-BR |
|---|---|---|
| 0 | sun | Sol |
| 1, 2 | sun-cloud | Parcialmente nublado |
| 3 | cloud | Nublado |
| 45, 48 | fog | Neblina |
| 51, 53, 55 | drizzle | Garoa |
| 61, 63, 65 | rain | Chuva |
| 71, 73, 75 | snow | Neve |
| 80, 81, 82 | shower | Pancadas |
| 95 | thunderstorm | Trovoada |

Códigos fora dessa lista caem em `cloud` + "Indefinido" (degradação graciosa).

---

## 5. Modelo de dados (cache)

Estrutura armazenada no transient `cafezinho_weather`:

```php
[
  'updated_at' => 1717760400,           // unix timestamp
  'cities' => [
    'londres' => [
      'country'      => 'Reino Unido',
      'city'         => 'Londres',
      'flag'         => 'gb',           // slug do SVG em assets/flags/
      'fetched_at'   => 1717760400,
      'days' => [
        ['date' => '2026-06-07', 'max' => 18, 'min' => 11, 'code' => 3],
        ['date' => '2026-06-08', 'max' => 19, 'min' => 12, 'code' => 61],
        ['date' => '2026-06-09', 'max' => 17, 'min' => 10, 'code' => 80],
      ],
    ],
    'paris'     => [...],
    'berlim'    => [...],
    'madri'     => [...],
    'roma'      => [...],
    'estocolmo' => [...],
  ],
]
```

Cada cidade tem seu próprio `fetched_at` — assim o merge consegue saber qual leitura é mais recente quando uma chamada falha.

---

## 6. Tratamento de erros

**Princípio**: a barra do tempo nunca pode quebrar o site nem aparecer "errada". Em qualquer falha, degrada silenciosamente.

| Falha | Estratégia |
|---|---|
| 1 cidade falha no fetch | Mantém a leitura anterior dessa cidade (merge); loga warning |
| Todas as 6 cidades falham | Cache antigo não é sobrescrito; incrementa contador `cafezinho_weather_consecutive_failures` |
| Cache vazio (cold start) | Renderiza placeholder "Tempo carregando…"; dispara `wp_schedule_single_event` para refresh em background |
| Open-Meteo fora >24h | Cache antigo continua servindo; badge "atualizado há X horas" aparece quando idade >6h |
| WP-Cron não dispara (site de baixo tráfego no início) | Fallback: 1º pageview após TTL expirar agenda refresh em background, com lock para evitar stampede |
| Resposta com formato inesperado | Validação estrita (chaves + tipos); cidade entra em fallback; loga payload truncado |
| Plugin desativado | Função `cafezinho_render_weather_bar()` faz `function_exists()` check no tema → barra simplesmente não aparece |

**Observabilidade**:

- Logs no `error_log` do WordPress com prefixo `[cafezinho-weather]`.
- Página admin (`Weather_Admin`) com status por cidade.
- Contador `cafezinho_weather_consecutive_failures` exposto na admin; ≥6 falhas seguidas (12h) = banner de alerta vermelho na admin.

---

## 7. Testes

**Filosofia**: proporcional ao tamanho. Plugin pequeno em PHP não precisa do mesmo aparato dos módulos Python.

### 7.1 Unitários (PHPUnit, ~12 testes)

| Módulo | O que testar |
|---|---|
| `Weather_Fetcher::parse_response()` | JSON válido, JSON com chave faltando, JSON com tipo errado, JSON vazio |
| `Weather_Cache::merge_and_store()` | Fresh com 6/6 cidades; fresh com 4/6 (mantém 2 antigas); cache vazio inicial |
| `wmo-codes.php` | Cada código mapeado devolve ícone + descrição; código desconhecido devolve fallback |

Roda em <2 segundos. Sem rede. Fixtures de Open-Meteo em `tests/fixtures/`.

### 7.2 Smoke manual (`bin/smoke-weather.php`)

- Chama Open-Meteo de verdade para as 6 cidades.
- Valida resposta com `parse_response`.
- Imprime resumo na stdout.
- **Não escreve em cache nem aciona WordPress.**
- Rodado antes de cada deploy do plugin. Custo: $0.

### 7.3 QA visual pós-deploy

- Abrir o site em desktop e mobile.
- Verificar: 6 abas renderizadas, troca funciona, dados batem com smoke test.
- Verificar admin page mostra status verde nas 6 cidades.

### 7.4 Não-objetivos

- Testes de browser/Selenium (overkill para widget visual estático).
- Testes de carga (Open-Meteo absorve nosso volume sem problema).

---

## 8. Direção visual

### Conceito

A barra é parte do "ritual da manhã" — leve, cálida, igual ao resto do site. Não é um widget meteorológico genérico azul.

### Layout (desktop, ~40px de altura)

```
┌─────────────────────────────────────────────────────────────────┐
│ ☕ Tempo na Europa hoje   [🇬🇧] [🇫🇷] [🇩🇪] [🇪🇸] [🇮🇹] [🇸🇪]  │
└─────────────────────────────────────────────────────────────────┘
   ↓ aba ativa expande logo abaixo (slide suave, ~80px)
┌─────────────────────────────────────────────────────────────────┐
│ 🇫🇷 Paris    Hoje 18°/11° ☁️   Sáb 19°/12° 🌧   Dom 17°/10° ⛅  │
└─────────────────────────────────────────────────────────────────┘
```

### Comportamento

- País ativo padrão: se a página atual for categoria de país, abre nele; caso contrário, abre em Paris.
- Clique em aba: expansão DOM instantânea (todos os dados já estão no HTML).
- Reabrir mesma aba: colapsa (toggle).
- Sem auto-rotação, sem JS pesado — só `classList.toggle`.

### Paleta (encaixa em `2026-06-06-cafezinho-europa-design.md`)

- Fundo da barra: `#3E2723` (expresso)
- Texto: `#FAF6F0` (creme)
- Aba ativa: realce em `#D7822F` (caramelo)
- Ícones de tempo: SVG monocromáticos creme

### Tipografia

- Mesma sans-serif do corpo do site.
- 13px na barra de abas.
- 14px no painel expandido.
- Temperatura em destaque visual maior (16px, peso medium).

### Bandeiras

- SVGs reais (não emoji genérico).
- ~18px, cantos suavemente arredondados.
- Em `assets/flags/`: `gb.svg`, `fr.svg`, `de.svg`, `es.svg`, `it.svg`, `se.svg`.

### Mobile (<768px)

- Barra mantém ícones de bandeira; oculta o texto "Tempo na Europa hoje".
- Abas viram scroll horizontal se não couberem.
- Painel expandido empilha verticalmente os 3 dias.
- Altura total quando expandida: ~120px.

### Acessibilidade

- Cada aba é `<button>` com `aria-label="Tempo em Paris"` e `aria-expanded`.
- Painel com `role="region"` e `aria-live="polite"`.
- Contraste WCAG AA (creme em expresso passa).
- Funciona sem JS: por padrão renderiza o país default já expandido.

---

## 9. Roadmap

### Fase A — MVP do widget (1–2 dias de implementação)

- Plugin `cafezinho-weather` escrito e ativo.
- WP-Cron rodando a cada 2h.
- Barra renderizada no header via `wp_body_open` (enquanto o tema custom não está pronto).
- 6 cidades funcionando.
- Página admin com status.
- Testes PHPUnit + smoke.

### Fase B — Integração com o tema custom (junto da Fase 2 do projeto)

- `frontend-design` afina paleta/tipografia da barra para casar 100% com o tema.
- Animação de expansão refinada.
- Detecção automática de país-default pela categoria da página atual.

### Fase C — Melhorias opcionais (só se métricas justificarem)

- Adicionar mais cidades (ex.: Lisboa quando entrar Portugal nas fontes).
- Alertas climáticos (Open-Meteo tem endpoint de warnings).
- Pôr/nascer do sol no painel expandido.

---

## 10. Decisões adiadas (fora do escopo)

- **Geolocalização do leitor** — irrelevante: público é multi-país e mora em cidades diferentes.
- **Previsão estendida >3 dias** — ruído, baixa precisão, alonga o widget sem ganho.
- **Multi-idioma** — site é só pt-BR.
- **Histórico/gráficos** — não é app de meteorologia.
- **Múltiplas cidades por país** — pode entrar na Fase C se demanda surgir.

---

## 11. Riscos e mitigações

| Risco | Impacto | Mitigação |
|---|---|---|
| Open-Meteo mudar formato sem aviso | Médio — barra para de atualizar | Validação estrita em `parse_response`; cache antigo continua servindo; smoke test detecta antes do deploy |
| WP-Cron não disparar em site de baixo tráfego | Baixo (no início) | Fallback de refresh sob demanda no pageview |
| Bandeiras de SVG ficarem ruins em telas Retina | Baixo | SVG é vetorial; usar `viewBox` correto |
| Widget deixar header lento | Baixo | Tudo inline; sem AJAX no front; CSS/JS enfileirados só na função render |
| Conflito com plugin de cache de página (WP Rocket etc.) | Médio | Documentar que o transient deve ser ignorado pelo plugin de cache; admin mostra timestamp para validar |

---

## 12. Convenções

- **PHP**: 8.1+ (versão do WordPress recente).
- **Style**: WordPress Coding Standards (`phpcs` com `WordPress` ruleset).
- **Namespacing**: prefixo `Cafezinho_Weather_` em todas as classes (PSR-4 não exigido por ser plugin WP).
- **Comentários**: em português (mesma convenção do pipeline Python).
- **Logs**: `error_log()` com prefixo `[cafezinho-weather]`.
- **Configuração**: arquivos PHP em `config/` (sem YAML aqui — overkill para 6 cidades estáticas).
