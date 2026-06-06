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
