# Plano — Processamento Massivo de XMLs do eSocial

**Criado em:** 04/2026  
**Autor:** Xande (com pesquisa técnica)  
**Contexto:** XMLs baixados via "eSocial Download" (~51.600 por mês, ~200MB/mês)  
**Objetivo:** Extrair CPF, recibo, tipo de evento e dados de incidência de TODOS os XMLs para viabilizar retificações S-1210

---

## 1. Visão Geral do Problema

### 1.1 Resumo das Reuniões

**Call 1 (~25/03/2026):**

- Rubricas com código de incidência IR **errado (11 → deveria ser 41)** — Previdência Social zerada no extrator da Receita Federal
- GI não consegue retificar por divergência de recibos (programa do Sandro sobrepõe envios)
- 3 sistemas enviando ao eSocial simultaneamente — ninguém sabe qual tem o último evento válido
- Validador da Ana removido — bloqueio total pelo GI

**Call 2 (02/04/2026):**

- Sandro **recusou compartilhar** listagem de recibos — decisão: independência total
- Denis baixou **todos os XMLs via eSocial Download** (~51.600 arquivos por mês)
- Estratégia: extrair CPF + recibo + evento dos XMLs → construir base própria → retificar

### 1.2 O Que Precisamos Construir

```
┌─────────────────────────────────────────────────────────────────────────┐
│  PIPELINE: XML → Base de Dados → Cruzamento → Retificação             │
│                                                                         │
│  1. Ingestão: descompactar ZIPs + parsear 51k+ XMLs                    │
│  2. Extração: CPF, nrRecibo, tipo evento, codIncIRRF, codRubr, perApur │
│  3. Armazenamento: PostgreSQL com tabelas indexadas                     │
│  4. Cruzamento: GI vs eSocial — recibos, incidências, divergências     │
│  5. Retificação: gerar XMLs corrigidos S-1210 com novo codIncIRRF      │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Anatomia dos XMLs do eSocial Download

### 2.1 Como o eSocial Download Funciona

- Acesso: portal eSocial WEB → Downloads → Solicitação
- Filtros: período (máx 35 dias), tipo de evento, CPF específico
- Limite: **máximo 200 mil eventos** por pedido (senão status "excedido")
- Disponibilidade: ZIP assíncrono em até 7 dias, depois expira
- Máximo: **12 pedidos por dia**
- Conteúdo: evento XML + recibo no mesmo arquivo

### 2.2 Estrutura dos XMLs no ZIP

Cada XML dentro do ZIP contém:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<eSocial xmlns="http://www.esocial.gov.br/schema/evt/evtRemun/v_S_01_03_00">
  <evtRemun Id="ID1XXXXXXXX00000YYYYMMDDHHMMSS00001">
    <ideEvento>
      <indRetif>1</indRetif>           <!-- 1=Original, 2=Retificação -->
      <nrRecibo>X.X.XXXX...</nrRecibo> <!-- Só se indRetif=2 -->
      <perApur>2026-03</perApur>       <!-- Período de apuração -->
      <tpAmb>1</tpAmb>                 <!-- 1=Produção -->
    </ideEvento>
    <ideEmpregador>
      <tpInsc>1</tpInsc>
      <nrInsc>XXXXXXXX</nrInsc>        <!-- CNPJ raiz 8 dígitos -->
    </ideEmpregador>
    <ideTrabalhador>
      <cpfTrab>XXXXXXXXXXX</cpfTrab>   <!-- CPF do trabalhador -->
    </ideTrabalhador>
    <dmDev>
      <ideDmDev>XXX</ideDmDev>
      <infoPerApur>
        <ideEstabLot>
          <remunPerApur>
            <itensRemun>
              <codRubr>566</codRubr>    <!-- Código da rubrica -->
              <ideTabRubr>1</ideTabRubr>
              <vrRubr>1234.56</vrRubr>  <!-- Valor -->
            </itensRemun>
          </remunPerApur>
        </ideEstabLot>
      </infoPerApur>
    </dmDev>
  </evtRemun>

  <!-- RECIBO (adicionado pelo eSocial Download) -->
  <retornoEvento>
    <processamento>
      <cdResposta>201</cdResposta>
      <nrRecibo>1.2.0000000000.XXXX</nrRecibo>  <!-- ← RECIBO OFICIAL -->
    </processamento>
  </retornoEvento>
</eSocial>
```

