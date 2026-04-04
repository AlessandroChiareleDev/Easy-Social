# MAPA COMPLETO — Todos os Problemas e o Caminho para Resolução

**Data:** 02/04/2026  
**Autor:** Xande  
**Fontes:** Call 1 (~25/03), Call 2 (02/04), Respostas Sandro, MISSAO_ATUAL, código existente

---

## PARTE 1 — O PROBLEMA RAIZ (Por que estamos aqui)

```
┌─────────────────────────────────────────────────────────────────────┐
│                                                                     │
│   Rubricas com codIncIRRF = 11 (errado)                             │
│   Deveria ser codIncIRRF = 41 (Previdência Social - dedução IR)     │
│                                                                     │
│   CONSEQUÊNCIA:                                                     │
│   → Dedução de Previdência Social aparece ZERADA na Receita Federal │
│   → DIRF de 16.000-20.000 trabalhadores comprometida               │
│   → Empresas afetadas: APPA, Objetiva (Empresa 500)                 │
│   → Período: Janeiro/2025 até hoje                                  │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### Verbas Críticas Identificadas

| Verba | Nome              | Problema                                        |
| ----- | ----------------- | ----------------------------------------------- |
| **566** | INSS (dedução)  | Zerada no extrator da RF — certeza que precisa fix |
| **47**  | A identificar   | Alta prioridade — impacto no IR                  |
| Verbas indenizatórias de rescisão | Aviso Prévio etc. | Zeradas no eSocial |

---

## PARTE 2 — POR QUE NINGUÉM RESOLVE (Bloqueios)

### Bloqueio 1: Três Sistemas Enviando ao eSocial

```
          ┌──────────┐
          │  eSocial  │ ← Recebe de 3 fontes diferentes
          └────┬──┬──┬┘
               │  │  │
    ┌──────────┘  │  └──────────┐
    │             │             │
┌───▼───┐  ┌─────▼─────┐  ┌───▼───────┐
│  GI   │  │ Programa  │  │ Sistema 3 │
│ (Ana) │  │ do Sandro │  │ (outro?)  │
└───┬───┘  └─────┬─────┘  └───────────┘
    │             │
    │    Sandro envia DEPOIS do GI
    │    → gera NOVO recibo
    │    → GI fica com recibo ANTIGO
    │             │
    ▼             ▼
  GI mostra     eSocial tem
  recibo X      recibo Y
  (desatualizado) (vigente)
