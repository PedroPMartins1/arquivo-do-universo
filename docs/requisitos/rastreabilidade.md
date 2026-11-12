# Matriz de rastreabilidade

Requisito → critério de aceitação → código → testes. Atualizada em cada PR.

| Requisito | Critério | Código | Testes |
|---|---|---|---|
| AU-ENG | CI verifica lint, tipos, fronteiras entre módulos e testes | `.github/workflows/ci.yml`, `backend/pyproject.toml` (`[tool.importlinter]`) | execução da CI |
| AU-ENG | O sistema expõe o estado de saúde | `backend/src/arquivo/api/health.py` | `backend/tests/test_health.py`, `frontend/src/App.test.tsx` |
