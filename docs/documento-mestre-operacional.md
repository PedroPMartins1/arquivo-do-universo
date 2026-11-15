# Documento Mestre Operacional
## Governação, segurança, dados, contratos e continuidade — Arquivo do Universo

**Versão:** 1.0 — consolidação de planeamento funcional  
**Data de consolidação:** 15 de novembro de 2026  
**Estado:** documento de referência funcional; não constitui prova de implementação, validação técnica ou entrada em produção.  
**Âmbito:** governação operacional e fluxos FC-01 a FC-06, com responsabilidades F78–F82.

---

## 0. Finalidade e estatuto

Este documento reúne as regras transversais de governação, segurança, dados, rastreabilidade, execução e continuidade necessárias para coordenar os fluxos críticos do Arquivo do Universo.

Fontes consolidadas:
- **05 — FC-06 Recuperação de Desastres e Continuidade Operacional**, v1.0, 14-11-2026.
- **06 — Documento Mestre de Fluxos e Contratos FC-01–FC-06**, v1.0, 14-11-2026.
- **07 — Documento Mestre de Governação, Segurança, Dados, Rastreabilidade e Entrada em Produção**, v1.0, 14-11-2026.
- **08 — Adenda de Reconciliação dos Fluxos FC-01–FC-06 e Lacunas F78–F82**, v1.0, 14-11-2026.
- **08A — Reconciliação Histórica e Especificação Funcional FC-01–FC-03**, v1.1, 14-11-2026.
- Auditoria transversal FC-01–FC-06, v0.2, neste repositório.

### 0.1 Classificação da informação

| Classe | Significado | Regra de utilização |
|---|---|---|
| Decisão confirmada | Decisão explicitamente recuperada de conversa ou documento aprovado | Preservar sem alterar silenciosamente. |
| Responsabilidade recuperada | Fronteira funcional encontrada em reconciliação histórica | Usar como baseline; validar contra fontes autónomas quando indicado. |
| Especificação consolidada | Detalhe funcional produzido e consolidado em 05/06/07 | Tratar como especificação funcional, não como implementação. |
| Proposta de harmonização | Schema, evento, estado ou regra propostos para permitir integração | Não apresentar como contrato histórico aprovado; requer decisão/ADR. |
| Lacuna | Informação sem evidência suficiente | Manter explícita; não completar por inferência. |
| Evidência técnica | Código, teste, CI ou exercício observável | Só declarar o estado que a evidência realmente comprova. |

O código demonstra o que foi implementado, não necessariamente o que foi decidido. Uma especificação não prova que o comportamento exista no software.

---

## 1. Princípios operacionais vinculativos

1. **Segurança antes da velocidade:** não reabrir serviços apenas para reduzir indisponibilidade.
2. **Integridade antes da disponibilidade:** dados sem integridade demonstrada permanecem isolados.
3. **Autoridade funcional separada da execução técnica:** um componente que consegue executar uma ação não ganha autoridade para a aprovar.
4. **Menor privilégio:** identidade, permissões e segredos são verificados em cada operação sensível.
5. **Não ressurreição:** dados legitimamente eliminados não podem regressar por backup, réplica, failover ou reconstrução.
6. **Não reativação:** credenciais, sessões e autorizações revogadas não podem ser restauradas como efeito colateral.
7. **Quarentena e reintegração controlada:** serviço isolado só regressa após autorização da autoridade de segurança.
8. **Rastreabilidade:** pedidos, decisões, contratos, aprovações, ações, resultados e compensações devem poder ser reconstruídos.
9. **Idempotência:** operações repetíveis não podem duplicar efeitos.
10. **Reversibilidade proporcional:** cada ação deve prever rollback ou compensação quando tecnicamente possível; operações destrutivas não presumem reversão.
11. **Degradação controlada:** só disponibilizar capacidades parciais previamente aprovadas.
12. **Transparência epistemológica:** factos, evidência, hipóteses, inferências, interpretações e previsões mantêm classificações distintas.

---

## 2. Mapa funcional F78–F82

