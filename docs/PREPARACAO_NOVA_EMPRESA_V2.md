# Relatorio - Nova Empresa no Easy-eSocial V2

Documento de decisao para entrada de uma nova empresa no padrao atual do Easy-eSocial V2, separando duas fases: cadastro/importacao sem envio e habilitacao futura de envio com certificado.

Resumo direto:

- Para somente colocar uma empresa nova dentro do banco, certificado nao e obrigatorio. CNPJ, razao social, schema, usuarios e ZIPs/XMLs historicos ja bastam para montar historico, explorer, timelines e relatorios.
- Se a empresa entregar e-CNPJ da propria empresa/matriz, o caminho de envio e o mais parecido com o atual, mas ainda precisa garantir que o certificado seja gravado no schema correto.
- Se a empresa usar e-CPF com procuracao para o CNPJ, o eSocial aceita esse modelo quando o CPF e representante legal ou procurador eletronico valido, mas o codigo atual nao esta pronto para tratar isso como "igualzinho" ao e-CNPJ.
- O maior cuidado tecnico para e-CPF e separar empregador, assinante e transmissor. Hoje parte do codigo ainda assume que transmissor e CNPJ.
- Nenhuma consulta, download ou envio ao eSocial deve ser feito nessa fase sem autorizacao explicita.

## Estado de arquitetura verificado

- O V2 ativo esta em `C:\Users\xandao\Documents\GitHub\Easy-eSocial-v2`.
- O backend e FastAPI e fica em `backend/app`.
- O frontend e Vue/Pinia/Vite e fica em `src`.
- Ha dois niveis de banco:
  - Sistema DB: autenticacao, usuarios, empresas e permissoes.
  - Dados DB: dados operacionais, isolados por schema PostgreSQL.
- Empresas ativas hoje:
  - APPA: CNPJ `05969071000110`, schema `appa`, versao `1.1.0`, id legado `1`.
  - SOLUCOES: CNPJ `09445502000109`, schema `solucoes`, versao `1.1.0`, id legado `2`.
  - OBJETIVA: CNPJ `10874523000110`, schema `objetiva`, versao `1.1.0`, id legado `3`.
- Ana esta vinculada como operadora nas empresas liberadas para ela. O super_admin enxerga todas por override.
- Schemas `appa`, `solucoes` e `objetiva` seguem o modelo de migrations `empresa` versoes `1.0.0` e `1.1.0`.
- Volumes historicamente verificados:
  - `appa.explorador_eventos`: 375.985 linhas; `certificados_a1`: 1.
  - `solucoes.empresa_zips_brutos`: 24 ZIPs; `explorador_eventos`: 2.636.102 linhas; `timeline_mes`: 12; `timeline_envio`: 1.236; `timeline_envio_item`: 191.858.
  - `objetiva.empresa_zips_brutos`: 12 ZIPs; `explorador_eventos`: 169.261 linhas; `timeline_mes`: 12; `timeline_envio`: 12; certificado A1 ativo.

## Modelo que deve ser repetido

1. Cada empresa entra em `sistema.empresas_routing` com CNPJ, razao social, `schema_name`, versao e ativo.
2. Cada usuario autorizado entra em `sistema.user_empresas` com papel (`admin`, `operador` ou `leitor`).
3. O schema da empresa no Dados DB recebe as migrations `empresa_v1.0.0` e `empresa_v1.1.0`.
4. Os ZIPs originais sao preservados em `empresa_zips_brutos` como Large Object, com hash, tamanho, periodo e status de extracao.
5. Cada XML dentro do ZIP vira linha em `explorador_eventos`, apontando para `zip_id` e `xml_entry_name`.
6. S-1210 e S-5002 recebem enriquecimento em `dados_json` para alimentar analises, S-1210 anual e validacoes.
7. O chain walk cria `timeline_mes`, `timeline_envio` e `timeline_envio_item` por `per_apur`.
8. XML original permanece no ZIP bruto; XML enviado/alterado e XML de retorno ficam em `timeline_envio_item.xml_enviado_oid` e `xml_retorno_oid` quando houver envio.

## Roteiro DB-only, sem envio inicial

