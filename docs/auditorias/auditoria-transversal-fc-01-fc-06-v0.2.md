# Auditoria transversal FC-01–FC-06
## Versão 0.2 — diagnóstico documental e técnico atualizado

**Projeto:** Arquivo do Universo  
**Tipo de trabalho:** revisão transversal / consolidação  
**Branch:** audit/revisao-transversal-fc-01-fc-06  
**Base técnica inspecionada:** commit 0531e06f7a11132d996d2c9c79b4b9078b7e1afe  
**Estado:** diagnóstico preliminar; não constitui aprovação de arquitetura nem autorização para implementação.

## 1. Objetivo e âmbito

Esta revisão verifica a coerência entre os seis fluxos críticos:

| ID | Fluxo | Objetivo recuperado |
|---|---|---|
| FC-01 | Recuperação de dados após incidente | Recuperar dados a partir de versão íntegra e autorizada, separando contenção, recuperação dos dados e restabelecimento do serviço. |
| FC-02 | Eliminação de informação em todos os sistemas | Coordenar a eliminação de dados pessoais e derivados em todos os sistemas abrangidos, mantendo prova verificável do resultado. |
| FC-03 | Revogação de identidade e credenciais, incluindo operações em curso | Revogar identidade, credenciais e autorizações; impedir novas ações e avaliar individualmente operações já iniciadas. |
| FC-04 | Isolamento de serviços comprometidos | Conter um serviço comprometido, limitar propagação e preservar a capacidade de investigação/recuperação. |
| FC-05 | Expansão automática de infraestrutura | Detetar necessidade demonstrável, avaliar capacidade, previsão, custo, segurança e autonomia antes de provisionar recursos. |
| FC-06 | Recuperação de desastres e continuidade operacional | Recuperar a operação recorrendo a infraestrutura alternativa quando o ambiente principal não pode assegurar continuidade. |

A revisão distingue decisão recuperada, evidência de código, proposta e lacuna. Uma proposta nesta versão não é uma decisão aprovada.

## 2. Estado documental recuperado

### 2.1 FC-01 a FC-04

FC-01–FC-04 foram tratadas como fluxos funcionalmente desenvolvidos em etapas anteriores, mas a reconciliação 08A v1.1 refina o grau de evidência: para FC-01–FC-03 estão recuperados princípios, autoridades e sequências essenciais, enquanto contratos/estados normalizados permanecem propostas; FC-04 tem especificação anterior referida como 26 secções e 20 testes. Nenhum destes estados prova implementação ou validação técnica.

- **FC-01:** a recuperação não deve começar por restaurar cegamente. Primeiro contém-se o incidente; depois identifica-se uma versão íntegra/autorizada, valida-se de forma independente e obtém-se a autorização exigida; só então se recuperam dados e se restabelece o serviço.
- **FC-02:** o âmbito inclui sistemas primários e derivados, nomeadamente ficheiros, índices, caches, réplicas, backups, análises e modelos. A coordenação foi atribuída à F79 na especificação recuperada. Não se declara eliminação integral sem prova dos destinos abrangidos e do resultado. A política de backups e retenção legal tem de ser explícita.
- **FC-03:** a revogação abrange identidade, credenciais e autorizações. Deve bloquear novas ações e avaliar individualmente operações em curso, considerando risco, possibilidade de cancelamento, consistência e efeitos externos.
- **FC-04:** a especificação funcional foi concluída com responsabilidades, estados, contratos, eventos, falhas, autonomia, aprovação humana, auditoria, métricas, critérios de aceitação e 20 testes conceptuais. Implementação e testes técnicos permanecem pendentes.

### 2.2 FC-05

A especificação funcional foi declarada concluída em 14-11-2026. Foram recuperados:

- Autonomia A0–A4.
- Estados: MONITORING → NEED_DETECTED → ANALYSIS → FORECASTING → COST_EVALUATION → PROPOSED → AWAITING_APPROVAL → APPROVED → PROVISIONING → CONFIGURING → VALIDATING → ACTIVE, com saídas alternativas ROLLBACK, BLOCKED, FAILED, HUMAN_INTERVENTION e COMPLETED.
- Contratos identificados: InfrastructureMonitor, CapacityAssessment, CapacityForecast, ExpansionProposal, CostAssessment, AutonomyPolicy, SecurityValidation, ResourceProvisioning, ResourceConfiguration, DeploymentValidation, ScalingController, RollbackController, InfrastructureAudit e PerformanceEvaluation.
- Regras: só expandir com necessidade demonstrável, benefício operacional e custo aceitável; baixa confiança conduz a decisão conservadora; a autonomia não se eleva por iniciativa do próprio fluxo; falhas exigem contenção, recuperação ou reversão; segurança e conflitos com FC-04 bloqueiam o provisionamento.
- Foram definidos eventos, métricas e 20 testes conceptuais; implementação e validação técnica continuam pendentes.

