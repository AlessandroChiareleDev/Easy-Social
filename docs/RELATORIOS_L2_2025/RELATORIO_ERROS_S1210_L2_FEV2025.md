# Relatório de Erros — S-1210 · Lote 2 · Fevereiro/2025

> **Escopo:** Lote 2 · `2025-02` (CPFs com plano de saúde individual).
> **Gerado em:** 29/04/2026 21:29
> **Fonte:** endpoint `/api/s1210-repo/codigos-agregados` + `/por-lote` (mesmas rotas do front).

---

## 1. Números gerais

| Status | Qtd | % do total |
|---|---:|---:|
| `ok` (201) | 1279 | 98.4 % |
| `erro` | 21 | 1.6 % |
| **Total** | **1300** | 100 % |

### Distribuição dos erros

| Tipo | Qtd | % dos erros |
|---|---:|---:|
| `401/459` — recibo excluído/retificado | 1 | 4.8 % |
| `buscar_recibo` (pré-eSocial) | 20 | 95.2 % |

### Códigos brutos retornados pelo eSocial

| chave | qtd | tipo | descrição (primeiros 120 chars) |
|---|---:|---|---|
| `201/` | 1279 | ok | Sucesso. |
| `erro/` | 20 | err | buscar_recibo \| Nenhum S-1210 com nrRecibo encontrado no ZIP para CPF 48416363749 |
| `401/459` | 1 | err | Não foi localizado um evento para o recibo de entrega informado ou o mesmo foi excluído/retificado. Ação Sugerida: Dever |

---

## 3. Erro 459 — 1 caso(s)

> "Não foi localizado um evento para o recibo de entrega informado ou o mesmo foi excluído/retificado."

**Hipóteses:** (a) recibo no banco está obsoleto — alguém retificou por fora; (b) o evento foi excluído via S-3000; (c) o `nr_recibo_usado` foi gravado errado no legado.
**Validação:** exige consulta S-5001 vigente do CPF (custa quota — não consultar sem autorização).

## 5. `buscar_recibo` (pré-eSocial) — 20 caso(s)

Etapa **antes** do envio: o pipeline buscou no ZIP do S-5001 indexado e não encontrou S-1210 com `nrRecibo` para o CPF.

**Hipóteses:** (a) CPF nunca teve S-1210 enviado naquele mês (deveria ser **inclusão**, não retificação); (b) ZIP incompleto; (c) CPF inativo/desligado sem folha.

---

## 6. Lista de CPFs em erro (21)

| CPF | cd | descrição (curta) |
|---|---|---|
| `04551920738` |  | buscar_recibo \| Nenhum S-1210 com nrRecibo encontrado no ZIP para CPF 04551920738 |
| `05176915740` |  | buscar_recibo \| Nenhum S-1210 com nrRecibo encontrado no ZIP para CPF 05176915740 |
| `07908321780` |  | buscar_recibo \| Nenhum S-1210 com nrRecibo encontrado no ZIP para CPF 07908321780 |
| `09540449758` |  | buscar_recibo \| Nenhum S-1210 com nrRecibo encontrado no ZIP para CPF 09540449758 |
| `10127866760` |  | buscar_recibo \| Nenhum S-1210 com nrRecibo encontrado no ZIP para CPF 10127866760 |
| `11005374732` |  | buscar_recibo \| Nenhum S-1210 com nrRecibo encontrado no ZIP para CPF 11005374732 |
| `11944495738` |  | buscar_recibo \| Nenhum S-1210 com nrRecibo encontrado no ZIP para CPF 11944495738 |
| `12335776703` |  | buscar_recibo \| Nenhum S-1210 com nrRecibo encontrado no ZIP para CPF 12335776703 |
| `14148426780` |  | buscar_recibo \| Nenhum S-1210 com nrRecibo encontrado no ZIP para CPF 14148426780 |
| `14531252721` |  | buscar_recibo \| Nenhum S-1210 com nrRecibo encontrado no ZIP para CPF 14531252721 |
| `15084075761` |  | buscar_recibo \| Nenhum S-1210 com nrRecibo encontrado no ZIP para CPF 15084075761 |
| `15482172716` |  | buscar_recibo \| Nenhum S-1210 com nrRecibo encontrado no ZIP para CPF 15482172716 |
| `16117860706` |  | buscar_recibo \| Nenhum S-1210 com nrRecibo encontrado no ZIP para CPF 16117860706 |
| `16310872745` |  | buscar_recibo \| Nenhum S-1210 com nrRecibo encontrado no ZIP para CPF 16310872745 |
| `17884924714` |  | buscar_recibo \| Nenhum S-1210 com nrRecibo encontrado no ZIP para CPF 17884924714 |
| `18273510719` |  | buscar_recibo \| Nenhum S-1210 com nrRecibo encontrado no ZIP para CPF 18273510719 |
| `18396033722` |  | buscar_recibo \| Nenhum S-1210 com nrRecibo encontrado no ZIP para CPF 18396033722 |
| `19108908710` |  | buscar_recibo \| Nenhum S-1210 com nrRecibo encontrado no ZIP para CPF 19108908710 |
| `48416363749` |  | buscar_recibo \| Nenhum S-1210 com nrRecibo encontrado no ZIP para CPF 48416363749 |
| `58452591772` |  | buscar_recibo \| Nenhum S-1210 com nrRecibo encontrado no ZIP para CPF 58452591772 |
| `79308899715` | 401 | Conteudo do evento inválido. |
