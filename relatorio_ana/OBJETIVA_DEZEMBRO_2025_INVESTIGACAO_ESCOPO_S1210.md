# Objetiva - Investigacao empirica do escopo S-1210 dezembro/2025

Data: 2026-05-26

Empresa: Objetiva, CNPJ 10.874.523/0001-10, V2 `empresa_id=3`, schema `objetiva`.

## Escopo desta investigacao

Pedido: entender, empiricamente, como a pasta base `C:\Users\xandao\Downloads\mes a mes Objetiva zip` virou o escopo do S-1210 anual da Objetiva, e avaliar se o novo ZIP de 2026 contem o que falta para povoar dezembro/2025.

Importante: a investigacao inicial foi feita sem importacao nova, sem envio e sem consulta ao eSocial. Depois da validacao do criterio de ultimo S-1210 por CPF, em 2026-05-26 foi executado apenas o povoamento local/banco do escopo de dezembro, ainda sem qualquer chamada ao eSocial.

## Resposta curta

Sim: o arquivo novo `01-01 ate 31-01  2026  objetiva.zip` contem material suficiente para povoar o escopo S-1210 de dezembro/2025.

Ele contem:

- 21.648 XMLs no total.
- 2.431 XMLs S-1210.
- 1.284 CPFs distintos em S-1210.
- 100% dos S-1210 com `perApur=2025-12`.
- 100% dos `dtPgto` dos S-1210 em `2025-12`.
- 2.419 S-1210 com `indRetif=1` e 12 com `indRetif=2`.
- Os 12 `indRetif=2` tinham `nrRecibo` detectado no XML.

Status atualizado apos execucao de 2026-05-26:

- O ZIP foi importado no banco V2/schema `objetiva` como `zip_id=13`.
- A extracao terminou com 21.648 XMLs processados, 21.648 ok, 0 duplicados e 0 falhas.
- Foi criado `timeline_mes_id=13` para `per_apur=2025-12`.
- Foi criado `timeline_envio_id=28`, sequencia 0, tipo `zip_inicial`, status `concluido`.
- Foram associados 2.431 S-1210 a `origem_envio_id=28`.
- A tela anual passou a mostrar dezembro/2025 com 1.284 CPFs, todos pendentes, estado `pronto_para_processar`.

Nao foi feito envio/retificacao S-1210; isso foi somente povoamento do escopo a partir do ZIP local.

## Como a pasta virou escopo anual

O processo observado nos scripts V2 de upload/extracao/backfill segue este padrao:

1. O ZIP e cadastrado em `empresa_zips_brutos`.
   - O arquivo e armazenado como Large Object (`conteudo_oid`).
   - Sao gravados `empresa_id`, `dt_ini`, `dt_fim`, nome original, `sha256`, tamanho e status de extracao.

2. A extracao percorre todos os XMLs do ZIP.
   - O tipo de evento e detectado pelo nome do arquivo, por exemplo `*.S-1210.xml`.
   - `parse_xml_bytes` le o XML e extrai campos centrais.
   - O `per_apur` gravado em `explorador_eventos` vem da tag XML `<perApur>`, nao do nome do ZIP, nem de `dt_ini/dt_fim` do ZIP.

3. Para S-1210, a extracao enriquece `dados_json`.
   - `extrair_s1210` grava `pagamentos` com `dtPgto`, `tpPgto`, `perRef`, `ideDmDev`, `vrLiq`.
   - Tambem grava `infoIRCR`, `planSaude`, `indRetif` e `nrReciboAtual` quando existem.

4. O backfill cria/atualiza a competencia na timeline.
   - Cria `timeline_mes(empresa_id, per_apur)`.
   - Cria `timeline_envio` sequencia 0, tipo `zip_inicial`.
   - Associa os S-1210 daquele `per_apur` a esse envio inicial via `origem_envio_id`.