A reconciliação histórica 08A v1.1 recupera a seguinte distribuição funcional:

| ID | Responsabilidade recuperada | Autoridade e limite |
|---|---|---|
| F78 | Backups, preservação e recuperação de dados | Executa mecanismos de recuperação; não decide se um dado pode ser recuperado. |
| F79 | Retenção, preservação, eliminação e governação do ciclo de vida dos dados | Decide o estado de retenção/eliminação e as exceções aplicáveis. |
| F80 | Identidade, autenticação, credenciais, autorização e permissões | Autoridade funcional de identidade e permissões. |
| F81 | Cibersegurança, defesa ativa e resposta a incidentes | Deteta, classifica, contém e coordena risco. F81.01–F81.12 ainda carecem de recuperação individual. |
| F82 | Infraestrutura, recursos e execução operacional | Executa operações de infraestrutura dentro das autorizações recebidas; não decide legitimidade dos dados nem autorização funcional. |

**Estado da reconciliação:** responsabilidades recuperadas em síntese histórica v1.1. A confirmação contra as especificações autónomas originais continua pendente. A designação e o conteúdo integral de uma alegada «F82 Parte V» não foram localizados como fonte primária nesta revisão.

### 2.1 Regra de autoridade

- F78 seleciona/executa mecanismos de recuperação segundo as políticas e autorizações recebidas.
- F79 decide se os dados podem ser mantidos, restringidos, eliminados, anonimizados ou preservados.
- F80 decide se um ator, credencial ou operação está autorizado.
- F81 decide/coordena a resposta de segurança dentro da política aprovada e mantém autoridade sobre contenção e libertação.
- F82 executa operações técnicas de infraestrutura, isolamento, restauro e capacidade; não substitui as autoridades funcionais anteriores.

---

## 3. Catálogo dos fluxos críticos

| Fluxo | Responsabilidade principal | Limite de autoridade | Maturidade documental |
|---|---|---|---|
| FC-01 — Recuperação de dados após incidente | Recuperar conjuntos de dados a partir de ponto íntegro, autorizado e compatível com políticas vigentes | Não contém por si só o incidente nem autoriza o restabelecimento do serviço | Princípios e sequência recuperados; estados/contrato normalizados por validar |
| FC-02 — Eliminação de informação em todos os sistemas | Propagar eliminação/restrição/anonimização/preservação a dados e derivados abrangidos | F79 determina legitimidade, âmbito, retenção e exceções | Finalidade e autoridade recuperadas; estados/contrato normalizados por validar |
| FC-03 — Revogação de identidade e credenciais, incluindo operações em curso | Revogar credenciais e autorizações, invalidar sessões e avaliar operações em curso | F80 é autoridade de identidade; F81 coordena contexto de ameaça | Finalidade e regra central recuperadas; estados/contrato normalizados por validar |
| FC-04 — Isolamento de serviços comprometidos | Limitar propagação e preservar evidência; gerir quarentena e reintegração | F81 governa segurança; FC-04 mantém autoridade de isolamento/libertação | Especificação funcional anterior referida como 26 secções e 20 testes; harmonização de contratos pendente |
| FC-05 — Expansão automática de infraestrutura | Ajustar capacidade sob limites de necessidade, custo, segurança e autonomia | Não pode escalar serviço comprometido nem ultrapassar limites financeiros | Especificação funcional consolidada; implementação/validação pendentes |
| FC-06 — Recuperação de desastres e continuidade operacional | Coordenar recuperação global, ambiente alternativo, dependências e continuidade | Não substitui FC-01–FC-05 nem as autoridades F79/F80/F81 | Especificação funcional v1.0, 28 secções e 20 testes conceptuais; implementação/validação operacional pendentes |

---

## 4. Fronteiras, precedências e resolução de conflitos

### 4.1 Ordem funcional em incidente com serviço comprometido