**Nota de nomenclatura:** referências históricas a F81/F81.01–F81.12, R1–R3 e F78–F82 não estão reconciliadas com um catálogo validado no repositório. Não assumir equivalência automática entre A0–A4 e R1–R3, nem atribuir autoridade definitiva a F81/F82 sem reconciliação documental.

### 2.3 FC-06 — especificação integral recuperada

Foi localizado no Library do projeto o documento **05_FC06_Recuperacao_Desastres_Continuidade.docx**, versão 1.0, de 14-11-2026, com 28 secções e 11 páginas. O Documento Mestre de Fluxos e Contratos (06) e a Adenda de Reconciliação (08), ambos da mesma data, confirmam que este é o documento detalhado de referência da FC-06.

Elementos efetivamente especificados:
- Âmbito: preparação, continuidade, deteção, análise de impacto, seleção do ponto/estratégia de recuperação, ambiente isolado, validação, reintrodução gradual e retorno ao ambiente normal.
- Severidade: D0 degradação; D1 incidente localizado; D2 incidente alargado; D3 desastre crítico.
- Ativação: sinais de monitorização, segurança, fornecedor, corrupção, indisponibilidade regional/infraestrutura, erro de configuração ou decisão autorizada. Deteção automática gera avaliação; não declara automaticamente desastre crítico fora da política.
- RTO/RPO: definidos e aprovados por serviço/conjunto de dados. **Não existem valores universais aprovados na FC-06.** Serviços sem RTO/RPO aprovados são lacunas de prontidão.
- Ciclo: deteção/correlação → avaliação → declaração autorizada → contenção → seleção do ponto → preparação de ambiente isolado → validação de identidade, permissões, integridade, consistência e eliminações → recuperação por dependências → testes → reintegração gradual → monitorização → encerramento e relatório.
- Estratégias: restauro no primário, ambiente alternativo, recuperação por serviço, modo degradado e reconstrução limpa.
- Dados: origem, data, versão, escopo, integridade criptográfica e retenção dos pontos; segregação de permissões; histórico de pontos rejeitados; reconciliação de alterações posteriores; proibição de disponibilizar dados com origem ou consistência desconhecidas.
- Identidade: nenhuma identidade, chave, token, sessão ou credencial revogada pela FC-03 pode ser reativada pelo processo de recuperação.
- Segurança: quarentena até critérios de FC-04; FC-06 não levanta isolamento unilateralmente.
- Capacidade/custos: FC-05 provisiona; custos extraordinários, região ou fornecedor novo e ultrapassagem de limites exigem aprovação aplicável.
- Operações em curso: reconciliação com identificadores idempotentes; não repetir automaticamente efeitos externos ou destrutivos sem confirmação.
- Autonomia específica FC-06: A0 observação; A1 recomendação; A2 execução limitada (inclui failover previamente autorizado); A3 ativação de planos aprovados dentro de severidade, RTO/RPO, custos e escopo predefinidos; A4 exige aprovação humana para declaração crítica, perda potencial de dados, mudança de região, alteração de confiança ou retorno à produção.
- Estados: NORMAL, SIGNAL_DETECTED, ASSESSING, DECLARATION_PENDING, DECLARED, CONTAINING, RECOVERY_PLANNING, ENVIRONMENT_PREPARATION, RESTORING, VALIDATING, DEGRADED_OPERATION, REINTEGRATION_PENDING, REINTEGRATING, MONITORING, ROLLBACK, BLOCKED, HUMAN_INTERVENTION e CLOSED.
- Contratos: DisasterSignal, ImpactAssessment, RecoveryReadiness, RecoveryPlan, RecoveryPointSelection, RecoveryEnvironmentRequest, RestoreRequest, DataErasureReconciliation, IdentityRevalidation, ServiceReintegrationRequest, RecoveryValidation e RecoveryClosure.
- Eventos: DISASTER_SIGNAL_DETECTED, IMPACT_ASSESSMENT_STARTED, RECOVERY_READINESS_GAP_FOUND, DISASTER_DECLARATION_REQUESTED, DISASTER_DECLARED, CONTAINMENT_REQUIRED, RECOVERY_PLAN_PROPOSED, RECOVERY_APPROVAL_REQUIRED, RECOVERY_PLAN_APPROVED, RECOVERY_POINT_SELECTED, RECOVERY_ENVIRONMENT_REQUESTED/READY, RESTORE_STARTED/COMPLETED, DATA_ERASURE_RECONCILIATION_REQUIRED, IDENTITY_REVALIDATION_REQUIRED, RECOVERY_VALIDATION_FAILED/PASSED, SERVICE_REINTEGRATION_REQUESTED/APPROVED/REINTEGRATED, RTO_BREACHED, RPO_BREACHED, ROLLBACK_STARTED e RECOVERY_CLOSED.
- Falhas: ponto inválido, ambiente alternativo comprometido, fornecedor indisponível/não aprovado, RTO/RPO em risco, conflito de dados, estado FC-02 desconhecido, identidade revogada, isolamento FC-04 ativo, falha parcial e rollback falhado têm respostas de bloqueio, alternativa autorizada ou intervenção humana.
- Auditoria e métricas: cronologia, decisor, autoridade, versão do plano, pontos, aprovações, recursos, fornecedores, custos, validações, desvios RTO/RPO, ações FC-01–FC-05, rollback; RTO/RPO reais, prontidão, integridade, tempo de deteção/declaração, custo e falhas de reintegração.
- Testes conceptuais: 20 cenários, incluindo indisponibilidade regional, corrupção, ponto adulterado, RTO/RPO falhados, fornecedor não aprovado, quarentena FC-04, credencial revogada, eliminação pendente, operações repetidas, ambiente inseguro, falhas de restauro/failover, modo degradado não autorizado, ausência de aprovação D3, rollback e exercício de recuperação.

