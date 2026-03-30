# Relatório: Estado das Tabelas de Rubricas/Naturezas

**Data do relatório:** 29/03/2026

---

## Resumo Executivo

O sistema possui **17 tabelas** relacionadas a rubricas e naturezas. A fonte primária dos dados é o arquivo Excel **"Relatório DIRF 2025"** (importado em 25/03/2026), que contém 4 abas: ANALISE NATUREZA (455 rubricas), Dinamica (276 linhas), Tabela Eventos GI (1145 eventos), Tabela EB (1224 entradas).

Posteriormente, foi importada a planilha **"Análise Natureza (Certa)"** (importada em 27/03/2026), que trouxe as naturezas corrigidas.

---

## Inventário de Tabelas

### 🟢 TABELAS ATUALIZADAS (fonte de verdade)

| Tabela | Registros | Última Atualização | Descrição |
|--------|-----------|-------------------|-----------|
| **tabela_cruzamento** | 455 | 27/03/2026 | Rubricas com naturezas **corrigidas** (espelho da analise_natureza_certo). É a referência principal. |
| **analise_natureza_certo** | 455 | 25/03/2026 (dados) + 84 correções | Cópia da analise_natureza com 84 naturezas corrigidas via `natureza_nova`. Col_c já reflete os valores corretos. |
| **cruzamento_tabela_a** | 455 | 27/03/2026 | Cópia exata da tabela_cruzamento. **100% sincronizada.** |
| **cruzamento_eb** | 448 | 28/03/2026 | Rubricas válidas (455 - 7 sem natureza) importadas para envio ao eSocial. Naturezas atualizadas. 11 já enviadas (corrigido=true, envio_status=feito), 437 pendentes. |
| **tabela3_esocial_oficial** | 215 | Importação estática | Tabela 3 oficial do eSocial. 194 naturezas ativas, 21 expiradas (com dt_fim). Referência para validar naturezas. |
| **naturezas_esocial** | 206 | 25/03/2026 | Lista de naturezas do eSocial (código, nome, descrição, validade). Similar à tabela3 mas em formato diferente. |
| **esocial_tabela3_natureza** | 203 | Importação estática | Outra versão da Tabela 3 (código, nome, dt_inicio, dt_fim, versão 17). |

### 🟡 TABELAS DESATUALIZADAS (dados antigos ou parciais)

| Tabela | Registros | Última Atualização | Problema |
|--------|-----------|-------------------|---------|
| **analise_natureza** | 455 | 25/03/2026 | Versão **original** do upload, SEM as 80 correções. 8 rubricas com natureza "0-Não Informado". Não tem `natureza_nova`. |
| **dinamica** | 276 | 25/03/2026 (upload original) | Contém apenas 274 rubricas únicas (vs 455 total). **55 naturezas divergentes** em relação à tabela_cruzamento (códigos de natureza diferentes, não apenas formatação). Dados originais nunca atualizados. |
| **tabela_eb** | 1224 | 25/03/2026 (upload original) | Export completo do Datamace com 1056 códigos únicos. Inclui múltiplas entradas por rubrica (linhas de incidência/base legal). **Naturezas no formato original** ("1000 - Salário..." com espaço ao redor do hífen). Nunca atualizada com correções. |
| **tabela_eventos_gl** | 1145 | 25/03/2026 (upload original) | Tabela de Eventos GI do Datamace. Dados brutos originais, nunca atualizados. |

### 🔵 TABELAS DE CONTROLE/HISTÓRICO

| Tabela | Registros | Descrição |
|--------|-----------|-----------|
| **esocial_depara** | 2381 | De-Para para envio S-1010. 6 aplicados, 2375 pendentes. Gerado em 28/03/2026. |
| **rubrica_corrections** | 385 | Correções de incidências (INSS/IRRF/FGTS) da Tabela EB. |
| **auditoria_naturezas** | 91 | Log de alterações de natureza (feitas pela Ana em 27/03/2026). |
| **correcoes_staging** | 91 | Staging das correções antes de aplicar. Todas aplicadas. |
| **cruzamento_resultado** | 455 | Resultado do cruzamento (código, nome_evento, natureza_esocial, incidências). Gerado 27/03/2026. |
| **cruzamento_tabela_b** | 1145 | Tabela B do cruzamento (dados do Datamace/GI). |

---

