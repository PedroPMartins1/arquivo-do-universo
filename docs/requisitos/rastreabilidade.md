# Matriz de rastreabilidade

Requisito → critério de aceitação → código → testes. Atualizada em cada PR.

| Requisito | Critério | Código | Testes |
|---|---|---|---|
| AU-ENG | CI verifica lint, tipos, fronteiras entre módulos e testes | `.github/workflows/ci.yml`, `backend/pyproject.toml` (`[tool.importlinter]`) | execução da CI |
| AU-ENG | O sistema expõe o estado de saúde | `backend/src/arquivo/api/health.py` | `backend/tests/test_health.py`, `frontend/src/App.test.tsx` |
| AU-EPI | Classes epistemológicas distintas, com metadados obrigatórios por classe | `backend/src/arquivo/core/epistemics.py` | `backend/tests/test_epistemics.py` |
| AU-EPI | Astrologia só pode ser interpretação ou especulação (§11, §17.6) | `core/epistemics.py` (`ALLOWED_CLASSES`) | `test_epistemics.py`, `test_statements.py::test_astrology_cannot_be_stored_as_prediction` |
| AU-EPI | Inferência nunca é promovida a facto sem fonte nova (§10) | `core/epistemics.py` (`reclassification_issues`), `persistence/statements.py` | `test_statements.py::test_inference_cannot_become_fact_without_new_source` |
| AU-MEM | Proveniência estruturada; conteúdo externo não é instrução | `backend/src/arquivo/core/provenance.py` | `test_epistemics.py::test_provenance_satisfies_source_and_method` |
| AU-MEM | Afirmações versionadas; o passado não se reescreve (imposto pela BD) | `persistence/models.py`, `persistence/statements.py`, migração inicial (triggers) | `test_statements.py::test_record_and_revise_keeps_history`, `::test_database_forbids_rewriting_history` |
| AU-CTX | Isolamento por utilizador em todas as leituras e escritas | `persistence/statements.py` (`_owned`) | `test_statements.py::test_users_are_isolated` |
| AU-SEG | Eliminação a pedido apaga todas as versões; auditoria append-only e anonimizada | `persistence/statements.py` (`erase`), migração inicial | `test_statements.py::test_erase_removes_all_versions_and_is_audited`, `::test_audit_is_append_only_but_anonymised_on_user_deletion` |
| F60 | Fusos IANA históricos com versão do tzdata registada | `backend/src/arquivo/temporal/zones.py`, `local_time.py` | `test_temporal.py::TestLocalTime`, `::TestZones` |
| F60 | Horas ambíguas/inexistentes (mudança de hora) nunca são escolhidas em silêncio | `temporal/local_time.py` | `test_temporal.py::TestLocalTime` (inclui teste por propriedades) |
| F60 | Datas parciais e incerteza explícitas | `temporal/partial.py`, `local_time.py` | `test_temporal.py::TestPartialDate`, `::test_uncertainty_widens_the_interval` |
| F60 | Validação cronológica (ordem impossível, previsão retrospetiva) | `temporal/stamps.py` | `test_temporal.py::TestChronology`, `test_statements.py::test_rejects_chronology_errors` |
| F60 | Bitemporalidade: válido em T, conforme conhecido em T' | `persistence/statements.py` (`valid_at`, `as_known_at`) | `test_statements.py::test_valid_at_is_bitemporal` |
| F60 | API de resolução de hora local | `backend/src/arquivo/api/temporal.py` | `backend/tests/test_api.py` |
| AU-AST | Mapa natal: posições, casas (11 sistemas), ângulos e aspetos; tropical/sideral; Placidus por omissão (D-021) | `backend/src/arquivo/natal/chart.py`, `settings.py`, `api/natal.py` | `backend/tests/test_natal.py` |
| AU-AST | Validação cruzada: longitudes (Sol–Plutão, ≤2″; Lua ≤5″) e ASC/MC contra Skyfield + JPL DE421 | `backend/src/arquivo/natal/chart.py` | `backend/tests/test_natal_validation.py` |
| AU-AST | Data e hora de nascimento exatas (D-020): um único instante UTC, sem incerteza nem ambiguidade silenciosa | `backend/src/arquivo/natal/birth.py` | `backend/tests/test_birth.py` |
| AU-COM | Interpretações natal e diária estruturadas usam apenas factos calculados, validam os termos e guardam respostas por hash; slots diários são desbloqueados no fuso residencial, o conteúdo fechado é redigido e a leitura diária pode ser pré-gerada com fallback imediato (D-029, D-030, D-031) | `backend/src/arquivo/interpretation/`, `backend/src/arquivo/api/reading.py`, `backend/src/arquivo/api/profile.py`, `backend/src/arquivo/transits/unlock.py`, `backend/src/arquivo/pregeneration.py`, `frontend/src/Today.tsx`, `frontend/src/App.tsx` | `backend/tests/test_interpretation.py`, `backend/tests/test_interpretation_api.py`, `backend/tests/test_pregeneration.py`, `backend/tests/test_unlock.py`, `frontend/src/Today.test.tsx`, `frontend/src/App.test.tsx` |
