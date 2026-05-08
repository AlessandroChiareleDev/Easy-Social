# Guia de Montagem do XML S-1210 — Pagamentos de Rendimentos do Trabalho

> **Para o "montador de S-1210" do Easy-eSocial-v2.**
> Documento didático cobrindo o que cada tag significa, valores válidos, regras de negócio
> e o passo-a-passo conceitual para construir um XML válido para o WebService do eSocial.
>
> Fontes oficiais consultadas:
>
> - **Manual de Orientação do eSocial — Versão S-1.3** (gov.br/esocial)
> - **Leiautes eSocial S-1.3** — `gov.br/esocial/pt-br/documentacao-tecnica/leiautes-esocial-v-1.3`
> - VRi Consulting (resumo do MOS) e MGP Consultoria — referências cruzadas
> - XML real produzido pelo nosso pipeline em `python-scripts/_test_s1210_08769348740.xml`

---

## 1. Visão geral do evento

**S-1210 — Pagamentos de Rendimentos do Trabalho**

- **O que é:** evento periódico que informa pagamentos efetuados a trabalhadores
  (com ou sem vínculo) e benefícios pagos por entes públicos (RPPS).
  É a fonte oficial das informações do IRRF que vão para a DIRF/DIRPF.
- **Quem envia:** todo declarante que efetuou pagamento a trabalhador.
- **Periodicidade:** **um único S-1210 por (CPF, mês de apuração)**.
  Se vários pagamentos no mês, todos vão dentro do mesmo evento (em múltiplos `<infoPgto>`).
- **Prazo:** até o dia 15 do mês subsequente ao `perApur`, ou antes do S-1299
  (fechamento dos eventos periódicos), o que ocorrer primeiro.
- **Pré-requisitos:** S-1000 (empregador) + S-1010 (rubricas, quando aplicável) +
  S-1200/S-1202/S-1207/S-2299/S-2399 _anteriormente enviados_ (com os
  demonstrativos `dmDev` referenciados pelo S-1210 via `ideDmDev`).
- **Regra de ouro:** cada `infoPgto` aponta para um `ideDmDev` que **já existe**
  num evento de remuneração — o S-1210 é só o "carimbo" do pagamento, não recalcula
  nada.

---

## 2. Estrutura geral do XML (árvore)

```
<eSocial xmlns="http://www.esocial.gov.br/schema/evt/evtPgtos/v_S_01_03_00">
  <evtPgtos Id="ID...">
    <ideEvento>            ← cabeçalho do evento (ambiente, retificação, perApur)
    <ideEmpregador>        ← quem é o declarante (CNPJ raiz / CPF)
    <ideBenef>             ← o trabalhador beneficiário (CPF)
      <infoPgto> (1..N)    ← cada pagamento (data, tipo, demonstrativo, vrLiq)
      <infoIRComplem>      ← informações complementares de IR (deduções, planos)
        <infoIRCR> (0..N)  ← deduções por código de receita
          <dedDepen>       ← dedução por dependente
          <penAlim>        ← pensão alimentícia
          <previdCompl>    ← previdência complementar
          <infoProcRet>    ← processos administrativos/judiciais
        <planSaude> (0..N) ← plano de saúde coletivo empresarial
        <infoReembMed>     ← reembolso médico/odontológico
        <perAnt> (0..12)   ← retificações de IR de anos anteriores (S-1.3+)
  </evtPgtos>
  <Signature> ← assinatura digital XMLDSig (obrigatória pré-envio)
</eSocial>
```

> Há **um único `<ideBenef>` por evento** (1 CPF por S-1210).
> Para outro CPF, é outro evento — e cada um vai compor o lote a ser enviado.

---

## 3. Análise tag-por-tag — XML real do pipeline

XML referência: [python-scripts/\_test_s1210_08769348740.xml](../python-scripts/_test_s1210_08769348740.xml)

### 3.1 Raiz `<eSocial>`

```xml
<eSocial xmlns="http://www.esocial.gov.br/schema/evt/evtPgtos/v_S_01_03_00">
```

- **`xmlns`**: namespace específico da versão do leiaute do S-1210.
  `v_S_01_03_00` = versão **S-1.3.00** (atual em produção em 2025).
  Mudou? trocar este namespace é o primeiro passo para subir versão.
- Não usar `xmlns:xsi` / `xmlns:xsd` aqui (o XSD valida sem isso).

