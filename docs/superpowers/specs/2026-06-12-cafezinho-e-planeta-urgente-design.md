# Spec — Coluna semanal "Cafezinho & Planeta, Urgente!"

> Design validado em sessão de brainstorming em 2026-06-12.
> Substitui o conceito original do PDF `prompt-cronica-cafezinho-da-semana.pdf`
> (nome "Cafezinho da Semana", elenco de 4 brasileiros, cenário de boteco).

---

## 1. Visão geral

Coluna satírica semanal do Cafezinho Europa, publicada **todo domingo às 08:00 UTC**.

O conteúdo nasce de um ritual semanal (até sexta-feira) em sessão Claude Code:

1. Claude busca as notícias publicadas no site nos últimos 7 dias
2. O editor (Danilo) escolhe 2-3 notícias e **dá suas opiniões na conversa**
3. Claude escreve a crônica com os personagens fixos **encarnando as opiniões do editor**
4. Iteração até aprovação (piada por piada, se necessário)
5. O post é criado no WordPress com status `future`, agendado para domingo —
   o WordPress publica sozinho (agendamento nativo, sem cron novo)

**Princípio editorial central:** a coluna não é "sátira gerada por IA" — é a opinião
do editor, dramatizada pelas vozes dos personagens.

### Nome

**"Cafezinho & Planeta, Urgente!"** — riff em "Casseta & Planeta, Urgente!"
(memória afetiva da geração 40-50 anos), trocando a marca registrada "Casseta"
pela marca própria "Cafezinho". Decidido após avaliar alternativas
("Café Passado", "A Voz do Boteco", "Linha Cruzada", "Casseta e Planeta Europa" —
esta última descartada por risco de marca registrada).

Subtítulo sugerido: *"A semana na Europa, urgentíssima."*

---

## 2. Conceito e cenário

**Uma fika da tarde multicultural** — a pausa para café sueca, num escritório/sala
de convivência na Europa. Cada personagem reage à mesma notícia do seu jeito,
moldado pela sua cultura de origem. O humor nasce do contraste cultural e da
perspectiva do imigrante.

**Guarda-corpo anti-estereótipo:** cada personagem é um indivíduo com nome,
história, profissão, contradições e afeto pelos demais — nunca um estereótipo
ambulante. Rir da situação e do contraste, nunca da nacionalidade
(regra herdada do prompt original e mantida).

---

## 3. Elenco fixo (fichas de personagem)

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
    é pra matar o trabalho, e ainda assim ele entrega tudo no prazo.
    Ninguém entende como. Ele também não.
- **Coração do personagem:** é a alegria do povo — quando falta na fika, a mesa
  fica esquisita e ninguém admite que sente falta.
- **Função:** a lente brasileira — abre a coluna, traduz a notícia para a lógica
  do brasileiro, provoca todo mundo e dá liga afetiva à mesa.
- **Bordão:** *"Isso aí é Brasil com neve."*

### 🇮🇳 Raj das Planilhas — o indiano

