# Auditoria transversal FC-01–FC-06
## Versão 0.1 — diagnóstico documental e técnico preliminar

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

As quatro primeiras especificações foram dadas como concluídas ao nível funcional. Isso não significa que estejam implementadas ou tecnicamente validadas.

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

### 2.3 FC-06

O nome e objetivo geral estão recuperados: recuperação de desastre com infraestrutura alternativa e continuidade operacional. Não foi recuperado nesta revisão o texto integral da especificação funcional, incluindo estados, RTO/RPO, critérios de declaração de desastre, autoridade de failover/failback, integridade de dados, dependências externas, testes e condições de encerramento.

**Conclusão:** FC-06 não pode ainda ser considerada especificada de forma verificável. Esta lacuna impede fechar a matriz completa de contratos e transições sem inventar requisitos.

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
| L-01 | Texto integral e versão aprovada de FC-06. | Não é possível validar sequência, RTO/RPO, failover/failback e critérios de sucesso. |
| L-02 | Especificações completas de contratos/eventos de FC-01–FC-04 nesta base documental. | A matriz de compatibilidade é parcial. |
| L-03 | Catálogo validado e mapeamento de F78–F82/F81.01–F81.12. | Não atribuir responsabilidades finais por identificador histórico. |
| L-04 | Taxonomia comum de autonomia e equivalência (ou não) A0–A4/R1–R3. | Evitar escalada de permissões por interpretação. |
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
- FC-06 não tem especificação integral recuperada nesta passagem.

Não foram feitas alterações ao código nem à branch main. Esta versão é apenas documentação de diagnóstico e propostas explicitamente não aprovadas. Não se declara CI ou testes executados nesta auditoria.