```

**Resultado:** Ana tenta retificar pelo GI → BLOQUEIO porque o recibo que o GI conhece já foi substituído pelo Sandro.

### Bloqueio 2: Validador da Ana Removido

- Ana tinha um validador no GI que permitia enviar por cima de eventos existentes
- Quando Sandro assumiu os envios, o validador foi **removido**
- Sem validador → Ana não consegue enviar nada pelo GI
- Precisaria do validador **do Sandro** para operar

### Bloqueio 3: Sandro Recusou Colaborar

- Time pediu apenas listagem de recibos por CPF/evento (poderia ser um Excel)
- Sandro devolveu: "Você daria acesso ao SEU sistema?"
- Marcos não soube explicar o problema técnico do recibo divergente
- Doutora Cíntia não estava presente no momento crítico
- **Decisão: independência total do Sandro**

### Bloqueio 4: Erros Técnicos no GI

| Erro | Descrição |
| ---- | --------- |
| **301** | Conexão com ambiente (APPA) |
| **Recibo** | "O recibo de entrega informado não foi excluído" / "já foi excluído e retificado" |
| **Status 41** | Losango no evento 566 — erro de processamento |
| **Sem certificado** | Objetiva sem certificado digital — impede envios |
| **Nenhum evento** | "Não existe eventos periódicos a ser enviado" ao tentar ajuste complementar |

---

## PARTE 3 — O QUE O SANDRO CONFIRMOU (Fluxo Obrigatório)

### Resposta definitiva: Não basta corrigir S-1010

O Sandro confirmou que a retificação é um pipeline de **5 eventos na ordem exata**:

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                                                                              │
│  FLUXO OBRIGATÓRIO POR CPF × MÊS                                            │
│                                                                              │
│  ① S-1010  ─── Corrigir incidência da rubrica (codIncIRRF: 11 → 41)         │
│       ↓                                                                      │
│  ② S-1298  ─── Reabrir folha do período (perApur = 2025-01, etc.)           │
│       ↓                                                                      │
│  ③ S-1200  ─── Retificar remuneração (mesmo que valores não mudem)          │
│       │        O eSocial REAPLICAR as regras da rubrica corrigida            │
│       │        É AQUI que o INSS passa a abater a base de cálculo do IR      │
│       ↓                                                                      │
│  ④ S-1210  ─── Retificar pagamento (IRRF "ganha vida" para o fisco)         │
│       │        Deve apontar para o demonstrativo do S-1200 correspondente    │
│       ↓                                                                      │
│  ⑤ S-1299  ─── Fechar folha (dispara recálculo dos totalizadores)           │
│       │                                                                      │
│       ├──→ S-5001 (INSS/FGTS — deve ficar IGUAL, erro era só no IR)         │
│       ├──→ S-5002 (IRRF por CPF — AQUI confirma se dedução apareceu)        │
│       └──→ S-5012 (IRRF total — DCTFWeb)                                    │
│                                                                              │
│  ⑥ DCTFWeb retificadora no e-CAC (se houver diferença de imposto)           │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

### Amarrações Críticas

- **S-1210 aponta para S-1200** pelo número do demonstrativo — se mudar o identificador, eSocial rejeita
- **S-1200 e S-1210 são independentes em cálculo** — INSS no S-1200, IRRF no S-1210
- **Para rescisões:** substituir S-1200 por **S-2299** (desligamento), mas mesmo fluxo
- **DCTFWeb:** se imposto diminuiu → crédito (PER/DCOMP); se aumentou → guia complementar com juros

### Validação de Rubricas — Atenção

O S-1210 **não calcula nada sozinho** — ele só referencia. Se verbas aparecem zeradas:
- Para ativos: problema está no **S-1200**
- Para rescisões: problema está no **S-2299**
- Verbas indenizatórias: problema está no **S-1010** (codIncIRRF errado)

---

## PARTE 4 — ESCALA DO PROBLEMA

### Volume Estimado

| Dimensão | Quantidade |
| -------- | ---------- |
| Trabalhadores afetados | ~16.000 - 20.000 |
| Meses a corrigir | 18 (jan/2025 → jun/2026) |
| XMLs por mês (download) | ~51.600 |
| Eventos por pipeline | 5 (S-1010 + S-1298 + S-1200 + S-1210 + S-1299) |
| Retificações totais | até 360.000 eventos (20k × 18 meses) |
| Lote máximo eSocial | 50 eventos por lote |
| Lotes necessários | ~7.200 |
| Limite diário downloads | 12 pedidos/dia, máx 200k eventos/pedido |

### Nota: S-1010 é por rubrica, não por CPF

O S-1010 corrige a rubrica **uma vez** (ex: rubrica 566, codIncIRRF 11→41).  
Mas S-1298/S-1200/S-1210/S-1299 precisam ser enviados **por CPF × mês**.

---

## PARTE 5 — O QUE JÁ EXISTE NO SOFTWARE

### Infraestrutura Reutilizável (100% pronta)

| Módulo | Função | Status |
| ------ | ------ | ------ |
| `xml_signer.py` | Assina XML com certificado A1 (RSA-SHA256) | ✅ Testado |
| `soap_builder.py` | Monta envelope SOAP 1.1 | ✅ Testado |
| `esocial_client.py` | Envia e consulta lotes via mTLS | ✅ Testado (homologação + produção) |
| `certificate_manager.py` | Gerencia certificados A1 (Fernet encrypt) | ✅ Testado |
| `db_config.py` | Config PostgreSQL (Supabase + local) | ✅ Funcionando |

### Gerador XML — Precisa expandir

| O que existe | O que falta |
| ------------ | ----------- |
| `xml_generator.py` — gera S-1010 (inclusão/alteração) | Gerador de **S-1200** (retificação) |
| | Gerador de **S-1210** (retificação) |
| | Gerador de **S-1298** (reabertura de folha) |
| | Gerador de **S-1299** (fechamento de folha) |
| | Gerador de **S-2299** (desligamento — para rescisões) |

### Parser XML — NÃO EXISTE

| O que precisa | Para quê |
| ------------- | -------- |
| `xml_reader.py` — parser massivo de XMLs do download | Extrair CPF, recibo, rubricas, valores |
| Banco `esocial_eventos_xml` | Armazenar dados extraídos |
| Cruzamento recibos GI × eSocial | Identificar divergências |

### Correções de Rubricas (S-1010)

| Status | Quantidade |
| ------ | ---------- |
| Já corrigido (enviado com sucesso) | 11 rubricas |
| Pendentes | 154 rubricas |
| Bloqueadas (natRubr expirado/De-Para) | ~80 rubricas |
| Total no cruzamento_eb | 448 rubricas |

### Bot PyAutoGUI — PAUSADO

- `bot_esocial.py` — 90% pronto, falta calibrar
- Abordagem via mouse/teclado real — lenta e frágil
- **Decisão provável: abandonar bot em favor do envio por webservice**

---

## PARTE 6 — O QUE O SOFTWARE PRECISA SER (Produto Final)

### Visão do Produto

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                         EASY e-SOCIAL — PRODUTO FINAL                        │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐     │
│  │ MÓDULO 1: INGESTÃO DE XMLs                                         │     │
│  │                                                                     │     │
│  │  Upload ZIP → Descompactar → Parsear → Banco de dados              │     │
│  │  Extrai: CPF, recibo, tipo evento, rubricas, valores, período      │     │
│  └─────────────────────────────────────────────────────────────────────┘     │
│                              ↓                                               │
│  ┌─────────────────────────────────────────────────────────────────────┐     │
│  │ MÓDULO 2: DIAGNÓSTICO                                              │     │
│  │                                                                     │     │
│  │  Cruzar dados dos XMLs com rubricas corretas (cruzamento_eb)       │     │
│  │  Detectar: quais CPFs × meses têm incidência errada               │     │
│  │  Confrontar: recibos GI vs eSocial                                  │     │
│  │  Relatório: total de divergências por empresa/mês/rubrica          │     │
│  └─────────────────────────────────────────────────────────────────────┘     │
│                              ↓                                               │
│  ┌─────────────────────────────────────────────────────────────────────┐     │
│  │ MÓDULO 3: CORREÇÃO AUTOMATIZADA                                    │     │
│  │                                                                     │     │
│  │  Para cada CPF × mês com divergência:                               │     │
│  │    ① S-1010 (corrigir rubrica — se ainda não corrigida)             │     │
│  │    ② S-1298 (reabrir folha)                                         │     │
│  │    ③ S-1200 (retificar remuneração)                                 │     │
│  │    ④ S-1210 (retificar pagamento)                                   │     │
│  │    ⑤ S-1299 (fechar folha)                                         │     │
│  │                                                                     │     │
│  │  Enviar: lotes de 50, throttle, retry, log completo                │     │
│  └─────────────────────────────────────────────────────────────────────┘     │
│                              ↓                                               │
│  ┌─────────────────────────────────────────────────────────────────────┐     │
│  │ MÓDULO 4: VALIDAÇÃO                                                │     │
│  │                                                                     │     │
│  │  Conferir totalizadores: S-5001, S-5002, S-5012                    │     │
│  │  Verificar DCTFWeb (manual no e-CAC)                                │     │
│  │  Dashboard: progresso por empresa/mês/CPF                           │     │
│  └─────────────────────────────────────────────────────────────────────┘     │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## PARTE 7 — GERADORES XML QUE FALTAM (O QUE CONSTRUIR)

### 7.1 Gerador S-1298 (Reabertura de Folha)

```xml
<eSocial xmlns="http://www.esocial.gov.br/schema/evt/evtReaworb/v_S_01_03_00">
  <evtReaworb Id="ID...">
    <ideEvento>
      <indApuracao>1</indApuracao>       <!-- 1=mensal, 2=13º -->
      <perApur>2025-01</perApur>         <!-- Mês a reabrir -->
      <tpAmb>1</tpAmb>                   <!-- 1=produção -->
      <procEmi>1</procEmi>
      <verProc>EasySocial_1.0</verProc>
    </ideEvento>
    <ideEmpregador>
      <tpInsc>1</tpInsc>
      <nrInsc>XXXXXXXX</nrInsc>
    </ideEmpregador>
  </evtReaworb>
