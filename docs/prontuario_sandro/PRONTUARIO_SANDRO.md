# Prontuário de Correções eSocial — APPA

**Preparado para:** Sandro (tributarista)
**Empresa:** APPA — CNPJ 05.969.071/0001-10
**Data das correções S-1010:** 04/04/2026
**CPF piloto:** 081.325.889-83
**Competência demonstrada:** Janeiro/2025
**Última atualização:** 06/04/2026 (após reunião Ana + Xande)

---

## 1. Resumo Executivo

A empresa APPA possuía 11 rubricas com classificação incorreta de incidência tributária no eSocial. O problema principal: as rubricas de desconto de INSS (códigos 566 e 596) estavam com codIncIRRF = 11/12 ("rendimento tributável") ao invés de 41/42 ("dedução do IRRF").

**Consequência:** Dentro do eSocial o cálculo do INSS era feito corretamente, mas a informação **não era carregada para a Receita Federal**. O INSS era somado à remuneração no campo da Receita e a dedução não aparecia → base inflada de IRRF → informes de rendimentos com INSS = R$0,00.

**Ações realizadas:**

- ✅ 11 rubricas corrigidas via evento S-1010 (alteração de tabela) em produção
- ✅ Pipeline de retificação executado para 1 CPF piloto
- ✅ Totalizadores S-5001 e S-5003 recalculados pelo governo
- ✅ S-5002 (IRRF) confirmado funcionando no portal web — previdência oficial agora aparece corretamente
- ⚠️ DCTF retificadora gerada automaticamente no e-CAC — **abatimentos desapareceram** (ver seção 6)

**Impacto estimado:** ~20.000 funcionários × múltiplos meses

---

## 2. Correções nas Rubricas (S-1010)

### Rubricas exemplificadas (afetam TODOS os trabalhadores):

| Rubrica | Descrição                 | Campo      | ANTES (errado)                 | DEPOIS (correto)                     |
| ------- | ------------------------- | ---------- | ------------------------------ | ------------------------------------ |
| **566** | DESC. I.N.S.S.            | codIncIRRF | 11 (Rendimento tributável)     | **41** (Dedução - Prev. oficial)     |
| **596** | DESC. I.N.S.S. S/13º SAL. | codIncIRRF | 12 (Rendimento tributável 13º) | **42** (Dedução - Prev. oficial 13º) |

> Ana (reunião 06/04): "Essas daí foram as que — 566 e 596 são as que vão atingir todo mundo. Ninguém fica de fora."
> As demais 9 rubricas também foram corrigidas (total de 11 enviadas).

### Evidência visual:

<!-- TODO: Inserir prints do portal eSocial -->

> ⏳ Aguardando: `01_S1010_rubrica_566.png` e `02_S1010_rubrica_596.png`

---

## 3. Pipeline de Retificação — CPF Piloto

### ⛔ DECISÃO IMPORTANTE: NÃO retificar S-1200

Ana confirmou na reunião (06/04): **"Eu não gostaria de mexer na S-1200"**. Motivo: retificar a remuneração pode alterar valores declarados de recolhimento (a maior ou a menor).

> Ana: "Porque senão eu posso alterar os valores de — ah, você declarou uma coisa, mas tem que recolher a maior, entendeu? Ou a menor. Eu não queria mexer nisso."

### Pipeline simplificado (apenas S-1210):

O pipeline original de 8 etapas (que incluía S-1200) será **simplificado**. A correção consiste apenas em:

1. S-1010 — Correção das rubricas (já feito, permanente)
2. S-1210 — Retificação dos pagamentos por competência/CPF

> Confirmado por Ana que na Objetiva também fez apenas S-1210, sem mexer em S-1200.

### Pipeline executado no CPF piloto (antes da simplificação):

| Etapa | Evento               | Ação                                    | Status |
| ----- | -------------------- | --------------------------------------- | ------ |
| 1     | S-1298               | Reabertura do período Dez/2024          | ✅     |
| 2     | S-3000               | Exclusão do pagamento Jan/2025          | ✅     |
| 3     | S-1200               | Retificação da remuneração Dez/2024     | ✅     |
| 4     | S-1210               | Retificação dos pagamentos Dez/2024     | ✅     |
| 5     | S-1210               | Reinclusão do pagamento Jan/2025        | ✅     |
| 6     | S-1299               | Fechamento do período Dez/2024          | ✅     |
| 7     | —                    | Aguardar processamento governo          | ✅     |
| 8     | S-5001/S-5002/S-5003 | Download dos totalizadores recalculados | ✅     |

> ⚠️ **Nota:** O pipeline futuro NÃO fará as etapas 2, 3 e 5 (que envolviam S-1200). Ficará muito mais simples.

---

## 4. Evidências do Portal eSocial Web

### 4.1 Pagamentos (S-1210) — Jan/2025

<!-- TODO: Inserir print -->

> ⏳ Aguardando: `03_S1210_pagamentos_jan2025.png`

### 4.2 Totalizador INSS (S-5001) — Jan/2025

<!-- TODO: Inserir print -->

> ⏳ Aguardando: `04_S5001_totalizador_inss_jan2025.png`

### 4.3 Totalizador IRRF (S-5002) — Jan/2025 ⭐ CRÍTICO

**Confirmado na reunião que está funcionando no portal web.**

Ana demonstrou no eSocial:

