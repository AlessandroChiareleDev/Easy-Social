# BUG: planSaude — Valores Inflados (6x a 200x)

**Data descoberta:** 02/04/2026  
**Data correção parcial:** 15-17/04/2026  
**Status:** PARCIALMENTE CORRIGIDO  
**Impacto:** 10.443 CPFs com valores errados no eSocial  
**Período afetado:** Janeiro/2025 (per_apur=2025-01)

---

## Descrição do Bug

O script `_rebuild_jan_plansaude.py` que reconstrói o bloco `<planSaude>` do S-1210 tinha **DOIS bugs simultâneos**:

### Bug 1: Filtro Wildcard
```sql
-- ERRADO: capturava 99 rubricas ao invés de 4
WHERE nat_rubr LIKE '92%'

-- CORRETO: deveria filtrar apenas as 4 rubricas de saúde
WHERE nat_rubr IN ('9219') AND cod_rubr IN (607, 774, 775, 516)
```

### Bug 2: Soma Dupla (Original + Retificação)
O script somava tanto o S-1210 original (`indRetif=1`) quanto a retificação (`indRetif=2`), **dobrando** os valores:
```
Valor original: R$50.00
Valor retificação: R$50.00
Total calculado (ERRADO): R$100.00
Valor correto: R$50.00 (só o mais recente)
```

---

## Exemplos Reais

| CPF | Valor Errado | Valor Correto | Fator Inflação |
|-----|-------------|---------------|----------------|
| Waldelice | R$367.30 | R$0.00 | ∞ (sem saúde) |
| Suyane | R$1.251.30 | R$0.00 | ∞ (sem saúde) |
| Anaildes | R$1.503.18 | R$7.51 | 200x |

---

## Correção Aplicada

### Fase 1: 426 CPFs (Planilha 1600)
- **Script:** `C:\tmp\correcao_426_dobrado.py`
- **Fonte de verdade:** Planilha 1600 cpfs.xlsx (col17=ValorEvento em centavos)
- **Resultado:** 426 OK, 0 ERRO (9 lotes, todos aceitos)
- **Arquivo resultados:** `C:\tmp\correcao_426_resultados.json`

### Fase 2: 67 CPFs SINTACLUNS (pendente)
- Esses 67 CPFs NUNCA tiveram planSaude nos XMLs originais
- Valores foram injetados pela planilha "S_Tabela - certo" (duplicada, 6074 linhas)
- A planilha correta "caso final" (1801 linhas) NÃO tem esses CPFs
- **Decisão pendente:** Remover planSaude inteiramente desses 67 CPFs

---

## Scripts Criados

| Script | Função |
|--------|--------|
| `_rebuild_plansaude_correct.py` | Reconstrução correta (1.578 CPFs) |
| `C:\tmp\correcao_426_dobrado.py` | Correção dos 426 CPFs via S-1210 retif |
| `C:\tmp\investigar_67cpfs_v3.py` | Investigação DB dos 67 CPFs |
| `C:\tmp\buscar_zips_sintacluns.py` | Busca nos ZIPs originais |
| `C:\tmp\verificar_caso_final.py` | Comparação planilhas caso final vs certo |

---

## Lições Aprendidas

1. **NUNCA usar wildcards** em filtros de rubrica (`LIKE '92%'`); sempre listar explicitamente
2. **NUNCA somar indRetif=1 + indRetif=2**; usar apenas o mais recente
3. **Sempre validar** contra XML original antes de aplicar correções em massa
4. **Manter backup** dos XMLs antes de cada pipeline run
