# STATUS FINAL LOTE 1 — 22/04/2026

**Atualização:** 22/04/2026
**Contexto:** continuação da missão aberta em 21/04/2026. Lote 1 dos 3 meses (Fev/Mar/Abr 2025) foi **processado até o fim** nesta sessão via endpoint `/api/s1210-repo/enviar-lote-cpfs` em blocos de 1000.

---

## 1. Números finais — Lote 1 (último status por CPF)

| Período | Scope | OK | Erro | % OK |
|---|---:|---:|---:|---:|
| **Fev/2025 L1** | 9.471 | 8.540 | 931 | **90,2 %** |
| **Mar/2025 L1** | 8.164 | 7.317 | 847 | **89,6 %** |
| **Abr/2025 L1** | 7.142 | 6.187 | 955 | **86,6 %** |
| **TOTAL** | **24.777** | **22.044** | **2.733** | **89,0 %** |

Scope ainda não processado (L2 + L3 + L4 dos 3 meses): **8.024 CPFs**.

### Intervenções pré-lote que destravaram Mar e Abr

- **S-1298 Mar/2025** — recibo `1.1.0000000040115886503`
- **S-1298 Abr/2025** — recibo `1.1.0000000040115996084`

Antes do S-1298 esses dois meses estavam **100 % com ocorrência 620** (folha fechada). Depois da reabertura caíram para o patamar de Fev.

---

## 2. Breakdown dos 2.733 erros (Lote 1 consolidado)

| Etapa lógica | Qtd | % do total de erros |
|---|---:|---:|
| `buscar_recibo` (CPF não encontrado no ZIP) | **2.488** | **91 %** |
| `processamento_rejeitado` / cod HTTP 401 | **245** | **9 %** |

### Por período

| Período | buscar_recibo | proc_rej 401 | total erros |
|---|---:|---:|---:|
| Fev/2025 | 780 | 151 | 931 |
| Mar/2025 | 790 | 57 | 847 |
| Abr/2025 | 918 | 37 | 955 |
| **Total** | **2.488** | **245** | **2.733** |

### Dentro dos 245 rejeitados pelo eSocial (código HTTP 401)

O eSocial retorna uma ocorrência detalhada dentro do "conteúdo inválido":

| Ocorrência | Qtd | Mensagem do eSocial |
|---:|---:|---|
| **8** (pensão alimentícia) | **134** | `Grupo 'Informação dos beneficiários da pensão alimentícia' deve ser preenchido` |
| **459** (recibo stale) | **96** | `Não foi localizado um evento para o recibo de entrega informado ou o mesmo foi excluído/retificado` |
| **8** (plano de saúde) | **15** | `Grupo 'Plano de saúde coletivo' deve ser preenchido` |

*(A ocorrência 620 "folha fechada" foi **integralmente resolvida** com os dois S-1298; todos os 3.076 CPFs Mar + 5 Abr que batiam no 620 antes do S-1298 estão hoje OK.)*

---

## 3. Diagnóstico cirúrgico de cada categoria

### A) 2.488 × `buscar_recibo` — 91 % dos erros

**O que aconteceu:** o robô abriu o ZIP do eSocial (baixado em 10/04/2026) e não encontrou nenhum S-1210 com `nrRecibo` casando o CPF+período. Sem recibo prévio o robô pula o envio — **não é um "erro do eSocial"**, é que **ele sequer tentou enviar** esse CPF.

**Por que:**
1. O CPF nunca teve S-1210 aceito naquele período (e nesse caso deveria ser *origem* — envio sem `evtRemun` de retificação, igual a S-1200 mas com complementar). A XLSX da Ana lista esses CPFs no Lote 1 porque, para ela, são "folha normal sem plano de saúde", mas o eSocial ainda não tem remuneração gravada.
2. Ou o recibo ativo hoje não estava no ZIP de 10/04/2026 (o CPF foi retificado depois dessa data por outro sistema).

**Como resolver (3 caminhos):**
- **(a) Baixar ZIP novo do eSocial** (Download Cirúrgico por per_apur) — gasta 1 consulta/dia por período × 3 períodos = 3 das 10 consultas diárias. Depois reprocessar só esses 2.488 CPFs.
- **(b) Consultar `ConsultarIdentificadoresEventos`** por CPF+período (gasta 10/dia no total, inviável pros 2.488).
- **(c) Enviar como S-1210 de origem (não retificação)** — gera do zero com `<indRetif>1</indRetif>`. Precisa reunir os dados de folha (valor, rubricas) que hoje o robô copia do S-1210 anterior. *Se* a XLSX da Ana tem esses dados, dá pra gerar do zero. Caso contrário precisa de dados da folha APPA externa (pagamentos + retenções).