1. Confirmar CNPJ, razao social oficial, slug/schema desejado e usuarios que devem enxergar a empresa.
2. Criar schema novo no Dados DB e aplicar migrations `empresa_v1.0.0` e `empresa_v1.1.0`.
3. Cadastrar `sistema.empresas_routing` e vinculos em `sistema.user_empresas`.
4. Seedar `master_empresas`, `config_esocial` e tabelas auxiliares necessarias no schema novo.
5. Escanear os ZIPs/XMLs antes de importar, conferindo `per_apur`, tipos de evento e quantidade de XMLs.
6. Importar os ZIPs para `empresa_zips_brutos` e extrair os XMLs para `explorador_eventos`.
7. Rodar e validar o backfill de timeline/chain walk para os meses disponiveis.
8. Auditar contagens por mes e tipo: S-1210, S-5002, S-1200, S-2200, S-2299, S-3000 e demais eventos presentes.
9. Verificar recuperacao dos XMLs originais e renderizacao das telas/relatorios no frontend.
10. Somente validar certificado, enviar ou consultar eSocial depois de autorizacao explicita do usuario.

Comandos de migration, em formato de referencia:

```powershell
python -m app.migrate apply --target empresa --version 1.0.0 --schema novaempresa --dsn $env:SISTEMA_DB_URL
python -m app.migrate apply --target empresa --version 1.1.0 --schema novaempresa --dsn $env:SISTEMA_DB_URL
```

Esses comandos sao roteiro. Nao devem ser rodados sem definir CNPJ/schema real e confirmar ambiente.

## O que precisa para DB-only

| Item                    | Obrigatorio?     | Observacao                                                            |
| ----------------------- | ---------------- | --------------------------------------------------------------------- |
| CNPJ da empresa         | Sim              | Completo, 14 digitos.                                                 |
| Razao social            | Sim              | Usada em cadastro, rotas e telas.                                     |
| Schema/slug             | Sim              | Nome tecnico seguro, ex: `empresa_x`.                                 |
| Usuarios e papeis       | Sim              | Quem enxerga a empresa no seletor.                                    |
| ZIPs mensais do eSocial | Recomendado      | Melhor formato, preserva bruto em `empresa_zips_brutos`.              |
| XMLs soltos             | Possivel         | Exige importacao mais especifica e foge um pouco do padrao ZIP bruto. |
| Certificado A1          | Nao para DB-only | So entra quando houver assinatura/envio/consulta.                     |
| Senha do certificado    | Nao para DB-only | So pedir quando for validar/gravar certificado.                       |

Conclusao direta: para colocar a empresa no banco no padrao das outras, o certificado pode ficar para depois. O que nao pode faltar e cadastro correto da empresa e arquivos historicos suficientes.

## Plano operacional para subir a proxima empresa no V2

Escopo desta fase: cadastro, banco, Explorer, Chain Walk e S-1210 anual. Ficam desligados: envio, consulta de lote, Download do eSocial, ConsultarIdentificadores, certificado e qualquer chamada externa ao eSocial.

### 1. Informacoes minimas antes de executar

Quando o caminho da pasta for informado, ainda preciso confirmar ou inferir estes pontos:

| Campo           | Como usar                                                                 |
| --------------- | ------------------------------------------------------------------------- |
| CNPJ            | Chave em `sistema.empresas_routing`, `master_empresas` e header do front. |
| Razao social    | Nome exibido no seletor e gravado no schema da empresa.                   |
| Schema tecnico  | Nome PostgreSQL, ex: `empresa_nova`, sem acento, espaco ou hifen.         |
| Id legado       | Proximo inteiro livre, hoje depois de APPA=1, SOLUCOES=2, OBJETIVA=3.     |
| Ano de trabalho | Para classificar S-1210 mensal e montar a visao anual.                    |
| Pasta de ZIPs   | Local com ZIPs mensais ou XMLs historicos fornecidos pelo usuario.        |
| Usuarios        | Quem deve enxergar a empresa no seletor, normalmente Ana e/ou admin.      |

### 2. Ajuste obrigatorio de roteamento legado