### 2.3 Tipos de Evento nos XMLs

| Evento     | Tag raiz        | Namespace (sufixo)           | O que contém                                |
| ---------- | --------------- | ---------------------------- | ------------------------------------------- |
| **S-1010** | `evtTabRubrica` | `evtTabRubrica/v_S_01_03_00` | Tabela de rubricas (incidências)            |
| **S-1200** | `evtRemun`      | `evtRemun/v_S_01_03_00`      | Remuneração RGPS — INSS por trabalhador     |
| **S-1210** | `evtPgtos`      | `evtPgtos/v_S_01_03_00`      | Pagamentos — IRRF por trabalhador           |
| **S-1298** | `evtReaworb`    | Reabertura de folha          | Reabertura de período (pré-retificação)     |
| **S-1299** | `evtFechaEvPer` | Fechamento de folha          | Fechamento de período                       |
| **S-5001** | `evtBasesTrab`  | Totalizador INSS             | Bases de cálculo INSS (gerado pelo eSocial) |
| **S-5002** | `evtIrrf`       | Totalizador IRRF             | Bases de cálculo IRRF (gerado pelo eSocial) |
| **S-5003** | `evtBasesFGTS`  | Totalizador FGTS             | Bases de cálculo FGTS (gerado pelo eSocial) |

### 2.4 Campos-Chave para Extração

| Campo            | Onde encontrar               | Para que serve                |
| ---------------- | ---------------------------- | ----------------------------- |
| `cpfTrab`        | `ideTrabalhador/cpfTrab`     | Identificar trabalhador       |
| `nrRecibo`       | `retornoEvento/.../nrRecibo` | Recibo oficial do eSocial     |
| `Id` (do evento) | atributo do `evt*`           | Identificador único do evento |
| `perApur`        | `ideEvento/perApur`          | Competência (2026-01, etc.)   |
| `indRetif`       | `ideEvento/indRetif`         | 1=Original, 2=Retificação     |
| `codRubr`        | `itensRemun/codRubr`         | Código da rubrica             |
| `vrRubr`         | `itensRemun/vrRubr`          | Valor monetário               |
| `codIncIRRF`     | Tabela S-1010 (cruzar)       | Incidência IR da rubrica      |
| Tipo evento      | nome da tag raiz (`evt*`)    | S-1200, S-1210, etc.          |

---

## 3. Arquitetura do Sistema de Processamento

### 3.1 Stack Escolhida

| Componente     | Tecnologia                | Justificativa                                   |
| -------------- | ------------------------- | ----------------------------------------------- |
| Parser XML     | Python + **lxml**         | Já usado no projeto, 20x mais rápido que stdlib |
| Modo de parse  | **lxml.etree.iterparse**  | Streaming — não carrega 51k XMLs na memória     |
| Banco de dados | **PostgreSQL** (Supabase) | Já configurado e em uso no projeto              |
| API            | **FastAPI**               | Já existe (`bot_api.py`, rotas eSocial)         |
| Frontend       | **Vue 3** (existente)     | Dashboard para visualização de cruzamentos      |
| Processamento  | **multiprocessing.Pool**  | Paralelizar parsing de XMLs em múltiplos cores  |

### 3.2 Fluxo de Dados

