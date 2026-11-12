# Registo de decisões consolidadas

Cada decisão tem ID, origem e data. As decisões não se reabrem sem um novo registo que as substitua.

| ID | Decisão | Origem | Data |
|---|---|---|---|
| D-001 | O produto chama-se **Arquivo do Universo — Inteligência Pessoal** | Dossiê v2.0 §52 | 2026-11-12 |
| D-002 | Começou como app astrológica personalizada e foi ampliado para plataforma de inteligência pessoal | Dossiê §1–2 | 2026-11-12 |
| D-003 | Arquitetura e funcionamento seguem a **opção C**: integrada, híbrida, adaptativa e autónoma dentro de limites, com transparência e intervenção humana | Dossiê §6, §52 | 2026-11-12 |
| D-004 | O Documento Mestre deve ser completo e explicativo, não uma síntese curta | Dossiê §30, §52 | 2026-11-12 |
| D-005 | A astrologia fica epistemologicamente separada da ciência e da previsão empírica | Dossiê §11, §17.6 | 2026-11-12 |
| D-006 | F59 = Inteligência Preditiva; F60 = Inteligência Temporal; F61 = Inteligência Relacional; F62 = Inteligência Causal, Mecanismos e Explicabilidade | Dossiê §52 | 2026-11-12 |
| D-007 | Não criar motores duplicados. A monitorização integra-se na Observabilidade Global; a inteligência evolutiva é transversal | Dossiê §21, §24, §36 | 2026-11-12 |
| D-008 | Especificação, desenvolvimento, implementação, testes e validação são estados distintos. Nada é declarado sem evidência | Dossiê §31, §52 | 2026-11-12 |
| D-009 | Preservar histórico, proveniência, incerteza, versões e contradições | Dossiê §13.5, §52 | 2026-11-12 |
| D-010 | **Significado de "opção C"**: nas conversas originais com o ChatGPT, o utilizador escolhia sempre a alínea C por ser a alternativa mais completa. Nas decisões ainda por recuperar, "opção C" quer dizer *a alternativa mais completa entre as apresentadas*. O conteúdo exato de cada opção continua a ter de ser recuperado do histórico ([L-002](lacunas.md), [L-003](lacunas.md)) | Pedro, sessão Devin | 2026-11-12 |
| D-011 | Não existia código anterior: o projeto começa do zero | Pedro, sessão Devin | 2026-11-12 |
| D-012 | Stack: monólito modular em Python/FastAPI/PostgreSQL + React/TypeScript | [ADR-0001](../adr/0001-stack.md) | 2026-11-12 |
| D-013 | Cálculos astrológicos com Swiss Ephemeris, validados com Skyfield/JPL | [ADR-0001](../adr/0001-stack.md) | 2026-11-12 |
| D-014 | Vários utilizadores desde o início, com isolamento de dados por utilizador | Pedro, sessão Devin | 2026-11-12 |
| D-015 | Código-fonte publicado sob AGPL-3.0 | [ADR-0002](../adr/0002-licenca-agpl.md) | 2026-11-12 |
| D-016 | Entrega por fatia vertical: núcleo → F60 → Mapa Natal básico, antes dos restantes motores | [ADR-0003](../adr/0003-fatia-vertical.md) | 2026-11-12 |
| D-017 | A aplicação vai correr num servidor (não só localmente). Fornecedor ainda por decidir | Pedro, sessão Devin | 2026-11-12 |
| D-018 | O fornecedor de IA é escolhido pelo Devin com base técnica. Até lá, fica atrás de uma interface própria | Pedro, sessão Devin | 2026-11-12 |
| D-019 | A opção C do Mapa Natal dizia respeito ao aspeto visual; fica por definir e não bloqueia o cálculo | Pedro, sessão Devin | 2026-11-12 |
| D-020 | Data e hora de nascimento têm de ser exatas: data completa, hora ao minuto, local conhecido, sem margem de incerteza; uma hora repetida na mudança de hora exige indicação explícita da ocorrência e uma hora inexistente é rejeitada | Pedro, sessão Devin (regras operacionais: Devin) | 2026-11-12 |
| D-021 | Mapa Natal suporta vários sistemas. Por omissão, a prática corrente em Portugal (primeiro mercado, com expansão prevista para outros países): zodíaco tropical, casas Placidus, Nodo verdadeiro, aspetos ptolemaicos com orbes 8/8/7/7/5 (+2 para Sol/Lua). Sideral exige ayanamsa explícito; Placidus/Koch/Topocêntrico são recusados acima do círculo polar, sem troca silenciosa. Textos por locale (pt-PT primeiro) | Pedro, sessão Devin (valores concretos: Devin) | 2026-11-12 |
| D-022 | **Visão do produto**: aplicação de astrologia para consulta diária, por subscrição e sem anúncios, profundamente personalizada a partir do mapa natal ([visão](../produto/visao.md)). Os motores do dossiê v2.0 (F59–F62, autonomia) passam a secundários e só entram onde servirem a aplicação. Substitui o foco de D-002/D-003 | Pedro, prompt original e sessão Devin | 2026-11-12 |
| D-023 | Tom místico e envolvente na experiência; internamente nunca se inventam acontecimentos celestes nem se apresenta a astrologia como ciência comprovada (mantém D-005) | Pedro, sessão Devin | 2026-11-12 |
| D-024 | Identidade visual «opção C»: combinação de experiência mística com design premium e navegação simples | Conversa original com o ChatGPT | 2026-11-12 |
| D-025 | Nova ordem de entrega ([ADR-0004](../adr/0004-ordem-app-astrologica.md)), que substitui o passo 5 de D-016 | Devin, após D-022 | 2026-11-12 |
| D-026 | **Contas**: email + palavra-passe (mín. 10 caracteres, hash Argon2id). Sessão por cookie `httpOnly`, `SameSite=Lax`, válida 30 dias; na base de dados só fica o hash SHA-256 do token. Um perfil de nascimento por conta, validado pela regra D-020. Apagar a conta remove todos os dados e anonimiza a auditoria (RGPD) | Devin, passo 1 do ADR-0004 | 2026-11-12 |
