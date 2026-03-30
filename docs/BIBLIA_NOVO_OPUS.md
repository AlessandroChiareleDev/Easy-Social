# BÍBLIA — Integração eSocial S-1010 Web Service (Easy Social)

> **Para:** Alex (Engenheiro de Software Opus 4.6)  
> **De:** Equipe Easy Social  
> **Data:** 27/03/2026  
> **Objetivo:** Este documento contém TUDO que você precisa para implementar a comunicação com o web service do eSocial para envio de eventos S-1010 (Tabela de Rubricas) no projeto Easy Social.  
> **Abordagem:** TDD — os testes definem as features. Primeiro crie os testes em homologação, depois implemente até eles passarem.

---

## PARTE 1 — CONTEXTO DO PROJETO EASY SOCIAL

### 1.1 O que é o Easy Social

Sistema web para gestão e correção de rubricas do eSocial. O sistema:

1. Recebe upload de planilha DIRF.xlsx com dados de rubricas
2. Cruza dados entre tabelas (analise_natureza vs tabela_eventos_gl + tabela_eb)
3. Detecta divergências de natureza/incidência nas rubricas
4. Permite que o usuário corrija as naturezas
5. **[A IMPLEMENTAR]** Envia as correções ao eSocial via web service S-1010

### 1.2 Stack Atual

| Componente   | Tecnologia                                 | Detalhes                                                                           |
| ------------ | ------------------------------------------ | ---------------------------------------------------------------------------------- |
| **Backend**  | Node.js + Express 5 + TypeScript           | Porta 3333, entry: `backend/src/app.ts`                                            |
| **Frontend** | Vue 3 + Vite + TypeScript + Tailwind CSS 4 | Porta 5173                                                                         |
| **Banco**    | PostgreSQL 16.12                           | DB: `easy_social_db`, User: `easy_social_user`, Pw: `sua_senha_segura`, Port: 5432 |
| **Python**   | FastAPI                                    | Porta 8000, scripts auxiliares em `python-scripts/`                                |
| **Design**   | Dark theme glassmorphism                   | Orbit Navy #0A1024, Electric Blue #0066FF                                          |

### 1.3 Tabelas Existentes no Banco

| Tabela                   | Rows | Descrição                                                                                                |
| ------------------------ | ---- | -------------------------------------------------------------------------------------------------------- |
| `analise_natureza`       | 455  | Rubricas do empregador com análise (col_a=código, col_b=nome, col_c=natureza, col_d=status VERIFICAR/OK) |
| `analise_natureza_certo` | ~91  | Rubricas já corrigidas (com natureza_nova aplicada)                                                      |
| `dinamica`               | 276  | Dados dinâmicos                                                                                          |
| `tabela_eventos_gl`      | 1145 | Tabela GL do eSocial (eventos com incidências)                                                           |
| `tabela_eb`              | 1224 | Tabela EB do eSocial                                                                                     |
| `tabela_cruzamento`      | —    | Resultado do INNER JOIN entre analise_natureza e tabela_eb                                               |
| `correcoes_staging`      | ~91  | Fila de correções pendentes/aplicadas                                                                    |
| `auditoria_naturezas`    | —    | Log de auditoria das correções                                                                           |

### 1.4 O que já existe de fluxo

```
Upload DIRF.xlsx → Popular tabelas → Detectar divergências (Ponto 1)
→ Validar naturezas → Usuário corrige → Confirmar alterações
→ Cruzar dados (INNER JOIN) → VER resultado
→ [FALTA] Enviar ao eSocial via S-1010 web service
```

### 1.5 Dados-Chave da Tabela Cruzamento

O resultado do cruzamento contém as colunas:

- **Código** (col_a) — código da rubrica
- **Nome Evento** (col_b) — nome da rubrica
- **Natureza E-social** (col_c) — código+nome da natureza
- **Cód. INSS** — código de incidência INSS (extraído via raw_data JSONB da tabela_eb)
- **Cód. IRRF** — código de incidência IRRF
- **Cód. FGTS** — código de incidência FGTS

Estes dados são exatamente o que precisa ir no S-1010 `<alteracao>`.

### 1.6 Autenticação Existente

Multi-tenant com login: admin/admin123, Ana/123321, Lobo/180306.

---

## PARTE 2 — O QUE É O eSocial S-1010

### 2.1 Evento S-1010 (evtTabRubrica)

O S-1010 é o evento de **Tabela de Rubricas** do eSocial. Por meio dele, empregadores cadastram, alteram ou excluem rubricas. Cada rubrica tem campos de incidência tributária que dizem como aquele valor é tratado para fins de INSS, IRRF e FGTS.

### 2.2 Modos de Operação

| Modo          | Tag XML       | Quando usar                                          |
| ------------- | ------------- | ---------------------------------------------------- |
| **Inclusão**  | `<inclusao>`  | Cadastrar rubrica nova                               |
| **Alteração** | `<alteracao>` | Modificar rubrica existente ← **é o que precisamos** |
| **Exclusão**  | `<exclusao>`  | Remover rubrica                                      |

### 2.3 Campos de Incidência — o que estamos corrigindo

