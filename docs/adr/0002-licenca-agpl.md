# ADR-0002 — Licença AGPL-3.0

- Estado: aceite
- Data: 2026-11-12

## Contexto
O Swiss Ephemeris está disponível sob AGPL ou licença comercial. A aplicação vai servir vários utilizadores
pela rede (D-014, D-017). Sob AGPL, isso obriga a disponibilizar o código-fonte aos utilizadores.

## Decisão
O código do Arquivo do Universo é publicado sob **AGPL-3.0-or-later**, num repositório público.

## Consequências
- Não é preciso licença comercial do Swiss Ephemeris.
- **Nenhum dado pessoal, segredo ou conteúdo privado entra no repositório.** Configuração por variáveis de ambiente; `.env` está no `.gitignore`.
- Dependências com licenças incompatíveis com AGPL não podem ser usadas.
