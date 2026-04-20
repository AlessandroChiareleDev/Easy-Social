# PROBLEMA: Recibos GI Divergentes do eSocial

**Data descoberta:** 02/04/2026  
**Status:** SOLUÇÃO ARQUITETURAL EM ANDAMENTO 🟡  
**Impacto:** Impossibilidade de retificar via GI  
**Período afetado:** Todos os meses

---

## Descrição

O GI (sistema da folha) mostra eventos como "alterados" mas os **números de recibo não batem** com o eSocial. Isso impede a Ana de retificar eventos diretamente pelo GI.

---

## Causa Raiz

**3 sistemas enviam ao eSocial simultaneamente:**

```
GI (folha) ──────────────┐
                         ├──→ eSocial
Programa do Sandro ──────┤
                         │
Easy-Social ─────────────┘
```

### Fluxo problemático:
1. GI fecha o mês e envia S-1210 → eSocial retorna recibo A
2. Sandro retifica por cima → eSocial retorna recibo B
3. GI ainda tem recibo A (stale) → tentativa de retificação falha

---

## Solução: Extração Independente

O Easy-Social está construindo ferramenta própria para extrair recibos diretamente dos XMLs baixados do eSocial:

1. **Denis:** Baixa todos os XMLs do eSocial (ZIPs de ~500MB cada)
2. **Xande:** Script de extração CPF × evento × recibo
3. **Marcos:** Integra tabela DEPARA

### Scripts criados:
- `C:\tmp\buscar_zips_sintacluns.py` — busca dentro de ZIPs por CPFs específicos
- Tabela `explorador_eventos` no PostgreSQL — armazena dados parseados

---

## ZIPs Disponíveis

| Arquivo | Tamanho | Conteúdo |
|---------|---------|----------|
| 29429360 jan2025.zip | 545MB | 141.005 XMLs (21.839 S-1200, 22.687 S-1210) |
| Janeiro 2025 ou dezembro...zip | 596MB | 153.886 XMLs (dez/2024) |
| 29692114.zip | 596MB | 153.886 XMLs (dez/2024) |
| 29429415 fev2025.zip | 524MB | Fevereiro/2025 |

---

## Bloqueador Original

Sandro **recusou** compartilhar dados de recibos → decisão de construir independência total.

---

## Fonte

- CONCLUSOES_CALL_1 (02/04/2026)
- RESPOSTAS_SANDRO_CALL_02-04-2026.md
- MAPA_PROBLEMAS_02-04-2026.md
