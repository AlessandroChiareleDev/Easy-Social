# Perguntas sobre o Repositório o1 pro 4.6 (eSocial Web Service)

> **Objetivo:** Entender TUDO sobre como esse repositório se comunica com o eSocial em produção restrita (homologação), para usar como base na implementação do Easy Social.
> 
> **Instrução:** Responda cada pergunta diretamente abaixo dela. Pode ser curto ou longo, o importante é ser preciso.

---

## 1. VISÃO GERAL DO REPOSITÓRIO

### 1.1. Qual é a URL/caminho do repositório? (GitHub? Local? Onde está?)
**R:** Repositório local em `c:\Users\xandao\Documents\GitHub\Projeto`. É um repositório Git (GitHub).

### 1.2. Qual a stack/linguagem principal? (Node.js? Python? PHP? Java? C#?)
**R:** **Python 3.13** (backend) + **JavaScript/React 19** (frontend). O núcleo da comunicação eSocial é 100% Python.

### 1.3. Quais frameworks/libs principais ele usa? (Express? FastAPI? Spring? o quê?)
**R:**
- **Backend:** FastAPI + SQLAlchemy + Pydantic + `signxml` + `cryptography` + `requests` + `lxml` + `zeep` (importado mas não usado no fluxo principal) + APScheduler
- **Frontend:** React 19 + MUI 7 (Material-UI) + react-scripts (CRA)

### 1.4. Tem frontend ou é só backend/CLI?
**R:** Tem **frontend completo** em React 19 com MUI 7. Interface web com wizard de 8 steps para S-2500, gestão de certificados, repositório de envios, e painel de consulta de retornos. O backend é uma API FastAPI que serve tanto a UI quanto processa os envios SOAP.

### 1.5. Qual a estrutura de pastas principal? (src/, lib/, services/, etc.)
**R:**
```
python-backend/
├── main.py                    # 10,000+ linhas - TODOS os endpoints FastAPI
├── config.py                  # Configuração centralizada (ambiente, URLs, secrets)
├── models.py                  # SQLAlchemy models (Certificado, Processo, ReposWebService...)
├── database.py                # Conexão SQLite
├── esocial/                   # 🔑 CORE - Comunicação eSocial
│   ├── esocial_client.py      # Cliente SOAP (917 linhas) - envio + consulta
│   ├── xml_signer.py          # Assinatura XMLDSig (198 linhas)
│   ├── certificate_manager.py # Gestão certificados A1 (180 linhas)
│   ├── xml_generator.py       # Geração XML S-2501 (1084 linhas)
│   ├── xml_validator.py       # Validação XML
│   ├── xsd_validator.py       # Validação contra XSD
│   ├── s5501_parser.py        # Parser retorno S-5501 (294 linhas)
│   ├── s5501_endpoints.py     # Endpoints S-5501
│   ├── procuracao_service.py  # Consulta procurações (250 linhas)
│   ├── comparador_dados.py    # Comparação de dados (411 linhas)
│   └── schemas/               # XSDs do eSocial
├── services/                  # Lógica de negócio (SERPRO, PDF, Excel, CSV)
├── schedulers/                # Auto-consulta S-2500/S-5501 a cada 15min
├── certificados/              # Armazenamento .pfx
├── Repositorio_XML/           # XMLs gerados, assinados e retornos
│   ├── S2500/                 # ~200+ XMLs S-2500
│   └── S2501_*.xml            # ~150+ XMLs S-2501
├── esocial.db                 # SQLite database (S-2500)
└── s2501.db                   # SQLite database (S-2501)

frontend/
├── src/components/
│   ├── wizard/                # 8 Steps do Wizard S-2500
│   │   └── Step8XMLGeneration.js  # Geração XML no frontend
│   ├── CertificadoManager.js  # Upload/gestão de certificados
│   └── ReposWebServiceS2500.js # Painel de envios/retornos
```

### 1.6. Ele já está em produção real ou só funciona em produção restrita (homologação)?
**R:** Funciona em **produção restrita** (homologação). O config padrão é `ESOCIAL_AMBIENTE = 'producao_restrita'`. As URLs de produção real estão configuradas no código e são selecionáveis, mas todo uso documentado e evidenciado nos XMLs é em produção restrita. Há centenas de XMLs com `_RETORNO_` comprovando envios reais bem-sucedidos ao SERPRO.

### 1.7. Quais eventos do eSocial ele suporta? (Só S-1010? Também S-1000, S-1020, S-1200, etc.?)
**R:** **S-2500** (Processo Trabalhista), **S-2501** (Informações de Tributos Decorrentes de Processo Trabalhista), e recebe automaticamente o **S-5501** (retorno de tributos do governo). Há também tentativas de S-1000 nos debug files. **NÃO** suporta S-1010 diretamente.

### 1.8. Ele foi feito especificamente para o S-1010 ou é um sistema genérico de comunicação eSocial?
**R:** Foi feito **especificamente para S-2500/S-2501** (processos trabalhistas). Porém, a infraestrutura de comunicação (`esocial_client.py`, `xml_signer.py`, `certificate_manager.py`) é **genérica** — funciona para qualquer evento eSocial. O cliente SOAP aceita qualquer XML assinado e qualquer grupo de envio (1=tabelas, 2=não-periódicos, etc.). **Para S-1010, bastaria gerar o XML correto e usar o mesmo pipeline de assinatura + envio.**

---

## 2. CERTIFICADO DIGITAL A1

### 2.1. Como o certificado A1 (.pfx) é carregado? (Upload via UI? Caminho fixo no código? Variável de ambiente?)
**R:** **Upload via UI** (frontend `CertificadoManager.js`). O usuário faz upload do arquivo .pfx + senha pela interface web. O backend recebe via endpoint POST, valida o certificado, extrai informações (CNPJ, titular, validade, emissor) e salva o arquivo em `python-backend/certificados/` com nome `cert_{CNPJ}_{NumeroSerie}.pfx`.

### 2.2. Como a senha do certificado é fornecida? (Input do usuário? .env? Hardcoded?)
**R:** **Input do usuário** via formulário no frontend. A senha é então **criptografada com Fernet** e armazenada na coluna `senha_encrypted` da tabela `certificados`. Na hora do envio, é descriptografada em runtime com `CertificateManager.decrypt_password()`.

### 2.3. O certificado é armazenado em algum lugar persistente ou só fica em memória?
**R:** Sim, persistente. O arquivo `.pfx` é salvo em disco no diretório `python-backend/certificados/`. Os metadados (CNPJ, titular, validade, emissor, número de série, senha criptografada) ficam no SQLite na tabela `certificados`. O campo `ativo = True/False` marca qual é o certificado ativo.

