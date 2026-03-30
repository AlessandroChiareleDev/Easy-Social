# Estudo eSocial S-1010 — Web Service para Envio de Alterações INSS/IRRF/FGTS

> **Data do estudo:** 27/03/2026  
> **Versão do leiaute:** S-1.3 (vigente em produção e produção restrita)  
> **Objetivo:** Entender como enviar alterações de incidência tributária (INSS, IRRF, FGTS) de rubricas ao eSocial via web service XML

---

## 1. Visão Geral

O **S-1010 (evtTabRubrica)** é o evento de **Tabela de Rubricas** do eSocial. Por meio dele é possível:

- **Incluir** uma nova rubrica (`<inclusao>`)
- **Alterar** uma rubrica existente (`<alteracao>`) ← **é o que o Easy Social precisa**
- **Excluir** uma rubrica (`<exclusao>`)

Cada rubrica possui campos de incidência tributária que determinam como aquele valor é tratado para fins de INSS, IRRF e FGTS:

| Campo XML        | Tabela de Referência | Tributo                                     |
| ---------------- | -------------------- | ------------------------------------------- |
| `codIncCP`       | Tabela 04            | **INSS** (Contribuição Previdenciária)      |
| `codIncIRRF`     | Tabela 21            | **IRRF** (Imposto de Renda Retido na Fonte) |
| `codIncFGTS`     | Tabela 22            | **FGTS**                                    |
| `codIncCPRP`     | —                    | Regime Próprio Previdência (opcional)       |
| `codIncPisPasep` | —                    | **PIS/PASEP** (novo no S-1.3)               |

---

## 2. Namespace e Versão

```
Namespace S-1.3: http://www.esocial.gov.br/schema/evt/evtTabRubrica/vS01_03_00
```

Configuração de versão:

```json
{
  "tpAmb": 2,
  "verProc": "S_1.3.0",
  "eventoVersion": "S.1.3.0",
  "serviceVersion": "1.5.0"
}
```

---

## 3. Formato do ID do Evento

```
Id="ID{tpInsc}{nrInsc(14)}{AAAA}{MM}{DD}{HH}{mm}{ss}{seq(5)}"
```

Exemplo: `ID1123456780000002026032710370000001`

| Parte            | Valor        | Descrição                              |
| ---------------- | ------------ | -------------------------------------- |
| `ID`             | Prefixo fixo | Literal "ID"                           |
| `1`              | tpInsc       | 1=CNPJ, 2=CPF                          |
| `12345678000000` | nrInsc       | CNPJ com 14 dígitos (padded com zeros) |
| `20260327103700` | Timestamp    | AAAA+MM+DD+HH+mm+ss                    |
| `00001`          | Sequencial   | 5 dígitos, incrementado por evento     |

---

## 4. Estrutura XML Completa do S-1010

### 4.1. Inclusão (cadastrar rubrica nova)