</eSocial>
```

### 7.2 Gerador S-1200 (Retificação de Remuneração)

Campos-chave:
- `indRetif=2` + `nrRecibo` do S-1200 original (obtido dos XMLs do download)
- `cpfTrab` — CPF do trabalhador
- `dmDev` — demonstrativo com todas as rubricas (mesmos valores, rubrica agora com incidência corrigida)
- O eSocial reaplicará as regras do S-1010 corrigido

### 7.3 Gerador S-1210 (Retificação de Pagamento)

Campos-chave:
- `indRetif=2` + `nrRecibo` do S-1210 original
- `cpfBenef` — CPF do beneficiário
- `ideDmDev` — deve apontar para o demonstrativo do S-1200 correspondente
- Mesmos valores, mas agora com base de cálculo IRRF atualizada

### 7.4 Gerador S-1299 (Fechamento de Folha)

```xml
<eSocial xmlns="http://www.esocial.gov.br/schema/evt/evtFechaEvPer/v_S_01_03_00">
  <evtFechaEvPer Id="ID...">
    <ideEvento>
      <indApuracao>1</indApuracao>
      <perApur>2025-01</perApur>
      <tpAmb>1</tpAmb>
      <procEmi>1</procEmi>
      <verProc>EasySocial_1.0</verProc>
    </ideEvento>
    <ideEmpregador>
      <tpInsc>1</tpInsc>
      <nrInsc>XXXXXXXX</nrInsc>
    </ideEmpregador>
    <ideRespInf>
      <nmResp>Responsável</nmResp>
      <cpfResp>XXXXXXXXXXX</cpfResp>
      <telefone>XXXXXXXXXX</telefone>
      <email>email@empresa.com</email>
    </ideRespInf>
  </evtFechaEvPer>
