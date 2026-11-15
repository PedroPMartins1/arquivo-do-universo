# Auditoria global do projeto — v0.1

**Data:** 15 de novembro de 2026  
**Branch auditada:** `audit/revisao-transversal-fc-01-fc-06`  
**Commit auditado:** `8120063b753a985b4c37d1caa534ca705ab3e21c`  
**Base de comparação:** `main` em `0531e06f7a11132d996d2c9c79b4b9078b7e1afe`  
**Estado:** diagnóstico documental e técnico preliminar. Não aprova arquitetura nem autoriza produção.

## 1. Âmbito e método

Foram cruzados:
- visão do produto e Dossiê Mestre;
- decisões D-001–D-032;
- ADR-0001–ADR-0004;
- estados oficiais e registo de lacunas;
- catálogo de requisitos e matriz de rastreabilidade;
- baseline de engenharia;
- Documento Mestre Operacional e auditorias FC-01–FC-06 / F78–F82;
- README e estrutura efetiva do repositório;
- configuração CI, fontes de implementação e testes existentes;
- estado da PR #17 e execução de CI associada ao commit auditado.

A auditoria distingue decisão, especificação, código presente, teste automatizado, validação operacional e produção. Não presume que uma camada prove a seguinte.

## 2. Resultado executivo

A arquitetura documental tem uma base coerente: D-022 coloca a aplicação astrológica no centro; ADR-0004 orienta a entrega para fatias utilizáveis; D-008 exige evidência antes de alterar estados; o catálogo e a rastreabilidade identificam código e testes para várias capacidades já presentes.

A auditoria identificou contradições e metadados por reconciliar. Durante esta revisão foram já corrigidos o estado do README, o índice documental, as referências obsoletas L-002/L-003, a precedência D-018/D-029 e a contagem de Revelações em D-028/visão do produto. Permanecem por resolver: datas futuras D-030/PROMPT_VERSION, relação dos cinco horários com quatro revelações + bónus, versão DE440/DE421 e registo da evolução do worker de pré-geração.

## 3. Achados

| ID | Severidade | Achado | Evidência | Ação recomendada |
|---|---|---|---|---|
| GA-01 | Resolvido documentalmente | README atualizado para indicar fundação e primeira fatia vertical parcial, CI aprovada na branch de auditoria e ausência de validação operacional/produção demonstrada. | `README.md`; `backend/src/arquivo/`; `frontend/src/`; `docs/requisitos/rastreabilidade.md` | Manter o estado alinhado com o catálogo e a evidência de CI. |
| GA-02 | Resolvido documentalmente | O índice reconhece a primeira versão do Documento Mestre Operacional e distingue-a do Documento Mestre completo do produto. | `docs/README.md`; `docs/documento-mestre-operacional.md` | Manter esta distinção nas próximas consolidações. |
| GA-03 | Alta | D-030 tem data 16-11-2026, posterior à data desta auditoria (15-11-2026). D-029 contém `PROMPT_VERSION` 2026-11-17.1, também futura. | `docs/governanca/decisoes.md`, D-029/D-030 | Confirmar se são erros de data, conteúdo preparado para publicação futura ou registos importados com data incorreta. Não retrodatá-los nem tratá-los como aprovados antes da confirmação. |
| GA-04 | Resolvido documentalmente | A precedência foi explicitada em D-018: a escolha posterior de Claude/Anthropic em D-029 prevalece sobre a delegação inicial. | `docs/governanca/decisoes.md`, D-018/D-029 | Não reabrir sem nova decisão explícita. |
| GA-05 | Parcialmente resolvido | A visão do produto e D-028 foram alinhadas com quatro Revelações principais + bónus opcional. D-030 contém cinco horários, mas está datado no futuro e a relação entre horários e bónus requer confirmação. | `docs/produto/visao.md`; D-028–D-030 | Confirmar data e distribuição dos cinco horários antes de congelar o desbloqueio. |
| GA-06 | Média | A versão das efemérides JPL não está coerente: ADR-0001 indica DE440/DE440s; o script de aquisição e README usam DE421. | `docs/adr/0001-stack.md`; `backend/scripts/fetch_ephemerides.sh`; `README.md` | Confirmar a versão realmente usada nos testes de validação e atualizar ADR/documentação ou script de forma coordenada. |
| GA-07 | Resolvido documentalmente | ADR-0001 regista agora a evolução posterior para o worker de pré-geração ao abrigo de D-031; operação e supervisão em produção continuam pendentes. | ADR-0001; D-031; `pregeneration.py` | Definir supervisão/deploy no plano operacional antes de produção. |
| GA-08 | Resolvido documentalmente | D-010 foi atualizado para referir D-019/D-020, sem manter referências às lacunas já resolvidas. | `docs/governanca/decisoes.md`; `docs/governanca/lacunas.md` | Não requer ação adicional. |
| GA-09 | Média | A baseline 0000 é um retrato válido de 12-11-2026, mas não representa o estado atual do repositório. | `docs/auditoria/0000-baseline.md`; código atual; catálogo | Preservar a baseline histórica e referi-la sempre como fotografia inicial, nunca como estado corrente. |