1. FC-03/F80 revoga credenciais e autorizações comprometidas quando aplicável.
2. FC-04/F81 contém e isola o serviço, preservando evidência.
3. FC-01/F78 seleciona e recupera dados em ambiente isolado, após validação de origem e integridade.
4. FC-02/F79 reconcilia o estado de eliminação/retenção e impede a reintrodução de dados abrangidos.
5. FC-06 coordena dependências, continuidade, ambiente alternativo, validações e reintegração.
6. FC-05/F82 fornece capacidade dentro das autorizações, limites financeiros e requisitos de segurança.

Esta sequência é de coordenação; ações independentes como revogação e isolamento podem decorrer em paralelo. FC-06 coordena o plano global, mas não absorve decisões especializadas.

### 4.2 Regras de desempate

| Conflito | Regra obrigatória |
|---|---|
| Disponibilidade vs. segurança | Segurança/isolamento prevalece. |
| Continuidade vs. credenciais revogadas | Revogação prevalece; não reativar credenciais antigas. |
| Restauro vs. eliminação legítima | F79/FC-02 prevalece; não restaurar dados eliminados. |
| Execução técnica vs. autorização | Sem autorização da autoridade funcional, F82 não executa. |
| Expansão vs. orçamento/política | FC-05 bloqueia ou escala quando os limites são atingidos. |
| Estado desconhecido | Tratar como não autorizado até confirmação da autoridade competente. |
| RTO em risco vs. controlos de segurança | Escalar e comunicar; não remover controlos de segurança para cumprir o tempo. |
| Rollback impossível/falhado | Bloquear novas alterações e exigir intervenção humana. |

### 4.3 Interações críticas por par

- **FC-01 × FC-02:** cada restore consulta o estado F79 e reaplica eliminações antes de expor dados.
- **FC-01 × FC-03:** restore não reativa credenciais; identidade e permissões são revalidadas.
- **FC-01 × FC-04:** dados podem ser recuperados em quarentena, mas o serviço não regressa sem autorização de segurança.
- **FC-01 × FC-06:** FC-01 recupera dados; FC-06 coordena continuidade e dependências. São resultados diferentes.
- **FC-02 × FC-06:** pedidos de eliminação pendentes são reconciliados no ambiente alternativo antes de disponibilizar dados.
- **FC-03 × FC-06:** o failover usa credenciais válidas e autorizadas, nunca sessões ou segredos revogados.
- **FC-04 × FC-05:** autoscaling não encaminha tráfego nem expande a superfície de um serviço isolado/comprometido.
- **FC-04 × FC-06:** FC-06 não levanta quarentena; a reintegração depende de FC-04/F81.
- **FC-05 × FC-06:** FC-06 especifica necessidade e prioridade; FC-05 avalia custo/segurança e provisiona dentro dos limites.

---

## 5. Contratos e eventos transversais

### 5.1 Envelope comum de harmonização

O Documento Mestre 06 propõe um envelope comum. Os campos abaixo constituem uma base de harmonização; a versão final dos schemas deve ser aprovada e versionada.

| Campo | Finalidade |
|---|---|
| flow_id / flow_version | Identificar fluxo e versão funcional. |
| contract_id / schema_version | Identificar contrato e versão compatível. |
| execution_id / request_id | Identificar pedido ou execução individual. |
| correlation_id | Agrupar a cadeia ponta a ponta de operações relacionadas. |
| causation_id | Identificar a mensagem/ação que originou a mensagem atual, quando aplicável. |
| trigger | Evento, pedido ou condição que iniciou o fluxo. |
| initiating_module | Módulo que iniciou a operação. |
| authoritative_module | Módulo que detém a decisão de domínio. |
| actor / authority | Identidade técnica/humana e autoridade validada. |
| scope | Dados, utilizadores, serviços, regiões e recursos abrangidos. |
| policy_reference | Política e versão aplicáveis. |
| idempotency_key | Evitar duplicação de efeitos em operações repetíveis. |
| preconditions | Condições obrigatórias antes da execução. |
| approval_reference | Aprovação humana ou política automática aplicável. |
| steps | Ações ordenadas, responsáveis, timeouts e compensações. |
| status | Estado normalizado e transições permitidas. |
| evidence_refs | Referências a logs, métricas, checksums e provas, sem duplicar dados sensíveis. |
| result / error | Resultado estruturado ou erro classificado. |
| retry / rollback / compensation | Política de repetição, reversão ou compensação. |
| timestamps | requested_at, approved_at, started_at, completed_at. |
| retention | Política de retenção dos registos operacionais. |

