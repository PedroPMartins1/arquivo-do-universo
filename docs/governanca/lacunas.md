# Registo de lacunas

Lacunas recuperadas do dossiê §53. Uma lacuna só fecha com uma fonte (conversa, documento ou decisão explícita) registada.

| ID | Lacuna | Bloqueia | Estado | Notas |
|---|---|---|---|---|
| L-001 | Texto integral das primeiras conversas de conceção da app astrológica | — | **parcialmente fechada** | Prompt original e parte da conversa recebidos ([conversa-original-chatgpt.txt](../dossie/conversa-original-chatgpt.txt)); a conversa termina nas Revelações do Dia |
| L-002 | Definição exata da opção C do Mapa Natal | — | **resolvida** ([D-019](decisoes.md)) | Era sobre o aspeto visual do mapa; fica por definir mais tarde, sem impacto no cálculo |
| L-003 | Definição exata da opção C para a hora de nascimento | — | **resolvida** ([D-020](decisoes.md)) | Data e hora de nascimento têm de ser exatas |
| L-004 | Lista integral de funcionalidades e IDs anteriores a F59 | Fase 1 (catálogo final) | aberta | O catálogo usa IDs provisórios `AU-*` até à recuperação |
| L-005 | Especificação original completa de F60 e F61 | F60/F61 «especificada» | aberta | O F60 avança com o dossiê §18 como base mínima |
| L-006 | Documento Mestre do Produto, se existir | — | aberta | A visão consolidada está em [visao.md](../produto/visao.md) |
| L-007 | Decisões de interface, navegação e experiência de utilizador | UI detalhada | parcialmente fechada | Cinco áreas (Hoje, Explorar, Jornada, Arquivo, Perfil), onboarding e identidade «opção C» (D-024) definidos; ecrãs detalhados por fazer |
| L-008 | Técnicas astrológicas aprovadas para a primeira versão | Fase 4 (trânsitos, etc.) | aberta | Mapa natal base definido (D-021); faltam trânsitos, progressões, etc. |
| L-009 | Fontes/efemérides e regras de cálculo | Fase 4 | **fechada** | Swiss Ephemeris + Skyfield/JPL (D-013); zodíaco, casas e orbes por omissão em D-021 |
| L-010 | Arquitetura e stack existentes | — | **fechada** | Não havia código (D-011). Stack em ADR-0001 |
| L-011 | Nome, URL e estado do repositório | — | **fechada** | `arquivo-do-universo` (público, AGPL) |
| L-012 | Estado real de cada funcionalidade | — | **fechada** | Baseline: [auditoria 0000](../auditoria/0000-baseline.md) |
| L-013 | Testes, deployments e ambiente de execução | Fase 2 (deploy) | parcialmente fechada | CI no GitHub Actions. Fornecedor do servidor por decidir (D-017) |
| L-014 | Calendários não gregorianos (juliano, etc.) nas datas históricas | F60 completo | aberta | O F60 só aceita gregoriano proléptico até haver decisão |
| L-015 | Pesquisa do local de nascimento por nome (geocodificação) | Registo para o público | fechada (D-027) | Base offline GeoNames; localidades com menos de 500 habitantes podem faltar e ficam com a alternativa das coordenadas |
| L-016 | Recuperação de palavra-passe, verificação de email e limite de tentativas de login | Antes de abrir ao público | aberta | Exige escolher fornecedor de email |
| L-017 | Envio de dados pseudonimizados à Anthropic: rever os termos de tratamento de dados (DPA), listar a Anthropic como subcontratante na política de privacidade e confirmar retenção/região antes de abrir ao público | Abrir ao público | aberta | Claude recebe factos astrológicos calculados, sem dados de identificação ou nascimento |
| L-018 | Exportação das reflexões do Diário para assegurar a portabilidade dos dados ao abrigo do RGPD | Antes de abrir ao público | aberta | As reflexões são dados íntimos e nunca são enviadas ao modelo |
| L-019 | Cifragem das reflexões em repouso | Antes de abrir ao público | aberta | As reflexões são os dados mais íntimos da aplicação |

| L-020 | Texto integral aprovado da especificação FC-06: gatilhos, estados, RTO/RPO, autoridade de failover/failback, integridade, dependências e testes | Fecho da revisão transversal FC-01–FC-06 | **fechada documentalmente** | Fonte localizada: 05_FC06_Recuperacao_Desastres_Continuidade.docx, v1.0, 14-11-2026, 28 secções. Permanecem lacunas operacionais em L-025. Ver auditoria transversal v0.2 |
| L-021 | Schemas/eventos históricos FC-01–FC-03, correspondência exata dos códigos de estado e harmonização final dos contratos FC-04 | Fecho da revisão transversal FC-01–FC-06 | aberta | 08A v1.1 recupera princípios e sequências FC-01–FC-03, mas classifica estados/contratos normalizados como propostas; FC-04 tem especificação anterior, com nomes formais por harmonizar |
| L-022 | Confirmar mapa F78–F82 contra especificações autónomas; recuperar texto integral F81, títulos/detalhes das 12 componentes F82.01–F82.12 e formulação integral dos testes F82; validar autonomia e testes | Aprovação final de autoridade e arquitetura dos FCs | parcialmente fechada | 08A v1.1 recupera responsabilidades F78–F82. Sínteses históricas recuperam 12 títulos F81.01–F81.12, F81 R1–R3, F82 com 12 componentes, sete camadas, A1–A4 e oito famílias de teste. Fontes autónomas integrais e detalhe F82 ainda ausentes. A referência «PARTE V — DOMÍNIOS FUNCIONAIS E MOTORES» pertence ao Dossiê Mestre global; não há evidência de uma Parte V própria da F82. Ver reconciliacao-f78-f82-v0.1.md |
| L-023 | Definição de correlação ponta a ponta, envelope comum, idempotência, outbox e tratamento de operações parciais | Contratos transversais executáveis | aberta | Requisito histórico conceptual; implementação não demonstrada |
| L-024 | Inventário de sistemas derivados, destinos de eliminação e política de backups/retensão | Aprovação de FC-02 e interação com FC-01/FC-06 | aberta | Eliminação local não prova propagação distribuída |
| L-025 | Aprovar RTO/RPO por serviço, orçamento/quotas, fornecedores/regiões e critérios de integridade; definir autoridade D2/D3 e exercícios FC-06 | Prontidão operacional FC-01/FC-05/FC-06 | aberta | FC-06 v1.0 exige valores por serviço e não fixa valores universais. Topologia/fencing/failback e fornecedores disponíveis também não estão decididos. |
| L-026 | Confirmar a data futura de D-030 e da versão PROMPT_VERSION indicada em D-029, e validar os horários de desbloqueio face à regra de 4 Revelações principais + bónus opcional | Congelamento dos requisitos de interpretação e desbloqueio | parcialmente fechada | D-018/D-029 foram reconciliadas por precedência explícita; D-028 e a visão do produto foram alinhadas com 4 principais + bónus opcional. Falta confirmar a data futura D-030 (16-11-2026) e PROMPT_VERSION 2026-11-17.1. Ver auditoria global GA-03/GA-05. |
| L-027 | Harmonizar a versão das efemérides JPL e a decisão sobre execução do worker de pré-geração | Arquitetura astrológica/técnica e operação do worker | aberta | ADR-0001 refere DE440/DE440s, enquanto script/README usam DE421; ADR-0001 diz sem jobs de fundo na fase inicial, mas D-031 introduz pré-geração. Ver auditoria global GA-06/GA-07. |
