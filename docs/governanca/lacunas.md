# Registo de lacunas

Lacunas recuperadas do dossiê §53. Uma lacuna só fecha com uma fonte (conversa, documento ou decisão explícita) registada.

| ID | Lacuna | Bloqueia | Estado | Notas |
|---|---|---|---|---|
| L-001 | Texto integral das primeiras conversas de conceção da app astrológica | Fase 4 | **aguarda material**: o Pedro vai fornecer o histórico | — |
| L-002 | Definição exata da opção C do Mapa Natal | Fase 4 (Mapa Natal) | aberta | Princípio conhecido: C = a alternativa mais completa ([D-010](decisoes.md)). O conteúdo das opções tem de vir do histórico |
| L-003 | Definição exata da opção C para a hora de nascimento | Fase 4 (Mapa Natal) | aberta | Igual a L-002. O F60 já representa a hora exata, aproximada (± minutos) e desconhecida, sem escolher uma política |
| L-004 | Lista integral de funcionalidades e IDs anteriores a F59 | Fase 1 (catálogo final) | aberta | O catálogo usa IDs provisórios `AU-*` até à recuperação |
| L-005 | Especificação original completa de F60 e F61 | F60/F61 «especificada» | aberta | O F60 avança com o dossiê §18 como base mínima |
| L-006 | Documento Mestre do Produto, se existir | Fase 1 | aberta | — |
| L-007 | Decisões de interface, navegação e experiência de utilizador | Fase 4 (UI) | aberta | — |
| L-008 | Técnicas astrológicas aprovadas para a primeira versão | Fase 4 (trânsitos, etc.) | aberta | — |
| L-009 | Fontes/efemérides e regras de cálculo | Fase 4 | **parcialmente fechada** | Swiss Ephemeris + Skyfield/JPL (D-013). Faltam o zodíaco, o sistema de casas por defeito e as orbes |
| L-010 | Arquitetura e stack existentes | — | **fechada** | Não havia código (D-011). Stack em ADR-0001 |
| L-011 | Nome, URL e estado do repositório | — | **fechada** | `arquivo-do-universo` (público, AGPL) |
| L-012 | Estado real de cada funcionalidade | — | **fechada** | Baseline: [auditoria 0000](../auditoria/0000-baseline.md) |
| L-013 | Testes, deployments e ambiente de execução | Fase 2 (deploy) | parcialmente fechada | CI no GitHub Actions. Fornecedor do servidor por decidir (D-017) |
| L-014 | Calendários não gregorianos (juliano, etc.) nas datas históricas | F60 completo | aberta | O F60 só aceita gregoriano proléptico até haver decisão |
