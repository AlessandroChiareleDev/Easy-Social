# CONCLUSÕES — PESQUISA PLANO DE SAÚDE eSocial
**Data: 15 de abril de 2026**

---

## 1. DESCOBERTA CRÍTICA: FAQ 14.4 do eSocial

> **O grupo [planSaude] no S-1210 somente deve ser preenchido quando se tratar de plano de saúde coletivo empresarial contratado pela fonte pagadora.**

### Quando NÃO preencher planSaude:
1. **Plano coletivo por adesão** — quando sindicato/conselho/associação contrata a operadora, **mesmo que o desconto seja feito em folha pela empresa**
2. **Quando existe administradora de benefícios** na relação contratual com a operadora
3. **Autogestão**
4. **Quando a empresa paga 100%** e não desconta nada do trabalhador

### Implicação para APPA:
- Se as rubricas 774 (DESC. ASSIST. MEDICA) e 775 são de **plano por adesão via sindicato**, o planSaude **NÃO deveria ser preenchido**
- Apenas a rubrica 607 (Assistência médica), que é claramente a operadora direta (CNPJ 63554067000198 / regANS 368253), deveria ter planSaude
- **PERGUNTA-CHAVE que Ana precisa responder**: A rubrica 774/775 é plano empresarial ou plano por adesão via sindicato?

---

## 2. DESCOBERTA: FAQ 14.6 — codIncIRRF 67 vs 9

> **Recomenda-se o uso de codIncIRRF=67** para rubricas de plano de saúde, para que o desconto apareça individualizado no tpInfoIR=67 no totalizador S-5002.

### Situação APPA:
- **ZERO ocorrências de codIncIRRF=67** em TODOS os ZIPs disponíveis (Jun-Dez 2025 + Jan-Abr 2025)
- **ZERO tpInfoIR=67** em qualquer S-5002
- APPA usa codIncIRRF=9 (verba transitada na folha de natureza diversa)
- Isso **funciona** (não muda o valor da retenção do IRRF), mas **não é o recomendado**
- O valor de plano de saúde fica misturado no tpValorIR=7900 em vez de ficar isolado no 67

---

## 3. ANÁLISE DOS 49 CPFs COM ERRO [8] — "planSaude deve ser preenchido"

### Fatos apurados:

| Dado | Resultado |
|------|-----------|
| Total CPFs com erro | 49 |
| Têm S-1210 original no ZIP | 49/49 (100%) |
| planSaude no original | 1/49 (apenas CPF 12853157660, vlr=280.01) |
| Têm S-1200 no ZIP de Janeiro | 6/49 (12%) |
| Health rubricas no S-1200 | 0/6 |
| Têm S-2299 (desligamento) | 39/49 (80%) |
| Health rubricas no S-2299 | 0/39 |
| planSaude no S-2299 | 0/39 |
| CPFs sem S-1200 nem S-2299 | 4 |

### Perfil dos 49 CPFs:
- **39 são DESLIGADOS** (demitidos em Jan/2025) — S-1210 referencia demonstrativos do S-2299
- **6 têm S-1200** mas sem qualquer rubrica de saúde
- **4 restantes**: sem S-1200 e sem S-2299 (provavelmente S-1200 de dez/2024)
- **Nenhum tem rubricas de saúde** em qualquer evento no ZIP

### Hipóteses para o erro:
1. **Regras de validação do eSocial mudaram** entre o envio original (Feb/2025) e nossa retificação (Mar/2026) — a regra [8] pode ter sido implementada depois
2. **Referência cruzada com S-1200 de dezembro/2024** (que não temos no ZIP) — talvez esses CPFs tivessem rubricas de saúde no S-1200 de dezembro
3. **A retificação herda obrigatoriedades** que o original não tinha por conta de novas NTs

