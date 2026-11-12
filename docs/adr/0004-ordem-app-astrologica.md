# ADR-0004 — Ordem de entrega centrada na aplicação de astrologia

- Estado: aceite
- Data: 2026-11-12
- Substitui: passo 5 do [ADR-0003](0003-fatia-vertical.md)

## Contexto
A conversa original e o prompt do Pedro (D-022) mostram que o produto é uma aplicação de astrologia por
subscrição. O ADR-0003 seguia o dossiê v2.0 e punha F61 → F62 → F59 a seguir ao Mapa Natal.

## Decisão
Depois da fundação, do núcleo, do F60 e do cálculo do Mapa Natal (já entregues):
1. Contas de utilizador e registo com os dados de nascimento.
2. Mapa natal visível na interface.
3. Motor de trânsitos.
4. Interpretação com IA, assente nos cálculos (sem inventar posições).
5. Ecrã Hoje com as Revelações do Dia.
6. Arquivo do Universo, Jornada e, por fim, subscrições e pagamentos.

Os motores F59–F62 entram apenas quando uma funcionalidade da aplicação precisar deles (por exemplo, o
temporal para os ciclos e o relacional para a sinastria).

## Consequências
- Cada passo produz algo utilizável na aplicação.
- O núcleo epistemológico, a memória bitemporal e o isolamento por utilizador mantêm-se como base.
