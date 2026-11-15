# Reconciliação funcional F78–F82
## Versão 0.1 — síntese histórica e lacunas de fonte primária

**Data:** 15 de novembro de 2026  
**Estado:** reconciliação documental parcial; não constitui aprovação de implementação.  
**Fontes usadas:** 08A_Reconciliacao_Historica_e_Especificacao_FC01_FC03_v1.1.docx; 07_Documento_Mestre_Governanca_Seguranca_Dados_e_Producao.docx; sínteses históricas de conversas de 13–14 de novembro de 2026; Documento Mestre Operacional.

## 1. Método e limites

A reconciliação separa:
- **Recuperado em documento:** aparece em 08A v1.1.
- **Recuperado em síntese histórica:** foi identificado em resumos/auditorias anteriores de conversas, mas o texto original autónomo não está disponível nesta revisão.
- **Por confirmar:** necessita da especificação autónoma ou da mensagem original.
- **Não confirmado:** não incorporar como decisão.

A síntese histórica não substitui a fonte primária. Os títulos e responsabilidades abaixo podem ser usados como mapa de trabalho com essa qualificação, não como prova de que todas as regras ou contratos estão integralmente recuperados.

## 2. Mapa de responsabilidades

| ID | Título / responsabilidade recuperada | Fonte e confiança | Estado |
|---|---|---|---|
| F78 | Backups, preservação e recuperação de dados | 08A v1.1, §§1–2 | Responsabilidade recuperada em documento; especificação autónoma por confirmar |
| F79 | Retenção, preservação, eliminação e governação do ciclo de vida dos dados | 08A v1.1, §§1–2 | Responsabilidade recuperada em documento; especificação autónoma por confirmar |
| F80 | Identidade, autenticação, credenciais, autorização e permissões | 08A v1.1, §§1–2 | Responsabilidade recuperada em documento; especificação autónoma por confirmar |
| F81 | Inteligência de Cibersegurança, Defesa Ativa e Resiliência Operacional | Síntese histórica de 13–14 Nov 2026; 08A confirma domínio de cibersegurança/defesa ativa/resposta a incidentes | Título e componentes recuperados em síntese; fonte autónoma por confirmar |
| F82 | Inteligência de Infraestrutura, Orquestração e Gestão Autónoma de Recursos | Síntese de auditoria histórica de 13 Nov 2026; 08A confirma infraestrutura, recursos e execução operacional | Título/estrutura recuperados em síntese; fonte autónoma por confirmar |

### 2.1 Autoridade funcional

- F78 executa mecanismos de backup/preservação/recuperação; não decide legitimidade da recuperação.
- F79 decide retenção, eliminação, restrição, anonimização e preservação legal.
- F80 decide identidade, autenticação, credenciais e permissões.
- F81 deteta, classifica, contém e coordena resposta a ameaças; não substitui a execução de infraestrutura.
- F82 fornece e executa infraestrutura, recursos e orquestração dentro de autorizações recebidas; não substitui autoridade de F79/F80/F81.

Esta separação é coerente com 08A v1.1 e deve ser preservada.

## 3. F81 — Inteligência de Cibersegurança, Defesa Ativa e Resiliência Operacional

### 3.1 Componentes recuperados em síntese histórica

A auditoria histórica de 13–14 de novembro identifica 12 componentes, não 18:

| ID | Designação recuperada |
|---|---|
| F81.01 | Inteligência de ameaças |
| F81.02 | Gestão de vulnerabilidades |
| F81.03 | Deteção de intrusões |
| F81.04 | Monitorização comportamental |
| F81.05 | Defesa contra ataques |
| F81.06 | Proteção de APIs e comunicações |
| F81.07 | Segurança da cadeia de fornecimento |
| F81.08 | Isolamento de componentes |
| F81.09 | Resposta autónoma a incidentes |
| F81.10 | Recuperação segura |
| F81.11 | Testes e simulações |
| F81.12 | Avaliação contínua de segurança |

**Estado:** títulos e quantidade de 12 componentes recuperados em síntese histórica; não foi localizada nesta revisão a especificação autónoma integral de cada componente. A referência a 18 componentes foi explicitamente identificada em histórico como mistura documental e não deve ser reutilizada.

### 3.2 Autonomia F81 recuperada em síntese

| Nível | Regra recuperada | Limite |
|---|---|---|
| R1 | Ações automáticas de baixo impacto, como alertas e bloqueios predefinidos | Escopo e política previamente definidos |
| R2 | Ações automáticas condicionadas, como isolamento/revogação dentro de políticas e limites | Não altera políticas nem se autoeleva |
| R3 | Operações críticas exigem aprovação humana | Aprovação explícita e auditável |

Não existe evidência suficiente para mapear R1–R3 para A0–A4. Esta taxonomia é específica da F81 segundo o histórico recuperado.

## 4. F82 — Inteligência de Infraestrutura, Orquestração e Gestão Autónoma de Recursos

### 4.1 Estrutura recuperada em síntese histórica

A auditoria histórica de 13 de novembro identifica a designação F82 e 12 componentes F82.01–F82.12. A lista nominal completa desses componentes não está presente no contexto documental disponível e não será reconstruída por suposição.

Foram recuperadas sete camadas técnicas:
1. Governação.
2. Inteligência.
3. Orquestração.
4. Computação.
5. Armazenamento.
6. Comunicações.
7. Observabilidade.