```
  ┌──────────────────────────────────────────────────────────────────────┐
  │ FASE 1: INGESTÃO                                                    │
  │                                                                      │
  │  ZIP do eSocial Download (~200MB)                                    │
  │       ↓                                                              │
  │  Descompactar → pasta temporária com XMLs individuais                │
  │       ↓                                                              │
  │  Scanner identifica tipo de evento pelo nome do arquivo/tag raiz     │
  └───────────────────────────┬──────────────────────────────────────────┘
                              │
  ┌───────────────────────────▼──────────────────────────────────────────┐
  │ FASE 2: PARSING (BATCH)                                             │
  │                                                                      │
  │  Para cada XML:                                                      │
  │    1. lxml.etree.parse() — XML individual é pequeno (~3-4KB)         │
  │    2. Detectar tipo de evento (S-1200, S-1210, S-1010, etc.)         │
  │    3. Extrair campos-chave conforme tipo                             │
  │    4. Montar dict com dados extraídos                                │
  │                                                                      │
  │  Batch: processar em lotes de 1000 XMLs → INSERT em lote no banco    │
  │  Paralelismo: multiprocessing.Pool(workers=4)                        │
  └───────────────────────────┬──────────────────────────────────────────┘
                              │
  ┌───────────────────────────▼──────────────────────────────────────────┐
  │ FASE 3: ARMAZENAMENTO                                               │
  │                                                                      │
  │  Tabela: esocial_eventos_xml                                         │
  │    - id, tipo_evento, evento_id, cpf_trab, nr_recibo                 │
  │    - per_apur, ind_retif, nrInsc_empregador                          │
  │    - raw_data (JSONB com campos extras)                               │
  │    - created_at, arquivo_origem                                      │
  │                                                                      │
  │  Tabela: esocial_itens_remun (detalhes de rubricas)                  │
  │    - evento_xml_id (FK), cod_rubr, ide_tab_rubr, vr_rubr             │
  │                                                                      │
  │  Índices: cpf_trab, tipo_evento, per_apur, nr_recibo                 │
  └───────────────────────────┬──────────────────────────────────────────┘
                              │
  ┌───────────────────────────▼──────────────────────────────────────────┐
  │ FASE 4: CRUZAMENTO                                                  │
  │                                                                      │
  │  Query: para cada CPF + período:                                     │
  │    - Último S-1200 (recibo mais recente)                              │
  │    - Último S-1210 (recibo mais recente)                              │
  │    - S-1010 vigente para cada rubrica usada                           │
  │    - Verificar codIncIRRF da rubrica via S-1010                       │
  │    - Comparar com cruzamento_eb (valores corretos)                    │
  │    - Marcar divergências                                              │
  └───────────────────────────┬──────────────────────────────────────────┘
                              │
  ┌───────────────────────────▼──────────────────────────────────────────┐
  │ FASE 5: RETIFICAÇÃO (futuro)                                        │
  │                                                                      │
  │  Para cada divergência:                                               │
  │    1. Gerar XML S-1010 alteração (se incidência errada)               │
  │    2. Gerar XML S-1210 retificação (se necessário — validar c/ Ana)   │
  │    3. Assinar → SOAP → Enviar → Consultar protocolo                   │
  │    4. Registrar resultado no banco                                    │
  └──────────────────────────────────────────────────────────────────────┘
```

---

## 4. Modelagem do Banco de Dados

### 4.1 Tabela Principal: `esocial_eventos_xml`

