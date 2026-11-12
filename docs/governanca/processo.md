# Processo de trabalho

Baseado no dossiê §46–49.

## Antes de começar uma funcionalidade
1. Pesquisar o ID, o nome e sinónimos no catálogo, no código e nos PRs anteriores.
2. Procurar a especificação original (dossiê, conversas recuperadas).
3. Declarar o tipo de trabalho: **novo**, **consolidação**, **extensão**, **correção** ou **validação**.
4. Se faltar uma decisão: registar a lacuna em [lacunas.md](lacunas.md) e avançar só até ao limite seguro.

## Cada incremento
- Um branch e um PR pequeno e reversível. Commits descritivos.
- O PR indica: o que mudou e porquê, ficheiros afetados, testes executados e resultados, o que não foi testado, riscos ou limitações, e os passos seguintes.
- O catálogo de requisitos e a matriz de rastreabilidade são atualizados no mesmo PR.
- A CI (lint, tipos, fronteiras entre módulos, testes) tem de passar.
- Alterações de segurança, dados ou arquitetura ficam registadas num ADR.

## Dados
- Nunca usar dados pessoais reais em testes ou fixtures.
- Migrations sempre através do Alembic, com `downgrade`.
