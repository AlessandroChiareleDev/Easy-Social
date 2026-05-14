# ESTUDO - CHAIN WALK, CICLO100 E AGOSTO/2025 SOLUCOES

> Arquivo de consulta continua para nao misturar APPA/v1 com SOLUCOES/V2.
> Regra absoluta: nao rodar envio, consulta ou download eSocial sem autorizacao explicita.

## 1. O que eu confirmei ate agora

Este estudo foi feito lendo docs e codigo existentes. Nao houve envio ao eSocial, nao houve consulta de protocolo, nao houve download cirurgico.

Fontes principais lidas:

- `Solucoes Dia 2/ciclo100.md`
- `Solucoes Dia 1/RELATORIO_AGOSTO_2025_SOLUCOES.md`
- `Solucoes Dia 2/BIBLIA_V2_NORTE.md`
- `Solucoes Dia 2/ARQUITETURA_MULTI_EMPRESA.md`
- `python-scripts/relatorio_solucoes_agosto_v2.py`
- `python-scripts/relatorio_solucoes_agosto_v2_limpo.py`
- Codigo V2 no repo irmao `Easy-eSocial-v2`:
  - `backend/app/envio_paralelo_v2.py`
  - `backend/app/envio_teste_100.py`
  - `backend/app/timeline.py`
  - `backend/app/backfill_chain.py`
  - `backend/app/xml_s1210.py`
  - `src/components/explorador/timeline/ChainWalkPanel.vue`
  - `src/components/explorador/timeline/TimelineRegua.vue`
  - `src/components/explorador/timeline/DrawerCadeiaCpf.vue`
  - `src/services/exploradorApi.ts`
  - `backend/migrations/_legacy/003_chain_walk.sql`
  - `backend/migrations/_legacy/004_xml_por_evento.sql`

Arquivo que NAO deve ser usado como referencia para SOLUCOES/agosto:

- `python-scripts/envio_lote2_agosto.py`: isso e APPA/v1, nao e o fluxo SOLUCOES/V2 que estamos estudando.

## 1.1. Fonte correta dos XMLs/ZIPs SOLUCOES

Fonte local canonica para os XMLs/ZIPs da SOLUCOES em 2025:

```text
C:\Users\xandao\Downloads\todos os meses 2025 SOLUCOES\
```

Para setembro/2025, a fonte correta sao os dois ZIPs quinzenais:

```text
C:\Users\xandao\Downloads\todos os meses 2025 SOLUCOES\SOLUCOES_2025-09(01-15).zip
C:\Users\xandao\Downloads\todos os meses 2025 SOLUCOES\SOLUCOES_2025-09(16-30).zip
```

Contagem local feita dentro dos ZIPs:

- `SOLUCOES_2025-09(01-15).zip`: 80.817 entradas, 15.517 S-1210.
- `SOLUCOES_2025-09(16-30).zip`: 117.338 entradas, 15.501 S-1210.

Esses ZIPs explicam por que setembro deve ficar perto de 15 mil CPFs distintos, coerente com o frontend/anual e com agosto. Qualquer leitura que diga algo como 7 mil CPFs para setembro inteiro deve ser tratada como parcial/incompleta ate reconciliar com esses dois ZIPs.

Fontes que NAO devem ser usadas para SOLUCOES setembro:

- `C:\Users\xandao\Downloads\xmls do e social mes a mes\09-set2025.zip`: fonte APPA/legacy, nao SOLUCOES.
- `python-scripts/esocial/s1210_missao_routes.py` como mapa final de SOLUCOES: contem mapeamento antigo/legacy e pode apontar para APPA.
- Scripts `envio_lote2_*` e `ingest_lote2_*`: contexto APPA/v1 ou historico, nao fluxo SOLUCOES/V2.

## 2. Modelo mental correto

Existem tres camadas diferentes. Elas nao podem ser misturadas:

1. Escopo/importacao ZIP
   - Vem de `explorador_eventos` e dos ZIPs brutos.
   - Define quais CPFs existem no mes.
   - Nao significa sucesso de envio.
   - Para meses que acabamos de importar por ZIP, o correto e aparecer como `pendente`, nao `ok`.