```sql
CREATE TABLE esocial_eventos_xml (
    id SERIAL PRIMARY KEY,

    -- Identificação do evento
    tipo_evento VARCHAR(10) NOT NULL,      -- S-1010, S-1200, S-1210, S-1298, S-5002...
    evento_id VARCHAR(50),                  -- Id="ID1..." do XML

    -- Trabalhador
    cpf_trab VARCHAR(11),                   -- CPF (11 dígitos, sem pontos)

    -- Recibo
    nr_recibo VARCHAR(60),                  -- Recibo oficial do eSocial
    ind_retif SMALLINT DEFAULT 1,           -- 1=Original, 2=Retificação
    nr_recibo_retif VARCHAR(60),            -- Recibo do evento sendo retificado (se indRetif=2)

    -- Período e empregador
    per_apur VARCHAR(7),                    -- 2026-01, 2026-02, ...
    tp_insc SMALLINT,
    nr_insc VARCHAR(14),                    -- CNPJ do empregador

    -- Dados complementares
    raw_data JSONB,                         -- Campos extras específicos do tipo

    -- Metadados
    arquivo_origem VARCHAR(255),            -- Nome do ZIP/arquivo de origem
    competencia_download VARCHAR(7),        -- Mês do download (para controle)
    created_at TIMESTAMP DEFAULT NOW(),

    -- Controle de duplicatas
    UNIQUE(evento_id)
);

-- Índices para consultas frequentes
CREATE INDEX idx_xml_cpf ON esocial_eventos_xml(cpf_trab);
CREATE INDEX idx_xml_tipo ON esocial_eventos_xml(tipo_evento);
CREATE INDEX idx_xml_per_apur ON esocial_eventos_xml(per_apur);
CREATE INDEX idx_xml_recibo ON esocial_eventos_xml(nr_recibo);
CREATE INDEX idx_xml_cpf_tipo_per ON esocial_eventos_xml(cpf_trab, tipo_evento, per_apur);
```

### 4.2 Tabela de Itens de Remuneração: `esocial_itens_remun`

```sql
CREATE TABLE esocial_itens_remun (
    id SERIAL PRIMARY KEY,
    evento_xml_id INTEGER REFERENCES esocial_eventos_xml(id) ON DELETE CASCADE,

    -- Rubrica
    cod_rubr VARCHAR(30) NOT NULL,
    ide_tab_rubr VARCHAR(10),
    vr_rubr NUMERIC(14,2),

    -- Demonstrativo
    ide_dm_dev VARCHAR(30),

    -- Índice para consulta de rubricas
    CONSTRAINT idx_item_evento UNIQUE(evento_xml_id, cod_rubr, ide_dm_dev)
);

CREATE INDEX idx_itens_cod_rubr ON esocial_itens_remun(cod_rubr);
CREATE INDEX idx_itens_evento ON esocial_itens_remun(evento_xml_id);
```

### 4.3 Tabela de Divergências: `esocial_divergencias_recibo`

```sql
CREATE TABLE esocial_divergencias_recibo (
    id SERIAL PRIMARY KEY,
    cpf_trab VARCHAR(11) NOT NULL,
    per_apur VARCHAR(7) NOT NULL,
    tipo_evento VARCHAR(10) NOT NULL,

    -- Recibos
    nr_recibo_esocial VARCHAR(60),          -- O que o eSocial tem
    nr_recibo_gi VARCHAR(60),               -- O que o GI registrou (se disponível)

    -- Incidências
    cod_rubr VARCHAR(30),
    cod_inc_irrf_atual VARCHAR(5),           -- O que está no eSocial (ex: 11)
    cod_inc_irrf_correto VARCHAR(5),         -- O que deveria ser (ex: 41)

    -- Status
    status VARCHAR(20) DEFAULT 'pendente',   -- pendente, retificado, erro
    retificado_em TIMESTAMP,
    protocolo_retificacao VARCHAR(100),

    created_at TIMESTAMP DEFAULT NOW()
);
```

---

## 5. Implementação — Módulos Python

### 5.1 Estrutura de Diretórios

```
python-scripts/
├── esocial/
│   ├── xml_reader.py          ← NOVO: parser massivo de XMLs do download
│   ├── xml_reader_routes.py   ← NOVO: endpoints FastAPI para upload/status
│   ├── xml_generator.py       (existente: gera S-1010)
│   ├── xml_signer.py          (existente: assina XML)
│   ├── soap_builder.py        (existente: envelope SOAP)
│   ├── esocial_client.py      (existente: envio/consulta)
│   ├── esocial_routes.py      (existente: rotas S-1010)
│   └── certificate_manager.py (existente: certificados A1)
├── xml_downloads/              ← NOVO: pasta para ZIPs baixados
│   ├── 2025-01/
│   ├── 2025-02/
│   └── ...
└── bot_api.py                 (existente: app FastAPI principal)
```

### 5.2 Módulo Principal: `xml_reader.py`