5. A tela anual V2 nao usa apenas XML bruto.
   - A rota anual primeiro exige existencia de `timeline_mes` para o periodo.
   - Depois conta os S-1210 de `explorador_eventos` com aquele `per_apur`.
   - O total exibido na tela e por CPF distinto/head, nao por quantidade bruta de XMLs.

Conclusao do metodo: para povoar dezembro/2025, nao basta existir um ZIP com data janeiro/2026. O ponto decisivo e importar os XMLs que tenham `<perApur>2025-12</perApur>` e criar o `timeline_mes` de `2025-12`.

## Onde entra `dtPgto`

A tag `dtPgto` aparece dentro dos pagamentos (`infoPgto`) do S-1210. Ela e preservada no `dados_json.pagamentos` e e usada quando o XML precisa ser reconstruido/retificado, porque o gerador S-1210 monta de volta cada pagamento com:

- `dtPgto`
- `tpPgto`
- `perRef`
- `ideDmDev`
- `vrLiq`

Mas, no codigo observado, o agrupamento do escopo anual por mes nao e derivado de `dtPgto`. O agrupamento vem de `<perApur>`.

Mesmo assim, `dtPgto` foi usado nesta investigacao como prova empirica de coerencia: no ZIP novo de 2026, os S-1210 tem `perApur=2025-12` e os `dtPgto` tambem caem em `2025-12`. Ou seja, ele nao e apenas um ZIP processado em janeiro/2026; ele contem de fato pagamentos de dezembro/2025.

## Como o sistema escolhe o ultimo S-1210 por CPF

Este e o ponto mais sensivel para dezembro: o ZIP novo tem 2.431 XMLs S-1210, mas apenas 1.284 CPFs distintos. Portanto, nao se pode transformar cada XML em um alvo final. O sistema precisa escolher um unico S-1210 ativo/head por CPF.

O criterio observado no codigo atual e:

```sql
SELECT DISTINCT ON (ev.cpf)
          ev.id, ev.cpf, ev.nr_recibo, ev.id_evento,
          ev.xml_oid, ev.xml_bytes, ev.xml_entry_name,
          ev.zip_id, ev.dt_processamento
   FROM explorador_eventos ev
   JOIN empresa_zips_brutos z ON z.id = ev.zip_id
 WHERE z.empresa_id = <empresa>
    AND ev.tipo_evento = 'S-1210'
    AND ev.per_apur = <periodo>
    AND ev.retificado_por_id IS NULL
    AND ev.cpf IS NOT NULL
 ORDER BY ev.cpf ASC, ev.dt_processamento DESC NULLS LAST, ev.id DESC;
```

Em portugues simples:

1. Agrupa por CPF.
2. Ignora eventos ja marcados como retificados (`retificado_por_id IS NOT NULL`).
3. Dentro de cada CPF, pega primeiro o S-1210 com maior `dt_processamento`.
4. Se empatar ou faltar data, desempata pelo maior `id` do banco.

A informacao de data vem do proprio XML de retorno/importacao. O parser grava em `explorador_eventos.dt_processamento` a tag `<dhProcessamento>` ou `<dtProcessamento>` encontrada no XML. No ZIP novo, as amostras tem datas como `2026-01-08T16:58:32.377` e `2026-01-19T11:25:37.047`; pela regra atual, o evento de 19/01 vence o de 08/01 para o mesmo CPF.

Essa mesma regra aparece em duas partes importantes:

- Tela anual V2: conta o escopo via `DISTINCT ON (ev.cpf)` ordenado por `dt_processamento DESC, id DESC`.
- Envio V2 (`_carregar_eventos_alvo`): seleciona o XML original/head por CPF com o mesmo `DISTINCT ON`, antes de regenerar a retificacao.

Entao a tela e o envio nao deveriam usar os 2.431 XMLs como 2.431 pessoas. Eles devem usar 1.284 heads, um por CPF, escolhendo o ultimo processado.

### Validacao empirica dos duplicados no ZIP novo