```xml
<eSocial xmlns="http://www.esocial.gov.br/schema/evt/evtTabRubrica/vS01_03_00">
  <evtTabRubrica Id="ID1123456780000002026032710370000001">
    <ideEvento>
      <tpAmb>2</tpAmb>           <!-- 1=Produção, 2=Produção Restrita -->
      <procEmi>1</procEmi>       <!-- 1=App empregador, 2=Gov Simplif PF, 3=Gov Web, 4=Gov Simplif PJ -->
      <verProc>S_1.3.0</verProc> <!-- Versão do aplicativo emissor -->
    </ideEvento>
    <ideEmpregador>
      <tpInsc>1</tpInsc>         <!-- 1=CNPJ, 2=CPF -->
      <nrInsc>12345678</nrInsc>  <!-- 8 dígitos (raiz CNPJ) ou 11 (CPF) -->
    </ideEmpregador>
    <infoRubrica>
      <inclusao>
        <ideRubrica>
          <codRubr>CODIGO001</codRubr>       <!-- Max 30 chars, não pode começar com "eSocial" -->
          <ideTabRubr>1</ideTabRubr>          <!-- Max 8 chars, identificador da tabela -->
          <iniValid>2026-03</iniValid>        <!-- AAAA-MM início vigência -->
          <fimValid>2026-12</fimValid>        <!-- Opcional: AAAA-MM fim vigência -->
        </ideRubrica>
        <dadosRubrica>
          <dscRubr>HORAS EXTRAS 50%</dscRubr> <!-- Descrição, max 100 chars -->
          <natRubr>1003</natRubr>              <!-- Tabela 3 - Natureza da Rubrica (4 dígitos) -->
          <tpRubr>1</tpRubr>                  <!-- 1=Vencimento, 2=Desconto, 3=Informativa, 4=Informativa dedutora -->
          <codIncCP>11</codIncCP>              <!-- Tabela 04 - INSS -->
          <codIncIRRF>11</codIncIRRF>          <!-- Tabela 21 - IRRF -->
          <codIncFGTS>11</codIncFGTS>          <!-- Tabela 22 - FGTS -->
          <codIncCPRP>11</codIncCPRP>          <!-- Opcional: Regime Próprio Previdência -->
          <codIncPisPasep>11</codIncPisPasep>  <!-- NOVO no S-1.3: PIS/PASEP -->
          <tetoRemun>N</tetoRemun>             <!-- Opcional: S/N - teto remuneratório -->
          <observacao>texto</observacao>       <!-- Opcional: max 255 chars -->
          <!-- Grupos opcionais de processos judiciais: -->
          <ideProcessoCP>
            <tpProc>1</tpProc>                <!-- 1=Administrativo, 2=Judicial -->
            <nrProc>12345678901234567890</nrProc>
            <extDecisao>1</extDecisao>         <!-- 1=Patronal, 2=Patronal+Segurado -->
            <codSusp>12345</codSusp>
          </ideProcessoCP>
          <ideProcessoIRRF>
            <nrProc>12345678901234567890</nrProc>
            <codSusp>12345</codSusp>
          </ideProcessoIRRF>
          <ideProcessoFGTS>
            <nrProc>12345678901234567890</nrProc>
          </ideProcessoFGTS>
          <ideProcessoPisPasep>               <!-- NOVO no S-1.3 -->
            <nrProc>12345678901234567890</nrProc>
            <codSusp>12345</codSusp>
          </ideProcessoPisPasep>
        </dadosRubrica>
      </inclusao>
    </infoRubrica>
  </evtTabRubrica>
</eSocial>
```

### 4.2. Alteração (modificar rubrica existente) — O QUE O EASY SOCIAL PRECISA

```xml
<eSocial xmlns="http://www.esocial.gov.br/schema/evt/evtTabRubrica/vS01_03_00">
  <evtTabRubrica Id="ID1123456780000002026032710370000001">
    <ideEvento>
      <tpAmb>2</tpAmb>
      <procEmi>1</procEmi>
      <verProc>S_1.3.0</verProc>
    </ideEvento>
    <ideEmpregador>
      <tpInsc>1</tpInsc>
      <nrInsc>12345678</nrInsc>
    </ideEmpregador>
    <infoRubrica>
      <alteracao>
        <ideRubrica>
          <codRubr>CODIGO001</codRubr>       <!-- Código da rubrica existente -->
          <ideTabRubr>1</ideTabRubr>          <!-- Identificador da tabela existente -->
          <iniValid>2026-03</iniValid>        <!-- Período de vigência existente -->
          <fimValid>2026-12</fimValid>        <!-- Opcional -->
        </ideRubrica>
        <dadosRubrica>
          <!-- ⚠️ TODOS os campos são OBRIGATÓRIOS na alteração, não só os que mudaram -->
          <dscRubr>HORAS EXTRAS 50%</dscRubr>
          <natRubr>1003</natRubr>
          <tpRubr>1</tpRubr>
          <codIncCP>11</codIncCP>              <!-- NOVO código INSS -->
          <codIncIRRF>11</codIncIRRF>          <!-- NOVO código IRRF -->
          <codIncFGTS>11</codIncFGTS>          <!-- NOVO código FGTS -->
          <codIncCPRP>11</codIncCPRP>
          <codIncPisPasep>11</codIncPisPasep>
          <tetoRemun>N</tetoRemun>
          <observacao/>
        </dadosRubrica>
        <!-- Opcional: para alterar o próprio período de validade -->
        <novaValidade>
          <iniValid>2026-04</iniValid>         <!-- Novo início de vigência -->
          <fimValid>2026-12</fimValid>         <!-- Opcional: novo fim -->
        </novaValidade>
      </alteracao>
    </infoRubrica>
  </evtTabRubrica>
</eSocial>
```

