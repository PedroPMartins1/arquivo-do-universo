# ADR-0003 — Ordem de entrega por fatia vertical

- Estado: aceite
- Data: 2026-11-12

## Contexto
O dossiê (§41–42) prevê consolidar F60, F61, F62 e F59 antes da aplicação astrológica utilizável (Fase 4).
Sem código existente, isso adiaria por muito tempo qualquer funcionalidade utilizável e deixaria os motores
sem um caso de uso real que os valide. O Pedro delegou esta escolha ("como fizer mais sentido").

## Decisão
1. Fundação: esqueleto, CI e governação (Fase 1).
2. Núcleo mínimo (Fase 2): classificação epistemológica, proveniência, isolamento por utilizador, auditoria e persistência bitemporal.
3. F60 — modelo temporal comum: datas parciais, fusos IANA históricos, incerteza e bitemporalidade.
4. Mapa Natal básico (cálculo e renderização, sem interpretação), assim que as lacunas L-002/L-003 estiverem resolvidas.
5. Depois, F61 → F62 → F59 e os restantes, pela ordem do dossiê §41.

## Consequências
- O F60 é validado logo por um consumidor real (data, hora e local de nascimento).
- A ordem dos motores F61/F62/F59 mantém-se. Só a Fase 4 (parcial) é antecipada.