### 2.4. Qual biblioteca/módulo é usado para ler o PFX e extrair a chave privada + certificado público?
**R:** `cryptography.hazmat.primitives.serialization.pkcs12` — especificamente:
```python
from cryptography.hazmat.primitives.serialization import pkcs12, Encoding, PrivateFormat, NoEncryption

private_key, certificate, additional_certs = pkcs12.load_key_and_certificates(
    pfx_data,
    password.encode(),
    backend=default_backend()
)
```

### 2.5. Ele valida se o certificado é ICP-Brasil? Verifica validade/expiração?
**R:** **Verifica validade/expiração** — sim, lança `ValueError("Certificado vencido")` se `not_valid_after_utc < datetime.now()`. Extrai o CNPJ do campo `serialNumber` (OID 2.5.4.5) do subject X.509. **NÃO valida explicitamente se é ICP-Brasil** — não há verificação da cadeia de confiança contra raízes ICP-Brasil.

### 2.6. Como ele lida com a cadeia de certificados do Serpro? Baixa automaticamente? Está embutida no código? O usuário precisa instalar manualmente?
**R:** **Não lida explicitamente.** O `verify=False` no requests desabilita verificação SSL do servidor do SERPRO. A cadeia do certificado A1 do cliente é passada como está — se o .pfx incluir certificados intermediários, eles são carregados via `additional_certificates` no `pkcs12.load_key_and_certificates()`, mas **não são passados explicitamente** na requisição mTLS. Na prática, o SERPRO aceita sem problemas porque valida apenas o certificado leaf com a cadeia ICP-Brasil que já possui.

---

## 3. MONTAGEM DO XML DO EVENTO

### 3.1. Como o XML do S-1010 é montado? (Template string? Biblioteca de XML? Builder?)
**R:** Este repositório não implementa S-1010. Mas a lógica de montagem é:
- **S-2500:** Montado no **FRONTEND** (JavaScript!) em `Step8XMLGeneration.js`. A função `buildXML()` monta o XML completo como **template string** (f-string/template literal) usando os dados do wizard (`formData`).
- **S-2501:** Montado no **backend Python** via `xml_generator.py` (1084 linhas) usando **`lxml.etree`** (builder programático com `etree.SubElement()`).

### 3.2. De onde vêm os dados das rubricas para preencher o XML? (Banco de dados? Arquivo? API?)
**R:** Para S-2500: do **wizard de 8 steps** na interface (dados digitados pelo usuário + consultas SERPRO automáticas para CNPJ/CPF). Para S-2501: do **banco SQLite** (tabelas `ide_empregadors`, `evt_cont_procs`, `ide_trabs`, `calc_tribs`, `ResultCalc`) — dados são preenchidos e calculados no sistema.

### 3.3. Ele monta inclusão, alteração e exclusão, ou só um desses modos?
**R:** **Inclusão e retificação** (campo `indRetif`: 1=original, 2=retificação com `nrRecibo` obrigatório). Há lógica de retificação nos endpoints e evidência de XMLs `_RETIF_` no repositório. Exclusão não está implementada como fluxo completo, embora o campo `tipo` = 'D' exista no model.

### 3.4. Como o ID do evento é gerado? (Segue o padrão ID{tpInsc}{nrInsc14}{timestamp}{seq5}?)
**R:** Sim. Formato: `ID{tpInsc}{nrInsc14}{YYYYMMDDHHMMSS}{seq5}`, máximo 36 caracteres. Gerado no frontend para S-2500 e no backend para S-2501. O ID do `<evento>` no lote **DEVE ser idêntico** ao `Id` interno do evento — erro SERPRO 555 se diferente. Código relevante em `esocial_client.py`:
```python
id_match = re.search(r'<evt\w+[^>]*\s+Id="([^"]+)"', xml_evento_final)
id_evt_interno = id_match.group(1)
# ID do <evento> no lote = ID do evento interno (obrigatório!)
id_evento = id_evt_interno
```

### 3.5. Como ele preenche o `ideEmpregador` (tpInsc, nrInsc)? De onde vem o CNPJ?
**R:** O CNPJ vem de múltiplas fontes com fallback:
1. Tabela normalizada `S2500IdeEmpregador` (campo `nrInsc`)
2. Tabela S-2501 `IdeEmpregador` (campo `nrinsc`)

**CRÍTICO:** CNPJ do empregador no lote é truncado para **RAIZ 8 dígitos** (regra 646 do eSocial para empregadores não-públicos):
```python
if tp_insc_empregador == '1':  # CNPJ
    nr_insc_empregador = ''.join(filter(str.isdigit, nr_insc_empregador))[:8]
```

### 3.6. Qual namespace/versão do XML ele usa? (vS01_03_00 = S-1.3? Ou versão anterior?)
**R:** Múltiplos namespaces dependendo do contexto:
- **Evento S-2500:** `http://www.esocial.gov.br/schema/evt/evtProcTrab/v_S_01_02_00` (S-1.2) ou `v_S_01_03_00` (S-1.3)
- **Lote de envio:** `http://www.esocial.gov.br/schema/lote/eventos/envio/v1_1_1`
- **SOAP service:** `http://www.esocial.gov.br/servicos/empregador/lote/eventos/envio/v1_1_0`
- **Retorno envio:** `http://www.esocial.gov.br/schema/lote/eventos/envio/retornoEnvio/v1_1_0`
- **Consulta:** `http://www.esocial.gov.br/schema/lote/eventos/envio/consulta/retornoProcessamento/v1_0_0`

### 3.7. Ele valida o XML contra o XSD antes de enviar?
**R:** Existe um módulo `xsd_validator.py` e `xml_validator.py` no diretório `esocial/`, e uma pasta `esocial/schemas/` com XSDs. A validação é feita antes da assinatura no endpoint de sign, mas o foco principal é validação estrutural, não validação completa contra XSD em todos os cenários.

### 3.8. Pode colar aqui um exemplo real de XML que ele gera (pode censurar o CNPJ)?
**R:** Exemplo de RETORNO de sucesso real do eSocial:
```xml
<?xml version='1.0' encoding='UTF-8'?>
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
            <ideTransmissor>
              <tpInsc>2</tpInsc>
              <nrInsc>09332XXXXX0</nrInsc>
            </ideTransmissor>
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

---

## 4. ASSINATURA DIGITAL DO XML

### 4.1. Qual biblioteca é usada para assinar o XML? (xml-crypto? signxml? xmlsec? outra?)
**R:** **`signxml`** (Python) — biblioteca pura Python para XML Digital Signatures.
```python
from signxml import XMLSigner
import signxml