2. Tentativas reais de envio
   - Vivem em `timeline_envio` e `timeline_envio_item`.
   - Uma linha em `timeline_envio` representa uma execucao operacional.
   - Uma linha em `timeline_envio_item` representa um CPF dentro daquela execucao.
   - OK real vem de `timeline_envio_item.status = 'sucesso'`.

3. Cadeia de versoes/XML por CPF
   - Essa e a parte do Chain Walk.
   - O CPF tem XML original do ZIP, XML enviado, XML retorno, recibo anterior, recibo novo e historico de tentativas.
   - O frontend mostra essa caminhada como `v0`, `v1`, `v2`, etc.

Resumo curto: ZIP cria universo; timeline registra tentativa; Chain Walk explica a historia por CPF/XML.

## 3. O que e CICLO100

CICLO100 e a tecnica documentada para envio massivo S-1210 da SOLUCOES em producao, em levas pequenas e auditaveis.

Parametros principais do fluxo validado em agosto/2025:

- 100 CPFs por execucao.
- `workers=5`.
- `batch=50`.
- `--pular-ja-tentados` para idempotencia.
- Rodadas grandes de 20 execucoes, ou seja, 2.000 CPFs por bloco de trabalho.
- Regra de parada: se uma rodada de 100 passar de 20% de erro, parar e investigar.

Comando canonico documentado em `ciclo100.md`:

```powershell
python -m app.envio_paralelo_v2 --empresa-id 1 --per-apur 2025-08 --limite 100 --cert "C:\caminho\certificado.pfx" --senha "***" --cnpj 09445502000109 --ambiente producao --pular-ja-tentados --workers 5 --batch 50 --progress-every 50
```

Importante: este comando e referencia historica. Nao deve ser rodado sem autorizacao explicita.

## 4. Como agosto/2025 foi feito

Agosto e diferente dos meses recem-importados por ZIP porque agosto tem envios reais registrados na timeline.

O documento `ciclo100.md` registra que o CICLO100 foi validado em SOLUCOES/agosto:

- Total processado no ciclo documentado: 13.646 CPFs.
- Erros finais: 381.
- Taxa de erro: 2,79%.
- Depois do fix de ID: zero `543` e zero `1089` no ciclo final documentado.
- Histograma final documentado: muitos `401` e `202`, sem colisoes de ID.

O relatorio `RELATORIO_AGOSTO_2025_SOLUCOES.md` mostra a historia anterior e os aprendizados:

- Houve envios reais com XML retorno guardado.
- `1089` foi tratado como problema de concorrencia/ID, nao como recibo queimado.
- O fix importante foi `_gerar_id` atomico/global em `xml_s1210.py`.
- `459` foi associado a recibo ativo errado/desatualizado em alguns casos.
- As tentativas guardam `xml_enviado_oid` e `xml_retorno_oid`, permitindo auditoria posterior.

## 5. Como o codigo seleciona os CPFs

No V2, `envio_paralelo_v2.py` reaproveita funcoes de `envio_teste_100.py`.

A selecao vem de `_carregar_eventos_alvo`:

- Busca `explorador_eventos` para `tipo_evento='S-1210'` e `per_apur` alvo.
- Exige XML completo (`xml_oid IS NOT NULL`).
- Usa HEAD do evento: `retificado_por_id IS NULL`.
- Usa `DISTINCT ON (cpf)` para escolher uma linha por CPF.
- Com `--pular-ja-tentados`, remove CPFs ja presentes em `timeline_envio_item` naquele mes.

Isso significa que o ciclo nao pega “qualquer XML”; ele pega o XML HEAD por CPF dentro daquele periodo.

## 6. O que acontece dentro de uma rodada

Fluxo resumido do `envio_paralelo_v2.py`:

1. Carrega ate 100 CPFs alvo.
2. Cria um `timeline_envio` para a execucao.
3. Cria um `timeline_envio_item` por CPF com status inicial `pendente`.
4. Divide a rodada em batches de 50.
5. Para cada CPF:
   - Le o XML antigo do Large Object (`explorador_eventos.xml_oid`).
   - Extrai dados do S-1210.
   - Resolve o recibo ativo (`nr_recibo` do evento ou recibo extraido do XML).
   - Gera XML novo de retificacao com `indRetif='2'` e `nrRecibo` anterior.
   - Assina o XML.
   - Grava o XML assinado em `timeline_envio_item.xml_enviado_oid`.
   - Envia lote ao eSocial.
   - Faz polling do lote pelo protocolo.
   - Grava XML retorno em `timeline_envio_item.xml_retorno_oid`.
   - Atualiza status, codigo, mensagem e recibo novo.

Status importantes:

- `sucesso`: envio aceito, recibo novo salvo quando retornado.
- `erro_esocial`: eSocial rejeitou/advertiu conforme codigo.
- `pendente_consulta`: envio sem retorno conclusivo no polling.
- `falha_rede`: problema local/rede.
- `erro_preparo`: falha antes de enviar, por exemplo erro de XML/dados.

## 7. O que sao v0, v1, v2, v3, v4

No frontend Chain Walk, as bolinhas sao baseadas em `timeline_envio.sequencia`.

- `v0`: estado inicial vindo do ZIP, tipo `zip_inicial`.
- `v1`, `v2`, `v3`...: execucoes reais posteriores em `timeline_envio`.
- Cada bolinha pode representar uma rodada de envio e seus CPFs.
- O HEAD visual do mes e `timeline_mes.head_envio_id`.

No drawer por CPF, o frontend separa duas coisas:

1. Versoes na base
   - Vem de `explorador_eventos`.
   - Mostra recibo, referencia, HEAD ou retificada.

2. Tentativas registradas
   - Vem de `timeline_envio_item`.
   - Mostra status, recibo anterior, recibo novo, erro, XML enviado e XML retorno.

Entao Chain Walk nao e apenas uma interface bonita. Ele e a auditoria da caminhada do CPF: de qual XML partiu, qual XML foi enviado, qual retorno voltou e qual recibo passou a existir.

## 8. Onde cada informacao mora

Tabela `explorador_eventos`:

- Guarda XML original importado do ZIP em `xml_oid`.
- Guarda CPF, periodo, tipo do evento, recibo original, data de processamento.
- `retificado_por_id IS NULL` marca a versao HEAD daquele evento/CPF.
- `origem_envio_id` liga eventos importados a uma entrada inicial de timeline quando o backfill cria `v0`.

Tabela `timeline_mes`:

- Uma linha por mes operacional.
- Guarda `head_envio_id`, que aponta para a bolinha atual da regua mensal.

Tabela `timeline_envio`:

- Uma linha por execucao.
- `sequencia` vira `v0`, `v1`, `v2` no frontend.
- `tipo='zip_inicial'` para a origem; `tipo='envio_massa'` para CICLO100.

Tabela `timeline_envio_item`:

- Uma linha por CPF dentro da execucao.
- Guarda `versao_anterior_id`, `versao_nova_id`, recibo anterior, recibo novo, status, erro, XML enviado e XML retorno.

## 9. O ponto fino: `versao_nova_id` vs tentativa real

A busca focada por `versao_nova_id`, `retificado_por_id`, `origem_envio_id` e `xml_retorno_oid` no V2 confirmou uma diferenca importante.

O que esta claro:

- `backfill_chain.py` atualiza `explorador_eventos.retificado_por_id` para ligar versoes que ja existem na base, principalmente quando o ZIP/backfill encontra recibos relacionados.
- `timeline.py` usa `retificado_por_id IS NULL` para montar HEAD e cadeia por CPF.
- As migrations criam indice de HEAD S-1210 em `explorador_eventos(cpf, per_apur)` filtrando `retificado_por_id IS NULL`.
- O fluxo de envio em `envio_paralelo_v2.py`/`envio_teste_100.py` grava tentativa real em `timeline_envio_item`: status, recibo anterior, recibo novo, `xml_enviado_oid` e `xml_retorno_oid`.
- `reprocessar_envio.py` tambem atualiza `timeline_envio_item` ao consultar protocolos salvos: marca `sucesso`/`erro_esocial`, grava `nr_recibo_novo` e `xml_retorno_oid`.

