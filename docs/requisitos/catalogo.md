# Catálogo de requisitos

IDs `F59`–`F62` são originais e preservados. IDs `AU-*` são **provisórios** até se recuperar a lista
original de funcionalidades anteriores a F59 ([L-004](../governanca/lacunas.md)); nessa altura cada
`AU-*` recebe o ID original correspondente (o provisório fica registado como alias).

Estados conforme [estados oficiais](../governanca/estados.md). Baseline: [auditoria 0000](../auditoria/0000-baseline.md).

| ID | Nome | Fonte | Fase | Estado | Evidência |
|---|---|---|---|---|---|
| AU-NUC | Inteligência Pessoal / núcleo central | §12 | 2 | em especificação | — |
| AU-ORQ | Orquestração global e gestão de tarefas | §12, §29 | 2–3 | em especificação | — |
| AU-COM | Comunicação, síntese e personalização | §25 | 5 | em especificação | — |
| AU-CTX | Gestão de contexto, identidade e permissões | §26, §28 | 2 | em desenvolvimento | Isolamento por utilizador na persistência |
| AU-EPI | Classificação epistemológica transversal | §10–11 | 2 | em desenvolvimento | Classes, metadados e regra da astrologia implementados |
| AU-MEM | Memória e conhecimento | §13 | 2, 5 | em desenvolvimento | Afirmações versionadas e proveniência |
| AU-INV | Investigação e aquisição de fontes | §16 | 5 | em especificação | — |
| AU-RAC | Raciocínio e decisão | §22 | 3 | em especificação | — |
| AU-AST | Motor astrológico (inclui Mapa Natal) | §14 | 4 | em especificação | Bloqueado parcialmente por L-008 (técnicas/casas/orbes); hora de nascimento exata (D-020) implementada |
| AU-ASN | Motor astronómico | §15 | 4 | em especificação | — |
| AU-CIE | Motor científico / análise de evidência | §16 | 5 | em especificação | — |
| F59 | Inteligência Preditiva | §17 | 3 | em especificação | — |
| F60 | Inteligência Temporal | §18 | 2–3 | em desenvolvimento | Primitivas temporais implementadas; especificação original em falta (L-005) |
| F61 | Inteligência Relacional | §19 | 3 | em especificação | Especificação original em falta (L-005) |
| F62 | Inteligência Causal, Mecanismos e Explicabilidade | §20 | 3 | em especificação | — |
| AU-OBS | Observabilidade e monitorização global | §21 | 3, 6 | em especificação | — |
| AU-PLA | Planeamento estratégico, objetivos e execução | §23 | 3, 6 | em especificação | — |
| AU-EVO | Inteligência evolutiva e aprendizagem | §24 | 3 | em especificação | — |
| AU-VAL | Validação e qualidade | §12, §32 | transversal | em especificação | — |
| AU-ENG | Engenharia e gestão de versões | §34 | transversal | em desenvolvimento | CI, ADR, este catálogo |
| AU-SEG | Segurança e privacidade | §28 | transversal | em especificação | — |
| AU-EXT | Extensibilidade e portabilidade | §12, §45 | 7 | em especificação | — |

«em especificação» quer dizer que existe descrição funcional no dossiê, mas ainda não existe o conjunto
completo do §30 (regras, entradas/saídas, critérios de aceitação, testes associados).
