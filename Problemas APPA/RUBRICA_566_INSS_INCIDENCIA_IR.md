# PROBLEMA: Rubrica 566 (INSS) — codIncIRRF 11 → 41

**Data descoberta:** 02/04/2026  
**Status:** PENDENTE (aguarda pipeline S-1010 completo) 🔴  
**Impacto:** 16.000-20.000 pessoas com dedução INSS zerada na RF  
**Período afetado:** Janeiro/2025 em diante (~18 meses retroativos)

---

## Descrição

A rubrica 566 (INSS desconto) está com `codIncIRRF = 11` (remuneração genérica) quando deveria ser `codIncIRRF = 41` (Previdência Social — dedução IR).

### Consequência:
- O desconto de INSS **NÃO aparece como dedução** no extrator da RF (substituto da DIRF)
- A Receita Federal vê IR maior do que deveria para todos os funcionários
- O extrator mostra dedução de Previdência Social = **ZERO**

---

## Contexto: Fim da DIRF

Em 2025 a DIRF (Declaração do Imposto de Renda Retido na Fonte) foi **extinta**. Agora tudo é calculado pelo eSocial via eventos S-5002/S-5011.

Isso tornou a incidência de cada rubrica **crítica** — antes um erro de codIncIRRF era cosmético, agora afeta diretamente o IR na fonte.

---

## Fluxo de Correção Obrigatório

```
S-1010 (corrigir incidência da rubrica)
    → S-1298 (reabrir período)
        → S-1200 (retificar remuneração) ← CUIDADO
            → S-1210 (retificar pagamentos)
                → S-1299 (fechar período)
                    → DCTFWeb (retransmitir)
```

**⚠️ REGRA INVIOLÁVEL:** NÃO mexer no S-1200 sem autorização explícita!

---

## Bloqueadores

1. **3 sistemas enviando ao eSocial simultaneamente** (GI, programa do Sandro, Easy-Social)
2. **Recibos GI ≠ recibos eSocial** (Sandro envia depois, gerando novos recibos)
3. **154 rubricas S-1010 pendentes** (bot 90% pronto)
4. **~80 rubricas bloqueadas** (natureza expirada / De-Para não encontrado)

---

## Rubricas Prioritárias

| Rubrica | Problema | Impacto |
|---------|----------|---------|
| **566** | codIncIRRF 11 → 41 | INSS dedução zerada |
| **47** | Incompleta | Afeta cálculo IR |

---

## Fonte

- CONCLUSOES_CALL_1 (02/04/2026)
- MAPA_PROBLEMAS_02-04-2026.md
- MISSAO_ATUAL.md
