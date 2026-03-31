# PESQUISA — Tabela 21: Códigos de Incidência Tributária do IRRF (codIncIRRF)

> Pesquisa realizada via web em jul/2026 — Fontes: gov.br (Tabela oficial S-1.3), Fortes Tecnologia, Proform, Alterdata

---

## 1. O que é a Tabela 21

A Tabela 21 do eSocial define os **Códigos de Incidência Tributária da Rubrica para o IRRF**. Todo evento S-1010 (Tabela de Rubricas) tem o campo `codIncIRRF` que determina **como aquela rubrica será tratada para fins de Imposto de Renda**.

**Impacto direto:** O `codIncIRRF` determina:

- Se o valor aparece como **rendimento tributável** no Informe de Rendimentos
- Se o valor aparece como **rendimento isento/não tributável**
- Se o valor é uma **dedução** da base de cálculo do IR
- Se o valor é uma **retenção** de IRRF
- Se o valor é **completamente ignorado** pela Receita Federal (código 9)

---

## 2. Estrutura Completa dos Códigos

### Código 0 — Rendimento não tributável (EXTINTO em 01/07/2021)

- Usado até 30/06/2021
- **Não usar mais** — substituído pelos códigos 7x

### Código 9 — Verba transitada pela folha sem impacto fiscal

- **Descrição oficial:** "Verba transitada pela folha de pagamento de natureza diversa de rendimento ou retenção/isenção/dedução de IR"
- **Exemplos:** desconto de convênio farmácia, desconto de consignações, empréstimo consignado
- **Vigência:** desde 01/10/2015 — sem data fim
- **⚠️ CRÍTICO:** Valores com código 9 são **COMPLETAMENTE IGNORADOS** pela Receita Federal
- **Não aparecem no Informe de Rendimentos**
- **Não aparecem nos demonstrativos de IR**
- **Não aparecem na antiga DIRF**

#### Quando usar código 9:

- EXCLUSIVAMENTE para verbas que **NÃO são rendimento** do trabalhador
- Movimentações financeiras puras (farmácia, consignação, repasses)

#### Quando NÃO usar código 9:

- Quando o valor é um rendimento, mesmo que isento → usar 7x
- Quando o valor é uma dedução de IR → usar 4x
- Quando o valor é previdência social/complementar → usar 4x/6x
- **"Quando um valor é rendimento mas a legislação o classifica como isento, o código 9 deixa de ser adequado"** (Fortes Tecnologia)

### Grupo 1x — Rendimento tributável (base de cálculo do IR)

| Código | Descrição                | Vigência                |
| ------ | ------------------------ | ----------------------- |
| 11     | Remuneração mensal       | 01/10/2015 — atual      |
| 12     | 13º salário              | 01/10/2015 — atual      |
| 13     | Férias                   | 01/10/2015 — atual      |
| 14     | PLR                      | 01/10/2015 — atual      |
| 15     | RRA (extinto 30/06/2021) | 01/10/2015 — 30/06/2021 |

### Grupo 3x — Retenção do IRRF efetuada sobre

| Código | Descrição                | Vigência                |
| ------ | ------------------------ | ----------------------- |
| 31     | Remuneração mensal       | 01/10/2015 — atual      |
| 32     | 13º salário              | 01/10/2015 — atual      |
| 33     | Férias                   | 01/10/2015 — atual      |
| 34     | PLR                      | 01/10/2015 — atual      |
| 35     | RRA (extinto 30/06/2021) | 01/10/2015 — 30/06/2021 |

### Grupo 4x — Dedução do rendimento tributável do IRRF

| Código | Descrição                                                 | Vigência                |
| ------ | --------------------------------------------------------- | ----------------------- |
| **41** | **Previdência Social Oficial (PSO) — Remuneração mensal** | 01/10/2015 — atual      |
| **42** | **PSO — 13º salário**                                     | 01/10/2015 — atual      |
| **43** | **PSO — Férias**                                          | 01/10/2015 — atual      |
| 44     | PSO — RRA (extinto 30/06/2021)                            | 01/10/2015 — 30/06/2021 |
| **46** | **Previdência complementar — Salário mensal**             | 01/10/2015 — atual      |
| **47** | **Previdência complementar — 13º salário**                | 01/10/2015 — atual      |
| **48** | **Previdência complementar — Férias**                     | 01/10/2015 — atual      |

### Grupo 5x — Pensão alimentícia

| Código | Descrição                               | Vigência                |
| ------ | --------------------------------------- | ----------------------- |
| 51     | Pensão alimentícia — Remuneração mensal | 01/10/2015 — atual      |
| 52     | Pensão alimentícia — 13º salário        | 01/10/2015 — atual      |
| 53     | Pensão alimentícia — Férias             | 01/10/2015 — atual      |
| 54     | Pensão alimentícia — PLR                | 01/10/2015 — atual      |
| 55     | Pensão alimentícia — RRA (extinto)      | 01/10/2015 — 30/06/2021 |