O histórico distingue a especificação original F82.01–F82.12 de expansões posteriores F82.13–F82.124, classificadas como síntese/desenvolvimento posterior e não como inventário oficial da especificação original.

### 4.2 Autonomia F82 recuperada em síntese

| Nível | Regra recuperada |
|---|---|
| A1 | Monitorizar e recomendar. |
| A2 | Otimizar recursos dentro de limites aprovados. |
| A3 | Reorganizar serviços/capacidade segundo políticas predefinidas. |
| A4 | Aprovação humana para infraestrutura crítica e despesas extraordinárias. |

Esta taxonomia não deve ser confundida com os níveis A0–A4 definidos especificamente na FC-06. A semelhança de rótulos não prova equivalência de permissões.

### 4.3 Testes F82 recuperados

O histórico identifica oito cenários próprios, descritos por famílias:
- aumento de carga;
- redução de carga;
- falhas;
- excesso orçamental;
- estrangulamento de capacidade;
- falha de rede;
- recuperação;
- alteração não autorizada.

A descrição disponível enumera as famílias, mas não recupera a formulação integral dos oito casos, os IDs, pré-condições ou resultados esperados. Não converter esta lista em testes executáveis sem a fonte original.

### 4.4 F82 Parte V

Não foi recuperado texto primário que sustente uma «F82 Parte V» com:
- níveis R1–R4;
- modos NORMAL/DEGRADADO/CONTINGÊNCIA/RECUPERAÇÃO;
- failover geográfico cold/warm/hot;
- fencing ou prevenção de split-brain.

A fonte histórica consultada afirma que estes elementos não aparecem nos trechos disponíveis da especificação original de F82. Não devem ser incorporados como decisões. A continuidade e recuperação global já estão funcionalmente especificadas na FC-06 v1.0; as escolhas de topologia e mecanismos técnicos permanecem decisões de arquitetura pendentes.

## 5. Contratos e integração entre F78–F82

O histórico de 13 de novembro recupera princípios de integração por APIs, eventos e filas, com:
- contratos versionados;
- correlação entre operações;
- autenticação e autorização;
- idempotência e deduplicação;
- estados identificáveis;
- auditoria;
- tratamento de indisponibilidade sem transferência automática de autoridade;
- testes de integração.

A consolidação posterior identificou testes INT-01–INT-16 para interações entre capacidades. Estes testes são material de harmonização transversal, não prova de que pertençam à especificação autónoma original F82.

**Regra:** a indisponibilidade de F79, F80 ou F81 não autoriza F82 a assumir a respetiva decisão. A operação deve ficar suspensa, bloqueada ou escalada conforme política.

## 6. Divergências e decisões a preservar

| Tema | Evidência atual | Tratamento |
|---|---|---|
| Número de componentes F81 | Histórico identifica 12; referência a 18 foi classificada como mistura | Manter 12; não reabrir para 18 sem fonte primária |
| Componentes F81.01–F81.12 | Títulos recuperados em síntese; texto integral ausente | Registar como mapa preliminar; recuperar especificações autónomas |
| Componentes F82.01–F82.12 | Quantidade recuperada; títulos individuais ausentes | Não inventar títulos |
| F82.13–F82.124 | Expansão posterior não oficial segundo auditoria histórica | Não integrar no catálogo oficial |
| Autonomia F81 R1–R3 | Recuperada em síntese histórica | Manter separada de A0–A4 |
| Autonomia F82 A1–A4 | Recuperada em síntese histórica | Manter separada de FC-06 A0–A4 |
| F82 Parte V / R1–R4 | Fonte primária não recuperada | Não adotar |
| Modos cold/warm/hot, fencing/split-brain | Não aparecem nos trechos originais recuperados | Decisão técnica pendente, não requisito confirmado |

## 7. Lacunas e ações

| ID | Ação | Estado |
|---|---|---|
| F78-SRC | Localizar especificação autónoma F78 e confirmar processos de backup/recuperação | Aberta |
| F79-SRC | Localizar especificação autónoma F79 e confirmar políticas/autoridade | Aberta |
| F80-SRC | Localizar especificação autónoma F80 e confirmar contratos de identidade | Aberta |
| F81-SRC | Recuperar documento original F81 e detalhe das 12 componentes, estados, contratos e testes | Aberta |
| F82-SRC | Recuperar documento original F82 e títulos/contratos das 12 componentes | Aberta |
| F82-PV | Localizar eventual fonte intitulada Parte V; confirmar se existe e qual a versão | Aberta; não presumir conteúdo |
| F82-TST | Recuperar os oito testes próprios em forma integral | Parcial |
| F82-INT | Recuperar a fonte dos testes INT-01–INT-16 e distinguir original de integração posterior | Parcial |

## 8. Conclusão

O mapa funcional F78–F82 está recuperado em síntese suficientemente consistente para orientar responsabilidades e evitar sobreposições. F81 tem 12 componentes identificados e autonomia R1–R3 em síntese histórica. F82 tem título, 12 componentes, sete camadas, autonomia A1–A4 e oito famílias de testes recuperados em síntese.

A reconciliação não está documentalmente fechada ao nível das especificações autónomas: faltam as fontes integrais, os títulos de F82.01–F82.12, o detalhe de F81.01–F81.12, a fonte eventual de F82 Parte V e os testes completos. A implementação técnica não foi avaliada nem declarada.

Nenhum conteúdo posterior atribuído a F82 Parte V, R1–R4, cold/warm/hot ou fencing/split-brain é aceite como decisão sem fonte primária.
