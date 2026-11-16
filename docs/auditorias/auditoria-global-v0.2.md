# Auditoria global do projeto — v0.2

**Data da revisão:** 16 de novembro de 2026  
**Branch:** `audit/revisao-transversal-fc-01-fc-06`  
**HEAD da branch na atualização:** `67bbe4a6b6ca75ba8d254a806b2c3927c0de9a5f`  
**Commit com CI concluída:** `70ebc1eab6a8cd0361c46ddc94dbebf8231b5703`  
**PR:** [#17 — revisão transversal FC-01 a FC-06](https://github.com/PedroPMartins1/arquivo-do-universo/pull/17)  
**Estado:** auditoria documental e técnica atualizada. Não aprova produção nem substitui testes de segurança/operacionais.

## 1. Atualização face à v0.1

A revisão v0.2 preserva a auditoria v0.1 como fotografia de 15-11-2026 e atualiza os achados com a decisão D-030, a implementação observada, os testes e a execução CI associada ao commit atual.

## 2. Resultado executivo

- A data D-030 (16-11-2026) já não é futura na data desta revisão.
- A regra de quatro Revelações principais e bónus opcional é compatível com o limite técnico de cinco e os cinco horários configurados, mas a implementação atual ainda não distingue semanticamente as principais do bónus.
- O valor `PROMPT_VERSION=2026-11-17.1` continua a ser uma referência futura e carece de confirmação.
- A divergência DE440/DE421 foi esclarecida: a aplicação calcula em execução com Swiss Ephemeris; Skyfield + JPL DE421 são usados nos testes de validação cruzada. ADR-0001 foi atualizado para refletir esta divisão.
- A CI do commit `9d576000bb836c4a5ce72f3ab9815880cab08b54` terminou com sucesso nos dois jobs (backend e frontend).
- Permanecem riscos pré-produção de autenticação e questões de escopo/persistência do limite de falhas do worker.
- Não foram executados testes de exploração de segurança, testes de carga, exercícios de recuperação de desastres nem validação operacional de produção.

## 3. Achados atualizados

| ID | Severidade | Estado v0.2 | Evidência e conclusão | Ação |
|---|---|---|---|---|
| GA-01 | Baixa | Resolvido documentalmente | README distingue implementação parcial, CI e ausência de validação operacional/produção. | Manter alinhamento com catálogo e evidência. |
| GA-02 | Baixa | Resolvido documentalmente | Índice reconhece Documento Mestre Operacional v1 e distingue-o do Documento Mestre completo do produto. | Manter distinção. |
| GA-03 | Média | Parcialmente resolvido | D-030 está datada de 16-11-2026, data desta revisão; deixa de ser futura. D-029 continua a indicar `PROMPT_VERSION=2026-11-17.1`, futura face a 16-11. | Confirmar se a versão do prompt está deliberadamente preparada para 17-11 ou se a data está incorreta. Não alterar sem fonte. |
| GA-04 | Baixa | Resolvido documentalmente | D-018 declara explicitamente que a escolha posterior Claude/Anthropic em D-029 prevalece. | Não reabrir sem nova decisão. |
| GA-05 | Baixa | Parcialmente resolvido; semântica de bónus por fechar | D-028 fixa quatro principais + bónus opcional. `MAX_REVELATIONS=5`; D-030 define cinco horários e `unlock_times` distribui dinamicamente a quantidade disponível. Contudo, `candidates(... )[:MAX_REVELATIONS]` seleciona até cinco conclusões por ranking, sem marcar quatro como principais nem a quinta como bónus; também pode devolver menos de quatro se houver menos candidatos. Foi acrescentado um teste explícito para 4 horários; passou na CI #74 do commit `70ebc1eab6a8cd0361c46ddc94dbebf8231b5703`. | Confirmar a regra semântica: quatro principais e quinta opcional, incluindo critérios de elegibilidade e eventual tag de bónus; alinhar motor, contrato de interpretação, API e UI. Confirmar na CI o teste de quatro horários. |
| GA-06 | Baixa | Resolvido documentalmente | `chart.py` calcula com Swiss Ephemeris. `test_natal_validation.py` carrega Skyfield e `de421.bsp`; `pyproject.toml` coloca Skyfield nas dependências de desenvolvimento. O script descarrega DE421. Não foi encontrada utilização de Skyfield como motor de execução. ADR-0001 atualizado. | Manter documentação alinhada se o teste ou backend mudar. |
| GA-07 | Média | Parcialmente resolvido | ADR-0001 regista a evolução para worker de pré-geração via D-031. Supervisão, reinício, deploy, alertas e operação contínua não estão demonstrados. | Definir plano operacional antes de produção. |
| GA-08 | Baixa | Resolvido documentalmente | D-010 deixou de remeter para L-002/L-003 resolvidas. | Sem ação adicional. |
| GA-09 | Média | Informativo | Baseline 0000 é fotografia histórica de 12-11-2026, não estado corrente. | Preservar como histórico. |
| GA-10 | Alta | Aberto | Endpoints de registo/login não mostram rate limiting. Cookie de sessão é HttpOnly e SameSite=Lax; Secure é ativado em produção. CORS permite credenciais e usa lista configurada de origens, mas não há token CSRF explícito. Não foi demonstrada exploração; é uma lacuna de hardening e validação. | Definir threat model, rate limiting por IP/conta com proteção contra enumeração, política de bloqueio/backoff, CSRF adequado ao modelo de cookie, revisão CORS/HTTPS e testes negativos automatizados. |
| GA-11 | Média | Aberto — escopo por confirmar | `Pregenerator.failures` é um dicionário em memória da instância. A instância persiste durante o ciclo principal do worker, mas reiniciar o processo repõe os contadores; processos múltiplos não partilham o estado. Além disso, o `SELECT` de leituras existentes ocorre antes de chamar o modelo: dois processos podem gerar a mesma leitura em paralelo e a restrição única impedir apenas a segunda gravação, não o custo duplicado da chamada à IA. D-031 diz «neste processo», pelo que o escopo do limite e a necessidade de coordenação distribuída têm de ser clarificados. | Clarificar a semântica de D-031. Se o limite for global por utilizador/dia, persistir em Postgres com atualização atómica. Se forem permitidos vários processos, adicionar claim/lease ou lock por utilizador/dia para evitar chamadas duplicadas à IA. Testar reinício, concorrência e falhas. Se o limite for por processo, documentar e aceitar explicitamente o limite. |

## 4. Evidência técnica e CI

### 4.1 CI no commit verificado

Execução GitHub Actions **#74**, run ID `43865837168`, associada ao commit `70ebc1eab6a8cd0361c46ddc94dbebf8231b5703`. A execução anterior #69 também passou no commit `9d576000bb836c4a5ce72f3ab9815880cab08b54`.

- **Backend — sucesso:** aquisição de efemérides, sincronização de dependências, Ruff, formatação, mypy, import-linter e pytest.
- **Frontend — sucesso:** instalação, lint, testes Vitest e build.

A execução #74 confirma a passagem da suíte configurada, incluindo o novo teste de distribuição para quatro Revelações. O HEAD atual contém apenas atualizações documentais posteriores a esse commit; não há uma nova execução CI associada a esse HEAD no momento desta revisão. Não prova segurança, validade astrológica independente em ambiente de produção, operação contínua, recuperação de desastre ou prontidão comercial.

### 4.2 Efemérides

- O cálculo de mapa natal e trânsitos usa Swiss Ephemeris.
- Os ficheiros Swiss `sepl_18.se1`, `semo_18.se1` e `seas_18.se1` são descarregados pelo script.
- Os testes de validação cruzada usam Skyfield + JPL DE421 como referência independente.
- Skyfield é dependência de desenvolvimento/testes, não do runtime principal.
- O código regista backend e ficheiros efetivamente usados e pode emitir aviso de fallback Moshier.

A alteração a ADR-0001 é documental; não altera o cálculo nem os ficheiros descarregados.

### 4.3 Revelações e desbloqueios

- Máximo técnico: cinco Revelações.
- Horários por omissão: 09:00, 11:00, 13:00, 15:00 e 17:00 no fuso aplicável.
- Cinco Revelações usam os cinco horários.
- Menos de cinco são distribuídas uniformemente entre o primeiro e o último horário.
- Os testes cobrem 0, 1, 3 e 5; foi acrescentado um caso para 4 no commit 1a9bca6, ainda sem execução CI confirmada neste ponto.

## 5. Segurança e fiabilidade — limites da evidência

A análise estática identificou ausência de rate limiting no fluxo de autenticação e ausência de mecanismo CSRF explícito. O cookie HttpOnly/SameSite=Lax e a lista de origens CORS configuradas são controlos relevantes, mas não substituem uma avaliação de ameaças e testes de browser. Não se declara uma vulnerabilidade explorável sem demonstração.

O contador de falhas da pré-geração está em memória. A D-031 deve ser interpretada com precisão: «neste processo» pode significar limite apenas durante a vida do worker. Além disso, vários processos podem iniciar a mesma geração antes de a restrição única evitar a duplicação persistida; a chamada à IA pode ser duplicada. A decisão sobre escopo, persistência e coordenação deve preceder qualquer alteração de código.

## 6. Estado da PR

A PR #17 permanece Draft, sem reviews ou threads de revisão registadas no momento da consulta. A CI do commit atual está verde. Não foi feito merge e a branch `main` não foi alterada.

## 7. Próximas ações

1. Confirmar a intenção da versão `PROMPT_VERSION=2026-11-17.1`.
2. Definir e implementar a separação entre quatro Revelações principais e bónus opcional; o teste de distribuição de quatro horários já passou na CI #74.
3. Fechar o desenho de hardening de autenticação (rate limiting, CSRF, CORS, HTTPS e testes).
4. Clarificar se o limite D-031 é por processo ou global por utilizador/dia; só depois decidir persistência.
5. Definir supervisão e operação do worker.
6. Atualizar a matriz requisito → código → teste → evidência e executar revisão final.
7. Consolidar auditoria v1.0 e Documento Mestre após fechar os achados relevantes.

**Conclusão:** a auditoria global melhorou: a CI está verde no commit atual, a cronologia de D-030 foi reconciliada e a versão das efemérides está tecnicamente explicada. O projeto continua sem evidência de produção e não deve ser considerado pronto para lançamento público enquanto GA-10, L-017–L-019 e as lacunas operacionais relevantes permanecerem abertas.