</eSocial>
```

---

## PARTE 8 — LISTA COMPLETA DE PROBLEMAS

### Problemas Técnicos

| # | Problema | Impacto | Quem afeta |
| - | -------- | ------- | ---------- |
| P1 | codIncIRRF = 11 (deveria ser 41) na rubrica 566 | Dedução INSS zerada no IR | Todos os trabalhadores |
| P2 | Verbas indenizatórias de rescisão zeradas | Rescisões com IR errado | Desligados |
| P3 | Verba 47 com incidência incorreta | IR incorreto | A identificar |
| P4 | Recibos GI ≠ recibos eSocial | GI não consegue retificar | Ana/operação |
| P5 | 3 sistemas enviando simultaneamente | Eventos sobrescritos sem controle | Todos |
| P6 | 154 rubricas S-1010 ainda pendentes | Incidências erradas persistem | Envios futuros |
| P7 | ~80 rubricas bloqueadas (natRubr expirado) | Não podem ser enviadas ao eSocial | Pipeline S-1010 |
| P8 | Objetiva sem certificado digital | Não pode enviar nada | Empresa 500 |

### Problemas Operacionais

| # | Problema | Impacto |
| - | -------- | ------- |
| O1 | Sandro recusou compartilhar dados | Precisamos extrair tudo dos XMLs |
| O2 | Validador da Ana removido | GI inutilizável para retificação |
| O3 | Marcos fazendo DEPARA manual há dias | Processo lento e sujeito a erros |
| O4 | Eduardo ansioso por resolução | Pressão por prazos |
| O5 | Doutora Cíntia ausente no momento crítico com Sandro | Decisão política não foi tomada |

### Problemas de Software (O que FALTA no Easy-Social)

| # | O que falta | Prioridade |
| - | ----------- | ---------- |
| S1 | Parser de XMLs do eSocial Download | 🔴 CRÍTICO |
| S2 | Gerador XML S-1200 (retificação) | 🔴 CRÍTICO |
| S3 | Gerador XML S-1210 (retificação) | 🔴 CRÍTICO |
| S4 | Gerador XML S-1298 (reabertura) | 🔴 CRÍTICO |
| S5 | Gerador XML S-1299 (fechamento) | 🔴 CRÍTICO |
| S6 | Gerador XML S-2299 (para rescisões) | 🟡 ALTO |
| S7 | Pipeline orquestrado (S-1010→S-1298→S-1200→S-1210→S-1299) | 🔴 CRÍTICO |
| S8 | Banco para armazenar dados dos XMLs extraídos | 🔴 CRÍTICO |
| S9 | Cruzamento recibos GI vs eSocial | 🟡 ALTO |
| S10 | Dashboard de divergências no frontend | 🟢 MÉDIO |
| S11 | Dashboard de progresso de retificação | 🟢 MÉDIO |
| S12 | Conferência automática de totalizadores (S-5001/S-5002/S-5012) | 🟡 ALTO |

---

## PARTE 9 — REESTRUTURAÇÃO DO SOFTWARE

### Antes (estado atual)
```
python-scripts/esocial/
├── xml_generator.py        → Só S-1010
├── xml_signer.py           → OK
├── soap_builder.py         → OK
├── esocial_client.py       → OK
├── certificate_manager.py  → OK
├── esocial_routes.py       → Só rotas S-1010
├── depara_routes.py        → De-Para de campos
├── cruzamento_eb_routes.py → Consulta rubricas
└── certificate_routes.py   → Upload certificado
```

### Depois (proposta)
```
python-scripts/esocial/
│
│── INFRAESTRUTURA (já existe, manter)
├── xml_signer.py
├── soap_builder.py
├── esocial_client.py
├── certificate_manager.py
│
│── GERADORES XML (expandir)
├── xml_generator.py         → Renomear → xml_s1010.py
├── xml_s1200.py             ← NOVO: gera S-1200 retificação
├── xml_s1210.py             ← NOVO: gera S-1210 retificação
├── xml_s1298.py             ← NOVO: gera S-1298 reabertura
├── xml_s1299.py             ← NOVO: gera S-1299 fechamento
├── xml_s2299.py             ← NOVO: gera S-2299 desligamento (rescisões)
│
│── INGESTÃO (novo módulo)
├── xml_reader.py            ← NOVO: parser massivo de XMLs download
├── xml_reader_routes.py     ← NOVO: endpoints de upload/status
│
│── PIPELINE ORQUESTRADO (novo módulo)
├── pipeline_retificacao.py  ← NOVO: orquestra o fluxo completo por CPF
├── pipeline_routes.py       ← NOVO: endpoints de execução/monitoramento
│
│── ROTAS EXISTENTES (manter/expandir)
├── esocial_routes.py
├── depara_routes.py
├── cruzamento_eb_routes.py
└── certificate_routes.py
```

---

## PARTE 10 — ORDEM DE EXECUÇÃO (O QUE FAZER PRIMEIRO)

```
SEMANA 1 ── Ingestão + Diagnóstico
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  ▸ xml_reader.py — parsear XMLs do Denis (jan/2025 como piloto)
  ▸ Tabelas no banco (esocial_eventos_xml, esocial_itens_remun)
  ▸ Gerar relatório: quantos CPFs × meses × rubricas com problema
  ▸ Terminar S-1010 pendentes (154 rubricas)