### 3.2 `<evtPgtos Id="...">`

```xml
<evtPgtos Id="ID1059690710000002026041523323600001">
```

- **`Id`** (atributo obrigatório): identificador único do evento, **34 caracteres**,
  no formato:

  ```
  ID + tpInsc(1) + nrInsc(14, completado com 0 à esq.) + AAAAMMDDHHMMSS + sequencial(5)
  ```

  Exemplo decomposto: `ID` + `1` + `05969071000000` + `20260415233236` + `00001`.

- O `Id` é a **referência da assinatura XMLDSig** (`<ds:Reference URI="">` aponta
  para este nó via `enveloped-signature`).

### 3.3 `<ideEvento>` — identificação do evento

```xml
<ideEvento>
  <indRetif>2</indRetif>
  <nrRecibo>1.1.0000000039961684709</nrRecibo>
  <perApur>2025-01</perApur>
  <tpAmb>1</tpAmb>
  <procEmi>1</procEmi>
  <verProc>EasySocial_1.0</verProc>
</ideEvento>
```

| Campo      | Tipo  | Valores                                                                      | Significado                                                      |
| ---------- | ----- | ---------------------------------------------------------------------------- | ---------------------------------------------------------------- |
| `indRetif` | N(1)  | `1` = original / `2` = retificador                                           | Indicador de retificação.                                        |
| `nrRecibo` | C(40) | recibo do evento original                                                    | **Obrigatório se `indRetif=2`**. Não preencher quando original.  |
| `perApur`  | C(7)  | `AAAA-MM`                                                                    | Mês de apuração (mensal). 13º não usa S-1210 — usa S-1200 anual. |
| `tpAmb`    | N(1)  | `1` = produção / `2` = produção restrita / `3` = treinamento (descontinuado) | Ambiente.                                                        |
| `procEmi`  | N(1)  | `1` = aplicativo do declarante / `2` = aplicativo do governo                 | Quem emitiu.                                                     |
| `verProc`  | C(20) | livre                                                                        | Versão do software emissor (ex.: `EasySocial_1.0`).              |

> **Retificações:** podem alterar qualquer campo **exceto** `cpfBenef` e `perApur`.
> Para corrigir CPF ou competência → **excluir** com S-3000 e enviar novo original.

### 3.4 `<ideEmpregador>` — identificação do declarante

```xml
<ideEmpregador>
  <tpInsc>1</tpInsc>
  <nrInsc>05969071</nrInsc>
</ideEmpregador>
```

| Campo    | Tipo       | Valores                                        |
| -------- | ---------- | ---------------------------------------------- |
| `tpInsc` | N(1)       | `1` = CNPJ / `2` = CPF                         |
| `nrInsc` | C(8/11/14) | **CNPJ raiz (8 dígitos)** para PJ, ou CPF (11) |

> Pessoa jurídica usa **só os 8 dígitos da raiz** (sem filial) — o eSocial é por
> matriz no S-1210.

### 3.5 `<ideBenef>` — o beneficiário

```xml
<ideBenef>
  <cpfBenef>08769348740</cpfBenef>
  <infoPgto>...</infoPgto>
  <infoIRComplem>...</infoIRComplem>
</ideBenef>
```

- **`cpfBenef`** (C(11), obrigatório): CPF do trabalhador, 11 dígitos sem máscara.
- Pode existir também (não usado neste exemplo):
  - `nmBenef` — só quando residente no exterior;
  - `dtNascto`, `paisResid`, `paisResidExt` — para tratamento exterior;
  - `infoDep` (0..N) — dados cadastrais de dependentes ainda não cadastrados em
    S-2200/S-2205/S-2300/S-2400/S-2405 (S-1.3).

### 3.6 `<infoPgto>` — cada pagamento (1..N, até 999)

```xml
<infoPgto>
  <dtPgto>2025-01-07</dtPgto>
  <tpPgto>1</tpPgto>
  <perRef>2024-12</perRef>
  <ideDmDev>01510972</ideDmDev>
  <vrLiq>35.34</vrLiq>
</infoPgto>
<infoPgto>
  <dtPgto>2025-01-07</dtPgto>
  <tpPgto>1</tpPgto>
  <perRef>2024-12</perRef>
  <ideDmDev>01510971</ideDmDev>
  <vrLiq>2137.9</vrLiq>
</infoPgto>
```