No arquivo `01-01 ate 31-01  2026  objetiva.zip`, a distribuicao por CPF foi:

| Eventos S-1210 por CPF | Quantidade de CPFs |
| ---------------------: | -----------------: |
|                      1 |                149 |
|                      2 |              1.124 |
|                      3 |                 10 |
|                      4 |                  1 |

Ou seja, 1.135 CPFs tinham 2 ou mais S-1210 dentro do mesmo ZIP. Simulando a regra do sistema (`dt_processamento` desc, depois timestamp/id), o resultado foi exatamente 1.284 heads escolhidos.

Amostra real:

| CPF           | Evento escolhido pela regra                                                                  | Evento mais antigo ignorado                                                                  |
| ------------- | -------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------- |
| `06279703975` | `ID1108745230000002026011911253100004.S-1210.xml`, `dhProcessamento=2026-01-19T11:25:37.047` | `ID1108745230000002026010816582500001.S-1210.xml`, `dhProcessamento=2026-01-08T16:58:32.377` |
| `00097880183` | `ID1108745230000002026011911250900016.S-1210.xml`, `dhProcessamento=2026-01-19T11:25:20.91`  | `ID1108745230000002026010816465100001.S-1210.xml`, `dhProcessamento=2026-01-08T16:58:57.46`  |

Isto tambem explica o comportamento ja visto em producao para novembro: o banco tinha 3.855 linhas S-1210 de `2025-11`, mas a tela anual mostrou 1.284 CPFs no escopo, porque o overview deduplicou por CPF/head.

### Trava recomendada antes de importar dezembro

Antes de executar qualquer importacao/backfill de dezembro, deve existir um preflight que imprima:

- total bruto de S-1210 `per_apur=2025-12`;
- CPFs distintos;
- distribuicao de quantos S-1210 existem por CPF;
- linha escolhida como head por CPF (`dt_processamento DESC, id DESC`);
- CPFs em que o evento escolhido nao e o maior `dhProcessamento` esperado;
- contagem final esperada da tela anual.

Para o ZIP novo, a expectativa empirica e: bruto 2.431 S-1210, mas escopo/head final 1.284 CPFs.

## Inventario empirico da pasta local

Pasta analisada: `C:\Users\xandao\Downloads\mes a mes Objetiva zip`.

| ZIP                                   |   XMLs | S-1210 | CPFs S-1210 | `perApur` nos S-1210             | Meses de `dtPgto` nos S-1210     |
| ------------------------------------- | -----: | -----: | ----------: | -------------------------------- | -------------------------------- |
| `01-01 ate 31-01 objetiva.zip`        | 10.592 |  1.668 |         832 | `2024-12: 1668`                  | `2024-12: 4539`                  |
| `01-02 ate 28-02 objetiva.zip`        | 11.000 |  1.633 |         806 | `2025-01: 1633`                  | `2025-01: 1816`                  |
| `01-03 ate 31-03 objetiva.zip`        | 11.546 |  1.774 |         887 | `2025-02: 1774`                  | `2025-02: 1924`                  |
| `01-04 ate 30-04 objetiva.zip`        | 12.087 |  1.964 |         982 | `2025-03: 1964`                  | `2025-03: 2566`                  |
| `01-05 ate 31-05 objetiva.zip`        | 12.233 |  1.973 |         986 | `2025-04: 1972`, `2025-05: 1`    | `2025-04: 2162`, `2025-05: 2`    |
| `01-06 ate 30-06 objetiva.zip`        | 11.636 |  1.680 |         840 | `2025-05: 1680`                  | `2025-05: 1844`                  |
| `01-07 ate 31-07 objetiva.zip`        | 12.433 |  1.994 |         996 | `2025-06: 1994`                  | `2025-06: 2821`                  |
| `01-08 ate 31-08 objetiva.zip`        | 13.007 |  1.991 |         995 | `2025-07: 1990`, `2025-08: 1`    | `2025-07: 2370`, `2025-08: 2`    |
| `01-09 ate 30-09 objetiva.zip`        | 13.701 |  2.115 |       1.057 | `2025-08: 2114`, `2025-09: 1`    | `2025-08: 2338`, `2025-09: 1`    |
| `01-10 ate 31-10 objetiva.zip`        | 14.644 |  2.141 |       1.062 | `2025-09: 2135`, `2025-10: 6`    | `2025-09: 2726`, `2025-10: 8`    |
| `01-11 ate 30-11 objetiva.zip`        | 24.369 |  4.591 |       1.318 | `2025-10: 2458`, `2025-11: 2133` | `2025-10: 2928`, `2025-11: 2169` |
| `01-12 ate 31-12 objetiva.zip`        | 22.013 |  1.722 |       1.284 | `2025-11: 1722`                  | `2025-11: 2820`                  |
| `01-01 ate 31-01  2026  objetiva.zip` | 21.648 |  2.431 |       1.284 | `2025-12: 2431`                  | `2025-12: 5796`                  |

