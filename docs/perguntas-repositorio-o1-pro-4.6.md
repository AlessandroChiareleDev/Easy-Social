# Perguntas sobre o Repositório o1 pro 4.6 (eSocial Web Service)

> **Objetivo:** Entender TUDO sobre como esse repositório se comunica com o eSocial em produção restrita (homologação), para usar como base na implementação do Easy Social.
> 
> **Instrução:** Responda cada pergunta diretamente abaixo dela. Pode ser curto ou longo, o importante é ser preciso.

---

## 1. VISÃO GERAL DO REPOSITÓRIO

### 1.1. Qual é a URL/caminho do repositório? (GitHub? Local? Onde está?)
**R:**

### 1.2. Qual a stack/linguagem principal? (Node.js? Python? PHP? Java? C#?)
**R:**

### 1.3. Quais frameworks/libs principais ele usa? (Express? FastAPI? Spring? o quê?)
**R:**

### 1.4. Tem frontend ou é só backend/CLI?
**R:**

### 1.5. Qual a estrutura de pastas principal? (src/, lib/, services/, etc.)
**R:**

### 1.6. Ele já está em produção real ou só funciona em produção restrita (homologação)?
**R:**

### 1.7. Quais eventos do eSocial ele suporta? (Só S-1010? Também S-1000, S-1020, S-1200, etc.?)
**R:**

### 1.8. Ele foi feito especificamente para o S-1010 ou é um sistema genérico de comunicação eSocial?
**R:**

---

## 2. CERTIFICADO DIGITAL A1

### 2.1. Como o certificado A1 (.pfx) é carregado? (Upload via UI? Caminho fixo no código? Variável de ambiente?)
**R:**

### 2.2. Como a senha do certificado é fornecida? (Input do usuário? .env? Hardcoded?)
**R:**

### 2.3. O certificado é armazenado em algum lugar persistente ou só fica em memória?
**R:**

### 2.4. Qual biblioteca/módulo é usado para ler o PFX e extrair a chave privada + certificado público?
**R:**

### 2.5. Ele valida se o certificado é ICP-Brasil? Verifica validade/expiração?
**R:**

### 2.6. Como ele lida com a cadeia de certificados do Serpro? Baixa automaticamente? Está embutida no código? O usuário precisa instalar manualmente?
**R:**

---

## 3. MONTAGEM DO XML DO EVENTO

### 3.1. Como o XML do S-1010 é montado? (Template string? Biblioteca de XML? Builder?)
**R:**

### 3.2. De onde vêm os dados das rubricas para preencher o XML? (Banco de dados? Arquivo? API?)
**R:**

### 3.3. Ele monta inclusão, alteração e exclusão, ou só um desses modos?
**R:**

### 3.4. Como o ID do evento é gerado? (Segue o padrão ID{tpInsc}{nrInsc14}{timestamp}{seq5}?)
**R:**

### 3.5. Como ele preenche o `ideEmpregador` (tpInsc, nrInsc)? De onde vem o CNPJ?
**R:**

### 3.6. Qual namespace/versão do XML ele usa? (vS01_03_00 = S-1.3? Ou versão anterior?)
**R:**

### 3.7. Ele valida o XML contra o XSD antes de enviar?
**R:**

### 3.8. Pode colar aqui um exemplo real de XML que ele gera (pode censurar o CNPJ)?
**R:**

---

## 4. ASSINATURA DIGITAL DO XML

### 4.1. Qual biblioteca é usada para assinar o XML? (xml-crypto? signxml? xmlsec? outra?)
**R:**

### 4.2. A assinatura é enveloped (dentro do XML) conforme o padrão eSocial?
**R:**

### 4.3. Ele usa RSA-SHA256 para assinatura e SHA-256 para digest?
**R:**

### 4.4. A canonicalization é C14N conforme esperado?
**R:**

### 4.5. O `<Signature>` fica como último filho de `<eSocial>`, após o `<evtTabRubrica>`?
**R:**

### 4.6. Teve algum problema/bug com a assinatura que foi difícil de resolver? Qual?
**R:**

### 4.7. Pode colar aqui o trecho de código que faz a assinatura?
**R:**

---

## 5. ENVELOPE SOAP E ENVIO

### 5.1. Como o envelope SOAP é montado? (Template? Biblioteca SOAP? Builder?)
**R:**

### 5.2. Ele usa SOAP 1.1 conforme o eSocial exige?
**R:**

### 5.3. Qual biblioteca HTTP é usada para o POST? (axios? fetch? requests? HttpClient?)
**R:**

### 5.4. Como o mTLS (mutual TLS) é configurado? (O certificado A1 é passado como client cert na requisição HTTPS?)
**R:**

### 5.5. Pode colar aqui o trecho de código que faz o envio HTTP com mTLS?
**R:**

### 5.6. O SOAPAction header está configurado corretamente? Qual valor usa?
**R:**

### 5.7. Ele envia para produção restrita ou produção? A URL é configurável?
**R:**

### 5.8. Quantos eventos ele envia por lote? (1 por vez? Máximo 50? Configurável?)
**R:**

### 5.9. Ele agrupa os eventos por `grupo` (1=tabelas, 2=não periódicos, 3=periódicos)?
**R:**

---

## 6. TRATAMENTO DA RESPOSTA

### 6.1. Como ele parseia a resposta SOAP do eSocial?
**R:**

### 6.2. Ele extrai o `protocoloEnvio` da resposta de envio?
**R:**

### 6.3. Como ele faz a consulta do resultado? (Polling? Timer? Manual?)
**R:**

