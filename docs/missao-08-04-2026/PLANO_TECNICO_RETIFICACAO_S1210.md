# PLANO TÉCNICO — Pipeline de Retificação S-1210

> **Data:** 08/04/2026  
> **Arquivo técnico de referência para implementação**

---

## 1. Arquitetura do Pipeline (Novo — 3 Passos)

### Pipeline ANTIGO (5 passos) ← OBSOLETO

```
S-1010 → S-1298 → S-1200 → S-1210 → S-1299
  ↑                  ↑
  |                  |
  Opcional       <<<< REMOVER COMPLETAMENTE >>>>
```

### Pipeline NOVO (3 passos)

```
┌──────────────────────────────────────────────────────┐
│     S-1298 (Reabertura)                              │
│     → Requer: período fechado (S-1299 existente)     │
│     → Resultado: período reaberto                    │
│     → 1 evento por período/empresa                   │
└──────────────────┬───────────────────────────────────┘
                   │
┌──────────────────▼───────────────────────────────────┐
│     S-1210 (Retificação) × N CPFs                    │
│     → indRetif = 2                                   │
│     → nrRecibo = recibo do S-1210 vigente            │
│     → Mesmo CPF + mesmo perApur                      │
│     → Lotes de 50 eventos (máximo eSocial)           │
│     → Grupo SOAP: 3 (periódicos)                     │
└──────────────────┬───────────────────────────────────┘
                   │
┌──────────────────▼───────────────────────────────────┐
│     S-1299 (Fechamento)                              │
│     → Fecha o período                                │
│     → Dispara geração de novos totalizadores         │
│     → S-5002 atualizado com IR corrigido             │
└──────────────────────────────────────────────────────┘
```

### Observação sobre S-1010

O S-1010 (correção de rubricas) pode ser necessário como **pré-requisito** se as incidências IRRF das rubricas estiverem erradas no cadastro do eSocial. Mas ele é executado **separadamente**, antes de iniciar o pipeline de retificação — não faz parte do fluxo de retificação em si.

---

## 2. Fluxo de Dados Detalhado

### Etapa 0 — Download do XML original (pré-requisito)

```python
# Para cada CPF, baixar o S-1210 vigente do eSocial
result = ESocialClient.solicitar_download_por_nrrecibo(
    nr_recibos=[nr_recibo_s1210],  # do explorador_eventos
    pfx_data=cert_bytes,
    password=cert_password,
    empregador={"tpInsc": 1, "nrInsc": "05969071"},
    producao=False  # homologação primeiro
)
# result["arquivos"] contém os XMLs completos
```

**Por que precisamos disso:** O `dados_json` no banco tem apenas resumo (dtPgto, vrLiq, tpCR). O S-1210 completo tem os `infoPgto[]` com cada demonstrativo, rubricas, e as deduções de IR que precisamos corrigir.

### Etapa 0.5 — Parsing e Análise

```python
# Extrair estrutura completa do S-1210 original
dados = xml_payload_parser.extrair_s1210(xml_bytes)
# dados = {
#   "dtPgto": "2026-02-06",
#   "tpPgto": "1",
#   "infoPgto": [{
#     "ideDmDev": "10711955",
#     ...
#   }],
#   "infoIRComplem": {  # ← PODE ESTAR AUSENTE (o problema!)
#     "infoIRCR": [{
#       "tpCR": "056107",
#       "vrCR": "0.00",  # ← ZERADO!
#       "dedDepen": [...]
#     }]
#   }
# }
```

### Etapa 1 — S-1298 (Reabertura)

```python
from esocial.xml_s1298 import S1298XMLGenerator

xml = S1298XMLGenerator.gerar(
    empregador={"tpInsc": "1", "nrInsc": "05969071"},
    per_apur="2026-02",
    ind_apuracao="1",  # mensal
    proc_emi="1"
)
# Enviar via esocial_client.enviar_lote(xml, grupo="3")
```

### Etapa 2 — S-1210 (Retificação em lotes de 50)

```python
from esocial.xml_s1210 import S1210XMLGenerator

# Para cada CPF:
xml = S1210XMLGenerator.gerar_retificacao(
    empregador={"tpInsc": "1", "nrInsc": "05969071"},
    cpf=cpf_trabalhador,
    per_apur="2026-02",
    nr_recibo=nr_recibo_original,  # do S-1210 vigente
    info_pgto=info_pgto_corrigido,  # com deduções IR populadas
    info_ir_complem=ir_complem_correto  # infoIRComplem com valores reais
)
# Agrupar até 50 XMLs e enviar como lote
```