- Remuneração total do trabalhador: **R$ 3.352,43**
- Previdência oficial: **ANTES aparecia zerada**, agora mostra o valor correto (INSS da folha)
- Separação correta: cod 41 (dedução previdência) separado do cod 11 (rendimento tributável)
- 13º: rendimento tributário do 13º e previdência do 13º também separados corretamente

> Ana: "Antigamente, essa previdência oficial aparecia zerada, entendeu? Agora ela se apresenta aqui e é do INSS da folha de pagamento. Antes não estava aparecendo esse 41 aqui, tava tudo aparecendo apenas no 11, então tava somando na remuneração mensal. Agora está separado adequadamente."

<!-- TODO: Inserir print -->

> ⏳ Aguardando: `05_S5002_totalizador_irrf_jan2025.png`

### 4.4 Totalizador FGTS (S-5003) — Jan/2025

<!-- TODO: Inserir print -->

> ⏳ Aguardando: `06_S5003_totalizador_fgts_jan2025.png`

### 4.5 Rendimentos — Receita Federal (GI)

Ana mostrou a tela de "Rendimentos → Evidência Oficial": ao corrigir o evento 566, a informação carrega corretamente para a Receita Federal.

> Ana: "A gente vem em rendimentos, evidência oficial, tá vendo? A gente mudando o evento 566, ele vai carregar para cá a informação."

<!-- TODO: Inserir print -->

> ⏳ Aguardando: `07_receita_rendimentos.png`

---

## 5. O Que Mudou — Explicação Técnica

### ANTES (codIncIRRF = 11/12):

- Dentro do eSocial: cálculo do INSS **era feito corretamente**
- Na Receita Federal: INSS **NÃO aparecia como dedução**
- O INSS era somado à remuneração mensal (campo 11 = rendimento tributável)
- Informes de rendimentos: INSS = R$ 0,00
- Base de IRRF inflada → possível recolhimento a mais

### DEPOIS (codIncIRRF = 41/42):

- Dentro do eSocial: cálculo continua correto
- Na Receita Federal: INSS **aparece como dedução previdenciária**
- Separação adequada: remuneração no campo 11, INSS no campo 41
- Informes de rendimentos: INSS = valor correto
- Base de IRRF corrigida

### Propagação confirmada:

```
S-1010 (rubrica) → eSocial (totalizadores) → Receita Federal (rendimentos) → e-CAC (DCTF)
```

---

## 6. ⚠️ PROBLEMA CRÍTICO — DCTF Retificadora no e-CAC

### Descoberta da reunião (06/04/2026):

Ana verificou no e-CAC que a correção do eSocial gerou automaticamente uma **DCTF retificadora** para Janeiro/2025.

**O problema:** Na DCTF retificadora, **todos os valores de abatimento desapareceram**.

| Campo         | DCTF Original        | DCTF Retificadora    |
| ------------- | -------------------- | -------------------- |
| Abatimentos   | ✅ Valores presentes | ❌ **Todos zerados** |
| Contribuições | ✅ Valores presentes | ❌ **Sumiram**       |

> Ana: "Nesse momento tinha valores de abatimento e passa a não ter mais. [...] Todos esses abatimentos, tá vendo? Agora na retificada, retificadora, todos os abatimentos... sai tudo. É isso que a gente tem que evitar no caso, né?"

### Implicação:

A empresa pode perder créditos/deduções fiscais se as DCTFs retificadoras forem processadas com abatimentos zerados. **Este é o principal ponto que Sandro precisa analisar antes de escalar para os ~20.000 CPFs.**

<!-- TODO: Inserir prints comparativos -->

> ⏳ Aguardando: `08a_ecac_dctf_original_jan2025.png` e `08b_ecac_dctf_retificadora_jan2025.png`

---

## 7. Perguntas para Validação de Sandro

1. **DCTF — abatimentos:** Como evitar que os abatimentos desapareçam da DCTF retificadora? É possível corrigir isso manualmente no e-CAC, ou precisamos de uma abordagem diferente no pipeline?

2. **S-1200:** Confirmamos que NÃO vamos retificar S-1200 (remuneração). Sandro concorda com essa abordagem? Há risco de algum lado?

3. **Escala:** Podemos prosseguir com os ~20.000 CPFs restantes, ou devemos esperar a análise do impacto nos abatimentos?

4. **Períodos:** Quais competências precisam ser retificadas? (apenas 2024-2025, ou anos anteriores também?)

5. **Créditos:** Quantificar o impacto financeiro — quanto de IRRF foi recolhido a mais por conta da base inflada?

6. **Prazo:** Urgência para fazer as correções vs. risco dos abatimentos sumindo?

---

## 8. Dados Técnicos

- **Sistema:** Easy e-Social (https://easyesocial.com.br)
- **Página de prova online:** https://easyesocial.com.br/prova
- **Certificado:** A1 — cert_05969071000110_45C7EBE84F3FE665.pfx
- **Ambiente:** Produção (eSocial tipo 1)
- **API:** WebService REST eSocial v1.1.0

---

## Histórico de Reuniões

| Data       | Participantes           | Principais decisões                                                       |
| ---------- | ----------------------- | ------------------------------------------------------------------------- |
| 04/04/2026 | Dra. Cintia, Ana, Xande | Plano de 6 passos. Descoberta: eSocial propaga para e-CAC                 |
| 06/04/2026 | Ana, Xande              | S-1200 NÃO mexer. S-5002 funcionando. DCTF retificadora perde abatimentos |

---

_Documento gerado em 06/04/2026. Prints do portal eSocial pendentes de captura. Aguardando análise de Sandro._
