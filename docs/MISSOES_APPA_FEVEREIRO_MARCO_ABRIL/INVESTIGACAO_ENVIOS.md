# INVESTIGACAO_ENVIOS — O que já foi enviado do mega lote?

**Data:** 21/04/2026
**Método:** dados crus do banco (ZERO consultas ao eSocial)

---

## TL;DR — Resposta curta e correta

**O mega lote dos 3 meses (fev/mar/abr 2025) NÃO passou nada.** Todas as tentativas de hoje (20/04/2026) falharam: 0 CPFs aceitos.

| Mês          | CPFs aceitos no mega lote |                                        Tentativas |
| ------------ | ------------------------: | ------------------------------------------------: |
| **Fev/2025** |                     **0** | 9 runs (20–28) todas falharam, 0 `nr_recibo_novo` |
| **Mar/2025** |                     **0** |                                         zero runs |
| **Abr/2025** |                     **0** |                                         zero runs |

---

## Evidência: runs do mega lote (HOJE, 20–21/04/2026)

Todas as runs com `per_apur=2025-02` executadas hoje, com contagem real de recibos aceitos em `pipeline_cpf_results.nr_recibo_novo`:

| Run | Início           | CPFs tentados | Recibos aceitos |
| --: | ---------------- | ------------: | --------------: |
|  20 | 20/04/2026 19:58 |         8.691 |           **0** |
|  21 | 20/04/2026 20:02 |           150 |           **0** |
|  22 | 20/04/2026 20:06 |           150 |           **0** |
|  23 | 20/04/2026 20:08 |            36 |           **0** |
|  24 | 20/04/2026 20:13 |         8.691 |           **0** |
|  25 | 20/04/2026 20:17 |         8.691 |           **0** |
|  26 | 20/04/2026 20:23 |             1 |           **0** |
|  27 | 20/04/2026 20:28 |         8.691 |           **0** |
|  28 | 20/04/2026 21:01 |         8.691 |           **0** |

**Envios totais do dia 20/04/2026** (agregado `DATE(processed_at)` de `pipeline_cpf_results`):

- qtd registros: 1.981
- com `nr_recibo_novo`: **0**

**Hipótese provável:** o escopo de 8.691 CPFs estava errado (não é o XLSX APPA de 9.472 do Lote 1), e o envio quebrou por outro motivo (certificado, XML, bug 106, etc.). Não importa agora — **o ponto é que nada do mega lote foi aceito pelo eSocial**.

---

## O que isso significa pra missão

1. **Começamos do zero nos 3 meses.** Quando o XLSX da Ana for uploadado (fev/mar/abr), **todos os CPFs do Lote 1** serão `pendente`. Nenhum está `ja_feito` pelo mega lote.

2. **Março e Abril nunca foram tentados no mega lote.** Sem surpresas ali.

3. **Fevereiro também está zerado** no que diz respeito ao mega lote — as 9 tentativas de hoje (runs 20–28) todas abortaram sem gerar recibo.

4. **Erros das runs 20–28 precisam ser diagnosticados** antes de retentar (coluna `erro_descricao` em `pipeline_cpf_results`) — mas isso é da Fase 3 em diante.

---

## O que NÃO vou mais fazer

- ❌ Misturar runs antigas (de janeiro/2025 ou setembro/2025) com a missão do mega lote — são outras missões, irrelevantes aqui.
- ❌ Usar `explorador_eventos` como fonte (tá bloqueado permanentemente na memória do agente).
- ❌ Fazer consulta ao eSocial sem OK (0 usadas, limite 10/dia preservado).

---

## Regras cumpridas

- ✅ Dados crus do banco, sem interpretação em cima de interpretação
- ✅ Zero consultas ao eSocial
- ✅ Escopo da análise limitado ao mega lote de hoje (20–21/04/2026)