### Etapa 3 — S-1299 (Fechamento)

```python
from esocial.xml_s1299 import S1299XMLGenerator

xml = S1299XMLGenerator.gerar(
    empregador={"tpInsc": "1", "nrInsc": "05969071"},
    per_apur="2026-02",
    ind_apuracao="1",
    evt_remun="S",   # sim, existem S-1200 no período
    evt_pgtos="S",    # sim, existem S-1210 no período
    evt_com_prod="N",
    evt_contrat_av_np="N",
    evt_info_compl_per="N"
)
```

---

## 3. Modificações Necessárias em pipeline_correcao.py

### O que remover

1. **PipelineRequest model**: Campos `s1200_dm_devs` e `s1200_nr_recibo` — deletar
2. **Passo 3 (S-1200)**: Linhas ~500-555 — deletar inteiramente
3. **Renumeração**: Passo 4 (S-1210) vira Passo 2, Passo 5 (S-1299) vira Passo 3
4. **skip_s1200**: NÃO existe esse conceito — S-1200 não é "skipável", ele não existe no fluxo

### O que adicionar/modificar

1. **Download prévio**: Antes de gerar a retificação, baixar o XML original
2. **Lógica de batch**: Agrupar S-1210 em lotes de 50
3. **Tracking**: Registrar cada lote enviado no `esocial_envios`

---

## 4. Estimativa de Volume e Timing

### Para um mês (2026-02)

| Métrica | Valor |
|---|---|
| CPFs a processar | 8.414 |
| S-1210 a retificar | 8.421 |
| Lotes de S-1210 (50/lote) | ~169 lotes |
| S-1298 (reabertura) | 1 evento |
| S-1299 (fechamento) | 1 evento |
| Total de envios | ~171 lotes |

### Limites do eSocial

| Ambiente | Limite |
|---|---|
| Produção Restrita (homologação) | 1.000 vínculos por empregador, limites mais restritivos |
| Produção | Sem limite documentado de envios/dia, mas recomenda-se batching |
| Por lote | Máximo 50 eventos por lote (validação no XML) |
| Dias 1-7 do mês | **Download/consulta bloqueados** (não envios) |

### Bloqueio dias 1-7

Este bloqueio afeta CONSULTAS e DOWNLOADS — o código no `envio_tracker.py` já trata:
```python
if "dias 1 e 7" in descricao:
    status = "bloqueado"
```

Para ENVIOS de retificação, não há bloqueio documentado nos dias 1-7.

---

## 5. Validação Pós-Retificação

### Comparação S-5002 (IR)

```
ANTES (snapshot):
  totApurMen_vlrRendTrib: 1966.98
  totApurMen_vlrCRMen: 0          ← ZERADO (o problema)
  infoIR tpInfoIR=7900: -92.98

DEPOIS (esperado):
  totApurMen_vlrRendTrib: 1966.98  ← mantém
  totApurMen_vlrCRMen: 92.98       ← IR retido correto
  infoIR tpInfoIR=7900: -92.98     ← mantém
```

### Verificação S-5011 (créditos — NÃO deve mudar)

```
ANTES: vrSuspBcCp00 para lotação E00482-001-01A = 3.264.889,25
DEPOIS: vrSuspBcCp00 para lotação E00482-001-01A = 3.264.889,25  ← IGUAL
```

Se o S-5011 mudar → **PARAR TUDO** e revisar.

---

## 6. Scripts a Criar

### `retificar_s1210_massa.py` — Script principal

```
Responsabilidades:
1. Ler CPFs do explorador_eventos para o período
2. Baixar S-1210 original de cada CPF via download API
3. Parsear e identificar o que está faltando (deduções zeradas)
4. Gerar XML retificado com deduções corretas
5. Agrupar em lotes de 50
6. Enviar: S-1298 → lotes S-1210 → S-1299
7. Registrar tudo no envio_tracker
8. Validar S-5002 antes/depois
```

### `_diagnostico_s1210.py` — Diagnóstico pré-retificação

```
Responsabilidades:
1. Baixar amostra de S-1210 (5-10 CPFs)
2. Analisar quais campos estão zerados
3. Comparar com S-5002 para confirmar inconsistência
4. Gerar relatório: "X CPFs com dedução zerada, Y CPFs OK"
```

### `_snapshot_s5011.py` — Evidência de preservação de créditos

```
Responsabilidades:
1. Baixar S-5011 ANTES da retificação
2. Salvar como JSON (evidência)
3. Após retificação, baixar novamente
4. Comparar: diff deve ser ZERO para campos patronais
```