signer = XMLSigner(
    method=signxml.methods.enveloped,
    signature_algorithm="rsa-sha256",
    digest_algorithm="sha256",
    c14n_algorithm="http://www.w3.org/TR/2001/REC-xml-c14n-20010315"
)
```

### 4.2. A assinatura é enveloped (dentro do XML) conforme o padrão eSocial?
**R:** Sim. `method=signxml.methods.enveloped` — o `<Signature>` fica **dentro** do XML, como filho direto do `<eSocial>`, após o elemento do evento.

### 4.3. Ele usa RSA-SHA256 para assinatura e SHA-256 para digest?
**R:** Sim, exatamente: `signature_algorithm="rsa-sha256"` e `digest_algorithm="sha256"`.

### 4.4. A canonicalization é C14N conforme esperado?
**R:** Sim: `c14n_algorithm="http://www.w3.org/TR/2001/REC-xml-c14n-20010315"` (C14N 1.0 sem comentários).

### 4.5. O `<Signature>` fica como último filho de `<eSocial>`, após o `<evtTabRubrica>`?
**R:** Sim. O `signxml` com `method=enveloped` insere o `<Signature>` após o elemento do evento, como irmão, resultando em:
```xml
<eSocial>
  <evtProcTrab>...</evtProcTrab>
  <Signature>...</Signature>
</eSocial>
```

### 4.6. Teve algum problema/bug com a assinatura que foi difícil de resolver? Qual?
**R:** Sim, **dois problemas críticos documentados no código:**

1. **Erro SERPRO 142:** "A assinatura deverá ser realizada sobre todo documento Xml (Atributo URI deve ser vazio)" — O eSocial exige URI vazio (assinar o documento inteiro), não pode ter referência específica a um Id.

2. **Problema com atributo `Id` vs `id`:** O eSocial exige `Id` com I maiúsculo. O código faz correção explícita:
```python
if evento_element.get('id'):
    del evento_element.attrib['id']
evento_element.set('Id', evento_id)
```

### 4.7. Pode colar aqui o trecho de código que faz a assinatura?
**R:** Código de `xml_signer.py` (linhas 108-140):
```python
from signxml import XMLSigner
import signxml

# Configurar signer
signer = XMLSigner(
    method=signxml.methods.enveloped,
    signature_algorithm="rsa-sha256",
    digest_algorithm="sha256",
    c14n_algorithm="http://www.w3.org/TR/2001/REC-xml-c14n-20010315"
)

# Converter certificado para PEM
cert_pem = certificate.public_bytes(Encoding.PEM)

# Assinar (URI vazio = assinar todo o documento)
signed_root = signer.sign(
    root,            # lxml etree root element
    key=private_key,
    cert=cert_pem
)

# Salvar XML assinado
with open(signed_path, 'wb') as f:
    f.write(etree.tostring(signed_root,
                          pretty_print=True,
                          xml_declaration=True,
                          encoding='UTF-8'))
```

---

## 5. ENVELOPE SOAP E ENVIO

### 5.1. Como o envelope SOAP é montado? (Template? Biblioteca SOAP? Builder?)
**R:** **Template f-string** em Python. Não usa biblioteca SOAP para montar (zeep é importado mas o fluxo principal usa `requests` + template string):
```python
soap_envelope = f"""<?xml version="1.0" encoding="UTF-8"?>
<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/"
                  xmlns:v1="http://www.esocial.gov.br/servicos/empregador/lote/eventos/envio/v1_1_0">
   <soapenv:Header/>
   <soapenv:Body>
      <v1:EnviarLoteEventos>
         <v1:loteEventos>{lote_xml_sem_declaracao}</v1:loteEventos>
      </v1:EnviarLoteEventos>
   </soapenv:Body>
</soapenv:Envelope>"""
```

### 5.2. Ele usa SOAP 1.1 conforme o eSocial exige?
**R:** Sim. Namespace `http://schemas.xmlsoap.org/soap/envelope/` = SOAP 1.1. Header `Content-Type: text/xml; charset=utf-8` (SOAP 1.1, não `application/soap+xml` que seria 1.2).

### 5.3. Qual biblioteca HTTP é usada para o POST? (axios? fetch? requests? HttpClient?)
**R:** **`requests`** (Python). POST direto com certificado mTLS.

### 5.4. Como o mTLS (mutual TLS) é configurado? (O certificado A1 é passado como client cert na requisição HTTPS?)
**R:** Sim. O certificado A1 (.pfx) é extraído para arquivos PEM temporários e passado via parâmetro `cert=` do requests:
```python
# Extrair de .pfx para PEM temporários
temp_cert = tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.pem')
temp_key = tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.pem')

# Escrever cert PEM
temp_cert.write(certificate.public_bytes(Encoding.PEM))
temp_cert.close()

# Escrever private key PEM
temp_key.write(private_key.private_bytes(
    Encoding.PEM, PrivateFormat.TraditionalOpenSSL, NoEncryption()
))
temp_key.close()

# POST com mTLS
response = requests.post(
    url,
    data=soap_envelope.encode('utf-8'),
    headers=headers,
    cert=(temp_cert.name, temp_key.name),  # ← mTLS aqui
    verify=False,
    timeout=60
)

# Cleanup no finally
os.unlink(temp_cert.name)
os.unlink(temp_key.name)
```

### 5.5. Pode colar aqui o trecho de código que faz o envio HTTP com mTLS?
**R:** Código de `esocial_client.py` (linhas 186-215):
```python
import requests
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

url = self.urls['envio']

# Remover declaração <?xml do lote (senão fica duplicada no SOAP)
lote_xml_sem_declaracao = re.sub(r'<\?xml[^?]+\?>\s*', '', lote_xml)

# Envelope SOAP 1.1
soap_envelope = f"""<?xml version="1.0" encoding="UTF-8"?>
<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/"
                  xmlns:v1="http://www.esocial.gov.br/servicos/empregador/lote/eventos/envio/v1_1_0">
   <soapenv:Header/>
   <soapenv:Body>
      <v1:EnviarLoteEventos>
         <v1:loteEventos>{lote_xml_sem_declaracao}</v1:loteEventos>
      </v1:EnviarLoteEventos>
   </soapenv:Body>
</soapenv:Envelope>"""

headers = {
    'Content-Type': 'text/xml; charset=utf-8',
    'SOAPAction': 'http://www.esocial.gov.br/servicos/empregador/lote/eventos/envio/v1_1_0/ServicoEnviarLoteEventos/EnviarLoteEventos'
}

response = requests.post(
    url,
    data=soap_envelope.encode('utf-8'),
    headers=headers,
    cert=(temp_cert.name, temp_key.name),
    verify=False,
    timeout=60
)
```

### 5.6. O SOAPAction header está configurado corretamente? Qual valor usa?
**R:** Sim, dois valores diferentes para envio vs consulta:
- **Envio:** `http://www.esocial.gov.br/servicos/empregador/lote/eventos/envio/v1_1_0/ServicoEnviarLoteEventos/EnviarLoteEventos`
- **Consulta:** `http://www.esocial.gov.br/servicos/empregador/lote/eventos/envio/consulta/retornoProcessamento/v1_1_0/ServicoConsultarLoteEventos/ConsultarLoteEventos`

