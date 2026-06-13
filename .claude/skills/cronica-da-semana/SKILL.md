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