### 5.2 Tipos de mensagem

- **Command:** solicita que um componente execute uma ação.
- **Event:** regista algo que efetivamente ocorreu.
- **Request/Response:** representa pedido e resposta.
- **Approval:** regista decisão de autoridade, âmbito e validade da aprovação.

Não tratar estes tipos como intercambiáveis. Uma proposta não é uma aprovação; um evento de pedido não prova a conclusão da ação.

### 5.3 Regras de entrega e execução

- Idempotência em todas as operações repetíveis com efeitos.
- Deduplicação por identificador de mensagem/chave de idempotência.
- Retry limitado, com backoff e apenas para falhas transitórias.
- Timeout explícito; cancelamento cooperativo.
- Circuit breaker e escalonamento quando um consumidor não responde.
- Operações longas com execution_id, checkpoints e retoma controlada.
- Outbox transacional ou mecanismo equivalente quando a alteração de estado e a publicação do evento tenham de permanecer consistentes.
- Payload minimizado; nunca incluir segredos, tokens ou conteúdo pessoal integral sem necessidade.
- Versões incompatíveis são rejeitadas de forma controlada; não reinterpretar payloads silenciosamente.

### 5.4 Eventos

Os eventos específicos de FC-01 a FC-03 listados em documentos de harmonização são propostas normalizadas, não nomes históricos aprovados. FC-04 a FC-06 têm catálogos funcionais próprios a harmonizar com o envelope comum.

Todo o evento transversal deve, no mínimo, permitir identificar event_id, correlation_id, origem, timestamp, versão do schema, severidade quando aplicável, recurso afetado, autoridade e referência de auditoria.

---

## 6. Estados e execução parcial

Não se impõe uma única máquina de estados aos seis fluxos. Cada fluxo mantém a sua semântica. O ciclo comum de execução abaixo é uma proposta de orquestração, não substitui os estados específicos.

### 6.1 Estados comuns propostos

requested → validating → awaiting_approval → approved → executing → verifying → completed

Estados alternativos: partially_completed, failed, cancelled, compensating, rolled_back e escalated.

Uma execução parcial nunca pode ser reportada como concluída. Cada transição é auditada e idempotente.

### 6.2 Estados específicos recuperados

- **FC-01:** S0–S9/SE; a sequência foi recuperada, mas a correspondência exata de cada código carece de confirmação na fonte original.
- **FC-02:** D0–D9/DE; proposta de normalização, não sequência histórica confirmada.
- **FC-03:** R0–R9/RE; proposta de normalização, não sequência histórica confirmada.
- **FC-04:** máquina de estados da especificação funcional anterior; harmonização com o envelope comum pendente.
- **FC-05:** MONITORING, NEED_DETECTED, ANALYSIS, FORECASTING, COST_EVALUATION, PROPOSED, AWAITING_APPROVAL, APPROVED, PROVISIONING, CONFIGURING, VALIDATING, ACTIVE, ROLLBACK, BLOCKED, FAILED, HUMAN_INTERVENTION e COMPLETED.
- **FC-06:** NORMAL, SIGNAL_DETECTED, ASSESSING, DECLARATION_PENDING, DECLARED, CONTAINING, RECOVERY_PLANNING, ENVIRONMENT_PREPARATION, RESTORING, VALIDATING, DEGRADED_OPERATION, REINTEGRATION_PENDING, REINTEGRATING, MONITORING, ROLLBACK, BLOCKED, HUMAN_INTERVENTION e CLOSED.

### 6.3 Regras de falha

- BLOCKED significa que uma pré-condição, política ou dependência impede a execução.
- FAILED significa que a operação não atingiu o resultado pretendido.
- HUMAN_INTERVENTION significa que é necessária decisão/ação humana.
- CANCELLED não significa que os efeitos anteriores foram revertidos.
- ROLLED_BACK só pode ser declarado após confirmação do estado de destino.
- Operações destrutivas exigem resultado por destino; estados desconhecidos permanecem pendentes.
- Falhas parciais são representadas por componente/destino, não escondidas num estado global.

