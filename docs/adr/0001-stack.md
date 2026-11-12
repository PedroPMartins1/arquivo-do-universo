# ADR-0001 — Stack e forma da arquitetura

- Estado: aceite
- Data: 2026-11-12
- Decisores: Pedro (aprovação), Devin (proposta)

## Contexto
Não existe código anterior (D-011). O dossiê (§26.2, §54) exige a solução de menor complexidade que
satisfaça os requisitos e permita evoluir, sem decompor em microserviços só porque há motores conceptuais distintos.
O domínio exige cálculos astronómicos rigorosos, análise temporal, estatística, causalidade e ML.

## Decisão
- **Monólito modular**: um backend Python com pacotes por capacidade (`arquivo.core`, `arquivo.temporal`, ...).
  As fronteiras são verificadas na CI com `import-linter`.
- **Backend:** Python 3.12, FastAPI, Pydantic v2, SQLAlchemy 2, Alembic, uv.
- **Dados:** PostgreSQL 16 com pgvector. Relacional + JSONB (documentos) + `tstzrange` (bitemporalidade) +
  tabelas de arestas com CTE recursivas (grafo) + pgvector (pesquisa semântica). Bases dedicadas (grafo,
  vetorial) só com justificação medida.
- **Tempo:** `zoneinfo` sobre o pacote `tzdata` com versão fixada (reprodutível e registada como proveniência) e `timezonefinder`.
- **Astronomia:** Skyfield + efemérides JPL (DE440/DE440s).
- **Astrologia:** Swiss Ephemeris (`pyswisseph`), com validação cruzada das posições através do Skyfield.
- **Frontend:** React + TypeScript + Vite (SPA). Lint com oxlint, testes com Vitest.
- **Background jobs:** nenhum na fase inicial. Quando necessário, uma fila sobre Postgres.
- **IA/LLM:** sem fornecedor fixo. Interface própria; escolha num ADR na Fase 5 (D-018).
- **Deploy:** servidor (D-017). Fornecedor a decidir num ADR quando houver algo para implantar.

## Consequências
- Um único processo e uma única base simplificam o deploy, os backups e a consistência transacional.
- O Swiss Ephemeris é AGPL, o que exige publicar o código: aceite em ADR-0002.
- Se algum motor precisar de escalar à parte, a fronteira de pacote facilita extraí-lo para um serviço.