**Limites explícitos da especificação:** não fixa valores de RTO/RPO; não identifica fornecedores/regiões efetivamente disponíveis; não define o detalhe técnico de failover/failback (por exemplo, topologias cold/warm/hot, fencing ou prevenção de split-brain); não fecha quem declara D2/D3; não define frequência universal dos exercícios. Estes pontos permanecem lacunas de decisão/arquitetura, não razões para dizer que a FC-06 não tem especificação.

**Conclusão corrigida:** FC-06 está **especificada funcionalmente, versão 1.0**. Implementação técnica não demonstrada; 20 testes definidos, execução pendente; validação operacional pendente.

## 3. Diagnóstico transversal preliminar

### 3.1 Relações e precedências

A sequência abaixo é uma proposta de coordenação, não uma decisão histórica já aprovada:

1. **FC-03** pode ser acionado em qualquer incidente quando exista suspeita de comprometimento de identidade, credenciais ou autorização. Não deve esperar pela recuperação.
2. **FC-04** contém/isola o serviço comprometido. A contenção pode ser simultânea à revogação FC-03.
3. **FC-01** só inicia a recuperação de dados depois de existir uma fonte de recuperação considerada íntegra e autorizada e de a contenção permitir operar com segurança.
4. **FC-06** coordena a continuidade e recuperação do ambiente operacional alternativo. Pode decorrer em paralelo com a investigação e recuperação de dados, mas não pode expor dados ainda comprometidos nem contornar FC-03/FC-04.
5. **FC-02** é um fluxo de privacidade/eliminação que pode ocorrer durante operação normal ou resposta a incidente. Deve manter a obrigação de eliminação sem destruir prematuramente evidência forense ou dados necessários à recuperação. Qualquer retenção temporária tem de ter base, âmbito, prazo e controlo explícitos.
6. **FC-05** é um fluxo de capacidade, não de recuperação de desastre. Pode apoiar FC-06 apenas quando a infraestrutura alternativa for provisionada sob a autoridade e o plano de recuperação de FC-06. A expansão automática não pode sobrepor-se a isolamento, bloqueios de segurança ou limites de custo.

### 3.2 Matriz de interação