### Grupo 6x — FAPI e Desconto simplificado

| Código | Descrição                        | Vigência                |
| ------ | -------------------------------- | ----------------------- |
| 61     | FAPI — Remuneração mensal        | 01/10/2015 — atual      |
| 62     | FAPI — 13º salário               | 01/10/2015 — atual      |
| 63     | FAPI — Férias                    | 01/10/2015 — atual      |
| 64     | FAPI — RRA (extinto)             | 01/10/2015 — 30/06/2021 |
| 65     | FAPI — PLR                       | 01/10/2015 — atual      |
| 66     | FAPI — RRA                       | 01/10/2015 — atual      |
| **68** | **Desconto simplificado mensal** | **01/05/2023** — atual  |

### Código 67 — Plano de saúde (uso exclusivo na Declaração de Ajuste Anual)

| Código | Descrição                                     | Vigência           |
| ------ | --------------------------------------------- | ------------------ |
| 67     | Plano privado coletivo de assistência à saúde | 01/10/2015 — atual |

### Grupo 7x — Rendimento não tributável ou isento do IRRF

| Código | Descrição                                                         | Vigência           |
| ------ | ----------------------------------------------------------------- | ------------------ |
| **70** | **Parcela isenta 65 anos — Remuneração mensal**                   | 01/10/2015 — atual |
| **71** | **Parcela isenta 65 anos — 13º salário**                          | 01/10/2015 — atual |
| **72** | **Diárias**                                                       | 01/10/2015 — atual |
| **73** | **Ajuda de custo**                                                | 01/10/2015 — atual |
| **74** | **Indenização e rescisão de contrato, inclusive PDV e acidentes** | 01/10/2015 — atual |
| **75** | **Abono pecuniário**                                              | 01/10/2015 — atual |
| **76** | **Moléstia grave/acidente em serviço — Rem. mensal**              | 01/10/2015 — atual |
| **77** | **Moléstia grave/acidente em serviço — 13º salário**              | 01/10/2015 — atual |
| **79** | **Outras isenções (ex: PCMSO, benefícios isentos)**               | 01/10/2015 — atual |

### Grupo 9xxx — Exigibilidade suspensa (decisões judiciais)

| Código    | Descrição                                      | Vigência           |
| --------- | ---------------------------------------------- | ------------------ |
| 9011      | Remuneração mensal                             | 01/10/2015 — atual |
| 9012      | 13º salário                                    | 01/10/2015 — atual |
| 9013      | Férias                                         | 01/10/2015 — atual |
| 9014      | PLR                                            | 01/10/2015 — atual |
| 9031      | Retenção IRRF — Rem. mensal                    | 01/10/2015 — atual |
| 9032      | Retenção IRRF — 13º salário                    | 01/10/2015 — atual |
| 9033      | Retenção IRRF — Férias                         | 01/10/2015 — atual |
| 9034      | Retenção IRRF — PLR                            | 01/10/2015 — atual |
| 9041-9048 | Deduções suspensas (PSO, prev. compl., férias) | 01/10/2015 — atual |
| 9051-9054 | Pensão alimentícia suspensa                    | 01/10/2015 — atual |
| 9831-9834 | Depósito judicial                              | 01/10/2015 — atual |

---

## 3. O Problema da APPA — Análise Técnica

### Verba 566 (Desconto INSS)

A verba 566 é o desconto de contribuição previdenciária do trabalhador (INSS). Para que apareça como **dedução no demonstrativo de IR**, a rubrica precisa ter:

- **codIncIRRF = 41** (Previdência Social Oficial — Remuneração mensal)
- Ou **codIncIRRF = 42** para 13º salário
- Ou **codIncIRRF = 43** para férias

**Se estiver com codIncIRRF = 9 ou vazio:** O desconto de INSS desaparece completamente das deduções de IR. O trabalhador não consegue deduzir o INSS na declaração de IR.

**Confirmação da Ana:** "Sabe aquela verba 566, que é o INSS? Deveria estar aqui, ó, e não veio nada."

### Verba 47 (Previdência Complementar)

O `codIncIRRF = 47` significa **"Previdência complementar — 13º salário"**. É uma dedução do rendimento tributável. Se a rubrica de previdência complementar não estiver com o codIncIRRF correto (46/47/48), ela não aparece como dedução.

**Confirmação da Ana:** "Não subiu errada, mas não subiu completamente certa, ficou faltando um tiquinho de coisa."

### Verbas indenizatórias de rescisão

Verbas indenizatórias (aviso prévio indenizado, multa FGTS, etc.) devem ter:

- **codIncIRRF = 74** (Indenização e rescisão de contrato)
- Aparecem como "Rendimentos Isentos e Não Tributáveis" no Informe de Rendimentos

**Se estiverem com codIncIRRF = 9:** Ficam invisíveis — zeradas. Exatamente o que a Ana reportou.

---

## 4. Consequências de Classificação Errada

### Código 9 quando deveria ser 7x (rendimento isento)

1. O valor fica **invisível** para a Receita Federal
2. O trabalhador não consegue justificar a origem do dinheiro
3. Se comprar bem relevante (carro, imóvel) → **malha fina por variação patrimonial a descoberto**
4. O problema não está na declaração do trabalhador, mas na parametrização da empresa

### Código 9 quando deveria ser 4x (dedução)

1. O trabalhador **não pode deduzir** INSS, previdência complementar, pensão alimentícia
2. Paga mais IR do que deveria
3. O Informe de Rendimentos fica incompleto
4. 16-20 mil funcionários da APPA afetados

### Código errado nos rendimentos tributáveis (1x)

1. Base de cálculo do IR calculada incorretamente
2. IRRF retido a mais ou a menos
3. Divergência entre o que a empresa declarou e o que a Receita apura

---

## 5. Como o codIncIRRF Afeta os Totalizadores

### Evento S-5002 — Totalização do IRRF por Trabalhador

O S-5002 é gerado automaticamente pelo eSocial após cada S-1210. Ele totaliza:

| tpValor (S-5002)        | O que agrupa                                  |
| ----------------------- | --------------------------------------------- |
| Rendimentos tributáveis | Rubricas com codIncIRRF = 11, 12, 13, 14      |
| Retenção IRRF           | Rubricas com codIncIRRF = 31, 32, 33, 34      |
| Deduções                | Rubricas com codIncIRRF = 41-48, 51-55, 61-68 |
| Rendimentos isentos     | Rubricas com codIncIRRF = 70-79               |
| Ignorados (código 9)    | **NÃO entram em nenhum totalizador**          |

**Fórmula de totalização do S-5002:**

- Soma dos valores das rubricas com `tpRubr = 1` (vencimento) ou `tpRubr = 3` (informativa)
- Subtrai valores das rubricas com `tpRubr = 2` (desconto) ou `tpRubr = 4` (informativa dedutora)
- Agrupado por codIncIRRF

**Consequência:** Se a verba 566 (INSS) tem codIncIRRF = 9, ela não entra no grupo "Deduções PSO" do S-5002. Logo, o totalizador mostra zero de dedução de INSS para fins de IR.

---

## 6. Relação com a DIRF Extinta

Antes de 2025, a DIRF era preenchida manualmente e permitia ajustes. Agora:

- Os dados do eSocial **alimentam automaticamente** os sistemas da Receita Federal
- Não há margem para ajustes manuais posteriores
- **Se o codIncIRRF estiver errado no S-1010, o dado errado vai direto para a Receita**
- "A correta parametrização das rubricas no eSocial deixou de ser um detalhe técnico e passou a ser uma responsabilidade direta" (Fortes Tecnologia)

---

## 7. Resumo para a APPA

| Rubrica                        | codIncIRRF Correto                     | O que acontece se errado            |
| ------------------------------ | -------------------------------------- | ----------------------------------- |
| Verba 566 (INSS)               | 41 (PSO mensal), 42 (13º), 43 (férias) | Dedução de INSS desaparece do IR    |
| Verba 47 (Prev. complementar)  | 46 (mensal), 47 (13º), 48 (férias)     | Dedução de prev. compl. desaparece  |
| Verbas indenizatórias rescisão | 74 (indenização)                       | Rendimentos isentos desaparecem     |
| Salário base                   | 11 (rem. mensal)                       | Base tributável errada              |
| 13º salário                    | 12                                     | Tributação do 13º errada            |
| Férias                         | 13                                     | Tributação de férias errada         |
| IRRF retido                    | 31 (mensal), 32 (13º), 33 (férias)     | Retenção não aparece                |
| Pensão alimentícia             | 51-54                                  | Dedução de pensão desaparece        |
| Plano de saúde                 | 67                                     | Não aparece na declaração de ajuste |

---

## 8. Fontes

1. **gov.br** — Tabela 21 oficial, versão S-1.3 (cons. NT 06/2026)
2. **Fortes Tecnologia** — "Código de Incidência no eSocial: como evitar erros no Informe de Rendimentos" (Luanna Araujo, 08/01/2026)
3. **Proform** — "S-1010 x IRRF incidência — erro na rubrica gera risco fiscal"
4. **MGP Consultoria** — "Entenda o Evento S-5002 — Imposto de Renda Retido na Fonte"