O V2 ja autentica e seleciona empresa por CNPJ, mas Explorer e S-1210 anual ainda carregam `empresa_id` numerico em varios endpoints. Por isso, para a proxima empresa aparecer e funcionar no front sem uma refatoracao maior, o caminho rapido e registrar um novo id legado.

Pontos que precisam receber o novo id:

- Backend: `backend/app/tenant.py`, adicionando constante da empresa e entrada em `_EMPRESA_SCHEMA`.
- Frontend: `src/stores/empresa.ts`, adicionando o CNPJ/schema no `currentId`.
- Dados: `master_empresas.id` dentro do schema novo deve usar o mesmo id legado.
- Flags: `sistema.empresas_routing.flags` deve guardar algo como `empresa_id_legado` para auditoria.

Sem esse ajuste, a empresa pode ate aparecer pelo CNPJ no seletor, mas as telas que dependem de `empresaStore.currentId` tendem a falhar ou mostrar mensagem de empresa nao selecionada.

### 3. Provisionamento do banco

Sequencia prevista:

1. Criar schema no Dados DB.
2. Aplicar migrations `empresa_v1.0.0` e `empresa_v1.1.0` no schema novo.
3. Inserir ou atualizar `sistema.empresas_routing`.
4. Inserir vinculos em `sistema.user_empresas`.
5. Inserir `master_empresas` no schema novo com o id legado definido.
6. Inserir `config_esocial` apenas com configuracao basica local, sem certificado.
7. Garantir colunas auxiliares ja usadas pelo Explorer moderno, como `empresa_zips_brutos.extracao_progresso` e `explorador_eventos.xml_bytes`, se o ambiente ainda nao tiver aplicado esses ajustes.

Referencia de SQL esperado para o Sistema DB:

```sql
INSERT INTO sistema.empresas_routing
    (cnpj, razao_social, schema_name, schema_version, flags, ativo)
VALUES
    (:cnpj, :razao_social, :schema, '1.1.0', :flags::jsonb, TRUE)
ON CONFLICT (cnpj) DO UPDATE
   SET razao_social = EXCLUDED.razao_social,
       schema_name = EXCLUDED.schema_name,
       schema_version = '1.1.0',
       flags = EXCLUDED.flags,
       ativo = TRUE,
       atualizado_em = NOW();
```

Referencia de SQL esperado no schema da empresa:

```sql
INSERT INTO master_empresas (id, nome, cnpj, db_name, ativo, tipo_estado)
VALUES (:empresa_id, :razao_social, :cnpj, :schema, TRUE, 'estado_1')
ON CONFLICT (id) DO UPDATE
   SET nome = EXCLUDED.nome,
       cnpj = EXCLUDED.cnpj,
       db_name = EXCLUDED.db_name,
       ativo = TRUE,
       tipo_estado = 'estado_1';

INSERT INTO config_esocial (cnpj, ini_valid_padrao, auto_detected)
VALUES (:cnpj, :ano || '-01', TRUE);
```

### 4. Importacao local dos arquivos

O padrao mais limpo e trabalhar com ZIPs mensais. Cada ZIP entra em `empresa_zips_brutos` com hash SHA-256, tamanho, periodo, nome original, Large Object do conteudo e status `pendente`. Depois a rotina do Explorador extrai o ZIP e cria as linhas de `explorador_eventos`.

Fluxo confirmado no V2:

1. O upload da UI usa `/api/explorador/zips/upload` com `arquivo`, `empresa_id`, `dt_ini` e `dt_fim`.
2. O backend salva o ZIP bruto em `empresa_zips_brutos`.
3. A extracao roda `_extrair_zip_sync()`.
4. Cada XML vira evento em `explorador_eventos`, com `tipo_evento`, `cpf`, `per_apur`, `nr_recibo`, `id_evento`, `dados_json`, `zip_id`, `xml_entry_name` e XML original preservado.
5. No fim da extracao, o backend chama `backfill_chain.backfill_empresa()`.

Para volume grande, o caminho mais controlado e adaptar o script de onboarding ja usado na Objetiva. Ele deve trocar CNPJ, schema, id legado, ano e pasta de ZIPs; nesta fase, o bloco de certificado deve ser removido ou deixado desativado.

### 5. Chain Walk, o "tchaimewalk"