| Par | Interação necessária | Risco a controlar |
|---|---|---|
| FC-01 ↔ FC-02 | Coordenar restauração e pedidos de eliminação; dados eliminados não podem reaparecer silenciosamente após restore. | Reintrodução de dados que já deviam estar eliminados. |
| FC-01 ↔ FC-03 | Validar credenciais e permissões antes, durante e depois do restore. | Restaurar sessões, tokens ou permissões comprometidas. |
| FC-01 ↔ FC-04 | Não restaurar serviço antes de contenção e validação de integridade. | Reintrodução do compromisso ou reinfeção. |
| FC-01 ↔ FC-06 | FC-06 restabelece capacidade operacional; FC-01 recupera dados. São resultados diferentes e coordenados. | Declarar continuidade com dados inconsistentes/incompletos. |
| FC-01 ↔ FC-05 | Provisionamento pode disponibilizar capacidade para restore, mas não escolhe a fonte nem valida os dados. | Confundir infraestrutura disponível com recuperação válida. |
| FC-02 ↔ FC-03 | Eliminar dados de conta não pode impedir a revogação de credenciais e sessões antes da eliminação. | Sessões sobreviventes ou perda de prova da revogação. |
| FC-02 ↔ FC-04 | Eliminação distribuída deve alcançar serviços isolados quando recuperados, sem reabrir o serviço comprometido. | Falha silenciosa de eliminação em sistemas isolados. |
| FC-02 ↔ FC-05 | Recursos, snapshots, caches e volumes temporários podem conter dados abrangidos por eliminação. | Dados persistentes em recursos escalados ou descartados. |
| FC-02 ↔ FC-06 | A recuperação alternativa deve aplicar tombstones/listas de eliminação e reconciliar pedidos pendentes antes de disponibilizar dados. | Ressurgimento de dados apagados no ambiente alternativo. |
| FC-03 ↔ FC-04 | Revogação e isolamento devem ser coordenados, mas independentes: um pode falhar sem bloquear o outro. | Acesso lateral durante a contenção. |
| FC-03 ↔ FC-05 | Provisionamento e credenciais de fornecedor/automação devem respeitar revogação imediata. | Credenciais antigas continuarem a provisionar recursos. |
| FC-03 ↔ FC-06 | O ambiente alternativo deve usar identidade/segredos válidos, não copiar cegamente sessões do ambiente comprometido. | Failover com credenciais comprometidas. |
| FC-04 ↔ FC-05 | Serviço isolado ou sinal de compromisso deve bloquear expansão que aumente a superfície afetada. | Escalar um serviço comprometido. |
| FC-04 ↔ FC-06 | O failover não pode encaminhar tráfego para o serviço comprometido; a alternativa deve ser verificada antes da ativação. | Propagação do incidente para a região alternativa. |
| FC-05 ↔ FC-06 | FC-05 pode executar provisionamento pedido pelo plano FC-06, sujeito a limites e aprovação próprios. | Dupla autoridade sobre infraestrutura, custo ou ativação. |

## 4. Contratos e mensagens transversais

### 4.1 Evidência atual

A documentação histórica descreve mensagens com identificador, correlation ID, origem/destinatário, tipo, contexto, prioridade, dependências, versão do contrato, timestamps, estado, payload tipado, resultado/erro e proveniência. Também prevê idempotência, retries limitados, timeout, circuit breaker, deduplicação e recuperação.

Esta descrição é uma referência arquitetural recuperada, mas não foi encontrada uma implementação transversal desses contratos no código consultado.

No backend atual:
- main.py regista routers FastAPI diretamente; não foi observado um barramento de eventos transversal nessa composição.
- get_db() abre uma sessão e uma transação por pedido HTTP.
- O repositório de afirmações aceita correlation_id e reutiliza-o nos eventos da mesma operação.
- A função genérica accounts.audit() gera um novo UUID de correlação para cada evento, o que impede correlação ponta a ponta quando uma operação produz vários eventos através desse helper.
- Não foi identificado middleware de correlação de pedidos nos ficheiros consultados.

### 4.2 Proposta para aprovação

Adotar um envelope comum independente do transporte, sem obrigar a introduzir já um message broker:

- message_id: identificador único da mensagem.
- correlation_id: identificador estável da operação ponta a ponta.
- causation_id: mensagem/ação que originou esta mensagem.
- contract_name e contract_version.
- message_type: command, event, request, response ou approval.
- producer e consumer/destinatário.
- occurred_at e recorded_at.
- operation_id e idempotency_key, quando aplicável.
- priority, deadline/timeout e dependências.
- subject_ref: referência ao recurso, utilizador, serviço ou ambiente, evitando payload pessoal desnecessário.
- payload tipado.
- result ou error normalizado.
- provenance e versão da política aplicável.

**Regra:** eventos descrevem algo que ocorreu; comandos solicitam uma ação; pedidos/respostas representam uma interação; aprovações registam uma decisão de autoridade. Não tratar estes tipos como intercambiáveis.

### 4.3 Requisitos de execução