Leitura da tabela:

- Os ZIPs sao janelas de processamento/retorno, nao necessariamente a competencia S-1210 do mesmo nome do arquivo.
- O ZIP de janeiro/2025 contem S-1210 de `2024-12`.
- O ZIP de fevereiro/2025 contem S-1210 de `2025-01`.
- Esse deslocamento segue ate o fim do ano.
- O ZIP `01-12 ate 31-12 objetiva.zip` contem somente S-1210 de `2025-11`, por isso ele nao poderia povoar dezembro/2025.
- O ZIP novo de janeiro/2026 e o primeiro da pasta que contem S-1210 de `2025-12`.

## Detalhe do ZIP novo de 2026

Arquivo: `01-01 ate 31-01  2026  objetiva.zip`

- Tamanho local: 90,79 MB.
- SHA-256 parcial: `b76906444c35`.
- XMLs totais: 21.648.
- Principais tipos de evento:
  - S-5001: 3.617
  - S-5003: 3.617
  - S-5002: 3.566
  - S-1200: 3.259
  - S-1210: 2.431
  - S-2205: 2.071
  - S-3000: 1.137
  - S-2206: 1.086

S-1210 dentro dele:

- 2.431 XMLs S-1210.
- 1.284 CPFs distintos.
- `perApur=2025-12` em todos os 2.431 S-1210.
- `dtPgto` em `2025-12` com 5.796 ocorrencias.
- Datas `dtPgto` mais frequentes:
  - `2025-12-19`: 2.999
  - `2025-12-05`: 1.613
  - `2025-12-02`: 459
  - `2025-12-31`: 197
  - `2025-12-26`: 168
  - `2025-12-30`: 122
- `perRef` observado:
  - `2025`: 2.321
  - `2025-11`: 2.086
  - `2025-12`: 1.389
- `indRetif` observado:
  - `1`: 2.419
  - `2`: 12

Amostras do ZIP novo:

| XML                                               | CPF           | `perApur` | `dtPgto`                                 | `perRef`                     | `indRetif` |
| ------------------------------------------------- | ------------- | --------- | ---------------------------------------- | ---------------------------- | ---------- |
| `ID1108745230000002026010816582500001.S-1210.xml` | `06279703975` | `2025-12` | `2025-12-02`, `2025-12-19`               | `2025-11`, `2025`            | `1`        |
| `ID1108745230000002026010816582900001.S-1210.xml` | `06292104540` | `2025-12` | `2025-12-05`, `2025-12-19`               | `2025-11`, `2025`            | `1`        |
| `ID1108745230000002026010816583200001.S-1210.xml` | `06310313916` | `2025-12` | `2025-12-02`, `2025-12-19`               | `2025-11`, `2025`            | `1`        |
| `ID1108745230000002026010816584200001.S-1210.xml` | `06390418841` | `2025-12` | `2025-12-31`, `2025-12-19`               | `2025-12`, `2025`            | `1`        |
| `ID1108745230000002026010816465100001.S-1210.xml` | `00097880183` | `2025-12` | `2025-12-05`, `2025-12-19`, `2025-12-19` | `2025-11`, `2025-12`, `2025` | `1`        |

