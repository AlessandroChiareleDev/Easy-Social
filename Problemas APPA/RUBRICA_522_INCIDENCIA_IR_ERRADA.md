# PROBLEMA: Rubrica 522 — Incidência IR 09 → 67

**Data descoberta:** 16/04/2026  
**Data correção:** 16/04/2026  
**Status:** RESOLVIDO ✅  
**Impacto:** 751 CPFs com incidência errada no S-1010

---

## Descrição

A rubrica 522 (Desconto Plano de Saúde) estava com `codIncIRRF = 09` (diversas) quando deveria ser `codIncIRRF = 67` (assistência médica).

### Diferença:
- **09 (diversas):** Valor é informativo, NÃO soma no totalizador IR
- **67 (assistência médica):** Valor é dedutível, SOMA no totalizador S-5002

---

## Impacto

Os valores de plano de saúde desses 751 CPFs **não estavam sendo computados** na dedução de IR do S-5002, resultando em IR maior do que deveria.

---

## Correção

Pipeline executado: S-1010 retificação para alterar incidência 09 → 67.

| Métrica | Valor |
|---------|-------|
| Total CPFs | 751 |
| OK | 739 |
| Erro | 1 (recibo não encontrado, já retificado antes) |
| Não processados | 11 (sem dados) |

---

## Verificação

Xande checou aleatoriamente 5 CPFs no portal do eSocial — valores agora aparecendo corretamente com código 67.

**Exemplo:** Pessoa com 2 operadoras:
- R$49.40 (médico) + R$22.53 (odonto) = R$71.93 total ✓

---

## Fonte

- CALL_4_ANA (16/04/2026)
- Script de pipeline: `C:\tmp\retif_lote_1210.py`
