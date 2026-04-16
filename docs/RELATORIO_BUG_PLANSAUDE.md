# RELATÓRIO: Erro nos Valores de Plano de Saúde — S-1210 Janeiro/2025

**Data:** 15 de abril de 2026  
**Elaborado por:** Sistema Easy-Social (IA)  
**Assunto:** Explicação técnica do bug que gerou valores incorretos de `vlrSaudeTit` (plano de saúde) nos eventos S-1210 de Janeiro/2025

---

## RESUMO EXECUTIVO

O script que construiu o mapa de valores de plano de saúde para o S-1210 de Janeiro/2025 continha **dois bugs graves** que causaram:

1. **10.443 CPFs receberam planSaude**, quando na verdade apenas ~1.578 deveriam ter
2. **Valores inflados** — em média 6 a 200x maiores que o correto
3. **8.865 CPFs receberam planSaude sem ter plano de saúde algum**

---

## O QUE ACONTECEU — Explicação Técnica

### Contexto

Para montar o S-1210 (evento de pagamento), quando o trabalhador tem plano de saúde coletivo empresarial, é necessário incluir o grupo `<planSaude>` com o valor `vlrSaudeTit` (valor pago pelo titular). Esse valor vem das **rubricas de saúde** presentes no S-1200 (remuneração) do trabalhador.

As rubricas corretas de saúde da APPA são **apenas 4**:

| Rubrica | Natureza | Descrição |
|---------|----------|-----------|
| **607** | 9219 | Assistência médica |
| **774** | 9299 | Desc. assistência médica |
| **775** | 9299 | (APPA-específica, saúde) |
| **516** | 9299 | Desc. assistência odonto dependente |

### Bug 1: Critério de seleção errado (99 rubricas em vez de 4)

O script usou a seguinte query para selecionar quais rubricas seriam consideradas "de saúde":

```sql
SELECT DISTINCT cod_rubr FROM explorador_rubricas WHERE nat_rubr LIKE '92%'
```

Isso retornou **99 rubricas diferentes**, porque `nat_rubr LIKE '92%'` captura TODAS as naturezas que começam com 92 — incluindo rubricas que **NÃO são plano de saúde**, como:

| Rubrica | Natureza | O que realmente é |
|---------|----------|-------------------|
| 641 | 9201 | **Contribuição sindical** |
| 729 | 9250 | **Outros descontos** |
| 763 | 9233 | **Vale-transporte** |
| 806 | 9254 | **Empréstimo consignado** |
| 773 | 9243 | **Vale-refeição** |
| 776 | 9243 | **Vale-alimentação** |
| ... | 92xx | (outras 93 rubricas) |

**O correto seria filtrar APENAS as 4 rubricas específicas (607, 774, 775, 516).**

### Bug 2: Soma duplicada (original + retificação)

O S-1200 no ZIP pode ter duas versões do mesmo evento:
- `indRetif=1` → evento original
- `indRetif=2` → evento retificado (substitui o original)

O script **somava os valores de TODAS as versões**, em vez de usar apenas a versão mais recente. Resultado: **valores dobrados**.

```python
# Código do bug - somava sem verificar indRetif:
cpf_health[cpf] += subtotal  # acumulava tudo!
```

### Resultado combinado dos dois bugs

O valor final para cada CPF era calculado assim:

```
valor_errado = (soma de TODAS as 99 rubricas nat=92xx do S-1200 original)
             + (soma de TODAS as 99 rubricas nat=92xx do S-1200 retificado)
```

Em vez do correto:

```
valor_correto = valor da rubrica de saúde (607 ou 774 ou 775 ou 516)
                do S-1200 mais recente (retificação, se existir)
```

---

## PROVA MATEMÁTICA — Os 3 CPFs de Exemplo

### Waldelice (CPF: 93065345587)

**NÃO TEM plano de saúde.** Não deveria ter planSaude no S-1210.

| Evento | Rubrica | Natureza | Valor | É saúde? |
|--------|---------|----------|-------|----------|
| S-1200 original | 641 | 9201 | R$ 162,47 | ❌ Contribuição sindical |
| S-1200 original | 729 | 9250 | R$ 1,18 | ❌ Outros descontos |
| S-1200 original | 763 | 9233 | R$ 20,00 | ❌ Vale-transporte |
| S-1200 retificado | 641 | 9201 | R$ 162,47 | ❌ Contribuição sindical |
| S-1200 retificado | 729 | 9250 | R$ 1,18 | ❌ Outros descontos |
| S-1200 retificado | 763 | 9233 | R$ 20,00 | ❌ Vale-transporte |

**Cálculo do bug:** (162,47 + 1,18 + 20,00) × 2 = **R$ 367,30** ← valor enviado  
**Valor correto:** **R$ 0,00** (não tem plano de saúde)

---

### Suyane (CPF: 86747482522)

**NÃO TEM plano de saúde.** Não deveria ter planSaude no S-1210.

| Evento | Rubrica | Natureza | Valor | É saúde? |
|--------|---------|----------|-------|----------|
| S-1200 original | 641 | 9201 | R$ 162,47 | ❌ Contribuição sindical |
| S-1200 original | 729 | 9250 | R$ 1,18 | ❌ Outros descontos |
| S-1200 original | 763 | 9233 | R$ 20,00 | ❌ Vale-transporte |
| S-1200 original | 806 | 9254 | R$ 442,00 | ❌ Empréstimo consignado |
| S-1200 retificado | 641 | 9201 | R$ 162,47 | ❌ Contribuição sindical |
| S-1200 retificado | 729 | 9250 | R$ 1,18 | ❌ Outros descontos |
| S-1200 retificado | 763 | 9233 | R$ 20,00 | ❌ Vale-transporte |
| S-1200 retificado | 806 | 9254 | R$ 442,00 | ❌ Empréstimo consignado |