---

## 7. Autonomia e aprovação

### 7.1 Princípios transversais

- Nenhum fluxo pode elevar a própria autonomia, alterar políticas ou remover limites.
- A emergência só permite ações preautorizadas de contenção, dentro do escopo documentado.
- Operações financeiras, destrutivas, irreversíveis, com impacto externo, alteração de permissões ou exposição de dados exigem aprovação explícita adequada.
- A aprovação define ação, alvo, duração, âmbito, limite e autoridade.
- Deve existir suspensão global e por capacidade, além de cancelamento por tarefa.
- A suspensão de automação não pode desligar monitorização e controlos essenciais de segurança.

### 7.2 Autonomia específica FC-06

| Nível | Permissões |
|---|---|
| A0 — Observação | Detetar, correlacionar e registar sinais. |
| A1 — Recomendação | Preparar avaliação, plano e estimativa de recuperação. |
| A2 — Execução limitada | Verificações não destrutivas e failover previamente autorizado. |
| A3 — Autonomia operacional | Ativar planos aprovados dentro de severidade, RTO/RPO, custos e escopo predefinidos. |
| A4 — Operação crítica | Exige aprovação humana para declaração crítica, perda potencial de dados, mudança de região, alteração de confiança ou retorno à produção. |

**Não existe mapeamento aprovado entre A0–A4 e R1–R4/R1–R3.** A taxonomia de autonomia geral descrita no documento 07 tem A0–A3 e não deve ser fundida automaticamente com os níveis específicos de FC-06 ou FC-05. A harmonização requer decisão explícita.

---

## 8. Dados, privacidade e proveniência

### 8.1 Classes de informação

- Identidade e conta: identificadores, credenciais e sessões.
- Dados pessoais fornecidos: nascimento, preferências, objetivos e contexto.
- Conhecimento e memória: factos, afirmações, episódios, hipóteses e inferências.
- Fontes e documentos: ficheiros, URLs, excertos e metadados.
- Dados operacionais: logs, traces, métricas e auditoria.
- Modelos e previsões: versões, parâmetros, previsões e resultados.
- Dados temporais: evento, observação, registo, validade e execução.

### 8.2 Ciclo de vida

Aquisição com finalidade/origem → validação → classificação → normalização sem destruir o original → verificação/proveniência → armazenamento protegido → indexação necessária/autorizada → consulta com permissões → correção por nova versão → retenção/exportação/anonimização/eliminação.

### 8.3 Eliminação propagada

A FC-02/F79 deve localizar e tratar, conforme aplicável:
- registo primário, réplicas, versões e snapshots;
- ficheiros, anexos, documentos e exportações geridas;
- índices de pesquisa, caches, embeddings, vetores e grafos;
- análises, agregações, perfis e modelos derivados;
- filas, eventos pendentes, tarefas agendadas e integrações;
- backups e cópias imutáveis.

Backups imutáveis podem exigir expiração controlada. Durante esse período, dados abrangidos devem ficar inacessíveis para utilização normal. A prova de eliminação conserva apenas metadados mínimos e não o conteúdo eliminado.

### 8.4 Regras de recuperação

Antes de expor dados restaurados:
1. validar integridade/origem do ponto de recuperação;
2. consultar F79/FC-02 e aplicar eliminações/restrições;
3. consultar F80/FC-03 e impedir reativação de credenciais;
4. confirmar autorização de segurança F81/FC-04;
5. reconciliar operações posteriores ao ponto de recuperação;
6. registar prova e exceções.

---

## 9. FC-06 — continuidade e recuperação de desastres

### 9.1 Objetivo

A FC-06 prepara, coordena e executa recuperação de serviços, dados e operações após indisponibilidade, corrupção, perda, comprometimento ou degradação grave. Coordena a recuperação global, sem substituir as autoridades de FC-01 a FC-05.