**Responsabilidades:**

1. Descompactar ZIP do eSocial Download
2. Identificar tipo de evento de cada XML
3. Extrair campos-chave conforme o tipo
4. Inserir em lote no PostgreSQL
5. Reportar progresso (para o frontend)

**Abordagem de parsing:**

```python
# Pseudocódigo — abordagem batch com lxml
from lxml import etree
import zipfile
import os
from concurrent.futures import ProcessPoolExecutor

# Cada XML individual do eSocial Download é pequeno (~3-4KB)
# Não precisa de iterparse — parse completo é OK para arquivos pequenos
# O volume está na QUANTIDADE de arquivos (51k+), não no tamanho de cada um

def processar_xml(xml_path: str) -> dict:
    """Parseia 1 XML e retorna dict com dados extraídos."""
    tree = etree.parse(xml_path)
    root = tree.getroot()

    # Detectar tipo de evento pelo tag do primeiro filho
    ns = root.nsmap.get(None, "")
    evt_tag = root[0].tag  # evtRemun, evtPgtos, evtTabRubrica, etc.
    tipo = _detectar_tipo(evt_tag)

    # Extrair campos conforme tipo
    dados = _extrair_campos(root, tipo, ns)
    return dados

def processar_zip(zip_path: str, batch_size=1000):
    """Descompacta ZIP e processa XMLs em batches."""
    with zipfile.ZipFile(zip_path) as zf:
        xml_names = [n for n in zf.namelist() if n.endswith('.xml')]
        total = len(xml_names)

        # Processar em batches para não estourar memória
        for i in range(0, total, batch_size):
            batch = xml_names[i:i+batch_size]
            resultados = []

            for name in batch:
                xml_bytes = zf.read(name)
                dados = _parsear_bytes(xml_bytes, name)
                if dados:
                    resultados.append(dados)

            # INSERT em lote no PostgreSQL
            _inserir_lote(resultados)

            progresso = min(i + batch_size, total)
            print(f"  Processados: {progresso}/{total} ({progresso*100//total}%)")
```

**Estimativa de performance:**

- 51.600 XMLs × ~3-4KB cada = ~150-200MB descompactados
- lxml parse de 1 XML: ~0.5ms
- 51.600 × 0.5ms = ~26 segundos (single thread)
- Com 4 workers: **~7 segundos** por mês
- Total 18 meses (jan/2025 a jun/2026): **~2 minutos**

### 5.3 Rotas FastAPI: `xml_reader_routes.py`

```
POST /api/xml-reader/upload          Upload de ZIP → processar em background
GET  /api/xml-reader/status          Status do processamento atual
GET  /api/xml-reader/resumo          Totais por tipo de evento e período
GET  /api/xml-reader/buscar-cpf      Buscar eventos por CPF
GET  /api/xml-reader/divergencias    Listar divergências encontradas
GET  /api/xml-reader/cruzamento      Cruzar recibos GI vs eSocial
```

---

## 6. Regras de Negócio do Cruzamento

### 6.1 Identificar o Último Evento Válido

Para cada CPF + período de apuração + tipo de evento:

1. Se existem múltiplos eventos, o **último** (pelo recibo mais recente) é o vigente
2. Se `indRetif=2`, o evento **substitui** o identificado por `nrRecibo` no `ideEvento`
3. Eventos excluídos via S-3000 aparecem no download mas devem ser marcados

### 6.2 Detectar Divergência de Incidência IR

```
Para cada S-1200 vigente:
  Para cada rubrica (codRubr) no evento:
    Buscar S-1010 vigente dessa rubrica no perApur
    Se codIncIRRF do S-1010 == 11 E deveria ser 41:
      → DIVERGÊNCIA DETECTADA
      → Marcar para retificação
```

### 6.3 Confrontar Recibos GI × eSocial

- GI exporta recibos em formato próprio
- eSocial Download traz recibos oficiais
- Comparar: se GI tem recibo X mas eSocial tem recibo Y para mesmo CPF+período → o programa do Sandro sobrepôs

