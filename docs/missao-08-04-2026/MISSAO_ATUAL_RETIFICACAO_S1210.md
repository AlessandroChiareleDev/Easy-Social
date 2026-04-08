# MISSÃO ATUAL — Retificação em Massa S-1210 (APPA)

> **Data:** 08/04/2026  
> **Empresa:** APPA (CNPJ 05.969.071/0001-10)  
> **Problema central:** Deduções de IR zerando no eSocial (~20 mil pessoas precisam de declaração de IR correta)  
> **Última atualização com base em:** pesquisas web, documentação oficial gov.br, reuniões com Ana/Dra. Cintia, análise de XMLs

---

## 1. Contexto do Problema

O sistema da GI (Sandro) transmitiu eventos S-1210 com deduções incompletas — INSS (verba 566), indenizatórias de rescisão e outras verbas estão **zeradas** no portal. A DIRF acabou em 2025 e agora o eSocial é a fonte oficial para IR retido na fonte. Se os S-1210 não forem corrigidos, ~20.000 pessoas terão declaração de IR incorreta.

### O que está errado

| Campo no S-1210 | Esperado | Recebido |
|---|---|---|
| Dedução INSS (verba 566) | Valor real descontado | 0,00 |
| Verbas indenizatórias rescisão | Valores reais | 0,00 |
| Verba 47 | Valor real | Possivelmente incorreto |

### O que NÃO está errado

- **S-1200 (Remuneração INSS)**: Está correto. Os cálculos de INSS e contribuição patronal estão OK.
- **S-1020 (Lotações tributárias)**: As lotações com suspensão judicial de terceiros (via `codTercSusp` + `procJudTerceiro`) estão corretas. O sistema GI cria lotações com prefixo "E" — isso é só convenção de nome, o que importa são os campos `codTercSusp` no S-1020 que vinculam ao S-1070 (processo judicial).

---

## 2. Decisão Validada: Retificar SOMENTE o S-1210

### Confirmado por pesquisa na documentação oficial

A retificação do S-1210 é um procedimento padrão no eSocial:

1. **O S-1210 é evento de PAGAMENTO** — informa o que foi pago, data, IR retido. NÃO afeta cálculos de INSS/FGTS.
2. **A retificação do S-1210 NÃO altera o S-1200** — são eventos independentes. O S-1200 carrega a remuneração e lotação tributária; o S-1210 carrega pagamento e IR.
3. **Os créditos de suspensão de terceiros vivem no S-1020** — nos campos `codTercSusp` e `procJudTerceiro`. Retificar S-1210 não toca nesses campos.
4. **O S-5011 (totalizador patronal) é calculado a partir do S-1200 + S-1020** — NÃO do S-1210. Retificar S-1210 não impacta S-5011.
5. **O S-5002 (totalizador IR) É impactado pelo S-1210** — e esse é exatamente o objetivo: corrigir os valores de IR.

### Regra inviolável

> **NUNCA enviar retificação de S-1200.** O S-1200 carrega a lotação tributária (codLotacao) que vincula à suspensão judicial via S-1020. Qualquer alteração no S-1200 pode reprocessar o S-5011 e afetar os créditos de ~R$4.2M em suspensões.

---

## 3. Fluxo Técnico da Retificação

### Regra oficial do eSocial (REGRA_PAGTO_IND_RETIFICACAO)

> **"Se o evento a ser retificado for relativo a um período de apuração já encerrado, a retificação somente deve ser aceita se for enviada após o evento de Reabertura (S-1298)."**