### Ação necessária:
- Para o CPF 12853157660: incluir planSaude com vlrSaudeTit=280.01 (valor do original)
- Para os outros 48: **precisamos do download de dezembro/2024** para verificar se tinham rubricas de saúde no S-1200 de dezembro. **Alternativa**: perguntar à Ana se esses 49 CPFs deveriam ter planSaude
- **NÃO tentar enviar sem planSaude** — o eSocial rejeita

---

## 4. PANORAMA COMPLETO DOS ENVIOS (Pipeline DB)

| Run | Período | Status | Total | OK | Erro | S-1298 | S-1299 |
|-----|---------|--------|-------|-----|------|--------|--------|
| 1 | 2025-09 | parcial | 7.771 | 7.771 | 0 | ✅ | ✅ |
| 3 | 2025-01 | parcial | 11.290 | 8.768 | 2.522 | ✅ | ✅ |
| 4 | 2025-02 | parcial | 10.800 | 9.600 | 1.166 | ✅ | ❌ |
| 5 | 2025-01 | parcial | 1.565 | 1.565 | 0 | - | - |
| 6 | 2025-01 | parcial | 908 | 786 | 122 | - | - |
| 7 | 2025-01 | parcial | 121 | 7 | 114 | - | - |
| 8 | 2025-01 | parcial | 114 | 0 | 114 | - | - |

### Janeiro 2025 — Erros residuais (164 CPFs):
- **100 duplicidade** [106] — CPFs com S-1210 duplicado no eSocial (provável dez/2024 + jan/2025)
- **49 planSaude** [8] — Investigados acima
- **14 em processamento** — Lote ainda pendente
- **1 pensão alimentícia** [8] — Erro de campo obrigatório

### Setembro 2025 — Referência OK:
- 7.771 CPFs enviados, **ZERO erros**
- **ZERO planSaude** em qualquer S-1210 (nem original nem retificação)
- 1.014 CPFs com rubricas de saúde no S-1200 (774:511, 775:770, 516:183)
- **ZERO tpInfoIR=67** no S-5002

---

## 5. MAPA planSaude CORRETO vs ERRADO

### Mapa ERRADO (atual, salvo em JSON):
- 10.443 CPFs com valores inflados
- Bug: somava TODAS rubricas com nat_rubr LIKE '92%' (99 rubricas!) e dobrava por original+retif
- Exemplo: Waldelice (CPF ...588) → mapa: 367.30 vs correto: 56.66 (rubrica 774)

### Mapa CORRETO (script _rebuild_plansaude_correct.py):
- **1.578 CPFs** (somente rubricas 607/774/775/516/606)
- Prioridade: 607 > 774 > 775 > 516 > 606
- Distribuição: 774=849, 775=482, 516=229, 607=18
- **NÃO SALVO AINDA** (precisa rodar com --save)

### QUESTÃO ABERTA — Sindicato vs Operadora:
Se 774/775 forem **plano por adesão via sindicato** (FAQ 14.4), então:
- Apenas **18 CPFs** (rubrica 607) deveriam ter planSaude
- Os outros 1.560 CPFs NÃO deveriam ter
- Setembro comprova: 0 planSaude para 1.014 CPFs com rubricas de saúde

Se 774/775 forem **plano coletivo empresarial**, então:
- Todos os 1.578 CPFs deveriam ter planSaude
- Mas setembro contradiz isso (0 planSaude com rubricas de saúde)

### Evidências que apontam para "sindicato":
1. **Setembro/2025**: Zero planSaude com 1.014 CPFs tendo rubricas de saúde → Bahia nunca incluiu planSaude para 774/775
2. **Janeiro original**: Apenas 19 CPFs com planSaude (todos rubrica 607) de 1.578 com rubricas de saúde
3. **Julho original**: 34 CPFs com planSaude (15 com rubrica 774 matching, 19 sem) → mesmo em julho, poucos tinham planSaude
4. **FAQ 14.4**: Plano por adesão via sindicato NÃO deve ter planSaude no S-1210

