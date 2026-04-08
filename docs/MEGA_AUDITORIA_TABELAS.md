# MEGA AUDITORIA — Tabelas do Banco vs Marcos

**Data:** 07/04/2026  
**Banco:** Supabase (PostgreSQL 16) — 34 tabelas

---

## 1. INVENTÁRIO COMPLETO (34 tabelas)

| Tabela                   | Rows    | Última Atividade | Status                                             |
| ------------------------ | ------- | ---------------- | -------------------------------------------------- |
| cruzamento_eb            | 448     | 30/03            | **ATIVA — SOURCE OF TRUTH**                        |
| esocial_envios           | 20      | 04/04            | **ATIVA — log de envios S-1010**                   |
| esocial_depara           | 2,381   | 28/03            | **ATIVA — 6 aplicados, 2375 pendentes**            |
| rubrica_corrections      | 385     | 28/03            | **ATIVA — antes→correto por rubrica**              |
| config_esocial           | 1       | 30/03            | **ATIVA — config CNPJ/iniValid**                   |
| pipeline_audit           | 6       | 04/04            | **ATIVA — snapshots piloto**                       |
| pipeline_correcao        | 0       | —                | **ATIVA — schema pronto, sem dados**               |
| eb_skills_base_legal     | 534     | 29/03            | **ATIVA — base legal tributária**                  |
| explorador_eventos       | 51,600  | 02/04            | **ATIVA — módulo explorador**                      |
| explorador_importacoes   | 1       | 02/04            | **ATIVA — módulo explorador**                      |
| explorador_rubricas      | 282,491 | —                | **ATIVA — módulo explorador**                      |
| master_atividades        | 39      | 06/04            | **ATIVA — log admin**                              |
| master_empresas          | 1       | 26/03            | **ATIVA — config empresa**                         |
| master_perfis            | 3       | 06/04            | **ATIVA — autenticação**                           |
| master_usuario_empresa   | 3       | 04/04            | **ATIVA — permissões**                             |
| master_naturezas_esocial | 203     | 26/03            | **REFERÊNCIA — naturezas no master**               |
| naturezas_esocial        | 203     | 25/03            | DUPLICATA de master_naturezas_esocial              |
| esocial_tabela3_natureza | 203     | —                | DUPLICATA de master_naturezas_esocial              |
| tabela3_esocial_oficial  | 215     | 28/03            | REFERÊNCIA — upload raw tabela3                    |
| uploads                  | 2       | —                | CONTROLE — tracking de uploads                     |
| cruzamento_uploads       | 1       | 27/03            | CONTROLE — cruzamento upload                       |
| cruzamento_tabela_a      | 455     | 27/03            | INTERMEDIÁRIA — lado GI do cruzamento              |
| cruzamento_tabela_b      | 1,145   | 27/03            | INTERMEDIÁRIA — lado eSocial (= tabela_eventos_gl) |
| cruzamento_resultado     | 455     | 27/03            | INTERMEDIÁRIA — resultado do match                 |
| tabela_cruzamento        | 455     | —                | INTERMEDIÁRIA — upload raw cruzamento              |
| analise_natureza         | 455     | 25/03            | **OBSOLETA** — análise sem correções               |
| analise_natureza_certo   | 455     | 27/03            | **OBSOLETA** — supersedida por cruzamento_eb       |
| auditoria_naturezas      | 91      | 27/03            | **HISTÓRICA** — log de alterações                  |
| correcoes_staging        | 91      | 27/03            | **OBSOLETA** — staging já aplicado                 |
| dinamica                 | 276     | 25/03            | **OBSOLETA** — análise antiga                      |
| tabela_eb                | 1,224   | —                | **OBSOLETA** — upload raw EB Skills                |
| tabela_eventos_gl        | 1,145   | —                | **OBSOLETA** — = cruzamento_tabela_b               |
| base_ficha_financeira    | 0       | —                | **LIXO** — vazia, nunca usada                      |
| planilha_1               | 0       | —                | **LIXO** — vazia, nunca usada                      |

---

## 2. CLASSIFICAÇÃO RESUMIDA

### ATIVAS (15 tabelas) — NÃO MEXER