### 6.4. Qual o intervalo entre envio e consulta? Tem retry?
**R:**

### 6.5. O que ele faz quando recebe sucesso (nrRecibo)?
**R:**

### 6.6. O que ele faz quando recebe erro? Quais erros mais comuns já apareceram?
**R:**

### 6.7. Ele salva o protocolo/recibo em banco de dados?
**R:**

### 6.8. Pode colar aqui um exemplo de resposta de sucesso do eSocial?
**R:**

### 6.9. Pode colar aqui um exemplo de resposta de erro do eSocial?
**R:**

---

## 7. BANCO DE DADOS E PERSISTÊNCIA

### 7.1. Ele usa banco de dados? Qual? (PostgreSQL? MySQL? SQLite? MongoDB?)
**R:**

### 7.2. Quais tabelas/collections existem relacionadas ao envio de eventos?
**R:**

### 7.3. Ele guarda histórico de todos os envios (sucesso e erro)?
**R:**

### 7.4. Tem alguma tabela de "fila de envio" ou "staging" para eventos pendentes?
**R:**

### 7.5. Como ele controla quais rubricas já foram enviadas e quais ainda não?
**R:**

---

## 8. CONFIGURAÇÃO E AMBIENTE

### 8.1. Quais variáveis de ambiente ele usa? (.env? Config file? Quais chaves?)
**R:**

### 8.2. Como ele diferencia entre produção restrita e produção? (Flag? Variável? URL diferente?)
**R:**

### 8.3. Precisa instalar alguma dependência do sistema operacional? (OpenSSL? libxmlsec? outro?)
**R:**

### 8.4. Tem Docker? docker-compose?
**R:**

### 8.5. Qual versão do Node/Python/linguagem é necessária?
**R:**

---

## 9. ERROS E PROBLEMAS ENCONTRADOS

### 9.1. Quais foram os maiores problemas/bugs que vocês encontraram na integração com o eSocial?
**R:**

### 9.2. A assinatura digital deu trabalho? O que deu errado?
**R:**

### 9.3. O mTLS deu problema? Erro de SSL? Como resolveu?
**R:**

### 9.4. Algum problema com encoding (UTF-8, BOM, etc.) no XML?
**R:**

### 9.5. O eSocial retornou algum erro inesperado ou mal documentado?
**R:**

### 9.6. Quanto tempo levou para fazer o primeiro envio com sucesso em produção restrita?
**R:**

---

## 10. FLUXO DE USO

### 10.1. Qual o passo a passo para um usuário usar o sistema e enviar um S-1010?
**R:**

### 10.2. Ele tem interface gráfica ou é tudo via terminal/API?
**R:**

### 10.3. O usuário seleciona quais rubricas alterar ou é tudo automático?
**R:**

### 10.4. Tem preview do XML antes de enviar?
**R:**

### 10.5. Tem confirmação antes do envio definitivo?
**R:**

---

## 11. CÓDIGO-FONTE (TRECHOS IMPORTANTES)

### 11.1. Pode colar o arquivo/função principal que orquestra o fluxo de envio?
**R:**

### 11.2. Pode colar o arquivo/função que monta o XML do S-1010?
**R:**

### 11.3. Pode colar o arquivo/função que faz a assinatura digital?
**R:**

### 11.4. Pode colar o arquivo/função que faz o envio SOAP HTTP?
**R:**

### 11.5. Pode colar o arquivo/função que parseia a resposta?
**R:**

### 11.6. Pode colar o arquivo/função que faz a consulta do lote?
**R:**

### 11.7. Pode colar o package.json / requirements.txt / equivalente com as dependências?
**R:**

### 11.8. Pode colar o arquivo de configuração (.env.example, config.ts, etc.)?
**R:**

---

## 12. INTEGRAÇÃO COM O EASY SOCIAL

### 12.1. Na sua opinião, o que do repositório o1 pro 4.6 pode ser reaproveitado diretamente no Easy Social?
**R:**

### 12.2. O que precisaria ser adaptado?
**R:**

### 12.3. O que NÃO serve e teria que ser feito do zero?
**R:**

### 12.4. Qual a parte mais difícil/complexa de toda a integração?
**R:**

### 12.5. Alguma dica ou conselho para quem vai implementar isso?
**R:**

---

## 13. PERGUNTAS EXTRAS

### 13.1. O eSocial em produção restrita aceita qualquer CNPJ ou precisa ser um CNPJ real cadastrado?
**R:**

### 13.2. Tem algum CNPJ de teste ou sandbox?
**R:**

### 13.3. O certificado A1 usado em produção restrita precisa ser real (ICP-Brasil) ou aceita certificado de teste?
**R:**

### 13.4. Quanto tempo os dados ficam na produção restrita antes de serem limpos?
**R:**

### 13.5. Existe rate limit no web service do eSocial? Quantos requests por minuto/hora?
**R:**

### 13.6. O web service fica fora do ar com frequência? Tem janela de manutenção?
**R:**

### 13.7. Existe algum ambiente de teste que NÃO precisa de certificado A1 real?
**R:**

### 13.8. O S-1010 de alteração exige que o S-1010 de inclusão já tenha sido enviado antes? Ou as rubricas que já existem no eSocial (via outros sistemas) podem ser alteradas?
**R:**

### 13.9. Se enviar um S-1010 de alteração com dados idênticos aos que já estão no eSocial, dá erro ou aceita normalmente?
**R:**

### 13.10. Qual o tamanho máximo do XML/lote que o eSocial aceita?
**R:**

---

> **Depois de respondido:** Vou analisar todas as respostas e criar o plano de ação da Fase 3.