- Idempotência obrigatória para operações repetíveis e efeitos externos.
- Retry limitado e apenas para falhas transitórias; nunca repetir cegamente operações não idempotentes.
- Timeout explícito e cancelamento cooperativo.
- Deduplicação por message_id/chave de idempotência.
- Outbox transacional ou mecanismo equivalente quando uma alteração de estado tiver de publicar evento sem perder consistência.
- Registo de tentativas e resultado final.
- Operações longas com operation_id, checkpoints e recuperação após reinício.
- Nenhum evento deve conter segredos, tokens ou conteúdo pessoal integral sem necessidade demonstrada.

## 5. Autoridade, autonomia e aprovações

1. Os fluxos não podem elevar a própria autonomia, alterar políticas, criar permissões ou remover bloqueios de segurança.
2. FC-03 e FC-04 têm autoridade de contenção/revogação dentro dos limites aprovados; não devem depender da disponibilidade de FC-05.
3. FC-01 e FC-06 não podem declarar dados íntegros apenas porque a infraestrutura está saudável.
4. FC-02 não pode certificar eliminação sem confirmação dos sistemas/destinos abrangidos; estados desconhecidos devem permanecer explicitamente pendentes.
5. FC-05 só provisiona dentro da política de autonomia, orçamento, limites de capacidade e validação de segurança.
6. Aprovações devem ser emitidas por uma autoridade distinta do componente que propõe a operação, sempre que a política exigir controlo humano.
7. Em conflito entre disponibilidade e segurança, prevalece a contenção segura; qualquer exceção exige aprovação explícita e auditável.

**Pendente:** harmonizar A0–A4 de FC-05 com a taxonomia de autonomia usada por FC-01–FC-04 e FC-06. As referências R1–R3 não podem ser mapeadas por inferência.

## 6. Estados e operações parciais

Não existe ainda uma máquina de estados comum aprovada para os seis fluxos. Não se deve forçar todos a usar a mesma sequência: expansão, eliminação, revogação e recuperação têm semânticas distintas.

Requisitos transversais mínimos propostos:
- cada execução tem estado, versão do contrato, timestamps, responsável e correlation ID;
- transições têm pré-condições e efeitos verificáveis;
- estado terminal não pode ser reaberto sem nova execução ou procedimento explícito;
- falhas parciais são representadas por destino/componente, não ocultadas num único estado global;
- BLOCKED, FAILED e HUMAN_INTERVENTION não são sinónimos;
- cancelamento não significa reversão;
- rollback não é presumido possível para operações destrutivas;
- operações de eliminação e revogação precisam de resultados por destino;
- operações de restore/failover precisam de checkpoints e prova de integridade.

### Estados transversais sugeridos (proposta, não aprovada)

REQUESTED → VALIDATING → APPROVED/REJECTED → EXECUTING → VERIFYING → SUCCEEDED/PARTIAL/FAILED

Estados de exceção: BLOCKED, CANCEL_REQUESTED, CANCELLED, ROLLBACK_IN_PROGRESS, ROLLBACK_FAILED, MANUAL_INTERVENTION.

Esta máquina deve funcionar como ciclo de vida da execução/orquestração, mantendo máquinas de estados próprias dentro de cada FC.

## 7. Evidência técnica no repositório

A revisão foi limitada aos ficheiros efetivamente lidos nesta passagem; não equivale a auditoria integral do repositório.

| Área | Evidência observada | Leitura |
|---|---|---|
| Composição da API | main.py regista routers diretamente; não mostra barramento de eventos transversal. | Não existe evidência de orquestração de eventos entre FCs no ponto de entrada consultado. |
| Transações | deps.py:get_db() cria sessão e transação por pedido. | Bom limite transacional local; não resolve transações distribuídas ou efeitos externos. |
| Identidade | accounts.py usa hash Argon2, tokens de sessão armazenados por hash, expiração e fecho de sessão. | Base de autenticação existe; revogação abrangente de credenciais/autorizações e operações em curso não está demonstrada. |
| Auditoria de conta | accounts.audit() atribui novo correlation ID a cada evento e usa entity_type=user, entity_id=-. | Correlação ponta a ponta e precisão da entidade são insuficientes para operações compostas. |
| Afirmações | statements.py aplica isolamento por owner, versionamento, validação epistemológica/cronológica e eventos de auditoria com correlation ID partilhado no repositório. | Exemplo positivo de correlação dentro de uma operação local; não demonstra propagação entre serviços. |
| Eliminação | StatementRepository.erase() elimina versões de uma linhagem e regista evento. | Eliminação local de afirmações; não equivale a FC-02 distribuído, nem prova eliminação em caches, backups, índices ou fornecedores. |
| Diário/Arquivo | journal.py filtra por utilizador, guarda/elimina reflexões e regista eventos. | Isolamento local observado; não existe neste router um processo distribuído de eliminação/recuperação. |
| Acesso premium | has_immediate_access() devolve sempre False. | Placeholder funcional observado; não representa autorização premium operacional. |
| Modelos | AuditEvent é append-only e guarda referências, não conteúdo pessoal. | Boa orientação de minimização; falta verificar retenção, integridade e correlação global. |
| Infraestrutura | Nos ficheiros consultados não foram encontrados controladores de provisionamento, failover, disaster recovery ou isolamento automatizado. | FC-04–FC-06 não têm implementação comprovada nesta amostra. |