- `cruzamento_eb` — tabela principal: 448 rubricas, 13 corrigidas, 11 enviadas
- `esocial_envios` — 20 envios S-1010 documentados com XML e recibos
- `esocial_depara` — depara GI→eSocial (2381 mapeamentos)
- `rubrica_corrections` — 385 correções computadas (antes→correto)
- `config_esocial` — configuração do webservice
- `pipeline_audit` — 6 snapshots do pipeline piloto (CPF 08132588983)
- `pipeline_correcao` — schema pronto para pipeline em escala
- `eb_skills_base_legal` — fundamentação legal por tributo
- `explorador_*` (3 tabelas) — módulo do frontend
- `master_*` (4 tabelas) — autenticação/admin

### REFERÊNCIA (3 tabelas) — podem ficar

- `naturezas_esocial` + `esocial_tabela3_natureza` + `master_naturezas_esocial` — 3 cópias das mesmas 203 naturezas. Redundante, mas inofensivo.
- `tabela3_esocial_oficial` — upload original da tabela 3

### INTERMEDIÁRIAS (4 tabelas) — dados do cruzamento original

- `cruzamento_tabela_a` (455) — lado GI
- `cruzamento_tabela_b` (1145) — lado eSocial
- `cruzamento_resultado` (455)
- `tabela_cruzamento` (455) — upload raw

> Estas são insumos do cruzamento de 27/03. O resultado final está em `cruzamento_eb`. Se precisar refazer o cruzamento, elas servem.

### OBSOLETAS (6 tabelas) — podem ser deletadas

- `analise_natureza` — análise v1, sem correções
- `analise_natureza_certo` — análise v2, supersedida por cruzamento_eb
- `correcoes_staging` — staging aplicado em 27/03, já migrou para cruzamento_eb
- `dinamica` — análise dinâmica antiga
- `tabela_eb` — upload raw EB Skills (1224 linhas com header)
- `tabela_eventos_gl` — idêntica a cruzamento_tabela_b (1145)

### LIXO (2 tabelas) — deletar

- `base_ficha_financeira` — 0 rows, nunca usada
- `planilha_1` — 0 rows, nunca usada

---

## 3. ESTADO ATUAL DO CRUZAMENTO_EB

```
Total:      448 rubricas
Corrigidos: 13  (envio feito)
Enviados:   3   (566, 596 + 243 em homolog)
Pendentes:  434
```

### 13 Rubricas Corrigidas:

| Rubrica | Descrição                    | Envio                    |
| ------- | ---------------------------- | ------------------------ |
| 13      | REEMB. VALE TRANSPORTE       | feito                    |
| 19      | REEMB. EXAME ADMISSIONAL     | feito                    |
| 47      | SALARIO FAMILIA              | feito                    |
| 55      | PRO-LABORE                   | feito                    |
| 156     | DIF. FERIAS                  | feito                    |
| 185     | INDENIZACAO LEI 7.238/84     | feito                    |
| 228     | REEMB. DESC. ASSIST. MEDICA  | feito                    |
| 233     | REEMB. REFEICAO              | feito                    |
| 234     | REEMB. EXAMES MÉDICOS        | feito                    |
| 240     | REEMB. SALARIO FAMILIA       | feito                    |
| 241     | SALÁRIO FAMILIA MES ANTERIOR | feito                    |
| 566     | DESC. I.N.S.S.               | **enviado** (IRRF 11→41) |
| 596     | DESC. I.N.S.S. S/13º SALARIO | **enviado** (IRRF 12→42) |

> 566/596 estão como "enviado" e não "feito" porque foram corrigidos via S-1010 em produção (04/04) mas o status na cruzamento_eb não foi atualizado para "feito" manualmente.

---

## 4. TABELA DO MARCOS vs NOSSO SISTEMA

### Números-chave

| Fonte                         | Total Rubricas |
| ----------------------------- | -------------- |
| Marcos (tabela_marcos.xlsx)   | **1,145**      |
| cruzamento_eb (nosso)         | **448**        |
| cruzamento_tabela_b (eSocial) | **1,145**      |
| rubrica_corrections           | **385**        |

### Análise

**Por que Marcos tem 1145 e nós 448?**

