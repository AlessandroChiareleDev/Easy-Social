# PROBLEMA: S-1010 — 154 Rubricas Pendentes

**Data descoberta:** 02/04/2026  
**Status:** BOT 90% PRONTO, AGUARDANDO NATUREZAS 🟡  
**Impacto:** Incidências erradas em 154+ rubricas  
**Período afetado:** Retroativo desde jan/2025

---

## Descrição

Das 448 rubricas no cruzamento EB (Easy-Social × eSocial), **154 têm divergências de incidência** que precisam de correção via S-1010 (tabela de rubricas).

---

## Composição

| Categoria | Quantidade |
|-----------|-----------|
| Total rubricas | 448 |
| Corretas | ~214 |
| **Pendentes (divergentes)** | **154** |
| Bloqueadas (natureza expirada) | ~80 |

---

## Bloqueador

~80 rubricas têm **natureza expirada** ou De-Para não encontrado, impedindo a correção automática. Essas precisam de definição manual (Marcos/Ana).

---

## Bot de Correção

Bot pronto para executar alterações S-1010 em massa:
- Lê tabela de cruzamento
- Gera XML S-1010 com incidências corretas
- Assina e envia via SOAP
- Registra resultado

**Status:** 90% pronto, aguarda finalização das naturezas.

---

## Impacto da Correção

Após corrigir S-1010, será necessário:
1. S-1298 (reabrir cada período)
2. Possivelmente S-1200 retificação
3. S-1210 retificação  
4. S-1299 (fechar período)
5. DCTFWeb retransmissão

**Para ~18 meses retroativos** (jan/2025 a presente).

---

## Fonte

- MAPA_PROBLEMAS_02-04-2026.md
- MISSAO_ATUAL.md
- CALL_1_ANA (16/04/2026)
