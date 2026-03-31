# PESQUISA — Extinção da DIRF e Transição para o eSocial (2025-2026)

> Pesquisa realizada via web em jul/2026 — Fontes: Receita Federal, Proform, NetCPA, EasyDots, Fortes Tecnologia

---

## 1. O que era a DIRF

A **Declaração do Imposto sobre a Renda Retido na Fonte (DIRF)** era uma obrigação acessória anual apresentada à Receita Federal pela fonte pagadora (empresa). Continha:

- Rendimentos pagos a cada beneficiário (empregados, autônomos, etc.)
- Imposto de renda retido na fonte (IRRF)
- Deduções: INSS (PSO), previdência complementar, pensão alimentícia, dependentes
- Rendimentos isentos e não tributáveis
- Informações sobre plano de saúde coletivo

### Uso principal

- **Para a Receita:** Cruzar dados com a Declaração de Ajuste Anual (DIRPF) dos contribuintes
- **Para o trabalhador:** O Informe de Rendimentos (derivado da DIRF) era a base para preencher o IRPF
- **Para a empresa:** Podia fazer ajustes manuais antes do envio da DIRF

---

## 2. Extinção da DIRF

### Cronologia

| Data       | Marco                                                                           |
| ---------- | ------------------------------------------------------------------------------- |
| Jun/2023   | IN RFB nº 2.096/2022 — Publicação da norma de extinção                          |
| Jan/2024   | Última DIRF referente ao ano-calendário 2023                                    |
| Jan/2025   | **DIRF oficialmente extinta** — Não existe mais DIRF referente a 2024 em diante |
| Desde 2025 | Dados de IR passam a vir **exclusivamente** do eSocial (S-1210 + EFD-Reinf)     |

### O que mudou

**ANTES (com DIRF):**

```
Empresa calcula folha → Envia eSocial (S-1200, S-1210) → Fim do ano:
gera DIRF separadamente → Pode ajustar dados na DIRF → Envia DIRF à RFB
```

**DEPOIS (sem DIRF):**

```
Empresa calcula folha → Envia eSocial (S-1200, S-1210) → eSocial gera S-5002 →
Dados vão AUTOMATICAMENTE para a RFB → Não há etapa de ajuste manual
```

### A mudança crítica

> **"Com a extinção da DIRF, a responsabilidade de informar corretamente os dados tributários passou a ser inteiramente do eSocial. Não existe mais uma etapa intermediária onde a empresa pode revisar e corrigir dados antes de enviá-los à Receita."** — Fortes Tecnologia

---

## 3. Onde os Dados da DIRF Estão Agora

### Dados que saíram da DIRF e foram para o eSocial

| Dado antigo da DIRF                 | Onde está agora no eSocial | Campo/Código                |
| ----------------------------------- | -------------------------- | --------------------------- |
| Rendimentos tributáveis             | S-1210 via S-1200          | codIncIRRF = 11, 12, 13, 14 |
| IRRF retido                         | S-1210 via S-1200          | codIncIRRF = 31, 32, 33, 34 |
| Dedução INSS (PSO)                  | S-1210 via S-1200          | codIncIRRF = 41, 42, 43     |
| Dedução prev. complementar          | S-1210 via S-1200          | codIncIRRF = 46, 47, 48     |
| Pensão alimentícia                  | S-1210 via S-1200          | codIncIRRF = 51, 52, 53, 54 |
| Rendimentos isentos                 | S-1210 via S-1200          | codIncIRRF = 70-79          |
| Plano de saúde coletivo             | S-1210 via S-1200          | codIncIRRF = 67             |
| Dependentes                         | S-2200 / S-2205            | Dados cadastrais            |
| Compensação ano-calendário anterior | S-1210 (InfoIRComplem)     | Grupo específico de jan     |

### Dados que saíram da DIRF e foram para a EFD-Reinf

| Dado                                  | Onde está agora           |
| ------------------------------------- | ------------------------- |
| Serviços tomados (PJ)                 | EFD-Reinf (R-4020)        |
| Aluguéis pagos a PF/PJ                | EFD-Reinf (R-4010/R-4020) |
| Comissões e corretagens               | EFD-Reinf (R-4010/R-4020) |
| Rendimentos de aplicações financeiras | EFD-Reinf (R-4010/R-4020) |

---

## 4. Impacto Direto na APPA

### O problema antes da extinção da DIRF

Mesmo com rubricas configuradas incorretamente no eSocial:

- A empresa podia **ajustar os valores manualmente na DIRF** antes de enviar à Receita
- O Informe de Rendimentos era gerado a partir da DIRF (manual), não do eSocial (automático)
- Existia uma "rede de segurança" para corrigir erros de parametrização

### O problema depois da extinção da DIRF (2025+)

- **Não existe mais rede de segurança**
- Se o `codIncIRRF` da rubrica está errado no S-1010 → o dado errado vai direto para a Receita
- O S-5002 totaliza automaticamente com base no codIncIRRF
- O Informe de Rendimentos agora é gerado **automaticamente** pelo eSocial
- **16-20 mil funcionários da APPA com deduções zeradas** → todos com Informe de Rendimentos incompleto
- Funcionários que declararam IRPF com dados corretos (que tinham da DIRF do ano anterior ou dos holerites) vs. o que a Receita tem (do eSocial) → **divergência → malha fina**

### A urgência