### 6.4 Incidências que Importam (da Call 1)

| codIncIRRF | Significado                            | Problema   |
| ---------- | -------------------------------------- | ---------- |
| **11**     | Remuneração                            | ❌ ERRADO  |
| **41**     | Previdência Social — dedução IR mensal | ✅ CORRETO |
| **42**     | Previdência Social — dedução IR 13º    | ✅ CORRETO |
| **43**     | Previdência Social — dedução IR férias | ✅ CORRETO |
| **51-53**  | Pensão alimentícia (dedução)           | Verificar  |

---

## 7. Fluxo de Retificação S-1210

### 7.1 Quando Retificar o S-1210?

**Pergunta em aberto (Fase 2 da MISSAO_ATUAL):** Basta corrigir a rubrica no S-1010 para que o S-5002 (totalizador IRRF) recalcule automaticamente, ou é necessário retificar explicitamente cada S-1210?

**Cenários:**

A. **Só corrigir S-1010** → eSocial recalcula S-5002 automaticamente ← IDEAL (menos trabalho)  
B. **Corrigir S-1010 + retificar S-1210** → precisa reenviar S-1210 por CPF por mês ← MASSIVO  
C. **Corrigir S-1010 + reabrir folha (S-1298) + fechar (S-1299)** → força recálculo ← INTERMEDIÁRIO

### 7.2 Se Precisar Retificar S-1210 (cenário B)

Para cada CPF × mês com divergência:

1. **S-1298** — Reabrir folha do período (perApur)
2. **S-1210 retificação** — indRetif=2, nrRecibo do S-1210 original
   - Mesmos dados, mas agora o S-1010 corrigido muda a base de cálculo
3. **S-1299** — Fechar folha novamente

**Volume estimado:**

- ~16.000-20.000 trabalhadores × 18 meses = até 360.000 retificações
- Lote máximo eSocial: **50 eventos por lote**
- 360.000 / 50 = 7.200 lotes
- Com throttle de 1 segundo entre lotes: ~2 horas

### 7.3 Ordem de Retificação

Conforme discutido na Call 1:

1. Começar pelo **mês mais antigo** (jan/2025)
2. Testar com **1 CPF piloto** (ex: Nilza Estraló, CPF 008.209.967-77)
3. Verificar se S-5002 refletiu a mudança
4. Expandir para todos os CPFs daquele mês
5. Avançar mês a mês

---

## 8. Plano de Execução em Fases

### FASE 0 — Infraestrutura (Pré-requisito)

- [ ] Criar tabelas no PostgreSQL (`esocial_eventos_xml`, `esocial_itens_remun`, `esocial_divergencias_recibo`)
- [ ] Criar pasta `xml_downloads/` com subpastas por competência
- [ ] Garantir que Denis baixou os ZIPs e estão acessíveis

### FASE 1 — Ingestão + Parsing (~1-2 dias)

- [ ] Implementar `esocial/xml_reader.py` com funções de parse
- [ ] Criar extratores específicos para cada tipo de evento (S-1200, S-1210, S-1010, S-5002)
- [ ] Processar **janeiro/2025 primeiro** como piloto
- [ ] Validar dados extraídos (CPF, recibo, rubrica) manualmente com amostra
- [ ] Criar rota `POST /api/xml-reader/upload` para upload via frontend

### FASE 2 — Processamento de Todos os Meses (~1 dia)

- [ ] Processar todos os ZIPs (jan/2025 a mar/2026)
- [ ] Gerar relatório de totais: quantos eventos por tipo por mês
- [ ] Identificar eventos onde o mesmo CPF+período tem múltiplos recibos

### FASE 3 — Cruzamento e Diagnóstico (~2-3 dias)

- [ ] Implementar query de cruzamento (buscar último evento vigente por CPF)
- [ ] Cruzar codIncIRRF via S-1010 com valor correto do cruzamento_eb
- [ ] Gerar relatório de divergências: quantos CPFs, quantos meses, quais rubricas afetadas
- [ ] Confrontar recibos GI × eSocial (se Ana exportar os recibos do GI)
- [ ] Dashboard no frontend: tabela de divergências com filtros