### 7.1 Riscos técnicos prioritários

**R1 — Correlação inconsistente.** O helper genérico de auditoria cria um correlation ID novo em cada evento. Uma operação composta pode ficar fragmentada.  
**R2 — Ausência de contratos executáveis comuns.** O contrato de mensagem histórico não está demonstrado no backend consultado.  
**R3 — Eliminação apenas local.** Eliminar uma entidade numa tabela não prova a propagação da eliminação aos sistemas derivados.  
**R4 — Revogação incompleta não demonstrada.** Fechar uma sessão específica existe; revogação global, invalidação de credenciais e cancelamento/avaliação de operações em curso não estão provados.  
**R5 — Continuidade/DR não demonstrada.** Não foram encontrados artefactos operacionais de backup, restore, failover, failback, RTO/RPO ou testes de desastre nos ficheiros consultados.  
**R6 — Estado premium placeholder.** O controlo de acesso imediato está fixado em False; necessita de integração com a política real de subscrição/autorização antes de ser considerado funcional.

## 8. Lacunas que impedem aprovação final

| ID | Lacuna | Consequência |
|---|---|---|
| L-01 | Parâmetros operacionais finais FC-06: RTO/RPO por serviço, inventário de fornecedores/regiões, topologia e fencing/failback, autoridade D2/D3 e frequência de exercícios. | A especificação existe, mas a prontidão operacional não pode ser aprovada sem estes parâmetros. |
| L-02 | Especificações completas de contratos/eventos de FC-01–FC-04 nesta base documental. | A matriz de compatibilidade é parcial. |
| L-03 | Confirmar o mapa F78–F82 recuperado em 08A v1.1 contra as especificações autónomas originais; recuperar F81.01–F81.12. | A associação funcional está recuperada em síntese; falta validação das fontes autónomas e subfunções. |
| L-04 | Confirmar taxonomia de autonomia em cada fluxo e recuperar eventual F82 Parte V; não mapear A0–A4 para R1–R4/R1–R3 sem fonte. | FC-05 e FC-06 têm níveis A0–A4 próprios; equivalência com R1–R4/R1–R3 não demonstrada. |
| L-05 | RTO, RPO, retenção de backups e critérios de integridade. | Não aprovar recuperação/continuidade. |
| L-06 | Contratos reais de identidade, revogação e operações em curso. | Não provar cobertura FC-03. |
| L-07 | Inventário de sistemas de dados derivados e fornecedores. | Não provar cobertura FC-02. |
| L-08 | Política de evidência forense versus pedidos de eliminação. | Evitar destruição indevida ou retenção sem base. |
| L-09 | Orçamento, limites de escala, quotas e fornecedores aprovados. | Não aprovar execução automática de FC-05. |
| L-10 | Middleware/propagação de correlation ID e outbox/event delivery. | Não provar rastreabilidade ponta a ponta. |

## 9. Critérios de aceitação para a revisão transversal

A revisão só pode ser marcada como concluída quando:
1. As seis especificações e respetivas versões são identificadas.
2. Cada FC tem proprietário funcional, autoridade, entradas, saídas, contratos e eventos definidos.
3. Dependências e precedências estão documentadas sem ciclos injustificados.
4. A interação FC-01/FC-02 impede a reintrodução de dados eliminados após restore/failover.
5. FC-03 e FC-04 conseguem conter acessos e serviços sem depender do sucesso de FC-05/FC-06.
6. FC-05 não provisiona recursos em conflito com isolamento, revogação, orçamento ou política de desastre.
7. FC-06 não ativa infraestrutura alternativa sem validar identidade, integridade, dados e dependências.
8. Todas as operações compostas partilham correlation ID e deixam trilho auditável.
9. Idempotência, retries, timeouts, cancelamento e recuperação estão definidos por operação.
10. Estados parciais e falhas por destino são representáveis.
11. Testes de contrato e integração cobrem os cruzamentos críticos.
12. A documentação e o catálogo de requisitos são atualizados em conjunto, segundo docs/governanca/processo.md.