**Recomendação:** **caminho (a)** — 1 download por mês, reprocessar. Custo: 3 consultas do limite, ~1h de reprocessamento (2.488 CPFs × ~1,5 s com paralelismo já usado).

### B) 134 × ocorrência 8 — pensão alimentícia

**Mensagem:** `Grupo 'Informação dos beneficiários da pensão alimentícia' deve ser preenchido.`

**Por que:** o S-1210 prévio desse CPF tinha rubrica de pensão alimentícia (código específico no tpRubr), e o XML que nosso robô gerou descartou o grupo `detPenAlim`. O eSocial **exige** o bloco com os dados do beneficiário (CPF do dependente + valor) quando há rubrica de pensão.

**Como resolver:**
- Esses 134 CPFs pertencem ao **Lote 4** (pensão alimentícia) e não ao Lote 1. A XLSX da Ana classifica Lote 4 como "3 pessoas manuais" mas o volume real é 134 — precisa revalidar com a Ana.
- Alternativa técnica: ler o XML prévio (já tá no ZIP), extrair o bloco `detPenAlim`, reinjetar no XML retificado. Trabalho de parser, mas factível.

**Recomendação:** **reclassificar os 134 → Lote 4** e tratar fora do Lote 1.

### C) 96 × ocorrência 459 — recibo stale

**Mensagem:** `Não foi localizado um evento para o recibo de entrega informado ou o mesmo foi excluído/retificado.`

**Por que:** o `nrRecibo` que o robô pegou do ZIP (10/04) já não é mais o ativo — outro sistema retificou esse CPF entre 10/04 e 22/04. **Mesmo problema de A (ZIP defasado)**, mas aqui pelo menos havia *algum* recibo no ZIP, ele tentou, o eSocial disse "esse recibo já não vale".

**Como resolver:** **baixar ZIP novo** (mesmo caminho A). Cai automaticamente.

### D) 15 × ocorrência 8 — plano de saúde

**Mensagem:** `Grupo 'Plano de saúde coletivo' deve ser preenchido.`

**Por que:** esses 15 CPFs foram classificados errado na XLSX — estão no Lote 1 (sem planSaude) mas o S-1210 prévio traz rubricas `detPlanSaude`. Ao retificar sem o grupo, rejeição imediata.

**Como resolver:** **reclassificar os 15 → Lote 2 ou Lote 3** conforme a operadora (774 odonto ou 775/522).

---

## 4. Plano de resolução proposto (pendente aprovação)

| Passo | Ação | CPFs atingidos | Custo | Tempo |
|---|---|---:|---|---|
| **1** | Baixar 3 ZIPs novos (Fev + Mar + Abr) via Download Cirúrgico | 2.488 + 96 = **2.584** | 3 consultas (de 10/dia) | ~30 min download + ~1 h reprocessar |
| **2** | Reclassificar 134 CPFs pensão → Lote 4 | 134 | DB UPDATE + revisão Ana | ~15 min |
| **3** | Reclassificar 15 CPFs planSaude → Lote 2/3 (pela operadora) | 15 | DB UPDATE + revisão Ana | ~10 min |

**Resultado esperado pós-plano:** Lote 1 chega perto de **99 %+ OK**. Os casos que sobrarem (pensão sem CPF do beneficiário na XLSX, ou planos sem operadora) vão pra tratamento manual individual.

**Total de consultas gastas:** **3 de 10 diárias** — seguro.

---

## 5. Próximas decisões (aguardando usuário)

1. **Autorizar download dos 3 ZIPs novos?** (1 consulta/período × 3 = 3/10)
2. **Ou ir direto pros Lotes 2/3/4** (8.024 CPFs pendentes) e tratar os 2.733 erros do L1 depois?
3. **Ou reprocessar apenas os 96 com ocorrência 459** (menor risco, menor custo)?

---

## 6. Scripts de apoio usados neste relatório

- [`_status_geral_atual.py`](../../python-scripts/_status_geral_atual.py) — grid scope × OK × erro × pend por período/lote
- [`_breakdown_erros_lote1.py`](../../python-scripts/_breakdown_erros_lote1.py) — etapas lógicas dos erros L1
- [`_breakdown_final.py`](../../python-scripts/_breakdown_final.py) — breakdown definitivo considerando último status por CPF
