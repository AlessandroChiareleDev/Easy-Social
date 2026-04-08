# Guia de Captura de Prints — Prontuário para Sandro

> Atualizado após reunião Ana + Xande em 06/04/2026

**Objetivo:** Capturar evidências visuais do eSocial Web e e-CAC mostrando que as correções das rubricas foram aplicadas, os totalizadores recalculados, e o impacto na Receita Federal.

**Dados do caso:**

- Empresa: APPA — CNPJ 05.969.071/0001-10
- CPF piloto: 081.325.889-83
- Competência: Janeiro/2025 (01/2025) — período confirmado com Ana
- 11 rubricas corrigidas via S-1010
- Pipeline: apenas S-1210 (retificação de pagamentos). **NÃO mexer em S-1200.**

---

## Pré-requisitos

- Certificado digital A1 da APPA instalado no Windows (senha: 12345678)
- Acesso gov.br configurado com selo "Certificado Digital"
- Chrome ou Edge (Playwright/Copilot browser não acessa Windows Certificate Store)
- ⚠️ Semana de fechamento de folha — eSocial pode ficar lento

---

## Acesso ao eSocial

1. Abrir: https://login.esocial.gov.br/login.aspx
2. Clicar **"Entrar com gov.br"**
3. Na tela gov.br, clicar **"Seu certificado digital"**
4. Selecionar o certificado da APPA (CNPJ 05.969.071/0001-10)
5. Digitar senha se solicitado: `12345678`
6. ⚠️ Se ficar carregando eternamente ao clicar certificado, tentar novamente (instabilidade normal nessa semana)

---

## Print 1 — Rubrica 566 (S-1010)

**Caminho:** `Empregador → Tabelas → Tabela de Rubricas`

1. Buscar rubrica **566** (DESC. I.N.S.S.)
2. Abrir detalhes — verificar alteração: havia 3 ou 4 alterações
3. Print mostrando **codIncIRRF = 41** (Dedução - Previdência oficial)
4. Deve aparecer que houve alteração de 11 → 41
5. Salvar como: `01_S1010_rubrica_566.png`

---

## Print 2 — Rubrica 596 (S-1010)

**Mesmo caminho:** `Empregador → Tabelas → Tabela de Rubricas`

1. Buscar rubrica **596** (DESC. I.N.S.S. S/13º SALÁRIO)
2. Print mostrando **codIncIRRF = 42** (Dedução - Prev. oficial 13º)
3. Deve aparecer que houve alteração de 12 → 42
4. Salvar como: `02_S1010_rubrica_596.png`

> **Nota da reunião:** Ana mencionou "593" mas no código e no banco é **596**. Provável erro de transcrição/áudio.

---

## ~~Print S-1200 — REMOVIDO~~

> ⛔ **Ana confirmou: NÃO mexer na S-1200 (Remuneração Devida).** Motivo: retificar remuneração pode alterar valores declarados de recolhimento (a maior ou a menor), o que não é o objetivo. O pipeline deve usar **apenas S-1210** (pagamentos).

---

## Print 3 — Pagamentos S-1210

**Caminho:** `Folha de Pagamentos → Gestão de Folha`

- Selecionar competência: **Janeiro/2025** (01/2025)
- Clicar no botão **"Trabalhadores"**
- Buscar CPF: **081.325.889-83**
- Clicar em **"Pagamentos"**

**O que capturar:**

- Tela completa dos pagamentos do trabalhador
- O nrRecibo do evento S-1210
- Salvar como: `03_S1210_pagamentos_jan2025.png`

---

## Print 4 — Totalizador INSS (S-5001)

**Caminho:** `Folha de Pagamentos → Totalizadores → Contribuição Previdenciária por Trabalhador`

- Competência: **Janeiro/2025**
- CPF: **081.325.889-83**

**O que capturar:**

- Base de cálculo INSS
- Valor da contribuição previdenciária
- Salvar como: `04_S5001_totalizador_inss_jan2025.png`

---

## Print 5 — Totalizador IRRF (S-5002) ⭐ CRÍTICO

**Caminho:** `Folha de Pagamentos → Totalizadores → Imposto de Renda por Trabalhador`

- Competência: **Janeiro/2025**
- CPF: **081.325.889-83**

**O que capturar — MAIS IMPORTANTE do prontuário:**