SEMANA 2 ── Geradores XML + Pipeline
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  ▸ xml_s1298.py (reabertura — mais simples)
  ▸ xml_s1200.py (retificação remuneração)
  ▸ xml_s1210.py (retificação pagamento)
  ▸ xml_s1299.py (fechamento)
  ▸ pipeline_retificacao.py (orquestrador)

SEMANA 3 ── Teste Piloto
━━━━━━━━━━━━━━━━━━━━━━━━
  ▸ Retificar 1 CPF em jan/2025 em HOMOLOGAÇÃO
  ▸ Verificar S-5002 (dedução IRRF apareceu?)
  ▸ Se OK → repetir em PRODUÇÃO → verificar extrator RF
  ▸ Ajustar fluxo conforme resultado

SEMANA 4+ ── Retificação em Massa
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  ▸ Processar todos os CPFs de jan/2025
  ▸ Avançar mês a mês (fev/2025, mar/2025, ...)
  ▸ Monitorar totalizadores e DCTFWeb
  ▸ Tratar rescisões separadamente (S-2299 em vez de S-1200)
```

---

## PARTE 11 — REGRA DE OURO

```
┌──────────────────────────────────────────────────────────────────┐
│                                                                  │
│   ⚠️  ANTES DE FAZER EM MASSA:                                  │
│                                                                  │
│   1. Retificar 1 CPF piloto em jan/2025                          │
│   2. Verificar S-5002 → dedução IRRF apareceu?                  │
│   3. Verificar S-5001 → INSS/FGTS ficou IGUAL?                  │
│   4. Verificar extrator da Receita Federal                       │
│   5. SÓ ENTÃO expandir para todos                               │
│                                                                  │
│   CPF sugerido para teste: Nilza Estraló (008.209.967-77)       │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