## 10. Plano de trabalho recomendado

| Ordem | Trabalho | Resultado |
|---|---|---|
| 1 | Recuperar e fixar versão integral de FC-06. | Especificação verificável. |
| 2 | Recuperar contratos, eventos, estados e testes completos FC-01–FC-04. | Matriz de origem documental. |
| 3 | Validar F78–F82 e a taxonomia de autonomia, sem inferir equivalências. | Catálogo de responsabilidades. |
| 4 | Aprovar envelope de mensagens e correlação ponta a ponta. | Contrato transversal versionado. |
| 5 | Definir coordenação de restore/eliminação/revogação/isolamento/failover/escala. | Matriz final de precedências e conflitos. |
| 6 | Definir estados de execução e tratamento de operações parciais. | Máquina de execução transversal. |
| 7 | Criar testes de contrato e integração entre FCs. | Evidência técnica reproduzível. |
| 8 | Atualizar catálogo, rastreabilidade e Documento Mestre no mesmo PR. | Revisão documental fechada. |

## 11. Decisão desta versão

**Resultado: revisão transversal iniciada, mas não aprovada/concluída.**

A revisão já identificou conflitos e riscos transversais relevantes:
- restore pode reintroduzir dados eliminados;
- failover pode reintroduzir identidades/credenciais comprometidas;
- expansão pode contrariar isolamento ou limites de custo;
- auditoria atual não garante correlação ponta a ponta;
- eliminação local não equivale a eliminação distribuída;
- FC-06 tem especificação funcional integral recuperada (05, v1.0); permanecem por aprovar parâmetros operacionais e implementação.

Não foram feitas alterações ao código nem à branch main. Esta versão é apenas documentação de diagnóstico e propostas explicitamente não aprovadas. Não se declara CI ou testes executados nesta auditoria.


## 12. Correção e atualização documental — versão 0.2

A versão 0.1 afirmava que a especificação integral FC-06 não tinha sido recuperada. Essa afirmação ficou desatualizada após a pesquisa do Library do projeto. Foram localizados e lidos:
- 05_FC06_Recuperacao_Desastres_Continuidade.docx (FC-06, v1.0, 28 secções);
- 06_Documento_Mestre_Fluxos_e_Contratos_FC01_FC06.docx (consolidação transversal, v1.0);
- 08_Adenda_Fluxos_FC01_FC06_e_Reconciliacao_F78_F82.docx (adenda, v1.0).

A versão 0.2 corrige a classificação: FC-06 está especificada funcionalmente. A lacuna passa a incidir sobre parâmetros de prontidão/execução operacional e decisões técnicas não fixadas, não sobre a existência da especificação.

A fonte 08 confirma expressamente que FC-01, FC-02 e FC-03 têm nomes/objetivos recuperados, mas os contratos apresentados nessa adenda são reconstruções propostas, não especificações históricas integrais. FC-04 tinha especificação funcional anterior estruturada em 26 secções e 20 testes; a harmonização dos nomes dos seus contratos ainda deve ser confirmada. FC-05 e FC-06 têm especificações detalhadas próprias. O Documento Mestre 06 classifica a consolidação transversal como planeamento funcional, não implementação.

**RTO/RPO:** não adotar os valores R1–R4 recuperados em resumos de contexto como valores aprovados para FC-06. O documento FC-06 v1.0 determina aprovação por serviço e não fixa valores globais. A taxonomia A0–A4 da FC-06 também não deve ser mapeada automaticamente para R1–R4 ou R1–R3.

**F78–F82:** a adenda 08 mantém todos estes identificadores por recuperar e proíbe atribuir-lhes nomes/responsabilidades sem fonte primária. A suposta «F82 Parte V» com níveis R1–R4, modos NORMAL/DEGRADADO/CONTINGÊNCIA/RECUPERAÇÃO, failover cold/warm/hot e fencing não foi localizada como documento primário nesta pesquisa; não será incorporada como decisão.

Não foram feitas alterações de código. A atualização é documental e corrige o estado da evidência.

## 13. Reconciliação histórica adicional — FC-01 a FC-03 e F78–F82

Foi localizado o documento **08A_Reconciliacao_Historica_e_Especificacao_FC01_FC03_v1_1.docx**, versão 1.1, de 14-11-2026. Este documento corrige e aprofunda a adenda 08 e altera a classificação anterior de algumas lacunas.