| Campo XML        | Tabela Ref | Tributo   | Descrição                        |
| ---------------- | ---------- | --------- | -------------------------------- |
| `codIncCP`       | Tabela 04  | **INSS**  | Contribuição Previdenciária      |
| `codIncIRRF`     | Tabela 21  | **IRRF**  | Imposto de Renda Retido na Fonte |
| `codIncFGTS`     | Tabela 22  | **FGTS**  | Fundo de Garantia                |
| `codIncPisPasep` | —          | PIS/PASEP | Novo no S-1.3                    |

### 2.4 Versão Atual

- **Leiaute:** S-1.3 (vigente em produção e produção restrita)
- **Namespace do evento:** `http://www.esocial.gov.br/schema/evt/evtTabRubrica/vS01_03_00`
- **Namespace do lote:** `http://www.esocial.gov.br/schema/lote/eventos/envio/v1_1_1`
- **Namespace do serviço SOAP:** `http://www.esocial.gov.br/servicos/empregador/lote/eventos/envio/v1_1_0`

---

## PARTE 3 — XML DO EVENTO S-1010 (ALTERAÇÃO)

### 3.1 Estrutura Completa

```xml
<eSocial xmlns="http://www.esocial.gov.br/schema/evt/evtTabRubrica/vS01_03_00">
  <evtTabRubrica Id="ID1123456780000002026032710370000001">
    <ideEvento>
      <tpAmb>2</tpAmb>           <!-- 1=Produção, 2=Produção Restrita -->
      <procEmi>1</procEmi>       <!-- 1=App do empregador -->
      <verProc>S_1.3.0</verProc> <!-- Versão do app emissor -->
    </ideEvento>
    <ideEmpregador>
      <tpInsc>1</tpInsc>         <!-- 1=CNPJ -->
      <nrInsc>12345678</nrInsc>  <!-- 8 dígitos RAIZ do CNPJ -->
    </ideEmpregador>
    <infoRubrica>
      <alteracao>
        <ideRubrica>
          <codRubr>CODIGO001</codRubr>
          <ideTabRubr>1</ideTabRubr>
          <iniValid>2026-03</iniValid>
        </ideRubrica>
        <dadosRubrica>
          <!-- ⚠️ TODOS os campos obrigatórios, mesmo os que não mudaram -->
          <dscRubr>HORAS EXTRAS 50%</dscRubr>
          <natRubr>1003</natRubr>
          <tpRubr>1</tpRubr>
          <codIncCP>11</codIncCP>
          <codIncIRRF>11</codIncIRRF>
          <codIncFGTS>11</codIncFGTS>
          <codIncPisPasep>11</codIncPisPasep>
          <tetoRemun>N</tetoRemun>
        </dadosRubrica>
      </alteracao>
    </infoRubrica>
  </evtTabRubrica>
</eSocial>
```

### 3.2 Regras Críticas do XML

1. **TODOS os campos de `dadosRubrica` são obrigatórios na alteração**, não só os que mudaram
2. O `Id` do evento deve usar I **maiúsculo** — nunca `id` minúsculo (erro SERPRO)
3. `nrInsc` do empregador deve ser **CNPJ RAIZ (8 dígitos)**, não o completo (regra 646 eSocial)
4. `codRubr` máximo 30 caracteres, **não pode começar com "eSocial"**
5. `iniValid` no formato **AAAA-MM**

### 3.3 Formato do ID do Evento

```
ID{tpInsc}{nrInsc(14 dígitos padded)}{AAAA}{MM}{DD}{HH}{mm}{ss}{seq(5)}
```

Exemplo: `ID1123456780000002026032710370000001`

- Máximo 36 caracteres
- O ID do `<evento>` no lote **DEVE SER IDÊNTICO** ao `Id` interno do evento (erro 555 se diferente!)

---

## PARTE 4 — TABELAS DE INCIDÊNCIA (VALORES PERMITIDOS)

### 4.1 codIncCP — Tabela 04 (INSS)

| Código | Descrição                                      |
| ------ | ---------------------------------------------- |
| 00     | Não é base de cálculo                          |
| 01     | Não é base de cálculo (acordos internacionais) |
| 11     | Mensal                                         |
| 12     | 13° Salário                                    |
| 13     | Exclusiva Empregador - mensal                  |
| 14     | Exclusiva Empregador - 13°                     |
| 15     | Exclusiva do segurado - mensal                 |
| 16     | Exclusiva do segurado - 13°                    |
| 21     | Salário maternidade mensal (Empregador)        |
| 22     | Salário maternidade 13° (Empregador)           |
| 23     | Auxílio doença mensal - RPPS                   |
| 24     | Auxílio doença 13° - RPPS                      |
| 25     | Salário maternidade mensal (INSS)              |
| 26     | Salário maternidade 13° (INSS)                 |
| 31     | Contribuição descontada segurado - Mensal      |
| 32     | Contribuição descontada segurado - 13°         |
| 34     | SEST                                           |
| 35     | SENAT                                          |
| 51     | Salário-família                                |
| 61     | Complemento salário-mínimo - RPPS              |
| 91-98  | Suspensas judicialmente (requer S-1070)        |

### 4.2 codIncIRRF — Tabela 21

