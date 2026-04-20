# PROBLEMA: Dedução Dependentes Setembro — R$739k vs R$20k

**Data descoberta:** 16/04/2026  
**Status:** EM INVESTIGAÇÃO 🔴  
**Impacto:** Discrepância massiva entre eSocial e Receita Federal  
**Período afetado:** Setembro/2025

---

## Descrição

O S-5002 (totalizador) mostra **R$739.211,41** em deduções de dependentes, mas o extrator da Receita Federal mostra apenas **~R$20.000**.

---

## Timeline de Setembro/2025

| Data | Hora | Evento |
|------|------|--------|
| 06/Out | - | 7.762 S-1210 originais + 2.585 com dedDepen = R$739k |
| 09/Out | - | +9 S-1210 + S-1299 fechamento #1 |
| 24/Out | 10:43 | S-1298 reabertura #1 |
| 24/Out | 10:43 | S-1299 fechamento #2 (**7 segundos depois!**) |
| 24/Out | 10:44 | S-1298 reabertura #2 |
| 24/Out | 10:46 | **S-3000 EXCLUSÃO MASSIVA de TODOS 7.771 S-1210** |
| 24/Out | ~11-14h | Reenvio completo de 7.771 S-1210 |
| 24/Out | 14:04 | S-1299 fechamento #3 (sucesso 201) |

---

## 3 Gerações de S-5002 no Download

| Geração | CPFs com dedDepen | Total | Contexto |
|---------|-------------------|-------|----------|
| Gen 1 | 2.585 | R$739k | Original (06/Out) |
| Gen 2 | **0** | **R$0** | Após exclusão massiva |
| Gen 3 | 2.585 | R$739k | Após reenvio (24/Out) |

---

## Hipóteses

1. **Bug eSocial pós-exclusão massiva:** Gen2 (zerada) ficou como estado para maioria dos CPFs na RF
2. **Fechamento de 7 segundos:** S-1299 fechou tão rápido que gerou snapshot vazio/parcial
3. **DCTFWeb transmitida antes do reenvio:** Se transmitiu em 24/Out antes do reenvio completar, carregou Gen2 (zero)

---

## Investigação Necessária

- [ ] Qual campo exatamente mostra R$20k no extrator RF?
- [ ] DCTFWeb foi retransmitida após o reenvio?
- [ ] Ainda mostra R$20k hoje?

---

## Possíveis Soluções

1. **Se DCTFWeb não retransmitida:** Retransmitir
2. **Se retransmitida + ainda errado:** S-1298 reabertura + S-1299 fechar + retransmitir DCTFWeb
3. **Último recurso:** Consultar identificadores eSocial (**CUIDADO: 10 consultas/dia**)

---

## Fonte

- CALL_2_ANA (16/04/2026)
- MISSAO.md (seção M7/M8)
- Investigação com snapshots S-5002