- **Remuneração total** — Ana mostrou: R$ 3.352,43
- **Previdência oficial** — ANTES aparecia **zerada**, AGORA aparece o valor correto do INSS da folha
- **Separação cod 41 vs cod 11** — o INSS agora aparece no campo de dedução (41) e não mais como rendimento tributável (11)
- **Rendimento tributário do 13º** e **previdência do 13º** — também separados corretamente
- Este print prova que a correção propagou para o cálculo do IRRF
- Salvar como: `05_S5002_totalizador_irrf_jan2025.png`

> **Confirmado na reunião:** Ana abriu o S-5002 da competência Jan/2025 no portal web e está funcionando. A previdência oficial agora aparece corretamente.

---

## Print 6 — Totalizador FGTS (S-5003)

**Caminho:** `Folha de Pagamentos → Totalizadores → Trabalhador → FGTS`

- Competência: **Janeiro/2025**
- CPF: **081.325.889-83**

**O que capturar:**

- Base de cálculo do FGTS
- Valor do FGTS
- Salvar como: `06_S5003_totalizador_fgts_jan2025.png`

---

## Print 7 — Receita Federal: Rendimentos (GI)

**Caminho dentro do eSocial:** `Rendimentos → Evidência Oficial` (ou via GI — Gestão de Informações)

Ana mostrou: ao mudar o evento 566, a informação carrega para a Receita Federal nessa tela.

**O que capturar:**

- Tela de rendimentos mostrando a evidência oficial com os valores atualizados
- Salvar como: `07_receita_rendimentos.png`

---

## Print 8 — e-CAC: DCTF Original vs Retificadora ⚠️ CRÍTICO

**⚠️ PROBLEMA DESCOBERTO NA REUNIÃO:**

Ana mostrou que a correção gerou uma **DCTF retificadora** automaticamente no e-CAC para Jan/2025. Na retificadora, **todos os abatimentos desapareceram**:

- DCTF Original: tinha valores de abatimento (créditos/deduções)
- DCTF Retificadora: abatimentos **saíram todos** (zerados)

**Ana disse:** "É isso que a gente tem que evitar no caso."

**O que capturar — 2 prints:**

1. `08a_ecac_dctf_original_jan2025.png` — DCTF original COM abatimentos
2. `08b_ecac_dctf_retificadora_jan2025.png` — DCTF retificadora SEM abatimentos

> Este é o ponto que Sandro precisa analisar com urgência: como corrigir as rubricas sem perder os abatimentos da DCTF.

---

## Checklist de evidências

- [ ] `01_S1010_rubrica_566.png` — Rubrica 566: incidência IRRF 11→41
- [ ] `02_S1010_rubrica_596.png` — Rubrica 596: incidência IRRF 12→42
- [ ] `03_S1210_pagamentos_jan2025.png` — Pagamentos CPF piloto Jan/2025
- [ ] `04_S5001_totalizador_inss_jan2025.png` — Totalizador INSS
- [ ] `05_S5002_totalizador_irrf_jan2025.png` — ⭐ Totalizador IRRF (CRÍTICO)
- [ ] `06_S5003_totalizador_fgts_jan2025.png` — Totalizador FGTS
- [ ] `07_receita_rendimentos.png` — Rendimentos na Receita Federal
- [ ] `08a_ecac_dctf_original_jan2025.png` — ⚠️ DCTF original COM abatimentos
- [ ] `08b_ecac_dctf_retificadora_jan2025.png` — ⚠️ DCTF retificadora SEM abatimentos

---

## Insights da Reunião (06/04/2026)

### Decisões confirmadas:

1. **S-1200 NÃO RETIFICAR** — Ana: "eu não gostaria de mexer nessa". Pode alterar valores de recolhimento (a maior ou a menor)
2. **Pipeline simplificado** — Apenas S-1210 (pagamentos). Confirmado por Ana que na Objetiva também fez só S-1210
3. **Rubrica exemplo** — 566 e 596 afetam TODOS os trabalhadores (ninguém fica de fora)

### Problema crítico descoberto:

- A correção do eSocial gerou DCTF retificadora no e-CAC
- Na retificadora, os abatimentos (créditos/deduções) desaparecem
- **Sandro precisa dizer como proceder** antes de escalar para os 20.000 CPFs

### Observações técnicas:

- eSocial web fica muito lento nessa semana (fechamento de folha, muita gente usando)
- Certificado digital pode travar no loading ao fazer login (tentativa repetida funciona)
- S-5002 funciona normalmente no portal web (bloqueio é só via API dias 1-7)

---

## Após capturar os prints

Salvar todos os arquivos em: `docs/prontuario_sandro/`

**Quando voltar, me diga "prints prontos" e eu monto o prontuário completo.**
