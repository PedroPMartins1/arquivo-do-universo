# Arquivo do Universo — Inteligência Pessoal

Plataforma de conhecimento pessoal, análise temporal, astronomia/astrologia e apoio à decisão.
A visão completa está no [dossiê mestre](docs/dossie/dossie-mestre-v2.0.txt). A governação do projeto
(estados, decisões, lacunas, requisitos) está em [`docs/`](docs/README.md).

> Estado: **fundação**. Nenhuma funcionalidade de produto está implementada ou validada.
> O estado real de cada requisito está no [catálogo](docs/requisitos/catalogo.md).

## Estrutura

| Pasta | Conteúdo |
|---|---|
| `backend/` | API em Python 3.12 + FastAPI (monólito modular) |
| `frontend/` | Interface web em React + TypeScript + Vite |
| `docs/` | Dossiê, decisões (ADR), requisitos, lacunas, rastreabilidade e auditorias |

## Desenvolvimento local

Requisitos: [uv](https://docs.astral.sh/uv/), Node 22 com pnpm 9, Docker.

```bash
# Base de dados (PostgreSQL 16 + pgvector)
docker compose up -d db

# Backend: http://localhost:8000/docs
cd backend
./scripts/fetch_ephemerides.sh   # Swiss Ephemeris + JPL DE421 em data/ephe (não versionado)
uv sync
uv run alembic upgrade head
./scripts/fetch_places.sh        # localidades do GeoNames em data/geonames e na base de dados
uv run uvicorn arquivo.main:app --reload

# Frontend: http://localhost:5173 (encaminha /api para o backend)
cd frontend
pnpm install
pnpm dev
```

Noutro terminal, execute o worker de pré-geração diária:

```bash
cd backend
uv run python -m arquivo.pregeneration
```

### Verificações (as mesmas da CI)

```bash
cd backend && uv run ruff check . && uv run ruff format --check . && uv run mypy src tests && uv run lint-imports && uv run pytest
cd frontend && pnpm lint && pnpm test && pnpm build
```

Hooks opcionais: `pre-commit install`.

## Regras de dados

Nunca colocar dados pessoais reais (datas/horas/locais de nascimento, documentos, conversas) no
repositório nem em testes. Usar dados fictícios ou de figuras públicas com fonte documentada.

## Licença

[GNU Affero General Public License v3.0 ou posterior](LICENSE). Ver [ADR-0002](docs/adr/0002-licenca-agpl.md).

Os dados de localidades vêm do [GeoNames](https://www.geonames.org), sob licença [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).