Fonte: [gov.br — Regras eSocial v S-1.2](https://www.gov.br/esocial/pt-br/documentacao-tecnica/leiautes-esocial-v-1-2-versao-s-1-2-nt-05-2024/regras.html)

### Pipeline de 3 passos para cada período

```
Passo 1: S-1298 (Reabertura)
    → Reabre o período que já foi fechado com S-1299
    → Pré-requisito: deve existir S-1299 para o período
    → Grupo SOAP: 3 (periódicos)

Passo 2: S-1210 (Retificação)
    → indRetif = 2 (retificação)
    → nrRecibo = recibo do S-1210 original
    → Mesmo CPF, mesmo período de apuração
    → Conteúdo: dados corrigidos (deduções IR populadas)
    → Grupo SOAP: 3 (periódicos)
    → Máximo: 50 eventos por lote

Passo 3: S-1299 (Fechamento)
    → Fecha novamente o período
    → Gera novo S-5002 (totalizador IR) com dados corrigidos
    → Grupo SOAP: 3 (periódicos)
```

### IMPORTANTE: S-1200 NÃO faz parte deste fluxo

O pipeline anterior (pipeline_correcao.py) tinha 5 passos incluindo S-1200. **O novo fluxo tem 3 passos — sem S-1200 em nenhum lugar.**

---

## 4. Dados Disponíveis (estado do banco)

| Evento | Qtd | CPFs únicos | Período | Com nr_recibo |
|--------|-----|-------------|---------|---------------|
| S-1210 | 8.421 | 8.414 | 2026-02 | 8.421 (100%) |
| S-5002 | 8.424 | — | 2026-02 | — |
| S-5001 | 9.887 | — | 2026-02 | — |
| S-1200 | 9.066 | — | 2026-02 | — |
| S-1010 | 195 | — | — | — |
| S-5011 | 2 | — | — | — |

### Gap crítico: XML original do S-1210

O banco armazena apenas um **resumo** em `dados_json`:

```json
{
  "tpCR": "056107",
  "vrLiq": "1323",
  "dtPgto": "2026-02-06",
  "tpPgto": "1",
  "cdResposta": "201",
  "descResposta": "Sucesso."
}
```

Para retificar, precisamos do **XML completo** (com todos os `infoPgto`, `ideDmDev`, deduções, etc.). Soluções:

1. **Download do eSocial via API**: `solicitar_download_por_nrrecibo()` — já implementado no `esocial_client.py`
2. **Parser completo**: `xml_payload_parser.extrair_s1210()` — já implementado

---

## 5. Preservação dos Créditos — Análise de Segurança

### O que são os créditos em risco

A APPA tem processos judiciais que suspendem contribuições a terceiros (Sistema S). Isso está registrado no eSocial como:

```
S-1070 (Processo Judicial)
  └── nrProc = número do processo
  
S-1020 (Lotação Tributária)  
  └── codTercSusp = código dos terceiros suspensos
  └── procJudTerceiro → referencia o S-1070
```

O S-5011 (totalizador de contribuições patronais) calcula as suspensões baseado nesses campos. No período 2024-12, as suspensões somavam ~R$4.27M.

### Por que a retificação do S-1210 NÃO afeta esses créditos

| Componente | Depende de | S-1210 altera? |
|---|---|---|
| S-5011 (patronal + terceiros) | S-1200 + S-1020 | **NÃO** |
| S-5002 (IR) | S-1210 | **SIM** (objetivo) |
| S-5001 (INSS trabalhador) | S-1200 | **NÃO** |
| DCTFWeb (crédito suspensão) | S-5011 | **NÃO** (indireto) |

O S-1210 alimenta SOMENTE o totalizador S-5002 (IR retido na fonte). Os totalizadores S-5011 e S-5001, que alimentam a DCTFWeb com os valores de contribuição patronal e suspensão, vêm do S-1200 e S-1020 — que **não estamos tocando**.

### Evidência documental

> "É possível retificar múltiplas competências somente para os eventos S-1210 e S-1299 (isoladamente ou em conjunto). O evento S-1200 não permite retificação em intervalo de competências."  
> — Documentação Questor (referência a regras oficiais do eSocial)

> "O sistema é responsável por reabrir competências, excluir eventos relacionados, gerar novas inclusões e realizar o fechamento."  
> — Documentação Questor sobre retificação automatizada

---

## 6. Riscos Mapeados

### Risco 1 — DCTFWeb automática

**Cenário:** Ao fechar período com S-1299 após retificação, o eSocial gera novos totalizadores. Se uma retificadora da DCTFWeb for gerada automaticamente, ela usará os novos totalizadores. Se por alguma falha o S-5011 for recalculado (não deveria), os créditos de suspensão poderiam ficar diferentes.

**Mitigação:**
- Retificamos SOMENTE S-1210 (não toca S-1200/S-1020)
- Validamos S-5011 ANTES e DEPOIS do processo via snapshot
- Monitoramos DCTFWeb no e-CAC após cada batch

### Risco 2 — nrRecibo inválido

**Cenário:** Se o evento original já foi retificado/excluído, o nrRecibo não será mais válido.

**Mitigação:**
- Regra eSocial: nrRecibo deve referir-se a evento válido (não excluído nem retificado)
- Download prévio do S-1210 atual confirma qual é o recibo vigente
- Sistema de tracking (`envio_tracker.py`) registra cada tentativa

### Risco 3 — Processamento incompleto

**Cenário:** Abrir período (S-1298), enviar retificações, mas NÃO fechar (S-1299) — deixando o período aberto indefinidamente.

**Mitigação:**
- Pipeline atômico: S-1298 → S-1210(s) → S-1299 em sequência
- Timeout e retry automáticos
- Se S-1299 falhar, o período fica aberto (recuperável com novo S-1299)

### Risco 4 — Rate limits eSocial

**Cenário:** Homologação tem limites mais restritivos. Produção restrita limita 1.000 vínculos por empregador.

**Mitigação:**
- Testar com 1-5 CPFs primeiro
- Batch com delay entre lotes
- Tracking de erro 405 ("limite esgotado") já implementado

---

## 7. Próximos Passos Concretos

### FASE A — Preparação (código)

| # | Tarefa | Status |
|---|--------|--------|
| A1 | Modificar `pipeline_correcao.py`: remover S-1200 inteiramente, pipeline vira 3 passos | ❌ Pendente |
| A2 | Script de download em massa: baixar XMLs S-1210 originais com `solicitar_download_por_nrrecibo()` | ❌ Pendente |
| A3 | Script de comparação: extrair deduções IR do XML atual vs esperado (identificar o que falta) | ❌ Pendente |

### FASE B — Teste piloto (1 CPF, homologação)

| # | Tarefa | Status |
|---|--------|--------|
| B1 | Escolher CPF piloto (verbas 566/47) | ❌ Pendente |
| B2 | Capturar S-5002 "antes" (snapshot) | ❌ Pendente |
| B3 | Executar pipeline: S-1298 → S-1210(retif) → S-1299 | ❌ Pendente |
| B4 | Capturar S-5002 "depois" e comparar | ❌ Pendente |
| B5 | Verificar S-5011 inalterado (créditos preservados) | ❌ Pendente |

### FASE C — Validação com Sandro/Cynthia

| # | Tarefa | Status |
|---|--------|--------|
| C1 | Montar prontuário do CPF piloto (antes/depois) | ❌ Pendente |
| C2 | Enviar para Sandro avaliar impacto nos créditos | ❌ Pendente |
| C3 | Aprovar com Dra. Cintia para seguir em produção | ❌ Pendente |

### FASE D — Execução em escala (produção)

| # | Tarefa | Status |
|---|--------|--------|
| D1 | Batch de 5-10 CPFs em homologação → validar padrão | ❌ Pendente |
| D2 | Janeiro inteiro (~8.400 CPFs) em produção | ❌ Pendente |
| D3 | Verificação cruzada DCTFWeb no e-CAC | ❌ Pendente |
| D4 | Escalar para 12 meses se aprovado | ❌ Pendente |

---

## 8. Ferramentas Já Disponíveis no Sistema

| Ferramenta | Arquivo | Função |
|---|---|---|
| Gerador XML S-1210 | `xml_s1210.py` | `gerar_retificacao()` com indRetif=2 + nrRecibo |
| Gerador XML S-1298 | `xml_s1298.py` | Reabertura de período (máx 50/lote) |
| Gerador XML S-1299 | `xml_s1299.py` | Fechamento de período (máx 50/lote) |
| Download de eventos | `esocial_client.py` | `solicitar_download_por_nrrecibo()` |
| Parser S-1210 | `xml_payload_parser.py` | `extrair_s1210()` + `extrair_s1210_ir_complem()` |
| Snapshot S-5002 | `pipeline_audit_routes.py` | Pre/post comparação automática |
| Comparação totalizadores | `esocial_routes.py` | `/totalizadores/comparar/{cpf}/{per_apur}` |
| Tracking de envios | `envio_tracker.py` | Registra cada envio com status, protocolo, recibo |
| Pipeline (precisa ajuste) | `pipeline_correcao.py` | Orquestrador — PRECISA remover S-1200 |