| Código  | Descrição                                        |
| ------- | ------------------------------------------------ |
| 00      | Não tributável                                   |
| 01      | Não tributável (acordos internacionais)          |
| 09      | Outras verbas não base de cálculo                |
| 11      | Remuneração mensal                               |
| 12      | 13° Salário                                      |
| 13      | Férias                                           |
| 14      | PLR                                              |
| 15      | RRA                                              |
| 31-35   | Retenção IRRF (mensal/13°/férias/PLR/RRA)        |
| 41-44   | Dedução PSO (mensal/13°/férias/RRA)              |
| 46-47   | Previdência Privada (mensal/13°)                 |
| 51-55   | Pensão Alimentícia (mensal/13°/férias/PLR/RRA)   |
| 61-64   | FAPI/Funpresp (mensal/13°)                       |
| 68      | Pensão alimentícia - Férias                      |
| 70-79   | Isenções diversas                                |
| 81-83   | Depósito/Compensação judicial                    |
| 91-95   | Suspensas judicialmente                          |
| 702-704 | Novos S-1.3 (bolsa médico residente, juros mora) |

### 4.3 codIncFGTS — Tabela 22

| Código | Descrição                           |
| ------ | ----------------------------------- |
| 00     | Não é base de cálculo               |
| 11     | Base de cálculo FGTS                |
| 12     | Base de cálculo FGTS 13°            |
| 21     | Base FGTS rescisório (aviso prévio) |
| 91     | Suspensa judicial                   |
| 92     | Suspensa judicial (13°)             |
| 93     | Suspensa judicial (aviso prévio)    |

Regex XSD: `^(00|11|12|21|91|92|93)$`

---

## PARTE 5 — ASSINATURA DIGITAL (CERTIFICADO A1)

### 5.1 Requisitos