**⚠️ Regra crítica:** O eSocial armazena dados historicamente. Não é possível ter dados diferentes para a mesma rubrica no mesmo período de validade. Para alterar, envie um novo evento com `<novaValidade>` com um novo período.

### 4.3. Exclusão (remover rubrica)

```xml
<eSocial xmlns="http://www.esocial.gov.br/schema/evt/evtTabRubrica/vS01_03_00">
  <evtTabRubrica Id="ID1123456780000002026032710370000001">
    <ideEvento>
      <tpAmb>2</tpAmb>
      <procEmi>1</procEmi>
      <verProc>S_1.3.0</verProc>
    </ideEvento>
    <ideEmpregador>
      <tpInsc>1</tpInsc>
      <nrInsc>12345678</nrInsc>
    </ideEmpregador>
    <infoRubrica>
      <exclusao>
        <ideRubrica>
          <codRubr>CODIGO001</codRubr>
          <ideTabRubr>1</ideTabRubr>
          <iniValid>2026-03</iniValid>
          <fimValid>2026-12</fimValid>
        </ideRubrica>
      </exclusao>
    </infoRubrica>
  </evtTabRubrica>
</eSocial>
```

---

## 5. Tabelas de Incidência — Valores Permitidos

### 5.1. codIncCP — Tabela 04 (INSS / Contribuição Previdenciária)

| Código | Descrição                                                            |
| ------ | -------------------------------------------------------------------- |
| **00** | Não é base de cálculo                                                |
| **01** | Não é base de cálculo (acordos internacionais de previdência social) |
| **11** | Mensal                                                               |
| **12** | 13° Salário                                                          |
| **13** | Exclusiva Empregador - mensal                                        |
| **14** | Exclusiva Empregador - 13° salário                                   |
| **15** | Exclusiva do segurado - mensal                                       |
| **16** | Exclusiva do segurado - 13° salário                                  |
| **21** | Salário maternidade mensal (pago pelo Empregador)                    |
| **22** | Salário maternidade 13° salário (pago pelo Empregador)               |
| **23** | Auxílio doença mensal - RPPS                                         |
| **24** | Auxílio doença 13° salário - RPPS                                    |
| **25** | Salário maternidade mensal (pago pelo INSS)                          |
| **26** | Salário maternidade 13° salário (pago pelo INSS)                     |
| **31** | Contribuição descontada segurado - Mensal                            |
| **32** | Contribuição descontada segurado - 13° Salário                       |
| **34** | SEST                                                                 |
| **35** | SENAT                                                                |
| **51** | Salário-família                                                      |
| **61** | Complemento salário-mínimo - RPPS                                    |
| **91** | Suspensa judicial - Mensal                                           |
| **92** | Suspensa judicial - 13° Salário                                      |
| **93** | Suspensa judicial - Salário maternidade                              |
| **94** | Suspensa judicial - Salário maternidade 13°                          |
| **95** | Suspensa judicial - Exclusiva Empregador mensal                      |
| **96** | Suspensa judicial - Exclusiva Empregador 13°                         |
| **97** | Suspensa judicial - Exclusiva Empregador sal. mat.                   |
| **98** | Suspensa judicial - Exclusiva Empregador sal. mat. 13°               |