---

## PARTE 12 — RISCOS E DEPENDÊNCIAS

### Dependências Externas

| Dependência | De quem | Status |
| ----------- | ------- | ------ |
| XMLs de todos os meses baixados | Denis | Em andamento (mar/2026 pronto) |
| Certificado digital da Objetiva | Empresa 500 | ❌ Pendente |
| Coordenar com Sandro (parar envios dele) | Doutora Cíntia | ❌ Pendente |
| Validar fluxo com Ana (teste no GI) | Ana | Em andamento |
| DCTFWeb retificadora | Contador | Após retificação |

### Riscos

| Risco | Probabilidade | Mitigação |
| ----- | ------------- | --------- |
| Sandro envia por cima depois de nós | Alta | Doutora precisa parar Sandro antes |
| S-1210 rejeitado por demonstrativo divergente | Média | Extrair ideDmDev exato dos XMLs originais |
| Extrator RF não reflete mesmo após retificação | Média | Testar com 1 CPF antes de expandir |
| Volume de retificações causa bloqueio no eSocial | Baixa | Throttle entre lotes, processar mês a mês |
| S-1200 retificação altera INSS/FGTS sem querer | Baixa | Enviar mesmos valores, só rubrica muda |

---

## PARTE 13 — CONFLITO COM MISSAO_ATUAL

A MISSAO_ATUAL.md dizia:
> ❌ DO NOT touch S-1200 (INSS domain)

**MAS** o Sandro confirmou que **S-1200 precisa ser retificado obrigatoriamente**, mesmo que os valores não mudem. Sem retificar o S-1200, o eSocial não reaplicará as regras da rubrica corrigida.

**Atualização necessária:** A regra "não mexer no S-1200" **precisa ser revisada** com Ana e a Doutora. O S-1200 será retificado **sem alterar valores** — apenas para que o eSocial processe novamente com a rubrica corrigida.

---

_Este documento é o mapa central do projeto. Todas as decisões de desenvolvimento devem referenciar este documento._