- Ano-calendário 2024: **última DIRF** — dados de IRRF vieram da DIRF (manual)
- Ano-calendário 2025: **primeira vez sem DIRF** — dados de IRRF vêm exclusivamente do eSocial
- Se as rubricas da APPA estão erradas desde antes de 2025, os dados de 2025 serão os primeiros a causar problemas massivos
- A época da declaração de IRPF (mar-mai/2026) é quando os funcionários descobrirão que seus Informes estão incompletos

---

## 5. Mudanças na Tabela 03 (Natureza das Rubricas) para 2026

### Novos códigos previstos para 01/01/2026

A Tabela 03 do eSocial (Natureza das Rubricas) ganhou novos códigos em 2026 para cobrir dados que antes estavam na DIRF:

| Código | Descrição                                               | Por quê                                         |
| ------ | ------------------------------------------------------- | ----------------------------------------------- |
| 1015   | Abono anual (13º salário de benefícios previdenciários) | Separar do 13º salário comum para fins de IRRF  |
| 1799   | Outros rendimentos do trabalho                          | Catch-all para rendimentos que não se enquadram |
| 1811   | Rendimento de plano de previdência complementar         | Especificar origem para fins de tributação      |

### Novos codIncIRRF para 2026

| Código | Descrição                                                          | Vigência   |
| ------ | ------------------------------------------------------------------ | ---------- |
| 15     | Rendimento tributável — Rendimentos recebidos acumuladamente (RRA) | 01/01/2026 |
| 16     | Rendimento tributável — Outros rendimentos não classificados       | 01/01/2026 |
| 35     | Retenção de IRRF — RRA (reintroduzido)                             | 01/01/2026 |

### Implicação para a APPA

- A cada atualização da Tabela 03 ou Tabela 21, as rubricas podem precisar de revisão
- O sistema Easy e-Social precisa acompanhar essas mudanças
- Os 91 registros com "natureza duvidosa" podem estar usando códigos que foram atualizados
- As 2 naturezas expiradas detectadas pelo Easy e-Social já são consequência dessas mudanças

---

## 6. O Novo Informe de Rendimentos (Gerado pelo eSocial)

### Como era

- Empresa gerava o Informe de Rendimentos a partir do sistema de folha (GI)
- Podia ajustar antes de entregar ao funcionário
- DIRF e Informe podiam ser "acertados" manualmente

### Como é agora

- O eSocial totaliza via S-5002 e gera os dados de IR automaticamente
- O Informe de Rendimentos é derivado dos dados do eSocial
- **O que está no eSocial É o que a Receita tem**
- Se está errado no eSocial → está errado no Informe → está errado para a Receita
- Não há etapa de "revisão manual" entre a folha e a Receita

### Dados do Informe de Rendimentos (derivados do S-5002)

| Seção do Informe               | Origem no eSocial           |
| ------------------------------ | --------------------------- |
| 1. Rendimentos Tributáveis     | codIncIRRF = 11, 12, 13, 14 |
| 2. Deduções                    |                             |
| 2.1 Previdência oficial (INSS) | codIncIRRF = 41, 42, 43     |
| 2.2 Previdência complementar   | codIncIRRF = 46, 47, 48     |
| 2.3 Pensão alimentícia         | codIncIRRF = 51, 52, 53, 54 |
| 3. Imposto retido              | codIncIRRF = 31, 32, 33, 34 |
| 4. Rendimentos Isentos         | codIncIRRF = 70-79          |
| 5. Plano de saúde              | codIncIRRF = 67             |

**Se verba 566 (INSS desconto) tem codIncIRRF = 9:**

- Seção 2.1 do Informe = R$ 0,00
- 16-20 mil funcionários sem dedução de INSS no Informe de Rendimentos
- **Exatamente o que a Ana reportou**

---

## 7. Resumo do Impacto para a APPA

### Antes da extinção da DIRF (≤ 2024)

- Erro de codIncIRRF podia ser corrigido manualmente na DIRF
- Funcionários recebiam Informes corretos (ou corrigidos)
- Risco fiscal: baixo (existia margem para ajuste)

### Depois da extinção da DIRF (≥ 2025)

- Erro de codIncIRRF vai direto para a Receita Federal
- Funcionários recebem Informes incompletos (gerados pelo eSocial)
- Risco fiscal: **ALTO** (sem margem para ajuste, exceto retificação via eSocial)
- Volume afetado: 16-20 mil funcionários
- Verbas afetadas: verba 566 (INSS), verba 47 (prev. complementar), indenizatórias de rescisão
- Consequência: malha fina em massa, passivo trabalhista potencial

### O que precisa acontecer

1. **S-1010:** Corrigir codIncIRRF de todas as rubricas afetadas (verba 566 → 41, verba 47 → 47, etc.)
2. **S-1210:** Retificar os pagamentos dos períodos afetados para que o S-5002 recalcule
3. **InfoIRComplem:** Para anos anteriores, usar o mecanismo de janeiro
4. **Validação:** Verificar nos totalizadores S-5002 retornados se os dados agora estão corretos

---

## 8. Fontes

1. **Receita Federal** — IN RFB nº 2.096/2022 (extinção da DIRF)
2. **Fortes Tecnologia** — "DIRF extinta: o que muda para empresas em 2025" (08/01/2026)
3. **NetCPA** — "DIRF — Obrigação extinta a partir de 2025"
4. **EasyDots** — "Fim da DIRF: como o eSocial assume a responsabilidade"
5. **Proform** — "Mudanças Tabela 03 e Tabela 21 eSocial 2026"
6. **MGP Consultoria** — "Evento S-5002 — Totalizador de IRRF"
7. **gov.br** — Leiautes do eSocial, versão S-1.3 (cons. NT 06/2026)