> **Nota:** Códigos 91-98 requerem processo judicial registrado no evento S-1070.

### 5.2. codIncIRRF — Tabela 21 (Imposto de Renda Retido na Fonte)

| Código        | Descrição                                              |
| ------------- | ------------------------------------------------------ |
| **00**        | Rendimento não tributável                              |
| **01**        | Não tributável (acordos internacionais)                |
| **09**        | Outras verbas não consideradas como base de cálculo    |
| **11**        | Remuneração mensal                                     |
| **12**        | 13° Salário                                            |
| **13**        | Férias                                                 |
| **14**        | PLR (Participação nos Lucros e Resultados)             |
| **15**        | RRA (Rendimentos Recebidos Acumuladamente)             |
| **31**        | Retenção IRRF - Remuneração mensal                     |
| **32**        | Retenção IRRF - 13° Salário                            |
| **33**        | Retenção IRRF - Férias                                 |
| **34**        | Retenção IRRF - PLR                                    |
| **35**        | Retenção IRRF - RRA                                    |
| **41**        | Dedução PSO - Remuneração mensal                       |
| **42**        | Dedução PSO - 13° salário                              |
| **43**        | Dedução PSO - Férias                                   |
| **44**        | Dedução PSO - RRA                                      |
| **46**        | Previdência Privada - mensal                           |
| **47**        | Previdência Privada - 13° salário                      |
| **51**        | Pensão Alimentícia - Remuneração mensal                |
| **52**        | Pensão Alimentícia - 13° salário                       |
| **53**        | Pensão Alimentícia - Férias                            |
| **54**        | Pensão Alimentícia - PLR                               |
| **55**        | Pensão Alimentícia - RRA                               |
| **61**        | FAPI - Remuneração mensal                              |
| **62**        | FAPI - 13° salário                                     |
| **63**        | Funpresp - Remuneração mensal                          |
| **64**        | Funpresp - 13° salário                                 |
| **68**        | Pensão alimentícia - Férias                            |
| **70**        | Parcela Isenta 65 anos - Mensal                        |
| **71**        | Parcela Isenta 65 anos - 13° salário                   |
| **72**        | Diárias                                                |
| **73**        | Ajuda de custo                                         |
| **74**        | Indenização/rescisão/PDV/acidente                      |
| **75**        | Abono pecuniário                                       |
| **76**        | Pensão/aposentadoria moléstia grave - Mensal           |
| **77**        | Pensão/aposentadoria moléstia grave - 13°              |
| **78**        | Valores pagos a titular/sócio ME/EPP                   |
| **79**        | Outras isenções                                        |
| **81**        | Depósito judicial                                      |
| **82**        | Compensação judicial do ano calendário                 |
| **83**        | Compensação judicial de anos anteriores                |
| **91**        | Incidência suspensa judicial - Remuneração mensal      |
| **92**        | Incidência suspensa judicial - 13° salário             |
| **93**        | Incidência suspensa judicial - Férias                  |
| **94**        | Incidência suspensa judicial - PLR                     |
| **95**        | Incidência suspensa judicial - RRA                     |
| **702**       | Bolsa médico residente - mensal **(NOVO S-1.3)**       |
| **703**       | Bolsa médico residente - 13° **(NOVO S-1.3)**          |
| **704**       | Juros de mora por atraso de pagamento **(NOVO S-1.3)** |
| **9012-9064** | Códigos compostos para suspensão judicial              |

### 5.3. codIncFGTS — Tabela 22 (FGTS)