## Estado antes da execucao no banco/tela V2

Consulta read-only inicial na producao V2/schema `objetiva` mostrou:

- `empresa_zips_brutos` tem apenas 12 ZIPs importados para Objetiva.
- Ultimo ZIP importado: `01-12 ate 31-12 objetiva.zip`.
- Esse ultimo ZIP tem `perapur_dominante=2025-11`.
- O ZIP novo `01-01 ate 31-01  2026  objetiva.zip` nao aparece no banco.
- Nao existem S-1210 `per_apur=2025-12` em `explorador_eventos`.
- `timeline_mes` existe para `2025-01` ate `2025-11`.
- `timeline_mes` nao existe para `2025-12`.

Resumo atual dos S-1210 no banco:

| `per_apur` | Linhas S-1210 | CPFs distintos | ZIPs origem                    |
| ---------- | ------------: | -------------: | ------------------------------ |
| `2025-01`  |         1.633 |            806 | `01-02 ate 28-02 objetiva.zip` |
| `2025-02`  |         1.774 |            887 | `01-03 ate 31-03 objetiva.zip` |
| `2025-03`  |         1.964 |            982 | `01-04 ate 30-04 objetiva.zip` |
| `2025-04`  |         1.972 |            986 | `01-05 ate 31-05 objetiva.zip` |
| `2025-05`  |         1.681 |            840 | `01-05...` + `01-06...`        |
| `2025-06`  |         1.994 |            996 | `01-07 ate 31-07 objetiva.zip` |
| `2025-07`  |         1.990 |            995 | `01-08 ate 31-08 objetiva.zip` |
| `2025-08`  |         2.115 |          1.057 | `01-08...` + `01-09...`        |
| `2025-09`  |         2.136 |          1.059 | `01-09...` + `01-10...`        |
| `2025-10`  |         2.464 |          1.226 | `01-10...` + `01-11...`        |
| `2025-11`  |         3.855 |          1.284 | `01-11...` + `01-12...`        |
| `2025-12`  |             0 |              0 | nenhum                         |

Isso explicava exatamente a tela anual antes da execucao: dezembro aparecia como `sem_dados` porque, naquele momento, nao havia nem XML bruto S-1210 de `2025-12` nem `timeline_mes` de `2025-12`.

## Execucao realizada em 2026-05-26

Script criado/executado: `python-scripts/povoar_escopo_s1210_objetiva_dezembro.py`.

Guard-rails do script:

- travado para `empresa_id=3` / schema `objetiva`;
- travado para `per_apur=2025-12`;
- aborta se o ZIP local nao tiver exatamente 2.431 S-1210 alvo;
- aborta se o ZIP local nao tiver exatamente 1.284 CPFs alvo;
- aborta se existir S-1210 com `perApur` diferente de `2025-12`;
- aborta se algum S-1210 alvo nao tiver `dhProcessamento`/`dtProcessamento`;
- nao chama eSocial.

Dry-run antes da aplicacao:

- tenant: `schema=objetiva`, `search_path=objetiva, public`;
- ZIP: `01-01 ate 31-01  2026  objetiva.zip`;
- SHA-256: `b76906444c3579459e325168d8831537beec89864d435a40c1fd1a8baf74695b`;
- XMLs totais: 21.648;
- S-1210 alvo: 2.431;
- CPFs alvo/head: 1.284;
- S-1210 sem data de processamento: 0;
- estado inicial de dezembro no banco: 0 linhas, 0 CPFs, sem `timeline_mes`.

Aplicacao:

- `UPLOAD_DONE zip_id=13`;
- `EXTRACT_DONE zip_id=13 total=21648 ok=21648 dup=0 falhas=0 per_dom=2025-12`;
- `timeline_mes_id=13`;
- `timeline_envio_id=28`;
- `origem_set=2431`;
- `chains=0`.

Resultado final no banco:

| Indicador                        | Valor |
| -------------------------------- | ----: |
| Linhas S-1210 `per_apur=2025-12` | 2.431 |
| CPFs distintos                   | 1.284 |
| S-1210 com `origem_envio_id`     | 2.431 |
| ZIPs origem                      |     1 |
| Pagamentos `dtPgto=2025-12`      | 5.796 |
| `timeline_mes_id`                |    13 |
| `timeline_envio_id` sequencia 0  |    28 |

Resultado validado pela funcao real da tela anual `s1210_anual_overview(ano=2025, empresa_id=3)`:

| Campo dezembro/2025 |                   Valor |
| ------------------- | ----------------------: |
| Total               |                   1.284 |
| Sucesso             |                       0 |
| Erro                |                       0 |
| Enviando            |                       0 |
| Pendente            |                   1.284 |
| Estado              | `pronto_para_processar` |

Tambem apareceu fechamento aberto/nao fechado para dezembro:

- `fechado=false`;
- `nr_recibo_abertura=1.1.0000000037296318554`;
- `dt_abertura=2026-01-20T13:28:47.350000+00:00`.

## Auditoria da coincidencia 1.284 em novembro e dezembro

Depois da execucao, foi feita uma conferencia especifica porque novembro/2025 e dezembro/2025 ficaram ambos com 1.284 CPFs no overview anual. A primeira suspeita era erro de escopo ou reaproveitamento indevido do mes anterior.

Conclusao: o numero igual e uma coincidencia de saldo, nao reaproveitamento do mesmo conjunto.

Comparacao dos CPFs head/distintos:

| Comparacao                    | Valor |
| ----------------------------- | ----: |
| CPFs novembro/2025            | 1.284 |
| CPFs dezembro/2025            | 1.284 |
| CPFs presentes nos dois meses | 1.253 |
| CPFs somente em novembro      |    31 |
| CPFs somente em dezembro      |    31 |
| Conjuntos identicos?          |   Nao |

Amostras de CPFs que estavam em novembro e nao em dezembro:

- `03040816551`
- `03373646561`
- `03510718143`
- `03782427920`
- `06272022506`
- `06741535969`
- `08296009900`
- `08420283908`
- `08770193983`
- `09184159936`

Amostras de CPFs que entraram em dezembro e nao estavam em novembro:

- `00019754205`
- `00227657195`
- `00947203559`
- `01789677505`
- `02163300170`
- `04339832561`
- `08491889973`
- `11017749400`
- `12255381907`
- `13939996700`

Tambem foi conferido banco versus ZIP local:

| Periodo   | CPFs no banco | CPFs nos ZIPs locais | Diferença banco-local | Bate? |
| --------- | ------------: | -------------------: | --------------------: | ----- |
| `2025-11` |         1.284 |                1.284 |                     0 | Sim   |
| `2025-12` |         1.284 |                1.284 |                     0 | Sim   |

Fontes por periodo:

| Periodo   | ZIP origem                            | Linhas S-1210 |  CPFs |
| --------- | ------------------------------------- | ------------: | ----: |
| `2025-11` | `01-11 ate 30-11 objetiva.zip`        |         2.133 | 1.067 |
| `2025-11` | `01-12 ate 31-12 objetiva.zip`        |         1.722 | 1.284 |
| `2025-12` | `01-01 ate 31-01  2026  objetiva.zip` |         2.431 | 1.284 |

Datas de processamento tambem separam claramente as fontes:

- Novembro: `dt_processamento` entre `2025-11-11T10:16:49.910` e `2025-12-22T10:13:06.430`.
- Dezembro: `dt_processamento` entre `2026-01-08T16:45:29.097` e `2026-01-20T13:15:33.113`.