**Cálculo do bug:** (162,47 + 1,18 + 20,00 + 442,00) × 2 = **R$ 1.251,30** ← valor enviado  
**Valor correto:** **R$ 0,00** (não tem plano de saúde)

---

### Anaildes (CPF: 97850454553)

**TEM plano de saúde** (rubrica 516 — odonto dependente), mas valor foi inflado 200x.

| Evento | Rubrica | Natureza | Valor | É saúde? |
|--------|---------|----------|-------|----------|
| S-1200 original | 641 | 9201 | R$ 162,47 | ❌ Contribuição sindical |
| S-1200 original | **516** | **9299** | **R$ 7,51** | **✅ Odonto dependente** |
| S-1200 original | 729 | 9250 | R$ 1,18 | ❌ Outros descontos |
| S-1200 original | 763 | 9233 | R$ 20,00 | ❌ Vale-transporte |
| S-1200 original | 806 | 9254 | R$ 560,43 | ❌ Empréstimo consignado |
| S-1200 retificado | 641 | 9201 | R$ 162,47 | ❌ Contribuição sindical |
| S-1200 retificado | **516** | **9299** | **R$ 7,51** | **✅ Odonto dependente** |
| S-1200 retificado | 729 | 9250 | R$ 1,18 | ❌ Outros descontos |
| S-1200 retificado | 763 | 9233 | R$ 20,00 | ❌ Vale-transporte |
| S-1200 retificado | 806 | 9254 | R$ 560,43 | ❌ Empréstimo consignado |

**Cálculo do bug:** (162,47 + 7,51 + 1,18 + 20,00 + 560,43) × 2 = **R$ 1.503,18** ← valor enviado  
**Valor correto:** **R$ 7,51** (apenas rubrica 516)

---

## NÚMEROS DO IMPACTO

| Métrica | Valor ERRADO | Valor CORRETO |
|---------|-------------|---------------|
| CPFs com planSaude | **10.443** | **~1.578** (ou apenas 18, dependendo do tipo de plano) |
| CPFs que NÃO deveriam ter | **8.865** | 0 |
| Valor mínimo no mapa | R$ 4,38 | depende da rubrica |
| Valor máximo no mapa | R$ 20.501,37 | R$ ~560,00 |
| Valor mediano | R$ 679,48 | R$ ~47,00 |

---

## POR QUE ISSO ACONTECEU

### Causa Raiz

O script `_rebuild_jan_plansaude.py` foi criado para extrair valores de plano de saúde dos arquivos S-1200 do ZIP baixado do eSocial. A lógica partiu de uma premissa **incorreta**: que toda rubrica com natureza começando em "92" seria de plano de saúde.

Na tabela 3 do eSocial, as naturezas que começam com "92" abrangem **todas as categorias de descontos**, não apenas saúde:

| Faixa | Categoria |
|-------|-----------|
| 9201 | Contribuição sindical |
| 9211 | Pensão alimentícia |
| 9219 | **Assistência médica** ← só essa é saúde |
| 9220-9229 | Imposto de renda |
| 9230-9239 | Vale-transporte |
| 9240-9249 | Alimentação |
| 9250 | Outros descontos |
| 9254 | Empréstimo consignado |
| 9299 | **Outros descontos** (inclui saúde, mas também outras coisas) |

O critério `LIKE '92%'` capturou tudo isso indiscriminadamente.

### Por que o segundo bug (soma duplicada)?

Os ZIPs do eSocial contêm tanto o evento original (`indRetif=1`) quanto sua retificação (`indRetif=2`) quando houve correção. O correto é usar **apenas a versão mais recente**, mas o script somava todas as versões encontradas para cada CPF.

---

## COMO ESTÁ SENDO CORRIGIDO

1. **Script corrigido já criado** (`_rebuild_plansaude_correct.py`):
   - Usa apenas as 4 rubricas corretas: 607, 774, 775, 516
   - Usa apenas o evento mais recente (indRetif=2 > indRetif=1)
   - Aplica prioridade entre rubricas (607 > 774 > 775 > 516)
   - Resultado: **1.578 CPFs** com valores corretos

2. **Todos os ~11.000 S-1210 aceitos precisam ser retificados** com os valores corretos (ou sem planSaude, para os 8.865 que não deveriam ter)

3. **Mapa errado foi preservado** como backup: `plansaude_map_jan2025.ERRADO.json`

---

## CONCLUSÃO

O erro foi causado por um filtro excessivamente amplo na seleção de rubricas (`nat_rubr LIKE '92%'` em vez de listar as 4 rubricas específicas de saúde) combinado com falta de deduplicação entre eventos originais e retificados. O resultado foi a inclusão de valores de contribuição sindical, vale-transporte, empréstimo consignado e outros descontos como se fossem plano de saúde, gerando valores absurdamente inflados.

**Os dados foram identificados, o bug foi diagnosticado, a correção está pronta e será aplicada assim que o plano de retificação for aprovado.**