## Fluxo dos Dados

```
Excel "Relatório DIRF 2025" (25/03/2026)
    │
    ├─► analise_natureza (455 rubricas, dados ORIGINAIS)
    │       │
    │       └─► analise_natureza_certo (cópia + 84 correções de natureza)
    │               │
    │               └─► tabela_cruzamento (455, naturezas CORRIGIDAS) ← FONTE DE VERDADE
    │                       │
    │                       ├─► cruzamento_tabela_a (cópia exata, 455)
    │                       │
    │                       └─► cruzamento_eb (448 válidas, para envio eSocial)
    │                               │
    │                               └─► esocial_depara (2381 De-Para para S-1010)
    │
    ├─► dinamica (276 linhas, NUNCA ATUALIZADA)
    │
    ├─► tabela_eb (1224 entradas, NUNCA ATUALIZADA)
    │
    └─► tabela_eventos_gl (1145, NUNCA ATUALIZADA)
```

---

## Diferenças Encontradas

### analise_natureza vs analise_natureza_certo: **80 diferenças**
As 80 diferenças correspondem às correções de natureza feitas. Exemplos:
- Rubrica 243: `2920-Reembolsos diversos` → `6129-Outras multas ou indenizações`
- Rubrica 421: `1211-Gratificações` → `1603-Ajuda de custo`
- Rubrica 512: `9290-Desconto pagamento indevido` → `9209-Faltas ou atrasos`

### dinamica vs tabela_cruzamento: **55 diferenças de código**
A dinâmica tem 274 rubricas (faltam 181). Das 264 que cruzam, 55 têm natureza com **código diferente** (não apenas formatação). Exemplos:
- Rubrica 13: dinâmica `1629` vs cruzamento `1810`
- Rubrica 18: dinâmica `1211` vs cruzamento `1000`
- Rubrica 163: dinâmica `1002` vs cruzamento `1012`

### cruzamento_eb vs tabela_cruzamento: **Formato diferente, 3 códigos divergentes**
- cruzamento_eb usa formato "1000 - Salário..." (com espaços)
- tabela_cruzamento usa "1000-Salário..." (sem espaços)
- 3 divergências reais de código:
  - Rubrica 233: EB `1629` vs Cruz `1801`
  - Rubrica 258: EB `1019` (truncado) vs Cruz `1019` (completo)
  - Rubrica 420: EB `1403` vs Cruz `1403` (diferença de capitalização)

### 7 Rubricas sem natureza (em todas as tabelas):
| Código | Descrição |
|--------|-----------|
| 328 | ADIANTAMENTO DE SALARIO |
| 645 | DESCONTO DE 2 VIA VT |
| 685 | DESC. ADIANTAMENTO DE SALARIO |
| 692 | DESC. 2 VIA CARTAO |
| 693 | DESC. EMPRESTIMO FOLHA PGTO ANTERIOR |
| 897 | DESC. ANTECIPACAO VA E VR |
| 994 | PARCELAMENTO |

Essas 7 não estão no cruzamento_eb (excluídas por não terem natureza válida).

---

## Conclusão

| Pergunta | Resposta |
|----------|---------|
| A **tabela_cruzamento** está atualizada? | ✅ **SIM** — contém as 455 rubricas com as 80 correções aplicadas (27/03/2026) |
| A **cruzamento_eb** está atualizada? | ✅ **SIM** — 448 rubricas válidas para envio, 11 já enviadas (28/03/2026) |
| A **analise_natureza** (original) está atualizada? | ❌ **NÃO** — versão original sem correções |
| A **dinamica** está atualizada? | ❌ **NÃO** — 55 naturezas divergentes, faltam 181 rubricas |
| A **tabela_eb** está atualizada? | ❌ **NÃO** — dados originais do Datamace, nunca corrigidos |
| A **tabela_eventos_gl** está atualizada? | ❌ **NÃO** — dados brutos originais |
| A **Tabela 3 eSocial** está atualizada? | ✅ **SIM** — 215 registros (194 ativos + 21 expirados) |

**As tabelas que importam para o fluxo eSocial (tabela_cruzamento → cruzamento_eb → esocial_depara) estão todas atualizadas e sincronizadas.**

As tabelas desatualizadas (analise_natureza, dinamica, tabela_eb, tabela_eventos_gl) são dados originais do upload e servem como referência histórica.