| Campo        | Tipo      | Valores                                                                                           |
| ------------ | --------- | ------------------------------------------------------------------------------------------------- |
| `dtPgto`     | D         | Data do pagamento (`AAAA-MM-DD`). Não pode ser futura, salvo dentro do mesmo `perApur`.           |
| `tpPgto`     | N(1)      | Tipo de pagamento (vide tabela abaixo)                                                            |
| `perRef`     | C(4 ou 7) | Competência de **referência** do demonstrativo `ideDmDev`.                                        |
| `ideDmDev`   | C(30)     | Identificador do demonstrativo `dmDev` previamente enviado em S-1200/S-1202/S-1207/S-2299/S-2399. |
| `vrLiq`      | N(14,2)   | Valor líquido pago (R$). Usar **ponto decimal**, sem milhar.                                      |
| `indPgtoExt` | N(1)      | (opcional) `S/N` quando beneficiário no exterior.                                                 |

#### Valores válidos de `tpPgto`:

| Código | Descrição                                       | Demonstrativo de origem              |
| ------ | ----------------------------------------------- | ------------------------------------ |
| `1`    | Pagamento de remuneração                        | `dmDev` do **S-1200**                |
| `2`    | Verbas rescisórias                              | `dmDev` do **S-2299** (desligamento) |
| `3`    | Verbas rescisórias TSVE                         | `dmDev` do **S-2399** (sem vínculo)  |
| `4`    | Remuneração de servidor RPPS                    | `dmDev` do **S-1202**                |
| `5`    | Benefício previdenciário                        | `dmDev` do **S-1207**                |
| `7`    | Recibo de férias                                | sem `dmDev` (independente)           |
| `9`    | Pagamento anterior à obrigatoriedade do eSocial | sem `dmDev`                          |

> **Regra crucial:** se `tpPgto ∈ {1,2,3,4,5}` então `ideDmDev` **deve corresponder
> a um demonstrativo já existente** no evento de origem. Se não bater → erro 627
> "demonstrativo não encontrado".

### 3.7 `<infoIRComplem>` — informações de IR (S-1.3)

```xml
<infoIRComplem>
  <infoIRCR>
    <tpCR>056107</tpCR>
    <penAlim>
      <tpRend>11</tpRend>
      <cpfDep>00000000000</cpfDep>
      <vlrDedPenAlim>661.97</vlrDedPenAlim>
    </penAlim>
  </infoIRCR>
  <planSaude>
    <cnpjOper>08787782000162</cnpjOper>
    <regANS>416525</regANS>
    <vlrSaudeTit>39.60</vlrSaudeTit>
  </planSaude>
  <planSaude>
    <cnpjOper>44649812000138</cnpjOper>
    <regANS>359017</regANS>
    <vlrSaudeTit>47.00</vlrSaudeTit>
  </planSaude>
</infoIRComplem>
```

#### 3.7.1 `<infoIRCR>` — informações por **Código de Receita**

- **`tpCR`** (C(6)): Código de Receita do IRRF. Os mais comuns:
  - `056107` — **Trabalho assalariado** (rendimentos do trabalho com vínculo)
  - `056108` — Trabalho sem vínculo
  - `188901` — RRA (rendimentos recebidos acumuladamente)
  - `047301` — IRRF residente exterior
- Cada `tpCR` agrupa as deduções/isenções aplicáveis a aquele CR.

##### `<dedDepen>` — dedução por dependente IR

```xml
<dedDepen>
  <tpRend>11</tpRend>
  <cpfDep>14020816930</cpfDep>
  <vlrDedDep>189.59</vlrDedDep>
</dedDepen>
```

| Campo       | Valores                                                                               |
| ----------- | ------------------------------------------------------------------------------------- |
| `tpRend`    | `11` = remuneração mensal / `12` = 13º / `13` = férias                                |
| `cpfDep`    | CPF do dependente cadastrado em S-2200/S-2205/S-2300/S-2400/S-2405 (ou em `infoDep`). |
| `vlrDedDep` | R$ 189,59/mês desde 2015 (Lei 9.250/95).                                              |

##### `<penAlim>` — pensão alimentícia

```xml
<penAlim>
  <tpRend>11</tpRend>
  <cpfDep>00000000000</cpfDep>
  <vlrDedPenAlim>661.97</vlrDedPenAlim>
</penAlim>
```