### 9.2 Severidade

| Nível | Descrição | Resposta |
|---|---|---|
| D0 — Degradação | Impacto limitado; serviço ainda operacional | Monitorização reforçada e mitigação local |
| D1 — Incidente localizado | Um componente/serviço indisponível | Plano de recuperação do serviço |
| D2 — Incidente alargado | Vários serviços/dependências afetados | Coordenação entre módulos e recuperação prioritária |
| D3 — Desastre crítico | Perda significativa de ambiente, região, dados ou confiança | Comando de incidente, aprovação humana e recuperação faseada |

A autoridade exata para declarar D2/D3 permanece por definir.

### 9.3 RTO e RPO

Cada serviço/conjunto de dados tem RTO e RPO definidos e aprovados pelo responsável autorizado, com base no impacto e na capacidade técnica real. A FC-06 não impõe valores universais. Serviços sem RTO/RPO aprovados são lacunas de prontidão.

### 9.4 Ciclo operacional

Detetar/correlacionar → avaliar impacto/severidade/dependências → declarar segundo política → conter/preservar evidência → selecionar estratégia/ponto → preparar ambiente isolado → validar identidade, integridade, consistência e eliminação → recuperar segundo dependências → testar → reintegrar gradualmente → monitorizar → reconciliar operações → encerrar e emitir relatório.

### 9.5 Estratégias

- Restauro no ambiente primário quando este for considerado confiável.
- Ambiente alternativo quando o primário estiver indisponível/não confiável.
- Recuperação por serviço quando apenas parte das dependências estiver afetada.
- Modo degradado apenas se previamente aprovado e com limitações explícitas.
- Reconstrução limpa quando compromisso/corrupção invalida o ambiente anterior.

A especificação FC-06 não fixa topologias cold/warm/hot nem um mecanismo técnico de fencing/split-brain. Estes elementos requerem decisão de arquitetura após inventário de fornecedores e ambientes.

### 9.6 Critérios de prontidão

Cada serviço crítico deve ter:
- proprietário funcional;
- criticidade e dependências versionadas;
- dados tratados e localizações;
- fornecedor/região e contactos operacionais;
- estratégia e ponto de recuperação admissível;
- RTO/RPO aprovados;
- critérios de validação e reintegração;
- evidência de exercício/teste.

---

## 10. Observabilidade, auditoria e gestão de risco

### 10.1 Observabilidade técnica

- Logs estruturados: timestamp, nível, serviço, correlation_id, versão e evento; segredos e dados pessoais redigidos.
- Métricas: latência, erros, throughput, saturação, filas, custo e indicadores de serviço.
- Traces: trace/span IDs e propagação de contexto entre componentes.
- Auditoria: ator, autoridade, política, decisão, ação e resultado; registos protegidos contra alteração.
- Alertas: severidade, deduplicação, supressão, responsável, runbook e escalonamento.
- Proveniência: fonte, método, versão, transformações e confiança.

A observabilidade técnica de infraestrutura é distinta da Observabilidade e Monitorização Global do conhecimento/acontecimentos do produto. Partilham princípios, não finalidades nem modelos de dados.

### 10.2 Severidades de segurança

| Severidade | Critério orientador | Resposta |
|---|---|---|
| SEV-0 | Compromisso ativo, risco grave de dados ou controlo de segurança quebrado | Contenção preautorizada, escalonamento humano, preservação de evidência |
| SEV-1 | Indisponibilidade ampla ou degradação crítica | Responsável de incidente, mitigação e comunicação |
| SEV-2 | Degradação limitada ou falha parcial com alternativa | Registo, prioridade e correção |
| SEV-3 | Problema menor sem impacto material imediato | Backlog e monitorização |

### 10.3 Riscos transversais prioritários

1. Correlação inconsistente de eventos em operações compostas.
2. Contratos de mensagem ainda não executáveis/normalizados em todo o backend.
3. Eliminação distribuída não demonstrada.
4. Revogação abrangente e disposição de operações em curso não demonstradas.
5. Backup/restore/failover e reintegração não demonstrados em ambiente operacional.
6. Provisionamento e isolamento automatizados não demonstrados no código consultado.
7. RTO/RPO, fornecedores, regiões, custos e autoridade D2/D3 ainda por aprovar.