Portanto, dezembro nao foi preenchido copiando novembro. O que aconteceu foi: 31 CPFs sairam do conjunto de S-1210 e 31 CPFs entraram, mantendo o total final em 1.284.

## Por que o arquivo novo pode preencher dezembro

O arquivo novo pode preencher dezembro porque ele fecha o deslocamento natural dos ZIPs.

A sequencia real e:

- arquivo de fevereiro/2025 -> S-1210 `perApur=2025-01`
- arquivo de marco/2025 -> S-1210 `perApur=2025-02`
- ...
- arquivo de dezembro/2025 -> S-1210 `perApur=2025-11`
- arquivo de janeiro/2026 -> S-1210 `perApur=2025-12`

Ou seja: o arquivo antigo chamado dezembro nao era o mes de apuracao dezembro; ele era a janela em que retornaram XMLs do S-1210 de novembro. Para achar S-1210 de dezembro/2025, empiricamente era necessario olhar a janela de janeiro/2026.

O novo ZIP tem exatamente isso: eventos processados em janeiro/2026, mas com `<perApur>2025-12</perApur>` e pagamentos (`dtPgto`) em dezembro/2025.

## Plano tecnico executado para importar o escopo de dezembro

O caminho tecnico executado foi:

1. Cadastrar/uploadar o ZIP novo em `empresa_zips_brutos` da Objetiva.
2. Extrair os XMLs usando o mesmo parser ja usado nos 12 ZIPs anteriores.
3. Confirmar que os S-1210 extraidos gravaram `per_apur=2025-12` em `explorador_eventos`.
4. Criar/backfill `timeline_mes` para `empresa_id=3`, `per_apur=2025-12`.
5. Criar `timeline_envio` sequencia 0, tipo `zip_inicial`, para dezembro.
6. Preencher `origem_envio_id` dos S-1210 de `2025-12`.
7. Validar a tela anual antes de qualquer envio.

Resultado obtido do povoamento, antes de qualquer envio/correcao:

- `2025-12` deixou de ser `sem_dados`.
- O escopo final ficou em 1.284 CPFs distintos/head.
- A quantidade bruta de XMLs S-1210 importados ficou em 2.431.
- A tela conta CPFs/head, nao linhas brutas, entao o numero visual ficou em 1.284, nao 2.431.

## Cuidados importantes

- Nao usar o nome do ZIP nem `dt_ini/dt_fim` como competencia do S-1210. O periodo correto vem de `<perApur>`.
- Nao criar dezembro a partir de `01-12 ate 31-12 objetiva.zip`, porque esse ZIP so tem `perApur=2025-11`.
- Nao criar `2026-01` para esse novo ZIP no S-1210 anual de 2025; apesar do arquivo ser de janeiro/2026, os S-1210 dentro dele sao de `2025-12`.
- Filtrar por `e.per_apur='2025-12'` no backfill; varios ZIPs da pasta tem pequenas misturas de competencia.
- Manter a importacao restrita ao schema/empresa Objetiva (`empresa_id=3`, schema `objetiva`).
- A importacao/backfill do escopo ja foi feita em 2026-05-26, mas nenhum envio S-1210 foi executado.

## Conclusao final

Temos base empirica suficiente para afirmar que o ZIP novo de janeiro/2026 era a fonte que faltava para povoar o escopo S-1210 de dezembro/2025 da Objetiva.

O motivo de dezembro estar vazio antes da execucao nao era falta de logica na tela: era falta de importacao/backfill desse novo ZIP. Os 12 ZIPs originais importados terminavam, em termos de S-1210, em `perApur=2025-11`. O novo ZIP de 2026 trazia `perApur=2025-12` e `dtPgto=2025-12`; depois da importacao/backfill, a tela anual passou a exibir dezembro com 1.284 CPFs pendentes, pronto para processamento posterior.