| Campo           | Valores                                                            |
| --------------- | ------------------------------------------------------------------ |
| `tpRend`        | `11`, `12`, `13`, `14` (PLR), `18` (RRA), `79` (rend isento)       |
| `cpfDep`        | CPF do alimentando. **Se não exigido em lei**, usar `00000000000`. |
| `vlrDedPenAlim` | Valor pago no mês a título de pensão.                              |

##### `<previdCompl>` — previdência complementar

| Campo             | Valores                                     |
| ----------------- | ------------------------------------------- |
| `tpPrev`          | `1` = privada / `2` = FAPI / `3` = Funpresp |
| `vlrDedPrevCompl` | Valor da contribuição                       |
| `cnpjEntidPC`     | CNPJ da entidade                            |

#### 3.7.2 `<planSaude>` — plano de saúde coletivo empresarial

```xml
<planSaude>
  <cnpjOper>08787782000162</cnpjOper>
  <regANS>416525</regANS>
  <vlrSaudeTit>39.60</vlrSaudeTit>
</planSaude>
```

| Campo         | Tipo    | Significado                                              |
| ------------- | ------- | -------------------------------------------------------- |
| `cnpjOper`    | C(14)   | CNPJ da operadora                                        |
| `regANS`      | C(6)    | Registro ANS da operadora                                |
| `vlrSaudeTit` | N(14,2) | Valor descontado **do titular** (custo + coparticipação) |

- **Detalhamento por dependente:** subgrupo opcional `<infoDepSau>` dentro de cada
  `<planSaude>`, com `cpfDep` + `vlrSaudeDep`. O CPF tem que estar cadastrado.
- **Múltiplos planos:** múltiplos `<planSaude>` no mesmo evento (uma por operadora,
  como no exemplo).

#### 3.7.3 `<perAnt>` (S-1.3, vigência jan/2026)

Permite, em janeiro de cada ano, **retificar** o `infoIRComplem` de competências
do ano anterior **sem retificar o S-1210 daquela competência**:

```xml
<perAnt>
  <perRefAjuste>2025-03</perRefAjuste>
  <nrRec1210Orig>1.1.0000000039932...</nrRec1210Orig>
  <infoIRCR>...</infoIRCR>
</perAnt>
```

- Até 12 ocorrências (jan + 12 meses do ano anterior).
- O retificador **substitui integralmente** o `infoIRComplem` original — todos os
  campos têm que voltar.

---

## 4. Regras de negócio críticas (resumo prático)

1. **1 evento = 1 CPF = 1 perApur.** Vários pagamentos do mesmo CPF no mês →
   múltiplos `<infoPgto>` dentro do mesmo evento.
2. **`ideDmDev`** tem que existir num evento de remuneração já enviado
   (exceto `tpPgto=7` ou `9`).
3. **Retificação:** `indRetif=2` + `nrRecibo` original. Não muda CPF nem perApur
   (para isso → S-3000 + novo original).
4. **`vrLiq`** usa ponto decimal e não tem separador de milhar (`2137.9`, não
   `2.137,90`).
5. **Datas** sempre `AAAA-MM-DD` ISO 8601.
6. **`Id` do evento** é **único e imutável** após assinado — qualquer reenvio
   precisa de um `Id` novo.
7. **Assinatura digital obrigatória** com certificado e-CNPJ (ou e-CPF do MEI):
   - Algoritmo: `RSA-SHA256`
   - Canonicalização: `xml-c14n-20010315`
   - Transform: `enveloped-signature`
   - Reference URI: `""` (todo o documento) ou `#Id` do `<evtPgtos>`
8. **Pagamento total `vrLiq=0`:** se houve rendimento/IR no mês mas zero líquido,
   ainda é obrigatório enviar S-1210 — `dtPgto` = data de vencimento.
9. **Trabalhador no exterior** (`paisResidExt ≠ 105`): preencher `infoPgtoExt` e
   o CR vira `047301` no `infoIRCR`.
10. **Movimento aberto:** S-1210 só é aceito se o `perApur` ainda não estiver
    fechado por S-1299. Se fechado → primeiro S-1298 (reabertura).

---

## 5. Passo-a-passo conceitual para o "montador de S-1210"

1. **Coletar dados do beneficiário** (1 CPF):
   - perApur, dados do empregador, lista de pagamentos efetuados no mês.