| Código | Descrição                                      |
| ------ | ---------------------------------------------- |
| **00** | Não é Base de Cálculo do FGTS                  |
| **11** | Base de Cálculo do FGTS                        |
| **12** | Base de Cálculo do FGTS 13° salário            |
| **21** | Base de cálculo FGTS Rescisório (aviso prévio) |
| **91** | Incidência suspensa judicial                   |
| **92** | Incidência suspensa judicial (13°)             |
| **93** | Incidência suspensa judicial (aviso prévio)    |

> **Regex de validação do XSD:** `^(00|11|12|21|91|92|93)$`

---

## 6. Comunicação via SOAP 1.1

O eSocial **NÃO usa REST**. Toda comunicação é via **SOAP 1.1**.

### 6.1. Envelope SOAP para EnviarLoteEventos

```xml
<soapenv:Envelope
    xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/"
    xmlns:v1="http://www.esocial.gov.br/servicos/empregador/lote/eventos/envio/v1_1_1">
  <soapenv:Header/>
  <soapenv:Body>
    <v1:EnviarLoteEventos>
      <v1:loteEventos>
        <eSocial xmlns="http://www.esocial.gov.br/schema/lote/eventos/envio/v1_1_1"
                 xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
          <envioLoteEventos grupo="1">
            <ideEmpregador>
              <tpInsc>1</tpInsc>
              <nrInsc>12345678</nrInsc>
            </ideEmpregador>
            <ideTransmissor>
              <tpInsc>1</tpInsc>
              <nrInsc>12345678000195</nrInsc>  <!-- CNPJ completo 14 dígitos -->
            </ideTransmissor>
            <eventos>
              <evento Id="ID1123456780000002026032710370000001">
                <!-- XML do S-1010 JÁ ASSINADO digitalmente vai aqui -->
              </evento>
              <!-- Máximo 50 eventos por lote -->
            </eventos>
          </envioLoteEventos>
        </eSocial>
      </v1:loteEventos>
    </v1:EnviarLoteEventos>
  </soapenv:Body>
</soapenv:Envelope>
```

### 6.2. Parâmetro `grupo`

| Valor | Tipo de Eventos                                                                    |
| ----- | ---------------------------------------------------------------------------------- |
| `1`   | **Eventos de Tabela** (S-1000, S-1005, **S-1010**, S-1020, S-1030, S-1050, S-1070) |
| `2`   | Eventos Não Periódicos (S-2200, S-2205, etc.)                                      |
| `3`   | Eventos Periódicos (S-1200, S-1210, S-1299, etc.)                                  |

### 6.3. Headers HTTP Obrigatórios

```
Content-Type: text/xml;charset=UTF-8
SOAPAction: "http://www.esocial.gov.br/servicos/empregador/lote/eventos/envio/v1_1_1/ServicoEnviarLoteEventos/EnviarLoteEventos"
Content-Length: {tamanho}
```

### 6.4. Limites

- **Máximo 50 eventos por lote**
- Autenticação via **mutual TLS** com o mesmo certificado A1

---

## 7. URLs dos Web Services

### 7.1. Produção Restrita (Homologação) — usar durante desenvolvimento

| Serviço              | URL                                                                                                                       |
| -------------------- | ------------------------------------------------------------------------------------------------------------------------- |
| **Enviar Lote**      | `https://webservices.producaorestrita.esocial.gov.br/servicos/empregador/enviarloteeventos/WsEnviarLoteEventos.svc`       |
| **Consultar Lote**   | `https://webservices.producaorestrita.esocial.gov.br/servicos/empregador/consultarloteeventos/WsConsultarLoteEventos.svc` |
| **Download Eventos** | `https://webservices.producaorestrita.esocial.gov.br/servicos/empregador/dwlcirurgico/WsSolicitarDownloadEventos.svc`     |

### 7.2. Produção (ambiente real)

