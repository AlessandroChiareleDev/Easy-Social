# PROBLEMA: Mudança de Operadora Plano de Saúde — Setembro/2025

**Data descoberta:** 14/04/2026  
**Status:** DOCUMENTADO ✅  
**Impacto:** Dados de operadora diferentes antes e depois de set/2025

---

## Descrição

A APPA trocou de operadora de plano de saúde em setembro/2025.

---

## Códigos

| Período | CNPJ Operadora | CodANS |
|---------|---------------|--------|
| **Antes de Set/2025** | 44649812000138 | 359017 |
| **A partir de Set/2025** | 63554067000198 | 368253 |

---

## Implicação

- Janeiro-Abril 2025: usa códigos NOVOS (63554067000198 / 368253)
- Dados de set/2025 para trás: usa códigos ANTIGOS
- Scripts e pipeline precisam usar o código correto por período

---

## Pendência

Giovana (Bahia) precisa confirmar se tem valores de plano de saúde por CPF.

---

## Fonte

- call_14_04.md (14/04/2026)
