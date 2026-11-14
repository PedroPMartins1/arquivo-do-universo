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
