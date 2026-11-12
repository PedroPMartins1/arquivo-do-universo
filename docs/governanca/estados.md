# Estados oficiais

## Ciclo de vida de um requisito (dossiê §31)

```
especificação pendente → em especificação → especificada → em desenvolvimento
  → implementada → em validação → validada → em produção
(qualquer estado) → suspensa | descontinuada
```

Regras:
- Os estados avançam um de cada vez. **Não se salta de «especificada» para «validada».**
- «implementada» exige código integrado no `main` com testes automáticos a passar.
- «em validação» / «validada» exige verificação em ambiente real, com evidência registada (relatório, gravação ou PR).
- «em produção» exige deploy no servidor e verificação após o deploy.
- Cada mudança de estado é registada no [catálogo](../requisitos/catalogo.md), com ligação à evidência.

## Estados de tarefa (dossiê §23)

por iniciar · preparada · em execução · bloqueada · em validação · concluída · cancelada

Uma tarefa só fica «concluída» quando os critérios de aceitação estão satisfeitos.

## Níveis de autonomia do produto (dossiê §9)

| Nível | Significado |
|---|---|
| A0 | Consultivo: analisa e recomenda, não executa |
| A1 | Preparatório: prepara ações para revisão |
| A2 | Supervisionado: executa só depois de aprovação humana |
| A3 | Autónomo por operação: executa operações previamente autorizadas, dentro de limites explícitos |

O sistema nunca eleva o próprio nível de autonomia.