2. **Para cada pagamento** (data + ideDmDev de S-1200/S-1202/...):
   - calcular/recuperar `vrLiq`;
   - decidir `tpPgto` conforme a origem do demonstrativo;
   - montar um `<infoPgto>`.
3. **Montar `<infoIRComplem>`** se houver:
   - dependentes para abater IR (`dedDepen`);
   - pensão alimentícia (`penAlim`);
   - previdência complementar (`previdCompl`);
   - planos de saúde com CNPJ + ANS (`planSaude`, 1 por operadora);
   - reembolsos (`infoReembMed`).
4. **Compor o evtPgtos** com `Id` gerado:
   `ID` + tpInsc + nrInsc(14, zfill) + timestamp(`%Y%m%d%H%M%S`) + seq(5).
5. **Validar contra o XSD oficial** do leiaute v_S_01_03_00.
6. **Assinar** com XMLDSig (RSA-SHA256, c14n, enveloped).
7. **Empacotar no lote** `EnviarLoteEventos` (até **40 eventos por lote** no
   Simplificado, ou conforme regra do ambiente) e POST no WS.
8. **Persistir** o `nrRecibo` retornado em `nrRecibo` da nossa base — esse vira a
   referência para qualquer retificação futura.

---

## 6. Checklist anti-erro mais comum

| Erro/código                        | Causa típica                                           | Como evitar                                |
| ---------------------------------- | ------------------------------------------------------ | ------------------------------------------ |
| 201 — `Id` inválido                | tamanho ≠ 36 ou nrInsc não-zfilled                     | montar Id com regra do §3.2                |
| 627 — demonstrativo não encontrado | `ideDmDev` não bate com `dmDev` em S-1200              | conferir tabela `dmdev` antes de montar    |
| 750 — perApur fechado              | mês já tem S-1299 enviado                              | enviar S-1298 antes                        |
| 1042 — assinatura inválida         | canonicalização errada ou cert errado                  | usar RSA-SHA256 + c14n-20010315            |
| TPRUBR-like (rubrica errada)       | rubrica ausente em S-1010 vigente                      | validar S-1010 ativo no `perApur`          |
| dependente sem cadastro            | `cpfDep` em `dedDepen` não está em S-2200/etc          | enviar `infoDep` no próprio S-1210 (S-1.3) |
| pensão sem CPF                     | exige CPF e foi enviado `00000000000` quando lei exige | usar CPF real quando exigido               |
| valor com vírgula                  | `vrLiq` com vírgula brasileira                         | usar ponto decimal                         |

---

## 7. Mapeamento das fontes consultadas

- **Manual de Orientação do eSocial v S-1.3** (PDF oficial) — base conceitual,
  itens 1–9 da seção 3 do guia técnico do S-1210 (assuntos gerais, retificação,
  IR, plano de saúde, perAnt).
- **Leiautes eSocial v S-1.3** (página HTML oficial) — descrição campo-a-campo,
  ocorrências, validações e tabelas relacionadas (Tabela 05 - tpInsc, etc).
- **VRi Consulting — guia 787** — resumo didático do MOS, valores válidos de
  `tpPgto`, `tpRend`, `tpCR`, `tpPrev`, `indTpDeducao`.
- **MGP Consultoria** — exemplos de relação S-1200×S-1210, regras de pagamento
  parcial vs total e prazo.
- **XSD oficial** `evtPgtos_v_S_01_03_00.xsd` — validação final do leiaute
  (não consultado neste guia, mas recomendado ao implementar).

---

## 8. Próximos passos para o montador

1. Implementar gerador de `Id` (sequencial por (empregador, dia, segundo)).
2. Função pura `montar_s1210(beneficiario, pagamentos, ir_complem) → ElementTree`.
3. Validador XSD opcional antes de assinar (catch early).
4. Assinador XMLDSig (já existe no pipeline atual, reaproveitar).
5. Empacotador de lote `EnviarLoteEventos` (já existe, integrar).
6. UI: formulário com (CPF, perApur, lista de pagamentos, IR complem) → preview
   do XML antes de assinar/enviar.

---

**Documento gerado em 07/05/2026** — baseado em S-1.3 vigente.
Quando subir versão (ex.: S-1.4), revisar §3.1 (namespace) e §3.7.3 (regras `perAnt`).