### 5.7. Ele envia para produção restrita ou produção? A URL é configurável?
**R:** Configurável via variável de ambiente `ESOCIAL_AMBIENTE`. Suporta 3 ambientes:
- **`producao_restrita`** (padrão): `https://webservices.producaorestrita.esocial.gov.br/servicos/empregador/enviarloteeventos/WsEnviarLoteEventos.svc`
- **`producao`**: `https://webservices.esocial.gov.br/servicos/empregador/enviarloteeventos/WsEnviarLoteEventos.svc`
- **`homologacao`**: mesma URL da produção restrita

O ambiente também pode ser passado por parâmetro no endpoint de envio: `POST /api/s2500/send/{id}?ambiente=producao_restrita`.

### 5.8. Quantos eventos ele envia por lote? (1 por vez? Máximo 50? Configurável?)
**R:** **1 evento por lote.** O código monta o lote com um único `<evento>` dentro de `<eventos>`. Não há lógica de agrupamento de múltiplos eventos. Para S-2501 com parcelamento, envia cada parcela como lote separado (P01, P02...P06).

### 5.9. Ele agrupa os eventos por `grupo` (1=tabelas, 2=não periódicos, 3=periódicos)?
**R:** O parâmetro `grupo` é passado no lote XML. Para S-2500 usa `grupo='2'` (Eventos Não Periódicos). É configurável no `enviar_lote()`, mas não há lógica automática de agrupamento. Para S-1010 seria `grupo='1'` (Tabelas).

---

## 6. TRATAMENTO DA RESPOSTA

### 6.1. Como ele parseia a resposta SOAP do eSocial?
**R:** Usa `lxml.etree.fromstring()` para parsear o XML e depois `xpath` com `local-name()` para extrair dados independente do namespace:
```python
xml_response = etree.fromstring(response.text.encode('utf-8'))
status = xml_response.xpath('//*[local-name()="cdResposta"]/text()')
descricao = xml_response.xpath('//*[local-name()="descResposta"]/text()')
protocolo = xml_response.xpath('//*[local-name()="protocoloEnvio"]/text()')
dh_recepcao = xml_response.xpath('//*[local-name()="dhRecepcao"]/text()')
```

### 6.2. Ele extrai o `protocoloEnvio` da resposta de envio?
**R:** Sim. Busca em múltiplos caminhos com fallback:
```python
protocolo = (
    xml_response.xpath('//ns:protocoloEnvio/text()', namespaces=namespaces) or
    xml_response.xpath('//ret:protocoloEnvio/text()', namespaces=namespaces) or
    xml_response.xpath('//*[local-name()="protocoloEnvio"]/text()') or
    xml_response.xpath('//*[local-name()="nrProtocolo"]/text()') or
    xml_response.xpath('//*[local-name()="nrRecibo"]/text()')
)
```

### 6.3. Como ele faz a consulta do resultado? (Polling? Timer? Manual?)
**R:** **Três mecanismos:**
1. **Automático no envio:** 5 segundos após enviar, consulta automaticamente o S-5501 (`client.consultar_e_baixar_s5501()`)
2. **Scheduler automático (Polling):** APScheduler roda a cada 15 minutos buscando processos com protocolo pendente
3. **Manual:** Botão "Consultar" na UI chama `POST /api/s2500/consultar/{processo_id}`

### 6.4. Qual o intervalo entre envio e consulta? Tem retry?
**R:** 5 segundos após envio (primeira tentativa). Se ainda processando, o scheduler tenta a cada 15 minutos (configurável via `SCHEDULER_INTERVAL_MINUTES`). Alerta após 3 dias sem retorno (`SCHEDULER_ALERT_DAYS`). Retry com backoff exponencial no scheduler.

### 6.5. O que ele faz quando recebe sucesso (nrRecibo)?
**R:** Atualiza o banco de dados:
- `processo.status = "processed"`
- Salva o S-5501 XML completo (`repos.s5501_xml`, `repos.s5501_path`)
- Salva recibos em JSON (`repos.recibos`, `repos.nr_rec_arq_base`)
- Salva data de download (`repos.s5501_baixado_em`)
- Grava o XML de retorno em arquivo `*_RETORNO_{protocolo}_{timestamp}.xml`

### 6.6. O que ele faz quando recebe erro? Quais erros mais comuns já apareceram?
**R:** O sistema lida com três níveis de erro:
- **HTTP 500:** Parseia SOAP Fault (`faultstring` + `detail`)
- **Lote rejeitado (status != 201):** Salva em debug (`_debug_xml/debug_erro_envio_*.xml`), atualiza `processo.status = "error"`, grava `send_error` e `ocorrencias`
- **Evento rejeitado:** Lote aceito (201) mas evento individual com erro — detecta e diferencia código do lote vs código do evento

**Erros mais comuns evidenciados nos debug files:**
| Código | Qtd Ocorrências | Descrição |
|--------|-----------------|-----------|
| **401** | 37 instâncias | "Processo trabalhista não localizado" — SERPRO valida contra base CNJ/PJe |
| **402** | Vários | "evtProcTrab element is not declared" — namespace/envelope incorreto |
| **555** | Vários | Mismatch entre ID do lote e ID interno do evento |
| **142** | Vários | URI da assinatura não vazia |

### 6.7. Ele salva o protocolo/recibo em banco de dados?
**R:** Sim. Na tabela `s2500_repos_web_service`: campos `protocolo`, `dh_recepcao`, `recibos` (JSON), `nr_rec_arq_base`, `descricao_resposta`, `ocorrencias`, `xml_retorno`, `retorno_path`. Histórico completo persistido com timestamps e username.

### 6.8. Pode colar aqui um exemplo de resposta de sucesso do eSocial?
**R:** Real, extraído de `Repositorio_XML/S2500/S2500_11634750845_..._RETORNO_....xml`:
```xml
<?xml version='1.0' encoding='UTF-8'?>
<s:Envelope xmlns:s="http://schemas.xmlsoap.org/soap/envelope/">
  <s:Body>
    <EnviarLoteEventosResponse xmlns="http://www.esocial.gov.br/servicos/empregador/lote/eventos/envio/v1_1_0">
      <EnviarLoteEventosResult>
        <eSocial xmlns="http://www.esocial.gov.br/schema/lote/eventos/envio/retornoEnvio/v1_1_0"
                 xmlns:xsd="http://www.w3.org/2001/XMLSchema"
                 xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
          <retornoEnvioLoteEventos>
            <ideEmpregador>
              <tpInsc>1</tpInsc>
              <nrInsc>05969071</nrInsc>
            </ideEmpregador>
            <ideTransmissor>
              <tpInsc>2</tpInsc>
              <nrInsc>09332337870</nrInsc>
            </ideTransmissor>
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

### 6.9. Pode colar aqui um exemplo de resposta de erro do eSocial?
**R:** Os 37 arquivos `debug_erro_envio_401_*.xml` no diretório `_debug_xml/` contêm o erro mais frequente — código 401 ("Processo trabalhista não localizado"). Estrutura típica de erro:
```xml
<status>
  <cdResposta>401</cdResposta>
  <descResposta>Erro na validação do evento.</descResposta>
