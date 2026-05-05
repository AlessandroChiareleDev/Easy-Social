# Relatório de Erros — S-1210 · Lote 2 · Março/2025

> **Escopo:** Lote 2 · `2025-03` (CPFs com plano de saúde individual).
> **Gerado em:** 29/04/2026 21:29
> **Fonte:** endpoint `/api/s1210-repo/codigos-agregados` + `/por-lote` (mesmas rotas do front).

---

## 1. Números gerais

| Status | Qtd | % do total |
|---|---:|---:|
| `ok` (201) | 1275 | 99.0 % |
| `erro` | 13 | 1.0 % |
| **Total** | **1288** | 100 % |

### Distribuição dos erros

| Tipo | Qtd | % dos erros |
|---|---:|---:|
| `buscar_recibo` (pré-eSocial) | 13 | 100.0 % |

### Códigos brutos retornados pelo eSocial

| chave | qtd | tipo | descrição (primeiros 120 chars) |
|---|---:|---|---|
| `201/` | 1275 | ok | Sucesso. |
| `erro/` | 13 | err | buscar_recibo \| Nenhum S-1210 com nrRecibo encontrado no ZIP para CPF 06930802727 |

---

## 5. `buscar_recibo` (pré-eSocial) — 13 caso(s)

Etapa **antes** do envio: o pipeline buscou no ZIP do S-5001 indexado e não encontrou S-1210 com `nrRecibo` para o CPF.

**Hipóteses:** (a) CPF nunca teve S-1210 enviado naquele mês (deveria ser **inclusão**, não retificação); (b) ZIP incompleto; (c) CPF inativo/desligado sem folha.

---

## 6. Lista de CPFs em erro (13)

| CPF | cd | descrição (curta) |
|---|---|---|
| `00729210723` |  | buscar_recibo \| Nenhum S-1210 com nrRecibo encontrado no ZIP para CPF 00729210723 |
| `06930802727` |  | buscar_recibo \| Nenhum S-1210 com nrRecibo encontrado no ZIP para CPF 06930802727 |
| `08033981318` |  | buscar_recibo \| Nenhum S-1210 com nrRecibo encontrado no ZIP para CPF 08033981318 |
| `11209527782` |  | buscar_recibo \| Nenhum S-1210 com nrRecibo encontrado no ZIP para CPF 11209527782 |
| `11312387700` |  | buscar_recibo \| Nenhum S-1210 com nrRecibo encontrado no ZIP para CPF 11312387700 |
| `12238859764` |  | buscar_recibo \| Nenhum S-1210 com nrRecibo encontrado no ZIP para CPF 12238859764 |
| `12845380798` |  | buscar_recibo \| Nenhum S-1210 com nrRecibo encontrado no ZIP para CPF 12845380798 |
| `13817777752` |  | buscar_recibo \| Nenhum S-1210 com nrRecibo encontrado no ZIP para CPF 13817777752 |
| `15415879790` |  | buscar_recibo \| Nenhum S-1210 com nrRecibo encontrado no ZIP para CPF 15415879790 |
| `16450944722` |  | buscar_recibo \| Nenhum S-1210 com nrRecibo encontrado no ZIP para CPF 16450944722 |
| `17387028710` |  | buscar_recibo \| Nenhum S-1210 com nrRecibo encontrado no ZIP para CPF 17387028710 |
| `17439350723` |  | buscar_recibo \| Nenhum S-1210 com nrRecibo encontrado no ZIP para CPF 17439350723 |
| `62837893749` |  | buscar_recibo \| Nenhum S-1210 com nrRecibo encontrado no ZIP para CPF 62837893749 |
