# Auditoria 0000 — Baseline de engenharia

- Data: 2026-11-12
- Âmbito: dossiê §55 (auditoria obrigatória antes de desenvolvimento estrutural)

## Resultado
- **Repositório anterior:** não existe. Confirmado pelo Pedro (D-011). A sessão não tinha acesso a nenhum repositório
  privado, e o perfil público `github.com/PedroPMartins1` só tem o README do perfil.
- **Código, serviços, base de dados, APIs, integrações, deploy, pipelines:** nenhum.
- **Testes:** nenhum. Baseline = 0 testes.
- **Documentação:** só o dossiê mestre v2.0 (guardado em `docs/dossie/`). O Documento Mestre original e as
  conversas de conceção não estão disponíveis ([L-001](../governanca/lacunas.md), [L-006](../governanca/lacunas.md)).

## A. Inventário técnico
Vazio antes deste repositório. Stack decidida em [ADR-0001](../adr/0001-stack.md).

## B. Inventário funcional
Todas as funcionalidades estão só no dossiê. Ver [catálogo](../requisitos/catalogo.md).

## C. Matriz de maturidade
Nenhuma funcionalidade está implementada, em validação, validada ou em produção. Todas estão em
«em especificação» (descrição funcional no dossiê, sem critérios de aceitação completos).

## D. Auditoria arquitetural
Não aplicável a código. Riscos de especificação identificados:
- **Duplicação potencial** entre Observabilidade Global, F60 e F59, e entre Raciocínio e F62. Mitigação: as fronteiras do dossiê §36 vão ser codificadas como contratos do `import-linter`.
- **Dependências:** a matriz do §35 não tem ciclos aparentes. «Validação/Evolutiva/Orquestração → todos» são transversais e vão ser implementadas como serviços injetados, não como importações diretas.
- **Lacunas que bloqueiam a Fase 4:** L-002, L-003, L-008.

## E. Plano de execução
Ver [ADR-0003](../adr/0003-fatia-vertical.md). Backlog imediato:

| # | Tarefa | Razão | Depende de | Esforço | Risco | Aceitação |
|---|---|---|---|---|---|---|
| 1 | Esqueleto + CI + governação | Base verificável | — | S | baixo | CI verde, docs publicados |
| 2 | Núcleo epistemológico + proveniência + isolamento + auditoria | Princípios §10, §13.5, §28 | 1 | M | médio | Testes de isolamento e imutabilidade passam |
| 3 | F60 modelo temporal comum | §18. Consumido pelo Mapa Natal | 2 | M | médio | Testes de fusos/DST/datas parciais passam |
| 4 | Autenticação multiutilizador | D-014 | 2 | M | alto (segurança) | Testes de autenticação/autorização |
| 5 | Mapa Natal básico | Fase 4 | 3, L-002, L-003 | L | alto | Comparação com valores de referência |
| 6 | Deploy no servidor | D-017 | 4 | M | médio | App acessível com HTTPS |