## 4. Correções já aplicadas

- README atualizado para refletir o estado parcial real da implementação e distinguir CI de validação operacional.
- Índice de documentação atualizado para reconhecer o Documento Mestre Operacional v1 e a auditoria global.
- D-010 deixou de apontar para L-002/L-003, já resolvidas.
- D-018 clarifica que a escolha posterior de Claude/Anthropic em D-029 prevalece sobre a delegação inicial.
- D-028 e a visão do produto foram alinhadas com quatro Revelações principais e um bónus opcional.
- ADR-0001 regista a evolução posterior para o worker de pré-geração definida em D-031.
- L-026 e L-027 registam as questões ainda pendentes de cronologia, horários e versão das efemérides.

## 5. Evidência técnica verificada

A árvore da branch auditada contém backend e frontend, migrações, APIs, motor natal, motor temporal, trânsitos, interpretação, pré-geração, diário/arquivo e respetivos testes.

A CI do commit auditado `8120063b753a985b4c37d1caa534ca705ab3e21c` terminou com sucesso:
- Backend: Ruff lint/format, mypy, import-linter e pytest — todos concluídos com sucesso.
- Frontend: lint, testes Vitest e build — todos concluídos com sucesso.

Esta evidência confirma que a suíte automatizada configurada passou nesse commit. Não prova:
- validação independente dos cálculos astrológicos em produção;
- revisão de segurança ou RGPD;
- funcionamento contínuo do worker em ambiente implantado;
- testes de carga, failover, recuperação ou DR;
- deploy público ou funcionamento com fornecedor de IA real.

A PR #17 continua Draft e não foi mergeada. A auditoria não recomenda merge automático antes de os achados de alta severidade serem reconciliados e a documentação atualizada.

## 6. Estado de maturidade

| Área | Estado observado | Limite |
|---|---|---|
| Fundação técnica | Código e CI presentes | Deploy/produção não demonstrados |
| Núcleo epistemológico e proveniência | Implementação e testes identificados | Cobertura funcional integral não afirmada |
| Contas e sessões | Implementação e testes identificados | Recuperação de palavra-passe, verificação de email e limites de login continuam lacunas |
| Mapa Natal | Cálculo e testes identificados | Interpretação completa e apresentação final não concluídas |
| Temporalidade | Primitivas e testes identificados | Especificação original F60/F61 incompleta |
| Trânsitos e Revelações | Motor, desbloqueios, interpretação e pré-geração identificados | Decisões de contagem/horários e operação real do worker por reconciliar |
| Diário e Arquivo | Implementação e testes identificados | Exportação RGPD e cifragem em repouso permanecem lacunas |
| FC-01–FC-06 | Especificações/documentação | Implementação transversal não demonstrada |
| F78–F82 | Mapa funcional parcial | Fontes autónomas e detalhe F81/F82 em falta |
| Segurança e privacidade | Regras e componentes parciais | Auditoria de segurança, DPA, retenção/região e controlos pré-produção pendentes |

## 7. Lacunas e bloqueios a preservar

- L-016: recuperação de palavra-passe, verificação de email e limite de tentativas.
- L-017: DPA, subcontratação, retenção e região da Anthropic antes de abrir ao público.
- L-018: exportação RGPD das reflexões.
- L-019: cifragem das reflexões em repouso.
- L-021: contratos/estados históricos FC-01–FC-03 e harmonização FC-04.
- L-022: fontes autónomas F78–F82 e detalhe integral F81/F82.
- L-025: parâmetros e prontidão operacional FC-06, incluindo RTO/RPO, autoridades e exercícios.

Os achados GA-03, GA-06 e GA-07 continuam pendentes. GA-04 foi resolvido documentalmente; GA-05 foi parcialmente resolvido. As correções de estado público, índice documental e referências L-002/L-003 foram aplicadas no mesmo branch. As alterações preservam o histórico e não mudam main.

## 8. Próxima sequência recomendada

1. Resolver os achados de alta severidade GA-03, GA-04 e GA-05 com base nas decisões originais.
2. Corrigir GA-01, GA-02 e GA-08 na documentação.
3. Resolver GA-06 e GA-07 em ADR/decisões, sem alterar a configuração de efemérides sem validação.
4. Atualizar catálogo e rastreabilidade com estados que respeitem `docs/governanca/estados.md`.
5. Fechar a auditoria global v1.0 e consolidar o Documento Mestre.
6. Só depois avançar para a arquitetura astrológica e técnica detalhada.

**Conclusão:** a base de engenharia e a fatia vertical astrológica estão mais avançadas do que o README e a baseline sugerem. A CI está verde no commit auditado. O projeto ainda não está pronto para produção nem para declarar FC-01–FC-06 implementados. As contradições de decisão e de datas devem ser resolvidas antes de congelar a arquitetura.