O Chain Walk nasce do backfill local, nao de chamada externa. Depois que os ZIPs forem extraidos:

- `timeline_mes` deve ter uma linha por `per_apur` encontrado.
- `timeline_envio` deve ter a sequencia inicial `0`, tipo `zip_inicial`, representando o historico importado.
- `explorador_eventos.origem_envio_id` deve apontar para a origem do evento na timeline.
- Eventos retificados devem ficar ligados por `referenciado_recibo` e `retificado_por_id` quando o XML traz essa referencia.
- O painel do front em `/explorador` usa essa base para mostrar meses, CPFs, cadeia de versoes e tentativas.

Validacoes minimas:

```sql
SELECT COUNT(*) AS zips
  FROM empresa_zips_brutos
 WHERE empresa_id = :empresa_id;

SELECT per_apur, COUNT(*) AS eventos, COUNT(DISTINCT cpf) AS cpfs
  FROM explorador_eventos
 GROUP BY per_apur
 ORDER BY per_apur;

SELECT COUNT(*) AS meses
  FROM timeline_mes
 WHERE empresa_id = :empresa_id;

SELECT tm.per_apur, COUNT(*) AS envios
  FROM timeline_mes tm
  JOIN timeline_envio te ON te.timeline_mes_id = tm.id
 WHERE tm.empresa_id = :empresa_id
 GROUP BY tm.per_apur
 ORDER BY tm.per_apur;
```

### 6. S-1210 anual no front

A tela anual nao depende de envio novo. Ela depende de S-1210 importado, timeline montada e CPFs/head corretos no Explorer.

Fluxo confirmado no V2:

- Rota anual: `/esocial/s1210-anual`.
- Rota do mes: `/esocial/s1210-anual/:per_apur/:lote_num`.
- Backend anual: `/api/s1210-repo/anual/overview`.
- Backend CPFs do mes: `/api/s1210-repo/cpfs-do-mes`.
- Detalhe CPF: `/api/s1210-repo/anual/detalhe-cpf/{lote}/{per_apur}/{cpf}`.
- Download XML CPF: `/api/s1210-repo/anual/xml-cpf/{lote}/{per_apur}/{cpf}`.

O que precisa aparecer depois da importacao:

1. Grade anual com os meses do ano informado.
2. Total de CPFs S-1210 por mes.
3. Lista de CPFs ao abrir cada mes.
4. Modal de detalhe com pagamentos do S-1210.
5. S-5002 relacionado quando existir no ZIP.
6. Download do XML original pelo front.

Contagem principal para conferir o S-1210 anual:

```sql
SELECT per_apur, COUNT(DISTINCT cpf) AS cpfs_head
  FROM explorador_eventos
 WHERE tipo_evento = 'S-1210'
   AND retificado_por_id IS NULL
   AND per_apur LIKE :ano || '-%'
 GROUP BY per_apur
 ORDER BY per_apur;
```

### 7. Auditoria mes a mes que vou gerar

Depois que voce passar a pasta, a saida esperada e um quadro por mes com:

- nome do ZIP ou origem dos XMLs;
- periodo detectado por nome e por XML;
- total de XMLs lidos;
- contagem por tipo de evento;
- CPFs distintos em S-1210;
- CPFs distintos em S-5002;
- S-1210 sem S-5002 correspondente, quando der para comparar;
- quantidade de retificacoes e eventos head;
- meses ausentes, duplicados ou com `per_apur` divergente;
- status do ZIP no Explorer;
- status do Chain Walk;
- status da tela S-1210 anual.

### 8. Checklist de pronto para usar no front

Antes de dizer que a empresa ficou limpa no V2, a validacao deve passar por estes pontos:

1. Login mostra a empresa no seletor para o usuario certo.
2. `X-Empresa-CNPJ` resolve para o schema novo.
3. `empresaStore.currentId` devolve o id legado novo.
4. `/explorador` lista os ZIPs importados.
5. Cada ZIP abre resumo e eventos.
6. Download de XML do Explorer retorna XML valido.
7. Chain Walk lista os meses.
8. Cadeia de um CPF S-1210 abre no painel.
9. `/esocial/s1210-anual` mostra meses e totais.
10. Um mes abre a lista de CPFs.
11. O detalhe de CPF abre pagamentos e S-5002 quando existir.
12. Download de XML por CPF funciona.
13. Nenhuma tabela de envio real foi movimentada por essa importacao.
14. Nenhuma chamada externa ao eSocial foi feita.