### CONCLUSÃO PROVÁVEL:
> **As rubricas 774/775/516 são de plano coletivo por adesão (sindicato). Apenas a rubrica 607 é de plano coletivo empresarial (operadora direta).** Portanto, planSaude no S-1210 deveria existir APENAS para os ~18 CPFs com rubrica 607.

---

## 6. IMPACTO NOS ENVIOS JÁ REALIZADOS

### O que já foi enviado com valores ERRADOS:
- **Run 3** (Jan): 8.768 CPFs aceitos — MUITOS com planSaude com valores inflados
- **Run 5** (Jan fix): 1.565 CPFs aceitos — mesmos valores errados
- **Run 6** (Jan fix): 786 CPFs aceitos

### O que precisa ser corrigido:
1. **TODOS os 11.127 S-1210 aceitos** de janeiro precisam ser retificados novamente
2. Para CPFs com rubrica 607: incluir planSaude com valor CORRETO
3. Para CPFs com rubrica 774/775/516: **REMOVER planSaude** (se confirmado que é sindicato)
4. Para CPFs sem rubrica de saúde: enviar S-1210 SEM planSaude (como o original)

### Fevereiro:
- Run 4: 9.600 CPFs aceitos, 1.166 erros — **mesmos problemas** com mapa errado
- S-1299 NÃO fechado ainda

---

## 7. LISTA DE AÇÕES PENDENTES

### Depende de Ana:
- [ ] **CONFIRMAR**: Rubrica 774/775 é plano sindicato ou empresarial?
- [ ] **ENVIAR**: Lista dos CPFs de dezembro/2024 com plano de saúde (se houver)
- [ ] **CONFIRMAR**: Quais CPFs realmente devem ter planSaude no S-1210?

### Podemos fazer AGORA:
- [ ] Salvar mapa correto (somente 607 → 18 CPFs com planSaude)
- [ ] OU salvar mapa com todos 1.578 CPFs (se 774/775 forem empresariais)
- [ ] Cruzar dados de todos os meses disponíveis (Jun-Dez + Jan-Abr)
- [ ] Buscar download de dezembro/2024 (se disponível, para investigar os 49 CPFs + 100 duplicidade)

### Sequência para resolver Janeiro:
1. Confirmar tipo de plano (sindicato vs empresarial) → define o mapa
2. Salvar mapa correto
3. Retificar TODOS 11.127+ S-1210 aceitos com valores corretos
4. Resolver 49 planSaude (depende de dez/2024 ou info da Ana)
5. Resolver 100 duplicidade (precisa dez/2024 e fev/2025 downloads)
6. Fechar período com S-1299

---

## 8. DADOS DE REFERÊNCIA

### Operadora no S-1210:
- **cnpjOper**: 63554067000198 (CNPJ APPA)
- **regANS**: 368253

### Rubricas de saúde confirmadas:
| Rubrica | Descrição | Confirmado por |
|---------|-----------|----------------|
| 607 | Assistência médica | Ana (call 15/04) |
| 774 | DESC. ASSIST. MEDICA | Ana (call 15/04) |
| 775 | (saúde, específica APPA) | Ana (call 15/04) |
| 516 | DESC. ASSIST. ODONTO DEPENDENTE | Ana (call 15/04) |

### Rubricas que NÃO são saúde:
| Rubrica | Descrição | 
|---------|-----------|
| 776 | DESC. VALE ALIMENTACAO (nat=9243) |
| 773 | Desconto vale-refeição |
| Qualquer outra | nat_rubr LIKE '92%' mas fora da lista acima |

### ZIPs disponíveis:
Jun, Jul, Set, Out, Nov, Dez/2025 + Jan, Fev, Mar, Abr/2025
**NÃO disponível**: Dezembro/2024 (crítico para os 49 CPFs e 100 duplicidade)

---

*Documento gerado automaticamente com base em pesquisa do FAQ oficial do eSocial (gov.br), análise de 10 ZIPs do eSocial, e dados do pipeline local.*