</status>
<ocorrencias>
  <ocorrencia>
    <tipo>1</tipo>
    <codigo>401</codigo>
    <descricao>Processo trabalhista não localizado na base CNJ/PJe.</descricao>
  </ocorrencia>
</ocorrencias>
```

---

## 7. BANCO DE DADOS E PERSISTÊNCIA

### 7.1. Ele usa banco de dados? Qual? (PostgreSQL? MySQL? SQLite? MongoDB?)
**R:** **SQLite** — dois bancos:
- `esocial.db` — dados S-2500 (processos, empregadores, trabalhadores, contratos, envios)
- `s2501.db` — dados S-2501 (cálculos de tributos, envios de tributos)

SQLAlchemy como ORM.

### 7.2. Quais tabelas/collections existem relacionadas ao envio de eventos?
**R:**
| Tabela | Propósito |
|--------|-----------|
| `certificados` | Certificados A1 (arquivo .pfx, senha criptografada, CNPJ, validade, emissor, ativo) |
| `procuracoes_eletronicas` | Procurações eSocial vinculadas a certificados (outorgante, validade, tipos eventos) |
| `s2500_processos` | Processos trabalhistas S-2500 (CPF, nrProcTrab, status do workflow) |
| `s2500_repos_web_service` | Envios S-2500 (XML gerado, assinado, protocolo, retorno, S-5501, erros) |
| `repos_web_service` | Envios S-2501 (XML, protocolo, status, recibo) |
| `retorno_s5501` | Dados parseados do retorno S-5501 (contribuições, IRRF, valores) |

### 7.3. Ele guarda histórico de todos os envios (sucesso e erro)?
**R:** Sim. Cada envio cria/atualiza um registro em `s2500_repos_web_service` ou `repos_web_service` com timestamps, username, ambiente, XML completo, e todos os retornos. O scheduler também salva JSON de execuções (`s2500_scheduler_resumo.json` e `s5501_scheduler_resumo.json` com últimas 50 execuções).

### 7.4. Tem alguma tabela de "fila de envio" ou "staging" para eventos pendentes?
**R:** Não tem fila separada. O campo `status` do `S2500Processo` funciona como máquina de estados: `rascunho` → `signed` → `sent` → `processed`/`rejected`/`error`. O scheduler busca processos com `protocolo IS NOT NULL AND s5501_baixado_em IS NULL` para consultar pendentes automaticamente.

### 7.5. Como ele controla quais rubricas já foram enviadas e quais ainda não?
**R:** Via campo `status` no `S2500Processo` (para processos trabalhistas, não rubricas):
- `rascunho` — criado, não assinado
- `signed` — XML assinado, pronto para enviar
- `sent` — enviado ao eSocial, aguardando retorno
- `processed` — retorno S-5501 recebido com sucesso
- `rejected` — rejeitado pelo eSocial
- `error` — erro no envio

---

## 8. CONFIGURAÇÃO E AMBIENTE

### 8.1. Quais variáveis de ambiente ele usa? (.env? Config file? Quais chaves?)
**R:** Definidas em `config.py` (lidas via `os.getenv` com defaults):
```
ESOCIAL_AMBIENTE           = producao_restrita  (homologacao|producao_restrita|producao)
DATABASE_URL               = sqlite:///./s2501.db
SECRET_KEY                 = chave-fernet-para-criptografia-de-senhas
JWT_SECRET_KEY             = chave-jwt-para-tokens-autenticacao
SCHEDULER_INTERVAL_MINUTES = 15
SCHEDULER_ALERT_DAYS       = 3
REPOSITORIO_XML_PATH       = Repositorio_XML
LOG_LEVEL                  = INFO
```

### 8.2. Como ele diferencia entre produção restrita e produção? (Flag? Variável? URL diferente?)
**R:** Variável `ESOCIAL_AMBIENTE` que seleciona URLs diferentes do dict `ESOCIAL_URLS`. Também define `ESOCIAL_TP_AMB`: `"1"` para produção, `"2"` para restrita/homologação (usado no campo `tpAmb` do XML do evento).

### 8.3. Precisa instalar alguma dependência do sistema operacional? (OpenSSL? libxmlsec? outro?)
**R:** Não há dependências de SO explícitas. `signxml` e `cryptography` são pacotes Python com bindings compilados disponíveis via pip wheel. Não precisa de `libxmlsec1` nem OpenSSL separado — `cryptography` inclui tudo necessário.

### 8.4. Tem Docker? docker-compose?
**R:** **Não.** Existe um `render.yaml` na raiz (para deploy no Render.com), mas não tem Docker/docker-compose no repositório. Arquivo `DEPLOY_SEM_DOCKER.md` na docs confirma — deploy sem Docker.

### 8.5. Qual versão do Node/Python/linguagem é necessária?
**R:** Python 3.13 (conforme copilot-instructions). Frontend: Node.js + npm (react-scripts/CRA). Não há `.python-version` ou `pyproject.toml` com requisito explícito de versão mínima.

---

## 9. ERROS E PROBLEMAS ENCONTRADOS

### 9.1. Quais foram os maiores problemas/bugs que vocês encontraram na integração com o eSocial?
**R:** Baseado na análise do código, comentários e debug files:

1. **Erro 555 — ID mismatch:** O ID do `<evento>` no lote DEVE ser idêntico ao `Id` do evento interno. Foi a causa de muitas rejeições até ser corrigido com regex de extração do ID.

2. **Erro 402 — "evtProcTrab element is not declared":** Remover o wrapper `<eSocial>` do evento assinado fazia o SERPRO rejeitar. Solução documentada no código: manter o XML assinado INTACTO dentro do `<evento>` do lote, incluindo o `<eSocial>` do evento.

3. **Erro 401 — "Processo trabalhista não localizado":** Produção restrita valida contra base CNJ/PJe real. 37 instâncias nos debug files. Não é bug — é restrição do ambiente.

4. **CNPJ raiz vs completo:** eSocial regra 646 exige CNPJ raiz (8 dígitos) no lote para empregadores não-públicos. Enviava com 14 dígitos e era rejeitado.

5. **Declaração XML duplicada:** O SOAP envelope + lote + evento cada um tinha `<?xml?>`. Solução: `re.sub(r'<\?xml[^?]+\?>\s*', '', lote_xml)`.

### 9.2. A assinatura digital deu trabalho? O que deu errado?
**R:** Sim. Dois bugs críticos:
- **Erro 142:** URI da assinatura não podia ter referência específica — precisa assinar todo o documento (URI vazia). A lib `signxml` por padrão faz isso correto, mas configurações iniciais podiam referenciar o `Id` do evento.
- **`Id` vs `id`:** eSocial exige `Id` com I maiúsculo. O código corrige explicitamente removendo `id` minúsculo e adicionando `Id` maiúsculo.

### 9.3. O mTLS deu problema? Erro de SSL? Como resolveu?
**R:** O `verify=False` no código sugere que houve problemas com SSL verification (provavelmente certificado do servidor em produção restrita não era confiado pelo chain padrão). Solução: desabilitar verificação do servidor com `verify=False`. O mTLS do cliente (enviar certificado A1 como client cert) funciona via extração PFX→PEM em tempfiles + `cert=(cert_file, key_file)`.

### 9.4. Algum problema com encoding (UTF-8, BOM, etc.) no XML?
**R:** Tratado no código: XMLs são sempre `encoding='UTF-8'`. A remoção da declaração XML é feita com regex. O `data=soap_envelope.encode('utf-8')` no requests garante encoding correto. Sem evidência de problemas com BOM.

### 9.5. O eSocial retornou algum erro inesperado ou mal documentado?
**R:** O erro 401 em produção restrita ("Processo trabalhista não localizado") é semi-documentado — a questão de que produção restrita valida contra base CNJ/PJe real não é óbvia na documentação. 37 ocorrências nos debug files mostram tentativas com processos que não existem na base.

### 9.6. Quanto tempo levou para fazer o primeiro envio com sucesso em produção restrita?
**R:** Baseado nos timestamps dos XMLs os primeiros XMLs S-2501 com `_RETORNO_` (sucesso) são de 10/01/2026. Os primeiros S-2500 com sucesso são de 25-26/01/2026 (com ~20 tentativas num único dia para o mesmo CPF!). Estimativa: 1-2 semanas de iteração entre os primeiros testes e o fluxo estável.

---

## 10. FLUXO DE USO

### 10.1. Qual o passo a passo para um usuário usar o sistema e enviar um S-1010?
**R:** (Fluxo real do sistema para S-2500, adaptável para S-1010):
1. **Login** no sistema web (autenticação JWT)
2. **Upload certificado A1** (.pfx + senha) via tela CertificadoManager
3. **Criar novo processo** — Wizard de 8 steps:
   - Step 1: Info Evento (indRetif, tpAmb, procEmi, verProc)
   - Step 2: Empregador (tpInsc, nrInsc/CNPJ)
   - Step 3: Processo (origem, nrProcTrab, tpTrib, codVara, dtSentenca)
   - Step 4: Trabalhador (cpfTrab, nmTrab, dtNascto)
   - Step 5: Contrato (tpContr, indContr, matricula, codCateg...)
   - Step 6: Revisão/Validação
   - Step 7: Confirmação final
   - Step 8: Gerar XML
4. **Assinar XML** (botão na UI → `POST /api/s2500/sign/{id}`)
5. **Enviar ao eSocial** (botão → `POST /api/s2500/send/{id}`)
6. **Consultar retorno** (automático em 5s + scheduler 15min + botão manual)

### 10.2. Ele tem interface gráfica ou é tudo via terminal/API?
**R:** **Interface gráfica web** completa. React 19 + MUI 7 com wizard guiado, painel de certificados, repositório de envios com status por cores, preview de XML, botões de ação (Assinar/Enviar/Consultar), e tabela de retornos.

### 10.3. O usuário seleciona quais rubricas alterar ou é tudo automático?
**R:** Misto. Dados básicos (CNPJ, CPF) disparam consultas automáticas ao SERPRO para preencher dados. O wizard guia o preenchimento campo a campo. A geração do XML e envio é sob demanda (botões explícitos, não automático).

### 10.4. Tem preview do XML antes de enviar?
**R:** Sim. Step 8 do wizard gera e mostra o XML na tela. O componente `ReposWebServiceS2500` também permite visualizar o XML gerado/assinado antes e depois da assinatura.

### 10.5. Tem confirmação antes do envio definitivo?
**R:** Sim. Step 7 é a "Confirmação Final" antes de gerar XML. O envio ao eSocial requer clicar explicitamente o botão "Enviar" no painel de repositório — operação separada.

---

## 11. CÓDIGO-FONTE (TRECHOS IMPORTANTES)

### 11.1. Pode colar o arquivo/função principal que orquestra o fluxo de envio?
**R:** Endpoint `POST /api/s2500/send/{draft_id}` em `main.py` (linhas 7299-7600+):

Fluxo orquestrado:
1. Buscar processo no DB
2. Verificar se XML está assinado (`status == "signed"`)
3. Buscar certificado ativo no DB
4. Descriptografar senha do certificado via Fernet
5. Resolver caminho do .pfx no disco
6. Extrair dados do empregador (CNPJ raiz 8 dígitos)
7. Determinar transmissor (dados do certificado)
8. Criar `ESocialClient(ambiente)` e chamar `enviar_lote()`
9. Processar resultado (sucesso/erro)
10. Atualizar DB com protocolo/status
11. Auto-consultar S-5501 após 5 segundos
12. Retornar resultado ao frontend

### 11.2. Pode colar o arquivo/função que monta o XML do S-1010?
**R:** Não existe S-1010 neste repositório. Os XMLs são montados em:
- **S-2500:** `frontend/src/components/wizard/Step8XMLGeneration.js` — função `buildXML()` em JavaScript
- **S-2501:** `python-backend/esocial/xml_generator.py` — 1084 linhas com `lxml.etree`

### 11.3. Pode colar o arquivo/função que faz a assinatura digital?
**R:** `python-backend/esocial/xml_signer.py` — classe `XMLSignatureManager`, método `sign_xml()`:
```python
@staticmethod
def sign_xml(xml_path: str, cert_path: str, cert_password: str) -> str:
    # 1. Verificar arquivos
    # 2. Carregar .pfx → private_key, certificate, additional_certs
    # 3. Parsear XML com lxml
    # 4. Encontrar elemento evento (evtProcTrab ou evtInfoComplPer)
    # 5. Garantir atributo 'Id' (maiúsculo)
    # 6. Assinar com signxml:
    signer = XMLSigner(
        method=signxml.methods.enveloped,
        signature_algorithm="rsa-sha256",
        digest_algorithm="sha256",
        c14n_algorithm="http://www.w3.org/TR/2001/REC-xml-c14n-20010315"
    )
    signed_root = signer.sign(root, key=private_key, cert=cert_pem)
    # 7. Salvar como {nome}_ASSINADO.xml
    return signed_path