### 9. O que vou fazer quando receber o caminho da pasta

1. Examinar somente arquivos locais da pasta informada.
2. Separar ZIPs mensais, XMLs soltos e arquivos que nao entram no fluxo.
3. Detectar ano, `per_apur`, tipos de evento e quantidade de XMLs antes de importar.
4. Propor CNPJ/schema/id legado se ainda faltar algum dado.
5. Preparar ou adaptar o script DB-only da nova empresa, baseado no onboarding da Objetiva mas sem certificado.
6. Rodar migrations e inserts locais no banco correto somente depois de conferir as variaveis.
7. Importar e extrair os ZIPs/XMLs.
8. Rodar/validar backfill do Chain Walk.
9. Validar Explorer e S-1210 anual.
10. Entregar resumo de auditoria mes a mes.

Nada nessa lista usa cota do eSocial.

## O que ZIP/XML resolve e o que nao resolve

Com ZIPs/XMLs historicos, da para preservar arquivos originais, extrair eventos para `explorador_eventos`, montar visoes por CPF/evento/mes/recibo, reconstruir relatorios e alimentar timeline/chain walk quando os dados tiverem estrutura suficiente.

Com ZIPs/XMLs historicos, nao da para garantir sozinho envio futuro de novos eventos, retificacao correta sem recibo valido, permissao do certificado/procuracao ou consistencia da folha de origem quando o evento novo precisa ser gerado do zero.

Ou seja: ZIP/XML e excelente para historico e auditoria. Para envio entra outra camada: certificado, identidade de transmissao, regras do evento, recibos e dados fonte.

## Certificado e-CNPJ

Quando o certificado A1 pertence ao CNPJ da empresa ou a matriz do mesmo CNPJ-base, o fluxo e o mais parecido com o atual:

- o evento continua com `ideEmpregador` apontando para o CNPJ raiz da empresa;
- o lote usa `ideTransmissor` como CNPJ completo;
- o PFX assina o XML;
- o mesmo PFX e usado no HTTPS/mTLS contra o webservice;
- o eSocial valida se o assinante tem relacao permitida com o empregador.

Mesmo nesse caso, existe um cuidado tecnico: `backend/app/cert_routes.py` ainda declara e usa certificado em modo single-tenant via `app.db`, com TODO para `tenant.empresa_conn`. Antes de confiar no upload pela UI para empresa nova, e preciso garantir que ele grave no schema da empresa selecionada.

## e-CPF com procuracao

Pela orientacao publica do eSocial sobre Procuracao Eletronica e Assinatura Digital, quando o empregador e CNPJ e o assinante e pessoa fisica, o evento pode ser aceito quando:

Referencia publica consultada: `https://www.gov.br/esocial/pt-br/acesso-ao-sistema/orientacoes-assinatura-digital-e-procuracao-eletronica`.

- o CPF do assinante consta como representante legal do CNPJ na base da RFB; ou
- o CPF do assinante possui procuracao eletronica outorgada pelo empregador, com perfil de acesso que cobre os eventos enviados.

Na pratica, com e-CPF procurador:

- o empregador continua sendo o CNPJ da empresa nova;
- o XML do evento continua identificando a empresa em `ideEmpregador`;
- o certificado que assina e autentica a conexao e de CPF;
- o transmissor do lote deve ser tratado como CPF, nao como CNPJ;
- a procuracao precisa estar cadastrada no e-CAC/RFB com perfil compativel com eSocial e com os eventos desejados.

O codigo atual ja tem pecas genericas: `CertificateManager.validate_pfx()` consegue extrair documento de 11 ou 14 digitos, o assinador XML usa a chave privada sem exigir CNPJ e o mTLS tambem usa o PFX genericamente. Mas ainda ha pontos que assumem CNPJ no fluxo de envio.

Gaps encontrados para e-CPF:

1. `backend/app/esocial_client.py` monta `ideTransmissor` sempre com `tpInsc=1`, ou seja, CNPJ.
2. `enviar_lote()` assume `cnpj_transmissor = cnpj_empregador` quando nao recebe transmissor separado.
3. `envio_paralelo_v2.py` envia S-1210 sem identidade separada de transmissor.
4. `envio_s1298.py` pode assumir o documento do certificado como CNPJ do empregador se `--cert-id` for usado sem `--cnpj`; isso e perigoso para e-CPF.
5. `cert_routes.py` ainda nao esta plenamente tenant-aware.
6. A tabela `certificados_a1` usa coluna chamada `cnpj`, o que comporta CPF por tamanho, mas confunde a regra de negocio.

Conclusao tecnica: e-CPF com procuracao nao deve ser usado em envio real no estado atual sem uma adaptacao pequena antes.

## Alteracoes recomendadas para liberar e-CPF

1. Tornar certificado multi-tenant de ponta a ponta, sempre usando a empresa selecionada por CNPJ/header.
2. Guardar `documento_certificado` e `tipo_inscricao_certificado` (`1=CNPJ`, `2=CPF`), mesmo que a coluna legada continue existindo.
3. Criar configuracao explicita de envio por empresa: `empregador_cnpj`, `transmissor_tp_insc`, `transmissor_nr_insc`, `cert_id`.
4. Alterar `esocial_client._montar_lote_xml()` para receber tipo/documento do transmissor, permitindo `tpInsc=2` e CPF com 11 digitos.
5. Alterar S-1210 e S-1298 para nunca inferirem CNPJ empregador a partir do certificado quando o certificado for CPF.
6. Adicionar preflight local que gera lote sem enviar, mostrando `ideEmpregador`, `ideTransmissor`, certificado usado e ambiente.
7. Bloquear envio se certificado for CPF e nao houver CNPJ empregador explicito e confirmacao de procuracao.
8. Testar somente com autorizacao explicita, idealmente primeiro em ambiente permitido/producao restrita.

## Pontos de atencao antes de uma nova empresa

- O auth e o seletor de empresas ja funcionam por CNPJ via `X-Empresa-CNPJ`.
- Algumas rotas/telas antigas ainda dependem de `empresa_id` numerico.
- Hoje o mapeamento legado conhecido e APPA=1, SOLUCOES=2 e OBJETIVA=3.
- Para uma nova empresa, e preciso escolher uma destas estrategias:
  - caminho rapido: registrar um novo `empresa_id` legado, ajustar `tenant.py` e o store `empresa.ts` para mapear CNPJ -> id;
  - caminho correto: migrar Explorer, S-1210 anual, certificado e envio para usarem CNPJ/header diretamente.
- A rota atual de certificado ainda precisa ser tratada com cuidado porque ha trecho single-tenant/TODO multi-tenant.
- Importar ZIPs fornecidos pelo usuario nao consome cota de Download do eSocial. Download/ConsultarIdentificadores/SolicitarDownload continuam proibidos sem autorizacao explicita.

## Entradas que o usuario deve fornecer

- CNPJ e razao social da nova empresa.
- Schema/slug tecnico desejado.
- Quais usuarios devem ter acesso e com qual papel.
- Caminho da pasta com ZIPs mensais ou XMLs historicos.
- Se/quando for habilitar envio: caminho do arquivo `.pfx` ou `.p12` do certificado.
- Se/quando for habilitar envio: senha do certificado digitada diretamente pelo usuario quando necessario.
- Se o certificado for e-CPF: confirmacao de que o CPF e representante legal ou possui procuracao eletronica eSocial para o CNPJ, com perfil compativel com os eventos.

## Resposta final curta

Para DB-only, sim: e praticamente o mesmo padrao das empresas atuais e pode ser feito so com cadastro + ZIPs/XMLs. Certificado fica opcional nessa fase.

Para envio com e-CNPJ, o caminho e quase o atual, apos corrigir/validar o armazenamento tenant-aware do certificado.

Para envio com e-CPF procurador, o eSocial permite quando a procuracao/representacao esta correta, mas o codigo atual precisa ser ajustado antes porque ainda monta transmissor como CNPJ e tem pontos que confundem documento do certificado com CNPJ empregador.