| Serviço              | URL                                                                                                               |
| -------------------- | ----------------------------------------------------------------------------------------------------------------- |
| **Enviar Lote**      | `https://webservices.envio.esocial.gov.br/servicos/empregador/enviarloteeventos/WsEnviarLoteEventos.svc`          |
| **Consultar Lote**   | `https://webservices.consulta.esocial.gov.br/servicos/empregador/consultarloteeventos/WsConsultarLoteEventos.svc` |
| **Download Eventos** | `https://webservices.download.esocial.gov.br/servicos/empregador/dwlcirurgico/WsSolicitarDownloadEventos.svc`     |

> **WSDL:** Adicionar `?singleWsdl` a qualquer URL acima para obter a definição completa do serviço.

---

## 8. Assinatura Digital XML (Certificado A1)

### 8.1. Regras Gerais

- Cada evento individual é assinado **ANTES** de ser colocado no envelope SOAP
- A assinatura é do tipo **enveloped** (fica DENTRO do XML do evento)
- O `<Signature>` fica como **último filho** de `<eSocial>`, após o `<evtTabRubrica>`
- O certificado deve ser **ICP-Brasil A1** (arquivo PFX/PKCS#12)
- O **mesmo certificado** é usado para assinar os XMLs E para autenticação mTLS

### 8.2. Especificações Técnicas

| Parâmetro                   | Valor                                                                         |
| --------------------------- | ----------------------------------------------------------------------------- |
| **Algoritmo de Assinatura** | RSA-SHA256 (`http://www.w3.org/2001/04/xmldsig-more#rsa-sha256`)              |
| **Algoritmo de Digest**     | SHA-256 (`http://www.w3.org/2001/04/xmlenc#sha256`)                           |
| **Canonicalization**        | C14N (`http://www.w3.org/TR/2001/REC-xml-c14n-20010315`)                      |
| **Transform 1**             | Enveloped signature (`http://www.w3.org/2000/09/xmldsig#enveloped-signature`) |
| **Transform 2**             | C14N (`http://www.w3.org/TR/2001/REC-xml-c14n-20010315`)                      |
| **Reference URI**           | `""` (vazio = assina o documento todo, excluindo o próprio `<Signature>`)     |

### 8.3. Estrutura do XML Assinado

```xml
<eSocial xmlns="http://www.esocial.gov.br/schema/evt/evtTabRubrica/vS01_03_00">
  <evtTabRubrica Id="ID1...">
    <!-- conteúdo do evento -->
  </evtTabRubrica>
  <Signature xmlns="http://www.w3.org/2000/09/xmldsig#">
    <SignedInfo>
      <CanonicalizationMethod Algorithm="http://www.w3.org/TR/2001/REC-xml-c14n-20010315"/>
      <SignatureMethod Algorithm="http://www.w3.org/2001/04/xmldsig-more#rsa-sha256"/>
      <Reference URI="">
        <Transforms>
          <Transform Algorithm="http://www.w3.org/2000/09/xmldsig#enveloped-signature"/>
          <Transform Algorithm="http://www.w3.org/TR/2001/REC-xml-c14n-20010315"/>
        </Transforms>
        <DigestMethod Algorithm="http://www.w3.org/2001/04/xmlenc#sha256"/>
        <DigestValue>BASE64_DO_HASH_SHA256</DigestValue>
      </Reference>
    </SignedInfo>
    <SignatureValue>BASE64_DA_ASSINATURA_RSA</SignatureValue>
    <KeyInfo>
      <X509Data>
        <X509Certificate>BASE64_DO_CERTIFICADO_PUBLICO</X509Certificate>
      </X509Data>
    </KeyInfo>
  </Signature>
</eSocial>
```

### 8.4. Validação do Certificado pelo eSocial

Para eventos de empresa (CNPJ):

- O **CNPJ básico** (8 primeiros dígitos) do certificado deve ser igual ao CNPJ básico do empregador
- O certificado deve ser da **matriz** (filial não serve diretamente)
- Também aceita **procuração eletrônica** (transmissão por terceiros autorizados)

### 8.5. Bibliotecas para Assinatura

| Linguagem   | Biblioteca                | Notas                                         |
| ----------- | ------------------------- | --------------------------------------------- |
| **Node.js** | `xml-crypto`              | Biblioteca mais usada para XML DSig em Node   |
| **Node.js** | Chilkat `XmlDSigGen`      | Alternativa comercial                         |
| **Python**  | `signxml`                 | Simples e direto                              |
| **Python**  | `lxml` + `xmlsec`         | Mais controle, `pip install xmlsec pyOpenSSL` |
| **PHP**     | `nfephp-org/sped-esocial` | Implementação completa de referência          |

---

## 9. Cadeia de Certificados Serpro

Para se conectar ao web service do eSocial, é necessário ter a **cadeia de certificados do Serpro** instalada como CA confiável no sistema/aplicação:

| Certificado               | Onde instalar                         |
| ------------------------- | ------------------------------------- |
| **AC Raiz Brasileira v5** | Trusted Root (Raiz Confiável)         |
| **AC SERPRO v4**          | Intermediate CAs (CAs Intermediárias) |
| **AC SERPRO Final v5**    | Intermediate CAs (CAs Intermediárias) |

**Download:** `https://certificados.serpro.gov.br/serproacf/certificate-chain`

Sem esses certificados, a conexão HTTPS (mTLS) falhará com erro de SSL/TLS.

---

## 10. Fluxo Completo de Envio

```
┌─────────────────────────────────────────────────────────────────────┐
│  FLUXO DE ENVIO S-1010 (ALTERAÇÃO DE RUBRICA)                     │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  1. MONTAR XML                                                      │
│     └─ Criar XML do S-1010 com <alteracao>                         │
│        └─ Preencher codIncCP, codIncIRRF, codIncFGTS novos         │
│        └─ ⚠️ Enviar TODOS os campos, não só os alterados           │
│                                                                     │
│  2. GERAR ID DO EVENTO                                              │
│     └─ ID{tpInsc}{nrInsc14}{timestamp}{seq5}                      │
│                                                                     │
│  3. ASSINAR XML                                                     │
│     └─ Ler certificado A1 (PFX) com senha                         │
│     └─ Assinar com RSA-SHA256 + C14N                               │
│     └─ Inserir <Signature> como último filho de <eSocial>          │
│                                                                     │
│  4. EMPACOTAR NO ENVELOPE SOAP                                     │
│     └─ Colocar XML assinado dentro de <evento Id="...">           │
│     └─ grupo="1" (eventos de tabela)                               │
│     └─ Máximo 50 eventos por lote                                  │
│                                                                     │
│  5. ENVIAR VIA HTTPS + mTLS                                        │
│     └─ POST para WsEnviarLoteEventos.svc                          │
│     └─ Usar mesmo certificado A1 para autenticação TLS            │
│     └─ Headers: Content-Type + SOAPAction                          │
│                                                                     │
│  6. RECEBER PROTOCOLO                                               │
│     └─ Resposta contém protocoloEnvio                              │
│     └─ Exemplo: "1.2.202603.0000000000000007638"                   │
│                                                                     │
│  7. AGUARDAR PROCESSAMENTO                                          │
│     └─ Tipicamente alguns segundos a minutos                       │
│                                                                     │
│  8. CONSULTAR RESULTADO                                             │
│     └─ POST para WsConsultarLoteEventos.svc                       │
│     └─ Enviar protocoloEnvio recebido no passo 6                  │
│                                                                     │
│  9. VERIFICAR RESPOSTA                                              │
│     └─ Sucesso: recebe nrRecibo (número do recibo definitivo)      │
│     └─ Erro: recebe código de erro + descrição                     │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 11. Mudanças Específicas do S-1.3 para o S-1010

| Mudança                          | Detalhes                                                                                                                           |
| -------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------- |
| Novo campo `codIncPisPasep`      | Incidência de PIS/PASEP em `dadosRubrica`                                                                                          |
| Novo grupo `ideProcessoPisPasep` | Processos judiciais relacionados a PIS/PASEP                                                                                       |
| Novos códigos Tabela 21 (IRRF)   | **702** (Bolsa médico residente - mensal), **703** (Bolsa médico residente - 13°), **704** (Juros de mora por atraso de pagamento) |

---

## 12. Documentação Oficial — Links de Referência

| Documento                             | URL                                                                                                              |
| ------------------------------------- | ---------------------------------------------------------------------------------------------------------------- |
| Página principal documentação técnica | `https://www.gov.br/esocial/pt-br/documentacao-tecnica`                                                          |
| Manual do Desenvolvedor v1.15 (PDF)   | `https://www.gov.br/esocial/pt-br/documentacao-tecnica/manuais/manualorientacaodesenvolvedoresocialv1-15.pdf`    |
| MOS S-1.3 Consolidada (PDF)           | `https://www.gov.br/esocial/pt-br/documentacao-tecnica/manuais/mos-s-1-3-consolidada-ate-a-no-s-1-3-08-2026.pdf` |
| Leiautes S-1.3 NT 06/2026 (ZIP/PDF)   | `https://www.gov.br/esocial/pt-br/documentacao-tecnica/manuais/nota-tecnica-s-1-3-06-2026-pdf.zip`               |
| Esquemas XSD v.S.01.03.00 (ZIP)       | `https://www.gov.br/esocial/pt-br/documentacao-tecnica/manuais/2026-02-13_esquemas_xsd_v_s_01_03_00.zip`         |
| Consulta pública de tabelas eSocial   | `https://frontend.esocial.gov.br/adm/`                                                                           |
| Produção Restrita - orientações       | `https://www.gov.br/esocial/pt-br/documentacao-tecnica/producao-restrita`                                        |
| Orientações assinatura digital        | `https://www.gov.br/esocial/pt-br/documentacao-tecnica/orientacoes-assinatura-digital`                           |
| Cadeia de certificados Serpro         | `https://certificados.serpro.gov.br/serproacf/certificate-chain`                                                 |

---

## 13. Repositórios Open-Source de Referência

| Repositório                 | Linguagem | Notas                                                                                                    |
| --------------------------- | --------- | -------------------------------------------------------------------------------------------------------- |
| **nfephp-org/sped-esocial** | PHP       | Implementação mais completa. Suporta S-1.3, assinatura, todos os eventos. Gold standard para referência. |
| **tst-labs/esocial**        | Java      | Implementação do TST (Tribunais do Trabalho). 131 stars, 24 releases.                                    |

---

## 14. Resumo das Decisões Técnicas para o Easy Social

### O que precisamos implementar:

1. **Leitura de certificado A1 (PFX)** — o usuário fará upload do arquivo .pfx e digitará a senha
2. **Montagem do XML S-1010** — modo `<alteracao>` com os campos codIncCP, codIncIRRF, codIncFGTS corrigidos
3. **Assinatura XML** — RSA-SHA256 com enveloped signature usando o certificado A1
4. **Envelope SOAP** — empacotar evento(s) assinado(s) no formato de lote (grupo=1, max 50)
5. **Envio HTTPS + mTLS** — POST para o web service com certificado A1 como client cert
6. **Consulta de resultado** — polling do WsConsultarLoteEventos com o protocoloEnvio
7. **Tratamento de erros** — exibir erros do eSocial de forma amigável

### Opções de stack:

- **Node.js (backend existente):** `xml-crypto` para assinatura, `axios`/`node-fetch` com `https.Agent` para mTLS
- **Python (FastAPI existente):** `signxml` ou `xmlsec` para assinatura, `requests` com certificado client
- **Recomendação:** Usar o backend que for estudado na Fase 2 (o1 pro 4.6) como base

---

> **Próximo passo:** Fase 2 — Estudar o repositório "o1 pro 4.6" que já se comunica com o eSocial em homologação