- `cruzamento_tabela_b` também tem 1145 — ou seja, 1145 é o total de rubricas da APPA no eSocial
- O cruzamento só encontrou 448 correspondências entre GI (tabela_a: 455) e eSocial (tabela_b: 1145)
- As 697 rubricas que sobram existem no eSocial mas **não existem no GI** (ou não bateram no match)

**O Marcos está desatualizado?**

- **SIM, parcialmente.** Marcos baseou suas flags de divergência no estado ANTES das nossas correções S-1010
- Nós já corrigimos 13 rubricas via S-1010 em produção (11 "feito" + 2 "enviado")
- Marcos marcou 428 divergências de IRRF. Dessas, as 11 que já corrigemos (13, 19, 47, 55, 156, 185, 228, 233, 234, 240, 241) já não são mais divergentes no eSocial
- **MAS** Marcos cobre rubricas que NÃO estão no nosso cruzamento_eb (697 extras) — essas nós não analisamos

**O que Marcos agrega?**

1. **Cobertura muito maior** — 1145 vs 448 rubricas
2. **Análise de FGTS** — Marcos encontrou 28 divergências de FGTS que nós não analisamos
3. **Análise de INSS** — 13 divergências de INSS
4. **IRRF das rubricas que não estão no nosso cruzamento** — pode haver divergências nas 697 que não cobrimos

**O que Marcos NÃO tem que nós temos:**

1. **Execução real** — nós já enviamos S-1010 para o eSocial e temos recibos
2. **Pipeline completo** — S-1210 retificação + S-5002 confirmação
3. **Automação** — sistema web funcional para escalar
4. **Base legal** — `eb_skills_base_legal` com 534 fundamentações

### Recomendação

A tabela do Marcos é **complementar, não substituível**. Serve como:

1. Check extra para validar que nossas 385 `rubrica_corrections` estão certas
2. Expansão de cobertura para as 697 rubricas que não cruzamos
3. Referência para FGTS (que não priorizamos)

Mas para **decisão de envio**, o sistema usa o `cruzamento_eb` — que é onde temos controle de status, envio, recibos.

---

## 5. ESOCIAL_DEPARA — PONTO DE ATENÇÃO

```
Total: 2381 mapeamentos
Aplicados: 6  (apenas!)
Pendentes: 2375
```

Esta tabela tem 2381 regras de depara GI→eSocial, mas só 6 foram aplicadas (provavelmente as que geraram o cruzamento_eb). As 2375 pendentes podem conter mapeamentos úteis para expandir a cobertura.

---

## 6. TABELAS PARA LIMPAR (se quiser)

Podem ser deletadas sem impacto:

- `base_ficha_financeira` (0 rows)
- `planilha_1` (0 rows)
- `analise_natureza` (supersedida)
- `analise_natureza_certo` (supersedida)
- `correcoes_staging` (já aplicado)
- `dinamica` (análise antiga)
- `tabela_eventos_gl` (duplicata de cruzamento_tabela_b)

> **NÃO deletar `tabela_eb`** mesmo obsoleta — é o upload original do EB Skills, pode servir como referência.

---

## 7. RESUMO EXECUTIVO

| Categoria          | Qtd | Tabelas                                                                                                     |
| ------------------ | --- | ----------------------------------------------------------------------------------------------------------- |
| **ATIVAS**         | 15  | cruzamento*eb, esocial_envios, depara, corrections, config, pipeline*_, eb*skills, explorador*_, master\_\* |
| **REFERÊNCIA**     | 4   | naturezas (3x), tabela3_oficial                                                                             |
| **INTERMEDIÁRIAS** | 4   | cruzamento_tabela_a/b, resultado, tabela_cruzamento                                                         |
| **OBSOLETAS**      | 6   | analise_natureza(2x), correcoes_staging, dinamica, tabela_eb, tabela_eventos_gl                             |
| **LIXO**           | 2   | base_ficha_financeira, planilha_1                                                                           |
| **CONTROLE**       | 2   | uploads, cruzamento_uploads                                                                                 |
| **NÃO EXISTE**     | 1   | pipeline_snapshots (referenciada mas não criada)                                                            |