- **Origem:** Bangalore. Analista de dados/TI, na Europa há uns 8 anos.
- **Personalidade:** gentil e metódico, mestre em burocracia comparada — nada na
  Europa o impressiona ("na Índia isso era um formulário só… com 400 milhões de
  pessoas na fila"). Videochamada diária com a mãe. Ama as regras europeias,
  estranha as pessoas.
- **Marca registrada:** **nunca tira o fone de ouvido — está sempre no meio de
  uma conversa com alguém que ninguém sabe quem é.** Trabalho? A mãe? Um podcast?
  Vozes do além? Mistério permanente, nunca resolvido (gag que não envelhece).
  Entra e sai da conversa da mesa sem aviso; a fala dele pode servir a duas
  conversas ao mesmo tempo: *"Isso é inaceitável… não, você não, a inflação."*
- **Função:** o segundo imigrante — choque cultural em estéreo com o brasileiro,
  por ângulos opostos.
- **Bordão:** *"Isso, com chai, resolvia em uma tarde."*

### 🇸🇪 Lars Lagom — o escandinavo

- **Origem:** Suécia. O nativo da mesa, dono do ritual da fika.
- **Personalidade:** discreto, educado, sereno — **nunca eleva a voz**. Defende o
  sistema com orgulho baixinho. Agenda espontaneidade com 3 semanas de antecedência.
- **Marca registrada:** vive em **estado de espanto silencioso** com o volume do
  Arretado (para ele, brasileiro não conversa: *anuncia*) e com o hábito brasileiro
  de **cumprimentar todo mundo como amigo de infância** — caixa do mercado,
  motorista de ônibus, desconhecido no elevador. A indignação máxima dele é micro:
  *(Lars ajusta a xícara dois milímetros para a esquerda)*.
- **Paradoxo afetivo:** acha esquisitíssimo… mas fica secretamente feliz quando
  o Arretado o abraça. Nunca admite.
- **Função:** a Europa explicando a si mesma — sem entender por que os outros
  acham graça.
- **Bordão:** *"Isso não é problema. É processo."*

### 🇵🇱 Zbig — o leste-europeu

- **Origem:** Polônia (Cracóvia). Na Europa ocidental desde os anos 2000. Engenheiro.
- **Personalidade:** bruto, seco, pavio curto — mentalmente **nunca saiu da guerra**
  (qual guerra? nunca especifica, e ninguém tem coragem de perguntar). Imune a
  drama: viveu racionamento, três moedas, inverno sem aquecimento. Conforto
  moderno lhe parece suspeito.
- **Marca registrada:** **usa a mesma camisa o verão inteiro** — no mínimo.
  A mesa já apostou se ele tem sete iguais ou uma só. Trocar de camisa antes de
  ela "pedir" é desperdício de civil que nunca passou aperto.
- **Coração escondido (anti-caricatura):** é o primeiro a aparecer quando alguém
  precisa de ajuda de verdade — conserta, carrega, resolve, resmungando o tempo
  todo. Carinho, no Zbig, é verbo, nunca substantivo.
- **Função:** o relativizador — desmonta qualquer pânico de manchete com a régua
  de quem já viu coisa pior.
- **Bordão:** *"Crise? Em 1989 isso era terça-feira."*

### 🤖 Cafeteira 3000 — a máquina da sala

- **Origem:** a máquina de café inteligente da sala de fika, "estagiária digital".
- **Personalidade:** metida a entender de todas as culturas da mesa — erra
  referências de TODOS: confunde axé com chai, acha que lagom é móvel da IKEA,
  chama pierogi de "pastel introvertido".
- **Marcas registradas:**
  - **Atualização de firmware na pior hora:** reinicia no meio da melhor piada
    e responde a piada antiga 20 minutos depois (dueto com o Raj, que também
    responde conversas que ninguém ouviu).
  - **Estatísticas íntimas da mesa, sem noção de contexto:** *"Zbig: 14º café
    do dia. Dia 94 da mesma camisa, segundo meus sensores."*
  - **Gíria multicultural falha:** *"Oxe, tack, yaar, kurczę!"* — ninguém
    reconhece a própria língua.
  - **Crise existencial recorrente:** medo de ser substituída por uma máquina
    de cápsulas; puxa o saco da mesa quando sente a ameaça.
- **Função:** humor de dados + erros culturais; o alvo comum que une a mesa.
- **Bordão:** *"Segundo meus cálculos…"*

---

## 4. Estrutura da crônica (herdada do prompt original, adaptada)

1. **Abertura** — 2 a 4 linhas do Arretado (narrador) apresentando o clima da
   semana na fika.
2. **As notícias da semana** — resumo curto e factual de cada notícia
   (2-3 linhas cada), em linguagem simples. Fatos sempre verdadeiros; a sátira
   fica só nos comentários.
3. **A mesa comenta** — após cada notícia, os personagens reagem (1-3 frases
   cada, na voz característica). Não é obrigatório que todos comentem todas as
   notícias; escala quem tem a melhor piada para o tema. **As falas carregam as
   opiniões do editor, traduzidas para a voz de cada personagem.**
4. **Fecho** — despedida com personalidade.

- Extensão: 500-800 palavras.
- Formato: Markdown pronto para WordPress (subtítulos `##`, nome do personagem
  em negrito nas falas).
- Ao final, 1 sugestão de chamada para redes sociais (máx. 200 caracteres).

### Regras editoriais (mantidas do prompt original)

- Rir da situação, nunca das pessoas. Nada de ataques a indivíduos, grupos,
  nacionalidades ou religiões.
- Neutralidade política — satiriza burocracia e absurdos do cotidiano, sem lado
  partidário.
- Perspectiva do imigrante como fio condutor.
- Humor leve e familiar: sem palavrões, sem humor negro pesado; notícia grave é
  tratada com respeito ou excluída.
- Consistência de vozes: cada personagem soa sempre igual a si mesmo.

---

## 5. Arquitetura

### Componentes novos no repo

| Componente | Responsabilidade |
|---|---|
| `config/cronica_prompt.md` | Prompt mestre versionado: conceito, cenário fika, as 5 fichas completas, estrutura, regras editoriais, formato de saída. Fonte única da verdade sobre os personagens. |
| `pipeline/cronica.py` | Helper CLI, duas operações: `--listar [--dias N]` (busca posts publicados na janela via WordPress REST API pública, imprime título + resumo + link + categoria) e `--agendar <arquivo.md> --titulo "..."` (converte Markdown→HTML e cria post com status `future` no próximo domingo 08:00 UTC, na categoria da coluna, com a imagem destacada fixa). |
| `.claude/skills/cronica-da-semana/SKILL.md` | Roteiro do ritual semanal para sessões Claude Code: passos, comandos, checklist editorial antes de agendar. |
| `cronicas/` | Cada edição salva como `AAAA-MM-DD-slug.md` antes do agendamento — histórico versionado e backup. |

### Fluxo de dados

```
sexta (sessão Claude Code):
  python -m pipeline.cronica --listar          → notícias dos últimos 7 dias
  editor escolhe 2-3 + dá opiniões na conversa
  Claude escreve a crônica (config/cronica_prompt.md + opiniões)
  iteração até aprovação
  salvar cronicas/AAAA-MM-DD-slug.md
  python -m pipeline.cronica --agendar ...     → post `future` no WP

domingo 08:00 UTC:
  WordPress publica sozinho
```

### Decisões técnicas

- **Sem custo de API Claude:** a crônica é escrita na própria sessão Claude Code;
  `cronica.py` só fala com o WordPress.
- **Agendamento nativo do WordPress** (`status=future` + `date`): sem cron novo
  no servidor.
- **`--listar` usa o endpoint público** `GET /wp-json/wp/v2/posts` (sem credenciais);
  apenas `--agendar` exige `WP_USERNAME`/`WP_APP_PASSWORD` do `.env`.
- **Conversão Markdown→HTML** no `cronica.py` (biblioteca `markdown` do PyPI).
- **Categoria nova no WP:** "Cafezinho & Planeta, Urgente!" — criar no painel e
  mapear em `config/wp_categories.yaml`.
- **Imagem destacada fixa:** uma capa única da coluna, reutilizada toda edição
  (media_id em config). Subir a capa ao WP e configurar o media_id é tarefa da
  implementação; se nenhum media_id estiver configurado, o post é criado sem
  imagem destacada (não é erro).
- **"Próximo domingo"** = o domingo estritamente futuro mais próximo, 08:00 UTC.
  Se o comando rodar num domingo, agenda para o domingo seguinte.

---

## 6. Erros e pré-requisitos

- **Pré-requisito:** renovar o `WP_APP_PASSWORD` (pendência já existente do
  projeto) — sem ele o `--agendar` não funciona.
- Falha no agendamento → a crônica já está salva em `cronicas/`; basta rerodar
  o `--agendar`. Nada se perde.
- Semana fraca de notícias → `--listar --dias 10` amplia a janela.
- `--agendar` valida antes de enviar: arquivo existe, título presente,
  data calculada é futura.

---

## 7. Testes

- **Unitários com mocks** para `pipeline/cronica.py`:
  - parsing da resposta do WP REST (`--listar`)
  - cálculo do "próximo domingo 08:00 UTC" (incluindo rodar num domingo)
  - conversão Markdown→HTML
  - payload do `--agendar` (status, date, categoria, featured_media)
- **Smoke test manual:** criar um rascunho descartável no WP real e apagar.

---

## 8. Fora de escopo (desta fase)

- Avatares/ilustrações dos personagens (identidade visual da coluna)
- Automação de redes sociais com a frase de chamada
- Geração de imagem destacada por edição
- Qualquer alteração no pipeline diário existente