### FASE 4 — Retificação Piloto (~1-2 dias)

- [ ] **VALIDAR COM ANA E DOUTORA:** cenário A, B ou C (ver seção 7.1)
- [ ] Se cenário B: gerar 1 retificação S-1210 para o CPF piloto
- [ ] Enviar em homologação → validar resultado
- [ ] Enviar em produção → verificar S-5002 e extrator Receita Federal
- [ ] Documentar resultado e ajustar se necessário

### FASE 5 — Retificação em Massa (~3-5 dias)

- [ ] Implementar pipeline de retificação automática:
  - Gerar lotes de 50 XMLs S-1210
  - Assinar → SOAP → Enviar → Consultar → Registrar
  - Throttle entre lotes (evitar bloqueio do eSocial)
- [ ] Monitorar via dashboard: progresso, erros, protocolos
- [ ] Tratar erros e re-enviar falhas
- [ ] Validar resultado final no extrator da Receita Federal

---

## 9. Riscos e Mitigações

| Risco                                               | Impacto | Mitigação                                               |
| --------------------------------------------------- | ------- | ------------------------------------------------------- |
| ZIP com mais de 200k eventos (status "excedido")    | Alto    | Denis já filtra por período ≤ 31 dias                   |
| XMLs com layout diferente (versão S-1.2 vs S-1.0)   | Médio   | Parser deve detectar namespace e adaptar                |
| eSocial bloqueia envios massivos (rate limit)       | Alto    | Throttle de 1-2s entre lotes, máx 50 eventos/lote       |
| Retificação S-1210 não reflete no extrator da RF    | Crítico | Testar com 1 CPF piloto antes de expandir               |
| Programa do Sandro envia por cima depois de nós     | Alto    | Coordenar com Doutora Cíntia — Sandro deve parar envios |
| Recibos no GI são irrecuperáveis                    | Médio   | Usar recibos diretamente dos XMLs do eSocial Download   |
| Volume de retificações excede capacidade do eSocial | Médio   | Processar mês a mês, validar antes de expandir          |

---

## 10. O Que Já Existe no Projeto (Reaproveitar)

O Easy-Social já tem infraestrutura sólida:

| Módulo                   | O que faz                             | Reuso                    |
| ------------------------ | ------------------------------------- | ------------------------ |
| `xml_generator.py`       | Gera XML S-1010 (inclusão/alteração)  | Adaptar para S-1210      |
| `xml_signer.py`          | Assina XML com certificado A1         | 100% reutilizável        |
| `soap_builder.py`        | Monta envelope SOAP para envio        | 100% reutilizável        |
| `esocial_client.py`      | Envia e consulta lotes via mTLS       | 100% reutilizável        |
| `certificate_manager.py` | Gerencia certificados A1              | 100% reutilizável        |
| `esocial_routes.py`      | API de orquestração S-1010            | Padrão para rotas S-1210 |
| `db_config.py`           | Config de banco (Supabase + local)    | 100% reutilizável        |
| `cruzamento_eb` (tabela) | 448 rubricas com incidências corretas | Base de comparação       |
| `bot_api.py`             | App FastAPI (porta 8000)              | Adicionar novas rotas    |

---

## 11. Prioridade de Implementação

```
AGORA → xml_reader.py (parse dos XMLs do Denis) → jan/2025 como piloto
  ↓
Logo → processar todos os meses → gerar relatório de divergências
  ↓
Depende de validação → retificação S-1210 (só depois de testar com 1 CPF)
```

**A primeira entrega** é o parser que responde: **"Para o CPF X no mês Y, qual é o último recibo válido e quais rubricas foram usadas?"**

Essa é a funcionalidade que o Sandro se recusou a dar.

---

_Este documento deve ser atualizado conforme avançamos nas fases. Verificar seção 7.1 com Ana/Doutora antes de implementar retificação._