### 13.1 Responsabilidades F78–F82 recuperadas

A versão 08A recupera a seguinte associação funcional:
- **F78:** backups, preservação e recuperação de dados. Executa mecanismos de recuperação; não decide se os dados podem ser recuperados.
- **F79:** retenção, preservação, eliminação e governação do ciclo de vida dos dados. Decide o estado de retenção/eliminação.
- **F80:** identidade, autenticação, credenciais, autorização e permissões. Autoridade funcional de identidade.
- **F81:** cibersegurança, defesa ativa e resposta a incidentes. Deteta, classifica, contém e coordena risco; F81.01–F81.12 continuam por recuperar individualmente.
- **F82:** infraestrutura, recursos e execução operacional. Executa ações de infraestrutura dentro das autorizações recebidas; não decide legitimidade dos dados nem autorização funcional.

Esta associação está **recuperada em síntese histórica/documental v1.1**, mas as especificações autónomas originais de cada F78–F82 ainda devem ser confirmadas. Assim, a lacuna deixa de ser «não existe qualquer correspondência» e passa a ser «validar a correspondência recuperada contra as fontes autónomas originais». A autoridade funcional é separada da capacidade técnica de execução.

### 13.2 FC-01 — princípios e sequência histórica recuperados

A versão 08A recupera gatilhos e sequência de 10 passos: registo/âmbito; contenção e preservação coordenadas por F81; delimitação; seleção de ponto íntegro por F78; validação de retenção/eliminação por F79; identidade/autoridade por F80; ambiente isolado; recuperação/reconciliação; validação independente; autorização explícita para promoção e execução progressiva por F82.

Recupera também os princípios de não restaurar dados legitimamente eliminados, não reativar credenciais revogadas e não reintegrar serviço isolado sem autorização de segurança. Os estados S0–S9/SE têm origem histórica, mas a correspondência textual exata de cada código ainda carece de confirmação. O contrato normalizado está descrito; não deve ser rotulado como schema histórico aprovado.

### 13.3 FC-02 — autoridade F79 e processo distribuído recuperados

A finalidade distribuída e a autoridade F79 estão recuperadas. O âmbito inclui primários, réplicas, versões, snapshots, ficheiros, anexos, exportações, índices, caches, embeddings, vetores, grafos, análises, perfis, modelos derivados, filas, eventos, tarefas e backups. Distingue eliminar, restringir, anonimizar e preservar legalmente.

Os estados D0–D9/DE e o contrato normalizado são explicitamente propostas de normalização. Não reutilizar L0–L9/LE: a fonte 08A afirma que estes códigos pertencem a uma operação de recuperação seletiva/histórica ainda não identificada, e não ao FC-02.

### 13.4 FC-03 — regra central recuperada

F80 é a autoridade funcional de identidade/autenticação/permissões; F81 coordena o contexto de cibersegurança quando a revogação decorre de ameaça. A regra central recuperada é que revogar não significa interromper indiscriminadamente todas as operações em curso: bloquear novas ações não autorizadas e avaliar cada operação existente quanto a risco, integridade, consistência, revalidação e compensação.

Os estados R0–R9/RE e o contrato normalizado são propostas, não códigos históricos confirmados. A reemissão deve usar credencial nova; falha de propagação mantém o caso aberto.

### 13.5 Limites e estado do ponto 3

A fonte 08A declara o ponto 3 resolvido ao nível de recuperação e reconciliação funcional disponível, sem declarar FC-01–FC-03 historicamente completas nem tecnicamente implementadas. Esta auditoria adota a mesma distinção:
- **Resolvido documentalmente ao nível funcional disponível:** responsabilidades, princípios, precedências e sequências essenciais de FC-01–FC-03; mapa funcional F78–F82 recuperado em síntese.
- **Pendente de decisão/validação:** schemas/eventos originais FC-01–FC-03, correspondência exata dos códigos de estado, F81.01–F81.12, fonte autónoma F82 Parte V, autorização de emergência e parâmetros operacionais.
- **Pendente tecnicamente:** contratos executáveis, propagação de correlation ID, testes automatizados e implementação dos fluxos.

A «F82 Parte V» com R1–R4, modos NORMAL/DEGRADADO/CONTINGÊNCIA/RECUPERAÇÃO, topologias cold/warm/hot e fencing/split-brain não foi localizada como fonte primária. Não confundir com FC-06 A0–A4 nem usar como decisão aprovada.