O que NAO apareceu no caminho de envio lido:

- Insercao explicita de uma nova linha em `explorador_eventos` depois de sucesso.
- Atualizacao clara de `timeline_envio_item.versao_nova_id` depois de sucesso.
- Atualizacao de `explorador_eventos.retificado_por_id` no momento do envio real.

Conclusao provisoria, mas agora mais forte: no fluxo V2 atual estudado, o envio bem-sucedido fica comprovado pela tentativa (`timeline_envio_item`) e pelos XMLs enviados/retornados, enquanto a cadeia de `explorador_eventos` e ligada principalmente pelo backfill/importacao de eventos ja existentes. Se quisermos que cada sucesso crie uma nova versao formal em `explorador_eventos`, isso precisa ser confirmado em outro modulo ainda nao lido ou tratado como melhoria/pendencia arquitetural.

## 10. Como os relatorios de agosto consolidam o estado

Os scripts de relatorio nao tratam ZIP como OK.

`relatorio_solucoes_agosto_v2_limpo.py` faz a leitura correta:

1. Busca universo por CPF em `explorador_eventos`, usando somente HEAD:
   - `tipo_evento='S-1210'`
   - `per_apur='2025-08'`
   - `retificado_por_id IS NULL`
   - `DISTINCT ON (cpf)`

2. Busca ultimo item de envio por CPF em `timeline_envio_item`:
   - join com `timeline_envio` e `timeline_mes`
   - `DISTINCT ON (it.cpf)`
   - ordena por `criado_em DESC, id DESC`

3. Classifica:
   - `sucesso` -> `ENVIADO_OK`
   - `erro_esocial` com codigo `202` -> `ENVIADO_COM_ADVERTENCIA`
   - `erro_esocial` -> `ERRO_NAO_ENVIADO`
   - `pendente` ou `pendente_consulta` -> `PENDENTE`
   - sem item na timeline -> `PENDENTE`

Esta regra e a mesma ideia que precisa guiar a visao anual: CPF no ZIP sem envio real nao e OK.

## 11. Regras para replicar em outros meses

Antes de qualquer envio:

1. Confirmar que o mes esta populado por ZIP e aparece como pendente.
2. Confirmar que o universo vem de HEAD em `explorador_eventos`.
3. Confirmar certificado, CNPJ e ambiente de SOLUCOES.
4. Confirmar que nao estamos usando script APPA/v1.
5. Confirmar se vamos usar `--pular-ja-tentados`.
6. Fazer uma rodada pequena e auditar `timeline_envio` e `timeline_envio_item`.
7. Aplicar a regra de parada de 20%.

Nada disso deve ser executado sem autorizacao explicita.

## 12. Proximas leituras necessarias

Para fechar o entendimento antes de qualquer plano operacional:

- Buscar no V2 todos os usos de `versao_nova_id`.
- Buscar onde `retificado_por_id` e atualizado depois de um envio bem-sucedido.
- Ler `backend/app/esocial_client.py` para entender exatamente o shape do retorno parseado.
- Ler scripts antigos de reenvio citados no relatorio de agosto apenas como arqueologia, separando claramente V2/SOLUCOES de APPA/v1.
- Conferir se a constraint real de `timeline_envio_item.status` no banco ja aceita `pendente_consulta` e `erro_preparo`.

## 13. Frase de seguranca para esta missao

Quando o assunto for SOLUCOES/agosto/CICLO100, eu tenho que lembrar:

> Agosto nao e so um mes com ZIP. Agosto tem timeline real de envio. Os outros meses importados agora sao escopo pendente. Chain Walk e a cadeia CPF/XML/tentativas/retornos; OK so nasce de `timeline_envio_item.status='sucesso'`, nao de `explorador_eventos` sozinho.