---

## 11. Testes e validação

### 11.1 Tipos de teste

Unitários, integração, contrato, end-to-end, regressão, segurança, desempenho/carga, migração/recuperação, consistência temporal, proveniência/isolamento e exercícios operacionais.

### 11.2 Conjuntos conceptuais recuperados

| Origem | Quantidade | Estado |
|---|---:|---|
| FC-04 | 20 | Definidos em especificação anterior; execução pendente |
| FC-05 | 20 | Definidos conceptualmente; execução pendente |
| FC-06 | 20 | Definidos na especificação v1.0; exercícios pendentes |
| FC-01–FC-03 | 12 | Definidos na reconciliação 08A v1.1; execução pendente |
| Integração FC-01–FC-06 | 18 | Definidos no Documento Mestre 06; execução pendente |

Estes conjuntos podem sobrepor-se; não representam 90 testes independentes nem cobertura comprovada. É necessária deduplicação, atribuição de IDs TST, dados de teste, ambiente, resultado e evidência.

### 11.3 Gates de entrada em produção

A passagem a produção exige cumulativamente:
- G0 Produto: âmbito, requisitos, exclusões, critérios e responsáveis aprovados.
- G1 Arquitetura: ADR, dependências e contratos versionados.
- G2 Segurança/privacidade: threat model, riscos críticos, segredos e permissões revistos.
- G3 Qualidade: testes aplicáveis aprovados.
- G4 Dados: migrações, backup/restore, retenção e eliminação comprovados.
- G5 Operação: logs, métricas, traces, alertas, runbooks e responsáveis.
- G6 Resiliência: rollback, recuperação e modo degradado testados.
- G7 Aprovação: release, impacto, janela, comunicação e aprovação registados.
- G8 Pós-release: smoke tests, monitorização reforçada e rollback ativos.

Bloqueadores absolutos incluem vulnerabilidade crítica sem mitigação aceite, exposição de segredos, acesso cruzado entre utilizadores, ausência de autorização no servidor, risco de perda de dados sem recuperação comprovada, operação destrutiva sem idempotência/recuperação, falta de monitorização/responsável e tratamento de dados pessoais sem finalidade/acesso/retenção definidos.

---

## 12. Decisões, lacunas e próximos passos

### 12.1 Lacunas abertas

| ID | Lacuna | Impacto |
|---|---|---|
| L-004 | Lista integral de funcionalidades/IDs anteriores a F59 | Catálogo global ainda não definitivo |
| L-005 | Especificações originais completas de F60/F61 | Especificação histórica incompleta |
| L-021 | Schemas/eventos históricos FC-01–FC-03, códigos de estado e harmonização de contratos FC-04 | Contratos executáveis ainda não congelados |
| L-022 | Validar F78–F82 contra fontes autónomas; recuperar F81.01–F81.12 e alegada F82 Parte V | Catálogo especializado ainda não completamente reconciliado |
| L-023 | Envelope transversal executável, correlação, idempotência, outbox e operações parciais | Integração técnica não demonstrada |
| L-024 | Inventário de sistemas derivados e política de backup/retensão | Eliminação distribuída não comprovada |
| L-025 | RTO/RPO por serviço, orçamento/quotas, fornecedores/regiões, integridade, autoridade D2/D3 e exercícios | Prontidão operacional não aprovada |

L-020 — texto integral da FC-06 — está fechada documentalmente pela especificação 05 v1.0.

### 12.2 Próximos passos por dependência

1. Fechar a revisão dos contratos/estados FC-01–FC-04, preservando a distinção entre histórico e normalização proposta.
2. Recuperar F81.01–F81.12 e a fonte autónoma F82 Parte V, se existir.
3. Aprovar envelope de mensagens, correlação ponta a ponta e política de idempotência/outbox.
4. Definir inventário de dados derivados, backups, fornecedores e regiões.
5. Aprovar RTO/RPO por serviço, autoridade D2/D3, orçamento e frequência de exercícios.
6. Converter os cenários conceptuais em testes automatizados rastreáveis.
7. Auditar e implementar por incrementos pequenos, reversíveis e validados.
8. Executar exercícios controlados de restore, isolamento, failover/failback e reintegração antes de qualquer declaração de prontidão.