- Certificado **ICP-Brasil A1** (arquivo .pfx / PKCS#12) — **obrigatório, não aceita self-signed**
- O mesmo certificado serve para **assinar XMLs** E para **autenticação mTLS**
- CNPJ básico (8 dígitos) do certificado deve ser igual ao do empregador

### 5.2 Especificações da Assinatura

| Parâmetro            | Valor                                                   |
| -------------------- | ------------------------------------------------------- |
| Tipo                 | Enveloped (dentro do XML)                               |
| Algoritmo Assinatura | RSA-SHA256                                              |
| Algoritmo Digest     | SHA-256                                                 |
| Canonicalization     | C14N 1.0 sem comentários                                |
| Transform 1          | `http://www.w3.org/2000/09/xmldsig#enveloped-signature` |
| Transform 2          | `http://www.w3.org/TR/2001/REC-xml-c14n-20010315`       |
| Reference URI        | `""` (vazio — assina documento inteiro)                 |
| Posição              | `<Signature>` como último filho de `<eSocial>`          |

### 5.3 XML Assinado (resultado final)

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
        <DigestValue>BASE64_HASH</DigestValue>
      </Reference>
    </SignedInfo>
    <SignatureValue>BASE64_ASSINATURA</SignatureValue>
    <KeyInfo>
      <X509Data>
        <X509Certificate>BASE64_CERTIFICADO</X509Certificate>
      </X509Data>
    </KeyInfo>
  </Signature>
</eSocial>
```

### 5.4 Código de Referência (Python — funciona em produção restrita comprovado)

```python
from signxml import XMLSigner
import signxml
from cryptography.hazmat.primitives.serialization import pkcs12, Encoding, PrivateFormat, NoEncryption
from cryptography.hazmat.backends import default_backend
from lxml import etree

# 1. Carregar certificado .pfx
with open(pfx_path, 'rb') as f:
    pfx_data = f.read()
private_key, certificate, additional_certs = pkcs12.load_key_and_certificates(
    pfx_data, password.encode(), backend=default_backend()
)

# 2. Parsear XML
root = etree.parse(xml_path).getroot()

# 3. Garantir Id maiúsculo no evento
evento_element = root.find('.//{*}evtTabRubrica')
if evento_element.get('id'):
    del evento_element.attrib['id']
evento_element.set('Id', evento_id)

# 4. Configurar e assinar
signer = XMLSigner(
    method=signxml.methods.enveloped,
    signature_algorithm="rsa-sha256",
    digest_algorithm="sha256",
    c14n_algorithm="http://www.w3.org/TR/2001/REC-xml-c14n-20010315"
)
cert_pem = certificate.public_bytes(Encoding.PEM)
signed_root = signer.sign(root, key=private_key, cert=cert_pem)

# 5. Salvar
with open(signed_path, 'wb') as f:
    f.write(etree.tostring(signed_root, pretty_print=True, xml_declaration=True, encoding='UTF-8'))
```

### 5.5 Bugs Conhecidos da Assinatura (já resolvidos no código de referência)

| Bug                         | Erro SERPRO | Solução                                       |
| --------------------------- | ----------- | --------------------------------------------- |
| URI não vazia na assinatura | 142         | Usar URI="" (signxml faz por padrão)          |
| `id` minúsculo no evento    | Rejeição    | Corrigir para `Id` maiúsculo antes de assinar |

---

## PARTE 6 — ENVELOPE SOAP E ENVIO

### 6.1 Protocolo: SOAP 1.1

O eSocial **NÃO usa REST**. A comunicação é **SOAP 1.1** sobre HTTPS com mTLS.

### 6.2 Envelope SOAP Completo

```xml
<?xml version="1.0" encoding="UTF-8"?>
<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/"
                  xmlns:v1="http://www.esocial.gov.br/servicos/empregador/lote/eventos/envio/v1_1_0">
   <soapenv:Header/>
   <soapenv:Body>
      <v1:EnviarLoteEventos>
         <v1:loteEventos>
            <eSocial xmlns="http://www.esocial.gov.br/schema/lote/eventos/envio/v1_1_1">
               <envioLoteEventos grupo="1">
                  <ideEmpregador>
                     <tpInsc>1</tpInsc>
                     <nrInsc>12345678</nrInsc>
                  </ideEmpregador>
                  <ideTransmissor>
                     <tpInsc>1</tpInsc>
                     <nrInsc>12345678000195</nrInsc>
                  </ideTransmissor>
                  <eventos>
                     <evento Id="ID1123456780000002026032710370000001">
                        <!-- XML DO S-1010 ASSINADO (INTEIRO, COM <eSocial> wrapper) -->
                     </evento>
                  </eventos>
               </envioLoteEventos>
            </eSocial>
         </v1:loteEventos>
      </v1:EnviarLoteEventos>
   </soapenv:Body>
</soapenv:Envelope>
```

### 6.3 Regras Críticas do Envelope

| Regra            | Detalhe                                                                            |
| ---------------- | ---------------------------------------------------------------------------------- |
| `grupo="1"`      | Para S-1010 (eventos de tabela). S-2500 usa grupo=2                                |
| ID do `<evento>` | **DEVE SER IDÊNTICO** ao `Id` do evento interno (erro 555!)                        |
| CNPJ empregador  | **RAIZ 8 dígitos** no lote (regra 646)                                             |
| CNPJ transmissor | **14 dígitos completos**                                                           |
| `<?xml?>`        | Remover declaração do lote/evento antes de colocar no SOAP (duplicação causa erro) |
| Máximo           | 50 eventos por lote, 500KB total                                                   |
| XML evento       | Manter o XML assinado INTACTO (com `<eSocial>` wrapper) dentro do `<evento>`       |

### 6.4 Headers HTTP

```
Content-Type: text/xml; charset=utf-8
SOAPAction: http://www.esocial.gov.br/servicos/empregador/lote/eventos/envio/v1_1_0/ServicoEnviarLoteEventos/EnviarLoteEventos
```

### 6.5 mTLS (Mutual TLS)

O certificado A1 (.pfx) é usado TAMBÉM como client certificate na conexão HTTPS:

```python
import requests
import tempfile
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Extrair PFX → PEM temporários
temp_cert = tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.pem')
temp_key = tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.pem')
temp_cert.write(certificate.public_bytes(Encoding.PEM))
temp_cert.close()
temp_key.write(private_key.private_bytes(Encoding.PEM, PrivateFormat.TraditionalOpenSSL, NoEncryption()))
temp_key.close()

response = requests.post(
    url,
    data=soap_envelope.encode('utf-8'),
    headers=headers,
    cert=(temp_cert.name, temp_key.name),  # ← mTLS
    verify=False,  # Produção restrita tem problemas de SSL
    timeout=60
)

# Cleanup
os.unlink(temp_cert.name)
os.unlink(temp_key.name)
```

### 6.6 URLs dos Web Services

| Serviço       | Produção Restrita (Homologação)                                                                                           |
| ------------- | ------------------------------------------------------------------------------------------------------------------------- |
| **Enviar**    | `https://webservices.producaorestrita.esocial.gov.br/servicos/empregador/enviarloteeventos/WsEnviarLoteEventos.svc`       |
| **Consultar** | `https://webservices.producaorestrita.esocial.gov.br/servicos/empregador/consultarloteeventos/WsConsultarLoteEventos.svc` |

| Serviço       | Produção Real                                                                                                     |
| ------------- | ----------------------------------------------------------------------------------------------------------------- |
| **Enviar**    | `https://webservices.producao.esocial.gov.br/servicos/empregador/enviarloteeventos/WsEnviarLoteEventos.svc`       |
| **Consultar** | `https://webservices.producao.esocial.gov.br/servicos/empregador/consultarloteeventos/WsConsultarLoteEventos.svc` |

---

## PARTE 7 — CONSULTA DE RESULTADO

### 7.1 Fluxo Pós-Envio

1. Enviar lote → receber resposta SOAP com `protocoloEnvio`
2. Aguardar ≥5 segundos
3. Consultar via `WsConsultarLoteEventos` com o protocolo
4. Parsear resposta: sucesso (`nrRecibo`) ou erro com códigos

### 7.2 SOAP de Consulta

```xml
<?xml version="1.0" encoding="UTF-8"?>
<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/"
                  xmlns:v1="http://www.esocial.gov.br/servicos/empregador/lote/eventos/envio/consulta/retornoProcessamento/v1_1_0">
   <soapenv:Header/>
   <soapenv:Body>
      <v1:ConsultarLoteEventos>
         <v1:consulta>
            <eSocial xmlns="http://www.esocial.gov.br/schema/lote/eventos/envio/consulta/retornoProcessamento/v1_0_0">
               <consultaLoteEventos>
                  <protocoloEnvio>1.2.202603.0000000000200361784</protocoloEnvio>
               </consultaLoteEventos>
            </eSocial>
         </v1:consulta>
      </v1:ConsultarLoteEventos>
   </soapenv:Body>
</soapenv:Envelope>
```

### 7.3 SOAPAction da Consulta

```
SOAPAction: http://www.esocial.gov.br/servicos/empregador/lote/eventos/envio/consulta/retornoProcessamento/v1_1_0/ServicoConsultarLoteEventos/ConsultarLoteEventos
```

### 7.4 Resposta de Sucesso Real (extraída de envios reais)

```xml
<s:Envelope xmlns:s="http://schemas.xmlsoap.org/soap/envelope/">
  <s:Body>
    <EnviarLoteEventosResponse xmlns="http://www.esocial.gov.br/servicos/empregador/lote/eventos/envio/v1_1_0">
      <EnviarLoteEventosResult>
        <eSocial xmlns="http://www.esocial.gov.br/schema/lote/eventos/envio/retornoEnvio/v1_1_0">
          <retornoEnvioLoteEventos>
            <ideEmpregador>
              <tpInsc>1</tpInsc>
              <nrInsc>0596XXXX</nrInsc>
            </ideEmpregador>
            <status>
              <cdResposta>201</cdResposta>
              <descResposta>Lote Recebido com Sucesso.</descResposta>
            </status>
            <dadosRecepcaoLote>
              <dhRecepcao>2026-03-03T15:28:55.857</dhRecepcao>
              <versaoAplicativoRecepcao>0.1.0.0</versaoAplicativoRecepcao>
              <protocoloEnvio>1.2.202603.0000000000200361784</protocoloEnvio>
            </dadosRecepcaoLote>
          </retornoEnvioLoteEventos>
        </eSocial>
      </EnviarLoteEventosResult>
    </EnviarLoteEventosResponse>
  </s:Body>
</s:Envelope>
```

### 7.5 Resposta de Erro Real

```xml
<status>
  <cdResposta>401</cdResposta>
  <descResposta>Erro na validação do evento.</descResposta>
</status>
<ocorrencias>
  <ocorrencia>
    <tipo>1</tipo>
    <codigo>401</codigo>
    <descricao>Mensagem de erro específica aqui.</descricao>
  </ocorrencia>
</ocorrencias>
```

### 7.6 Parsing de Respostas (código de referência comprovado)

```python
from lxml import etree

xml_response = etree.fromstring(response.text.encode('utf-8'))

# Usar local-name() para ignorar namespaces (recomendação FORTE)
status = xml_response.xpath('//*[local-name()="cdResposta"]/text()')
descricao = xml_response.xpath('//*[local-name()="descResposta"]/text()')
protocolo = xml_response.xpath('//*[local-name()="protocoloEnvio"]/text()')
dh_recepcao = xml_response.xpath('//*[local-name()="dhRecepcao"]/text()')
ocorrencias = xml_response.xpath('//*[local-name()="ocorrencia"]')

resultado = {
    'sucesso': status[0] == '201' if status else False,
    'codigo_resposta': status[0] if status else None,
    'descricao': descricao[0] if descricao else None,
    'protocolo': protocolo[0] if protocolo else None,
    'dh_recepcao': dh_recepcao[0] if dh_recepcao else None,
    'ocorrencias': [...]
}
```

---

## PARTE 8 — GESTÃO DE CERTIFICADOS A1

### 8.1 Fluxo de Upload

1. Usuário faz upload do .pfx + digita a senha na UI
2. Backend valida: abre o .pfx com a senha, verifica se não expirou
3. Extrai metadados: CNPJ (OID 2.5.4.5 serialNumber), titular, validade, emissor, nº série
4. Salva o arquivo .pfx em disco
5. Criptografa a senha com **Fernet** e salva no banco
6. Na hora do envio: descriptografa a senha, usa o .pfx

### 8.2 Código de Referência para Carregar PFX

```python
from cryptography.hazmat.primitives.serialization import pkcs12
from cryptography.hazmat.backends import default_backend
from cryptography.fernet import Fernet

# Carregar
private_key, certificate, additional_certs = pkcs12.load_key_and_certificates(
    pfx_data, password.encode(), backend=default_backend()
)

# Verificar validade
if certificate.not_valid_after_utc < datetime.now(timezone.utc):
    raise ValueError("Certificado vencido")

# Extrair CNPJ do subject
for attr in certificate.subject:
    if attr.oid.dotted_string == '2.5.4.5':  # serialNumber
        cnpj = attr.value
        break

# Criptografar senha
fernet = Fernet(secret_key.encode())
senha_encrypted = fernet.encrypt(password.encode()).decode()
```

### 8.3 Cadeia de Certificados Serpro

Para conexão HTTPS funcionar, o sistema precisa confiar na cadeia Serpro:

- AC Raiz Brasileira v5 → Root
- AC SERPRO v4 + AC SERPRO Final v5 → Intermediate

Download: `https://certificados.serpro.gov.br/serproacf/certificate-chain`

**Na prática:** O repositório de referência usa `verify=False` e funciona — recomendamos o mesmo para produção restrita. Para produção real, considerar instalar a cadeia.

---

## PARTE 9 — ERROS CONHECIDOS E PITFALLS

### 9.1 Erros SERPRO já enfrentados em produção restrita

| Erro                     | Código | Causa                                            | Solução                                                      |
| ------------------------ | ------ | ------------------------------------------------ | ------------------------------------------------------------ |
| ID mismatch              | 555    | ID do `<evento>` no lote ≠ Id interno do evento  | Extrair o Id do XML interno com regex e usar o MESMO no lote |
| Assinatura URI não vazia | 142    | URI referenciava o Id em vez de ser vazia        | Usar URI="" (signxml faz certo por padrão)                   |
| Elemento não declarado   | 402    | Remover o `<eSocial>` wrapper do evento assinado | MANTER o XML assinado INTEIRO no lote, incluindo `<eSocial>` |
| CNPJ inválido            | 646    | CNPJ com 14 dígitos no lote                      | Usar CNPJ RAIZ (8 dígitos) para empregador                   |
| XML declaração duplicada | —      | `<?xml?>` no SOAP + no lote + no evento          | Remover `<?xml?>` do lote/evento antes de inserir no SOAP    |
| `id` minúsculo           | —      | atributo `id` em vez de `Id`                     | Corrigir para I maiúsculo antes de assinar                   |

### 9.2 Ambiente de Produção Restrita — Fatos Importantes

| Fato                             | Detalhe                                                            |
| -------------------------------- | ------------------------------------------------------------------ |
| CNPJ real obrigatório            | Não existe sandbox — produção restrita valida CNPJ/CPF reais       |
| Certificado A1 real obrigatório  | Self-signed ou teste não funciona                                  |
| Dados validados contra base real | Processos/rubricas que não existem são rejeitados                  |
| tpAmb                            | `2` para restrita, `1` para produção                               |
| Rate limit                       | Não documentado, mas 10-20 envios sequenciais não causam problemas |
| Timeout recomendado              | 60 segundos                                                        |
| Tamanho máximo                   | 50 eventos/lote, 500KB total                                       |

### 9.3 Dependências Python Necessárias

```
signxml          # Assinatura XML (enveloped, RSA-SHA256)
cryptography     # Leitura PFX, chaves, Fernet
lxml             # Parse/build XML + XPath
requests         # HTTP POST com mTLS
```

Nenhuma dependência de SO (OpenSSL, libxmlsec) — tudo roda com pip wheel.

---

## PARTE 10 — FLUXO COMPLETO A IMPLEMENTAR

### 10.1 Diagrama de Fluxo

```
FRONTEND (Vue 3)                          BACKEND                              eSocial SERPRO
═══════════════                          ═══════                              ═════════════

1. Upload .pfx + senha ────────────────→ Validar certificado
                                          Salvar .pfx + senha (Fernet)
                                          Extrair CNPJ, validade

2. Selecionar rubricas a alterar ──────→ Buscar dados da tabela_cruzamento
   (com novos códigos INSS/IRRF/FGTS)    + analise_natureza_certo

3. Preview do XML ─────────────────────→ Gerar XML S-1010 <alteracao>
   (mostrar na UI antes de enviar)        para cada rubrica selecionada

4. Confirmar envio ────────────────────→ Assinar cada XML (signxml)
                                          Montar lote SOAP (grupo=1)
                                          POST com mTLS ───────────────────→ Receber lote
                                          ←──── protocoloEnvio ──────────── Resposta 201

5. Aguardar resultado ─────────────────→ Esperar 5s
                                          Consultar lote ──────────────────→ Processar
                                          ←──── nrRecibo ou erro ────────── Retorno

6. Ver resultado na UI ←───────────────  Salvar protocolo/recibo no DB
   (sucesso ou erros detalhados)          Atualizar status da rubrica
```

### 10.2 Endpoints a Criar no Backend (Node.js/Express)

| Método | Rota                                      | Descrição                                       |
| ------ | ----------------------------------------- | ----------------------------------------------- |
| POST   | `/api/certificados/upload`                | Upload .pfx + senha, validar, salvar            |
| GET    | `/api/certificados/ativo`                 | Retornar certificado ativo                      |
| DELETE | `/api/certificados/:id`                   | Remover certificado                             |
| POST   | `/api/esocial/s1010/gerar-xml`            | Gerar XML S-1010 para rubrica(s) selecionada(s) |
| POST   | `/api/esocial/s1010/assinar`              | Assinar XML(s) com certificado A1               |
| POST   | `/api/esocial/s1010/enviar`               | Montar lote SOAP + enviar ao eSocial            |
| POST   | `/api/esocial/s1010/consultar/:protocolo` | Consultar resultado do lote                     |
| GET    | `/api/esocial/envios`                     | Listar histórico de envios                      |

### 10.3 Tabelas a Criar no PostgreSQL

```sql
-- Certificados A1
CREATE TABLE certificados_a1 (
    id SERIAL PRIMARY KEY,
    cnpj VARCHAR(14) NOT NULL,
    titular VARCHAR(255),
    emissor VARCHAR(255),
    numero_serie VARCHAR(100),
    validade_inicio TIMESTAMP,
    validade_fim TIMESTAMP,
    arquivo_path VARCHAR(500) NOT NULL,
    senha_encrypted TEXT NOT NULL,
    ativo BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Envios ao eSocial
CREATE TABLE esocial_envios (
    id SERIAL PRIMARY KEY,
    tipo_evento VARCHAR(10) NOT NULL,        -- 'S-1010'
    modo VARCHAR(20) NOT NULL,                -- 'alteracao', 'inclusao', 'exclusao'
    ambiente VARCHAR(30) NOT NULL,            -- 'producao_restrita' ou 'producao'
    grupo INTEGER NOT NULL DEFAULT 1,         -- 1=tabelas

    -- Dados da rubrica
    cod_rubrica VARCHAR(30),
    nome_rubrica VARCHAR(100),
    natureza VARCHAR(10),
    cod_inc_cp VARCHAR(5),
    cod_inc_irrf VARCHAR(5),
    cod_inc_fgts VARCHAR(5),

    -- XMLs
    xml_gerado TEXT,
    xml_assinado TEXT,
    xml_lote TEXT,
    xml_retorno_envio TEXT,
    xml_retorno_consulta TEXT,

    -- Status
    status VARCHAR(30) NOT NULL DEFAULT 'rascunho',
    -- rascunho → assinado → enviado → processado/rejeitado/erro

    -- Protocolo e recibo
    protocolo_envio VARCHAR(100),
    dh_recepcao TIMESTAMP,
    nr_recibo VARCHAR(100),

    -- Erros
    codigo_resposta VARCHAR(10),
    descricao_resposta TEXT,
    ocorrencias JSONB,

    -- Auditoria
    usuario VARCHAR(100),
    certificado_id INTEGER REFERENCES certificados_a1(id),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

---

## PARTE 11 — ABORDAGEM TDD (TESTES DEFINEM AS FEATURES)

### 11.1 Filosofia

**Os testes são o NORTE.** Cada teste descreve um resultado esperado. A implementação existe para fazer os testes passarem. Todos os testes são em **homologação (produção restrita)** — NUNCA em produção real.

### 11.2 Testes a Implementar (em ordem)

#### BLOCO 1 — Certificado A1

```
TEST-CERT-01: Upload de .pfx válido com senha correta → extrair CNPJ, titular, validade → salvar → retornar 200
TEST-CERT-02: Upload de .pfx com senha errada → retornar erro 400 "Senha incorreta"
TEST-CERT-03: Upload de .pfx vencido → retornar erro 400 "Certificado vencido"
TEST-CERT-04: Listar certificado ativo → retornar dados sem expor senha
TEST-CERT-05: Descriptografar senha do certificado → deve ser igual à original
```

#### BLOCO 2 — Geração de XML S-1010

```
TEST-XML-01: Gerar XML S-1010 de alteração para 1 rubrica → XML válido com namespace vS01_03_00
TEST-XML-02: Verificar que TODOS os campos obrigatórios estão no dadosRubrica
TEST-XML-03: Verificar que Id do evento segue formato ID{tpInsc}{nrInsc14}{timestamp}{seq5}
TEST-XML-04: Verificar que nrInsc do empregador tem 8 dígitos (CNPJ raiz)
TEST-XML-05: Verificar que codIncCP está na lista de valores válidos (Tabela 04)
TEST-XML-06: Verificar que codIncIRRF está na lista de valores válidos (Tabela 21)
TEST-XML-07: Verificar que codIncFGTS está na lista de valores válidos (Tabela 22)
TEST-XML-08: Gerar XML para lote de N rubricas (max 50) → N XMLs independentes
```

#### BLOCO 3 — Assinatura Digital

```
TEST-SIGN-01: Assinar XML com certificado A1 → <Signature> presente como último filho de <eSocial>
TEST-SIGN-02: Verificar algoritmo RSA-SHA256 na assinatura
TEST-SIGN-03: Verificar digest SHA-256
TEST-SIGN-04: Verificar URI="" (vazia) na Reference
TEST-SIGN-05: Verificar que Id do evento é maiúsculo 'Id' (não 'id')
TEST-SIGN-06: Verificar que o XML assinado ainda é XML válido (parseable)
```

#### BLOCO 4 — Envelope SOAP

```
TEST-SOAP-01: Montar envelope SOAP 1.1 com 1 evento → XML válido com namespaces corretos
TEST-SOAP-02: Verificar grupo="1" para S-1010
TEST-SOAP-03: Verificar que Id do <evento> no lote == Id interno do evento
TEST-SOAP-04: Verificar que não tem <?xml?> duplicado
TEST-SOAP-05: Verificar que XML assinado está INTACTO dentro do <evento> (com <eSocial> wrapper)
TEST-SOAP-06: Montar envelope com N eventos (max 50) → todos dentro de <eventos>
```

#### BLOCO 5 — Envio Real (Produção Restrita)

```
TEST-ENVIO-01: Enviar 1 evento S-1010 alteração ao eSocial → receber cdResposta 201 + protocoloEnvio
TEST-ENVIO-02: Verificar mTLS funciona (request não falha com erro SSL)
TEST-ENVIO-03: Verificar headers HTTP corretos (Content-Type + SOAPAction)
TEST-ENVIO-04: Enviar XML com erro proposital → receber código de erro (não crash)
TEST-ENVIO-05: Salvar protocoloEnvio no banco de dados
```

#### BLOCO 6 — Consulta de Resultado

```
TEST-CONSULTA-01: Consultar lote com protocoloEnvio válido → receber resultado
TEST-CONSULTA-02: Parsear resposta de sucesso → extrair nrRecibo
TEST-CONSULTA-03: Parsear resposta de erro → extrair código + descrição + ocorrências
TEST-CONSULTA-04: Atualizar status no banco: enviado → processado ou rejeitado
```

#### BLOCO 7 — Fluxo Completo End-to-End

```
TEST-E2E-01: Upload certificado → gerar XML → assinar → enviar → consultar → salvar resultado
TEST-E2E-02: Enviar rubrica real do tabela_cruzamento → verificar aceitação do eSocial
TEST-E2E-03: Enviar lote com 5 rubricas → todas processadas
```

### 11.3 Ordem de Implementação

```
FASE 1: Certificado (TEST-CERT-*) → feature de upload/gestão de certificados
FASE 2: XML (TEST-XML-*) → feature de geração de XML S-1010
FASE 3: Assinatura (TEST-SIGN-*) → feature de assinatura digital
FASE 4: Envelope (TEST-SOAP-*) → feature de montagem SOAP
FASE 5: Envio (TEST-ENVIO-*) → feature de envio real
FASE 6: Consulta (TEST-CONSULTA-*) → feature de consulta de retorno
FASE 7: E2E (TEST-E2E-*) → integração completa
```

---

## PARTE 12 — DECISÕES ARQUITETURAIS

### 12.1 Onde implementar o core da comunicação eSocial?

**Opção recomendada: Python (FastAPI)**

Razões:

- O código de referência comprovado é 100% Python
- Bibliotecas `signxml` + `cryptography` + `lxml` + `requests` são robustas e testadas
- O Easy Social já tem FastAPI na porta 8000
- Reaproveitamento direto do código que já funciona em produção restrita

O backend Node.js (Express) pode chamar o Python via HTTP interno, ou o frontend pode chamar o FastAPI diretamente.

### 12.2 Alternativa: Node.js

Se implementar em Node.js:

- Usar `xml-crypto` para assinatura (mais complexo que signxml)
- Usar `node-forge` ou `@peculiar/x509` para ler PFX
- Usar `axios` com `https.Agent` para mTLS
- Mais trabalho, menos código de referência comprovado

### 12.3 Armazenamento de Certificados

- Arquivo .pfx em disco (diretório protegido, não versionado)
- Senha criptografada com Fernet no PostgreSQL
- Chave Fernet em variável de ambiente (não no código)

---

## PARTE 13 — LINKS DE REFERÊNCIA

### 13.1 Documentação Oficial eSocial

| Documento                     | URL                                                                                                              |
| ----------------------------- | ---------------------------------------------------------------------------------------------------------------- |
| Documentação técnica          | `https://www.gov.br/esocial/pt-br/documentacao-tecnica`                                                          |
| Manual do Desenvolvedor v1.15 | `https://www.gov.br/esocial/pt-br/documentacao-tecnica/manuais/manualorientacaodesenvolvedoresocialv1-15.pdf`    |
| MOS S-1.3 Consolidada         | `https://www.gov.br/esocial/pt-br/documentacao-tecnica/manuais/mos-s-1-3-consolidada-ate-a-no-s-1-3-08-2026.pdf` |
| Leiautes S-1.3 NT 06/2026     | `https://www.gov.br/esocial/pt-br/documentacao-tecnica/manuais/nota-tecnica-s-1-3-06-2026-pdf.zip`               |
| Esquemas XSD S-1.3            | `https://www.gov.br/esocial/pt-br/documentacao-tecnica/manuais/2026-02-13_esquemas_xsd_v_s_01_03_00.zip`         |
| Consulta tabelas eSocial      | `https://frontend.esocial.gov.br/adm/`                                                                           |
| Cadeia certificados Serpro    | `https://certificados.serpro.gov.br/serproacf/certificate-chain`                                                 |

### 13.2 Repositório de Referência

O código de referência comprovado está em `c:\Users\xandao\Documents\GitHub\Projeto` — um sistema Python/FastAPI que já envia eventos S-2500/S-2501 ao eSocial em produção restrita com sucesso. Os arquivos reutilizáveis:

- `python-backend/esocial/esocial_client.py` (917 linhas) — cliente SOAP completo
- `python-backend/esocial/xml_signer.py` (198 linhas) — assinatura XMLDSig
- `python-backend/esocial/certificate_manager.py` (180 linhas) — gestão certificados A1

---

## PARTE 14 — CHECKLIST FINAL

Antes de considerar a feature "pronta":

- [ ] Certificado A1 pode ser uploadado e validado
- [ ] XML S-1010 de alteração é gerado corretamente com todos os campos
- [ ] XML é assinado com RSA-SHA256 + C14N + URI vazia
- [ ] Envelope SOAP é montado com grupo=1 e IDs idênticos
- [ ] Envio funciona com mTLS em produção restrita
- [ ] Resposta é parseada corretamente (sucesso e erro)
- [ ] Protocolo e recibo são salvos no banco
- [ ] Consulta de resultado funciona
- [ ] UI mostra preview do XML antes de enviar
- [ ] UI mostra resultado (sucesso/erro) após envio
- [ ] Histórico de envios é consultável
- [ ] Todos os testes passam em produção restrita

---

> **Este documento é a única referência necessária para implementar a integração eSocial S-1010 no Easy Social.**