```

### 11.4. Pode colar o arquivo/função que faz o envio SOAP HTTP?
**R:** `python-backend/esocial/esocial_client.py` — classe `ESocialClient`, método `enviar_lote()`:
```python
def enviar_lote(self, xml_assinado_path, cert_path, cert_password, grupo='1',
                tp_insc_empregador='1', nr_insc_empregador='',
                tp_insc_transmissor='1', nr_insc_transmissor=''):
    # 1. Ler XML assinado
    # 2. Montar lote via _montar_lote_envio()
    # 3. Extrair PFX → PEM temporários
    # 4. Remover <?xml?> duplicada
    # 5. Montar envelope SOAP 1.1
    # 6. requests.post(url, data, headers, cert=(cert,key), verify=False, timeout=60)
    # 7. Parsear resposta via _parsear_resposta_envio()
    # 8. Salvar retorno em arquivo
    # 9. Retornar dict {sucesso, protocolo, dh_recepcao, ...}
```

### 11.5. Pode colar o arquivo/função que parseia a resposta?
**R:** `python-backend/esocial/esocial_client.py` — método `_parsear_resposta_envio()`:
```python
def _parsear_resposta_envio(self, response):
    xml_response = etree.fromstring(response_text.encode('utf-8'))
    
    status = xml_response.xpath('//*[local-name()="cdResposta"]/text()')
    descricao = xml_response.xpath('//*[local-name()="descResposta"]/text()')
    protocolo = xml_response.xpath('//*[local-name()="protocoloEnvio"]/text()')
    dh_recepcao = xml_response.xpath('//*[local-name()="dhRecepcao"]/text()')
    
    # Extrair ocorrências de erro
    ocorrencias = xml_response.xpath('//*[local-name()="ocorrencia"]')
    
    return {
        'sucesso': status[0] == '201',
        'codigo_resposta': status[0],
        'descricao': descricao[0],
        'protocolo': protocolo[0],
        'dh_recepcao': dh_recepcao[0],
        'ocorrencias': erros,
        'response_xml': response_text
    }