---

## 13. Estado de maturidade — resumo executivo

| Camada | Estado documental | Estado técnico |
|---|---|---|
| Princípios de governação e segurança | Consolidados em 07 v1.0 | Adoção/implementação integral não demonstrada |
| Mapa F78–F82 | Recuperado em síntese em 08A v1.1 | Fontes autónomas e subfunções ainda por confirmar |
| FC-01–FC-03 | Princípios e sequências essenciais recuperados; contratos/estados normalizados pendentes | Implementação abrangente não demonstrada |
| FC-04 | Especificação anterior referida; harmonização de contratos pendente | Isolamento automatizado não demonstrado |
| FC-05 | Especificação funcional consolidada | Provisionamento automatizado não demonstrado |
| FC-06 | Especificação funcional v1.0 consolidada | Implementação DR e exercícios operacionais não demonstrados |
| Contratos/eventos transversais | Envelope proposto e catálogos parciais | Propagação transversal não demonstrada |
| Testes | Cenários conceptuais identificados | Execução e evidência pendentes |
| Entrada em produção | Gates definidos | Não declarar produção sem evidência cumulativa |

**Conclusão:** este Documento Mestre consolida a base funcional e de governação disponível. Não aprova automaticamente as propostas de harmonização, não fecha as lacunas históricas e não declara qualquer FC implementado, validado ou em produção. As decisões pendentes devem ser resolvidas por fonte primária ou ADR explícito; a execução técnica deve seguir a sequência de dependências e os gates definidos.


## 14. Detalhe histórico adicional F81/F82

A reconciliação documental complementar encontra-se em [reconciliacao-f78-f82-v0.1.md](auditorias/reconciliacao-f78-f82-v0.1.md). Resumo do que foi recuperado em sínteses históricas, sem o promover a especificação autónoma aprovada:

### F81 — 12 componentes identificadas
1. F81.01 Inteligência de ameaças.
2. F81.02 Gestão de vulnerabilidades.
3. F81.03 Deteção de intrusões.
4. F81.04 Monitorização comportamental.
5. F81.05 Defesa contra ataques.
6. F81.06 Proteção de APIs e comunicações.
7. F81.07 Segurança da cadeia de fornecimento.
8. F81.08 Isolamento de componentes.
9. F81.09 Resposta autónoma a incidentes.
10. F81.10 Recuperação segura.
11. F81.11 Testes e simulações.
12. F81.12 Avaliação contínua de segurança.

Autonomia histórica F81: R1 ações automáticas de baixo impacto; R2 ações automáticas condicionadas por políticas/limites; R3 operações críticas com aprovação humana. A referência a 18 componentes foi identificada no histórico como mistura documental e não deve ser reutilizada.

### F82 — estrutura e autonomia recuperadas
- Título histórico: **Inteligência de Infraestrutura, Orquestração e Gestão Autónoma de Recursos**.
- 12 componentes F82.01–F82.12; títulos individuais ainda não recuperados.
- Sete camadas: governação, inteligência, orquestração, computação, armazenamento, comunicações e observabilidade.
- Autonomia histórica F82: A1 monitorizar/recomendar; A2 otimizar recursos dentro de limites; A3 reorganizar serviços/capacidade segundo políticas; A4 aprovação humana para infraestrutura crítica/despesas extraordinárias.
- O histórico refere oito cenários de teste: aumento/redução de carga, falhas, excesso orçamental, estrangulamento, falha de rede, recuperação e alteração não autorizada. A formulação integral e os IDs não foram recuperados.

Estas taxonomias são específicas dos respetivos módulos. Não mapear R1–R3 de F81 ou A1–A4 de F82 para os níveis A0–A4 de FC-06.