```

### 11.6. Pode colar o arquivo/função que faz a consulta do lote?
**R:** `python-backend/esocial/esocial_client.py` — método `consultar_lote()`:
```python
def consultar_lote(self, protocolo, cert_path, cert_password):
    # 1. Extrair PFX → PEM temporários
    # 2. Montar SOAP de consulta com protocoloEnvio
    soap_envelope = f"""...
    <eSocial xmlns="http://www.esocial.gov.br/schema/lote/eventos/envio/consulta/retornoProcessamento/v1_0_0">
       <consultaLoteEventos>
          <protocoloEnvio>{protocolo}</protocoloEnvio>
       </consultaLoteEventos>
    </eSocial>..."""
    # 3. POST com mTLS
    # 4. Parsear: status do LOTE + status do EVENTO (podem ser diferentes!)
    # 5. Extrair recibos (nrRecibo)
    # 6. Retornar dict {sucesso, codigo_lote, codigo_evento, recibos, ocorrencias}
```

### 11.7. Pode colar o package.json / requirements.txt / equivalente com as dependências?
**R:** `python-backend/requirements.txt`:
```
fastapi
uvicorn
sqlalchemy
pydantic
python-jose[cryptography]
passlib[bcrypt]
bcrypt==4.0.1
python-multipart
lxml
signxml
pytz
cryptography
zeep
requests
APScheduler
python-dateutil
python-dotenv
httpx
beautifulsoup4
reportlab
openpyxl
psycopg2-binary
psutil
gunicorn
```

### 11.8. Pode colar o arquivo de configuração (.env.example, config.ts, etc.)?
**R:** `python-backend/config.py`:
```python
import os

# Ambiente eSocial: 'homologacao' | 'producao_restrita' | 'producao'
ESOCIAL_AMBIENTE = os.getenv('ESOCIAL_AMBIENTE', 'producao_restrita')

# tpAmb para XML: "1" = Produção, "2" = Restrita/Homologação
ESOCIAL_TP_AMB = "1" if ESOCIAL_AMBIENTE == 'producao' else "2"

# URLs WebService
ESOCIAL_URLS = {
    'producao': {
        'envio': 'https://webservices.producao.esocial.gov.br/.../WsEnviarLoteEventos.svc',
        'consulta': 'https://webservices.producao.esocial.gov.br/.../WsConsultarLoteEventos.svc'
    },
    'producao_restrita': {
        'envio': 'https://webservices.producaorestrita.esocial.gov.br/.../WsEnviarLoteEventos.svc',
        'consulta': 'https://webservices.producaorestrita.esocial.gov.br/.../WsConsultarLoteEventos.svc'
    }
}

DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///./s2501.db')
SECRET_KEY = os.getenv('SECRET_KEY', 'a_very_secret_key_that_should_be_in_env_var')
JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', SECRET_KEY)
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_MINUTES = 60 * 24  # 24 horas
SCHEDULER_INTERVAL_MINUTES = int(os.getenv('SCHEDULER_INTERVAL_MINUTES', '15'))
SCHEDULER_ALERT_DAYS = int(os.getenv('SCHEDULER_ALERT_DAYS', '3'))
REPOSITORIO_XML_PATH = os.getenv('REPOSITORIO_XML_PATH', 'Repositorio_XML')
```

---

## 12. INTEGRAÇÃO COM O EASY SOCIAL

### 12.1. Na sua opinião, o que do repositório o1 pro 4.6 pode ser reaproveitado diretamente no Easy Social?
**R:**
- **`esocial_client.py`** — Cliente SOAP completo (envio + consulta + parsing) — 100% reaproveitável para qualquer evento
- **`xml_signer.py`** — Assinatura XMLDSig — funciona para qualquer evento eSocial sem alteração
- **`certificate_manager.py`** — Gestão de certificados A1 — genérico, reutilizável
- **Lógica de lote** (`_montar_lote_envio`) — envelope funciona para qualquer grupo/evento
- **Parsing de respostas** — lógica de extração de protocolo/status/recibos/ocorrências
- **Config de URLs e ambientes** — estrutura já pronta para 3 ambientes
- **Models de Certificado e ReposWebService** — estrutura de tabelas reutilizável

### 12.2. O que precisaria ser adaptado?
**R:**
- **XML Generator** — criar geradores específicos para S-1010 (rubricas), S-1000, S-1020, etc.
- **Models/DB** — adaptar tabelas para estrutura de rubricas ao invés de processos trabalhistas
- **Frontend** — wizard e UI são específicos para S-2500 — precisaria de forms para rubricas
- **Config** — ajustar `grupo='1'` para tabelas (S-1010 é grupo 1, não grupo 2)
- **Scheduler** — adaptar para consultar retornos dos novos eventos
- **Namespace do evento** — mudar de `evtProcTrab` para `evtTabRubrica`

### 12.3. O que NÃO serve e teria que ser feito do zero?
**R:**
- Toda a lógica de negócio de processos trabalhistas (Steps 1-7, cálculos S-2501, SELIC, multa)
- O wizard de 8 steps é específico demais
- Os verificadores e comparadores de dados são específicos
- O parser de S-5501 é específico (Easy Social precisaria de parser para S-5001 ou outro)
- A integração SERPRO (CPF/CNPJ) é útil mas não essencial para S-1010

### 12.4. Qual a parte mais difícil/complexa de toda a integração?
**R:** **A assinatura digital XML e o mTLS são os maiores pontos de dificuldade.** Uma vez que funciona (e esse repo já resolveu todos os bugs), o resto é montagem de XML e parsing de resposta.

O segundo ponto difícil é entender exatamente os **namespaces, versões e formatos** que o SERPRO espera:
- Lote `v1_1_1`, serviço `v1_1_0`, consulta `v1_0_0`
- ID matching obrigatório (lote = evento interno)
- CNPJ raiz 8 dígitos
- `<?xml?>` duplicada
- `Id` maiúsculo vs `id` minúsculo

### 12.5. Alguma dica ou conselho para quem vai implementar isso?
**R:** Baseado nas lições aprendidas documentadas no código:

1. **Copie o `esocial_client.py` + `xml_signer.py` + `certificate_manager.py` como está** — não refatore, funciona
2. **O ID do `<evento>` no lote DEVE ser idêntico ao Id interno do evento** (erro 555!)
3. **Use CNPJ raiz (8 dígitos)** no lote para empregadores CNPJ
4. **Remova `<?xml?>` do XML antes de colocar no SOAP** — declaração duplicada causa rejeição
5. **`verify=False`** no requests resolve problemas de SSL em produção restrita
6. **Assine com URI vazia** — eSocial requer assinatura sobre todo documento
7. **Use `local-name()` nos XPath** para parsear respostas — evita problemas de namespace
8. **Salve TUDO em debug** — XMLs enviados, responses, erros — vai precisar para troubleshooting
9. **Teste com processo/dados REAIS** em produção restrita — dados fictícios são rejeitados

---

## 13. PERGUNTAS EXTRAS

### 13.1. O eSocial em produção restrita aceita qualquer CNPJ ou precisa ser um CNPJ real cadastrado?
**R:** **Não aceita qualquer CNPJ.** Conforme documentação (`AMBIENTE_PRODUCAO_RESTRITA_ANALISE.md`), produção restrita é uma **réplica de produção** com as mesmas validações. Valida CNPJ/CPF reais, estrutura XSD, regras de negócio, e até números de processo contra base CNJ/PJe. Os 37 erros 401 comprovam que processos fictícios são rejeitados.

### 13.2. Tem algum CNPJ de teste ou sandbox?
**R:** **NÃO existe sandbox.** Produção restrita IS produção (com flag tpAmb=2). Precisa usar CNPJ e CPF reais (com certificado A1 válido vinculado). Os XMLs no repositório usam CNPJs e CPFs reais de empresas e trabalhadores.

### 13.3. O certificado A1 usado em produção restrita precisa ser real (ICP-Brasil) ou aceita certificado de teste?
**R:** **Precisa ser ICP-Brasil real.** O mTLS do SERPRO valida o certificado contra a cadeia ICP-Brasil. Certificado self-signed ou de teste não funciona.

### 13.4. Quanto tempo os dados ficam na produção restrita antes de serem limpos?
**R:** A documentação do repositório não especifica período de limpeza exato. Baseado nos XMLs de retorno que cobrem Jan/2026 a Mar/2026 (3+ meses), os dados permanecem ao menos por esse período. O eSocial geralmente faz limpezas periódicas em produção restrita, mas sem calendário público fixo.

### 13.5. Existe rate limit no web service do eSocial? Quantos requests por minuto/hora?
**R:** Não documentado explicitamente no código. O timeout por request é 60 segundos. Os XMLs mostram envios a cada poucos minutos sem rejeição por rate limit. O SERPRO não rejeita burst pequeno — há evidência de 10-20 envios em sequência sem problemas (ex: CPF 37152942803 com ~20 envios em 26/01/2026).

### 13.6. O web service fica fora do ar com frequência? Tem janela de manutenção?
**R:** Não há evidência de problemas de disponibilidade no código/debug. Todos os erros nos debug files são de validação (401, 402, 555), não de timeout ou indisponibilidade. O eSocial publica janelas de manutenção no portal, mas não afetou o uso documentado.

### 13.7. Existe algum ambiente de teste que NÃO precisa de certificado A1 real?
**R:** **Não.** Todo ambiente eSocial (restrito ou produção) exige certificado A1 ICP-Brasil para mTLS. Não existe simulador público oficial do SERPRO. Para testes sem certificado, seria necessário criar um mock local do webservice.

### 13.8. O S-1010 de alteração exige que o S-1010 de inclusão já tenha sido enviado antes? Ou as rubricas que já existem no eSocial (via outros sistemas) podem ser alteradas?
**R:** Este repositório não implementa S-1010, mas pela regra geral do eSocial: sim, para alterar uma rubrica o S-1010 de inclusão deve existir no ambiente (a rubrica precisa existir no RET - Registro de Eventos Trabalhistas). Porém, rubricas enviadas por outros sistemas (como folha de pagamento) já existem no eSocial e **podem ser alteradas** por qualquer sistema autorizado pelo certificado.

### 13.9. Se enviar um S-1010 de alteração com dados idênticos aos que já estão no eSocial, dá erro ou aceita normalmente?
**R:** Pela regra geral do eSocial: aceita alteração idêntica sem erro (não valida se houve mudança real nos dados). Gera novo recibo substituindo o anterior.

### 13.10. Qual o tamanho máximo do XML/lote que o eSocial aceita?
**R:** O eSocial aceita até **50 eventos por lote** e o XML total não pode exceder **500KB** descompactado. Este repositório envia 1 evento por lote, muito abaixo de ambos os limites.

---

## RESUMO TÉCNICO — CHEAT SHEET

| Item | Valor |
|------|-------|
| **Linguagem Backend** | Python 3.13 |
| **Framework** | FastAPI + SQLAlchemy |
| **Banco** | SQLite (esocial.db + s2501.db) |
| **Lib Assinatura** | `signxml` (enveloped, RSA-SHA256, SHA256, C14N) |
| **Lib Certificado** | `cryptography` (pkcs12) |
| **Lib HTTP** | `requests` (POST com mTLS) |
| **Lib XML** | `lxml` (parse + xpath) |
| **Protocolo** | SOAP 1.1 via template f-string |
| **mTLS** | PFX → PEM tempfiles → cert=(cert,key) |
| **Ambiente Padrão** | Produção Restrita |
| **Eventos Enviados** | S-2500, S-2501 (recebe S-5501) |
| **Grupo S-2500** | 2 (Não Periódicos) |
| **Eventos/Lote** | 1 |
| **Auto-consulta** | APScheduler 15min |
| **Certificado** | Upload UI → disco + SQLite (senha Fernet) |
| **verify SSL** | False (produção restrita) |
| **Timeout** | 60 segundos |

---

> **Próximo passo:** Analisar todas as respostas e criar o plano de ação da Fase 3.
> 
> *Documento gerado automaticamente a partir da análise do código-fonte em 27/03/2026*
