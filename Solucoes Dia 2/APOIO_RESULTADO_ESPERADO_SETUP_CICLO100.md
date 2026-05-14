# APOIO - RESULTADO ESPERADO E SETUP INICIAL CICLO100

> Segundo MD de apoio para consulta antes de qualquer envio S-1210 da SOLUCOES.
> Complementa `ESTUDO_CHAINWALK_CICLO100_AGOSTO.md` e `ciclo100.md`.

## 1. Regra principal de trabalho

Eu nao rodo CICLO100 aberto, sem alvo definido.

O usuario sempre da um target operacional, por exemplo:

- "fazer os primeiros 100 de setembro"
- "fazer mais 1000"
- "fazer mais 2000"

Eu executo somente ate o target combinado. Se o target for 1000, isso significa 10 rodadas de 100. Se for 2000, isso significa 20 rodadas de 100, uma leva grande completa. Depois eu paro, resumo o resultado e espero novo alvo.

O `ciclo100.md` ja cita a logica de levas de 100 e levas grandes de 20 rodadas (= 2.000 CPFs), alem de repetir ate zerar pendentes. Esta regra nova deixa explicito o controle humano: o target vem do usuario, nao da minha iniciativa.

## 2. Ordem correta para um mes novo

Mesmo que o CICLO100 rode 100 por vez, para mes novo eu devo pensar em degraus:

1. Teste de 1 CPF, se o usuario pedir validacao minima.
2. Teste de 10 CPFs, se for preciso confirmar estabilidade curta.
3. Rodada de 100 CPFs, que e o CICLO100 real.
4. Rodadas adicionais de 100 ate bater o target autorizado.

Para setembro/2025, se o usuario disser "pega os primeiros 100", o padrao esperado e rodar uma unica execucao com `--per-apur 2025-09 --limite 100 --pular-ja-tentados`, acompanhar o resumo, auditar a timeline e parar.

## 3. Setup inicial antes de rodar qualquer coisa

Antes de aceitar uma rodada real, eu preciso confirmar:

- Estou no backend V2: `C:\Users\xandao\Documents\GitHub\Easy-eSocial-v2\backend`.
- Ambiente Python correto esta ativo: venv de `Easy-Social\.venv`.
- Mes alvo esta populado por ZIP e aparece como escopo pendente.
- `explorador_eventos` tem S-1210 HEAD para a `per_apur` alvo.
- A selecao usa `retificado_por_id IS NULL` e `xml_oid IS NOT NULL`.
- O comando usa certificado/CNPJ da SOLUCOES.
- O comando usa `--pular-ja-tentados`.
- O limite continua `100`, salvo teste menor explicitamente pedido.
- Nao estou usando script APPA/v1.
- Nao estou fazendo download cirurgico ou consulta de identificadores.

## 4. Comando-base mental

O comando real vem de `ciclo100.md`; a forma mental e:

```powershell
cd 'C:\Users\xandao\Documents\GitHub\Easy-eSocial-v2\backend'
python -m app.envio_paralelo_v2 `
  --per-apur 2025-09 `
  --limite 100 `
  --workers 5 `
  --batch 50 `
  --progress-every 50 `
  --cert '<PFX_SOLUCOES>' `
  --senha '<SENHA_PFX>' `
  --cnpj '09445502000109' `
  --ambiente producao `
  --pular-ja-tentados `
  2>&1 | Tee-Object -FilePath '_envio_setembro_loteNN.log'
```

Nunca rodar este comando por conta propria. Precisa de autorizacao explicita do usuario para envio real.

## 5. Resultado esperado no Chain Walk

Ao rodar 100 CPFs de setembro:

- Uma nova linha nasce em `timeline_envio` para aquela execucao.
- Essa execucao vira uma nova bolinha/versao operacional no Chain Walk: `v1`, `v2`, etc., conforme a sequencia do mes.
- Cem linhas nascem em `timeline_envio_item`, uma por CPF.
- Cada CPF tentado passa a ter uma tentativa registrada no drawer.
- O XML original segue em `explorador_eventos.xml_oid`.
- O XML novo assinado que foi tentado fica em `timeline_envio_item.xml_enviado_oid`.
- O XML de retorno do eSocial, quando existir, fica em `timeline_envio_item.xml_retorno_oid`.
- O recibo anterior fica em `nr_recibo_anterior`.
- O recibo novo, se aceito, fica em `nr_recibo_novo`.

O Chain Walk deve permitir baixar:

- XML antigo/original pela versao/base do evento.
- XML enviado pela tentativa.
- XML retorno pela tentativa, quando o eSocial devolveu retorno.

## 6. Resultado esperado no S-1210 anual

O S-1210 anual nao deve virar OK em massa so porque o ZIP existe.

Depois de uma rodada de 100:

- CPFs aceitos mudam para `ok`.
- CPFs rejeitados mudam para `erro`.
- CPFs sem retorno conclusivo ficam `pendente` ou `pendente_consulta`.
- CPFs do escopo que nao foram tentados continuam `pendente`.

Exemplo: se setembro tem 19.000 CPFs pendentes e a rodada de 100 retorna 92 sucessos, 6 erros e 2 pendentes de consulta, o anual deve mostrar apenas esses 100 alterados; os outros 18.900 continuam pendentes.

## 7. O que significa sucesso de verdade

Sucesso operacional vem de `timeline_envio_item.status = 'sucesso'`.

O ZIP/importacao nao e sucesso. `explorador_eventos` sozinho define universo e XML original, mas nao prova envio novo.

O fluxo V2 lido ate agora comprova o envio aceito por:

- status da tentativa;
- recibo novo;
- XML enviado salvo;
- XML retorno salvo quando retornado;
- totalizadores de `timeline_envio`;
- visualizacao no Chain Walk e no anual.

Ponto fino ainda registrado: no caminho principal estudado, nao apareceu criacao automatica clara de uma nova linha formal em `explorador_eventos` apos cada sucesso. Entao eu nao devo prometer isso sem confirmar antes. O que esta amarrado com certeza e a tentativa + XML enviado + XML retorno + recibo novo em `timeline_envio_item`.

## 8. Como eu devo operar targets maiores

Se o usuario disser "faz mais 1000":

1. Calculo 10 rodadas de 100.
2. Rodo a primeira rodada.
3. Leio o resumo.
4. Se erro >20%, paro.
5. Se aparecer 543 ou 1089, paro.
6. Se o comando falhar, paro.
7. Se tudo estiver dentro do esperado, sigo para a proxima rodada.
8. Ao completar 10 rodadas, paro mesmo que ainda existam pendentes.

Se o usuario disser "faz mais 2000":

- Isso equivale a 20 rodadas de 100, exatamente uma leva grande do `ciclo100.md`.

Se o usuario disser "faz tudo que falta":

- Eu ainda devo transformar em blocos controlados e confirmar o alvo pratico, porque a regra desta missao e operar por target humano.

## 9. Linha de resumo apos cada rodada

Depois de cada rodada de 100, eu devo reportar curto:

```text
Rodada N/TARGET (envio M): sucesso=X, erro=Y, pendente_consulta=Z, taxa_erro=K%.
```

Se estiver no formato do `ciclo100.md`, usar:

```text
N/20 (envio M): X ok / Y erro (K%). Segue.
```

Sem texto longo entre rodadas, a menos que haja erro, taxa alta, 543/1089, pendente_consulta relevante ou outro sinal estranho.

## 10. Criterios de parada

Parar imediatamente se acontecer qualquer um destes:

- Taxa de erro da rodada >20%.
- Erro 543.
- Erro 1089.
- Falha de certificado/assinatura.
- Falha de banco ou Large Object.
- `selecionados 0 eventos` quando ainda esperamos pendentes.
- Muitos `pendente_consulta`.
- Divergencia entre total tentado e total de itens gravados.
- Usuario mandar parar.

## 11. Primeiros 100 de setembro - estado esperado

Quando o usuario autorizar os primeiros 100 de setembro, o que eu devo fazer:

1. Conferir contagem de pendentes de `2025-09` sem consultar eSocial.
2. Conferir que ha XML HEAD em `explorador_eventos`.
3. Rodar uma unica execucao com `--limite 100`.
4. Salvar log com nome unico.
5. Ler o resumo final.
6. Auditar `timeline_envio` e `timeline_envio_item`.
7. Conferir impacto no anual: so 100 CPFs devem mudar de estado.
8. Parar e reportar resultado.

## 12. Frase de controle

Eu estou pronto para executar apenas quando a autorizacao vier assim, de forma clara:

> "Pode rodar os primeiros 100 de setembro."

Antes disso, eu posso preparar, contar, validar e explicar, mas nao envio nada.

## 13. Preflight real - 2026-05-12 - setembro/2025

Autorizacao recebida para comecar em degraus, com feedback continuo: 1, depois 10, depois 100.

Preflight local inicial executado antes de qualquer envio eSocial:

- Base: `easy_social_solucoes` local.
- `per_apur`: `2025-09`.
- `total_head` S-1210: 0.
- `ja_tentados`: 0.
- `pendentes`: 0.
- Eventos existentes em setembro:
  - `S-5001`: 312 eventos, 302 CPFs, 312 com XML.
  - `S-5003`: 311 eventos, 301 CPFs, 311 com XML.

Correcao importante deste diagnostico: a conclusao "nao existem ZIP/XML locais de SOLUCOES setembro" estava errada. Ela veio de procurar nas pastas APPA/legacy e nao na pasta correta da SOLUCOES.

## 14. Fonte correta SOLUCOES - setembro/2025

Pasta local correta dos XMLs/ZIPs SOLUCOES:

```text
C:\Users\xandao\Downloads\todos os meses 2025 SOLUCOES\
```

ZIPs corretos de setembro:

```text
C:\Users\xandao\Downloads\todos os meses 2025 SOLUCOES\SOLUCOES_2025-09(01-15).zip
C:\Users\xandao\Downloads\todos os meses 2025 SOLUCOES\SOLUCOES_2025-09(16-30).zip
```

Validacao local feita dentro dos ZIPs:

- `SOLUCOES_2025-09(01-15).zip`: 80.817 entradas, 15.517 S-1210.
- `SOLUCOES_2025-09(16-30).zip`: 117.338 entradas, 15.501 S-1210.

Esses numeros sao coerentes com o frontend/anual mostrando aproximadamente 15 mil CPFs pendentes em setembro. Setembro nao deve ser tratado como mes de 7 mil CPFs.

Fontes erradas que nao devo usar para SOLUCOES setembro:

- `C:\Users\xandao\Downloads\xmls do e social mes a mes\09-set2025.zip`: APPA/legacy.
- `python-scripts/esocial/s1210_missao_routes.py` como fonte final: mapa antigo, pode apontar para APPA.
- `envio_lote2_setembro.py`, `ingest_lote2_setembro.py` e scripts `lote2`: APPA/v1 ou historico, nao SOLUCOES/V2.

## 15. Explicacao do numero errado `7771 CPFs`

Consulta feita depois encontrou em `explorador_eventos`:

- `15.542` eventos S-1210 de `2025-09`.
- `7.771` CPFs distintos.
- `zip_id = NULL`.
- `xml_oid = 0` eventos preenchidos.

Essa leitura NAO representa o universo real de setembro. Ela representa uma base parcial/incompleta ou importacao quebrada: os eventos existem sem vinculo com `empresa_zips_brutos` e sem XML elegivel para o motor CICLO100.

Conclusao correta:

- O numero `7771` nao deve ser usado como total de setembro.
- A referencia fisica correta sao os dois ZIPs quinzenais SOLUCOES.
- O frontend/anual perto de 15 mil CPFs esta coerente com agosto e com os ZIPs.
- Antes de enviar, preciso alinhar a base usada pelo motor com esses dois ZIPs corretos.

## 16. Impedimento tecnico antes do envio

O motor `envio_paralelo_v2.py` seleciona eventos via `_carregar_eventos_alvo` em `envio_teste_100.py`.

Essa selecao exige:

- `explorador_eventos.tipo_evento = 'S-1210'`.
- `explorador_eventos.per_apur = '2025-09'`.
- `explorador_eventos.retificado_por_id IS NULL`.
- `explorador_eventos.xml_oid IS NOT NULL`.
- `JOIN empresa_zips_brutos z ON z.id = explorador_eventos.zip_id`.
- `z.empresa_id` correspondente a SOLUCOES.
- `--pular-ja-tentados` para excluir CPFs ja tentados.

O estado encontrado (`zip_id = NULL`, sem `xml_oid`) nao e elegivel. Se eu rodar o CICLO100 assim, ele tende a selecionar 0 ou selecionar fonte errada.

Tambem existe uma incompatibilidade a validar: a extracao mais nova do Explorador grava `xml_bytes`, mas o motor lido espera `xml_oid`. Antes de qualquer envio, uma destas coisas precisa estar verdadeira:

- os S-1210 de setembro foram importados com `xml_oid` preenchido; ou
- o motor foi confirmado/adaptado para ler `xml_bytes`; ou
- houve backfill seguro de `xml_oid` a partir dos ZIPs corretos.

## 17. Preparacao correta antes de receber target de envio setembro

1. Usar somente os dois ZIPs SOLUCOES de `C:\Users\xandao\Downloads\todos os meses 2025 SOLUCOES\`.
2. Registrar/importar esses ZIPs na base/tenant que o backend e o frontend realmente usam.
3. Garantir `zip_id` e XML elegivel (`xml_oid` ou leitura validada de `xml_bytes`) para os S-1210 HEAD de setembro.
4. Recontar CPFs diretamente depois da importacao/reconciliacao.
5. Validar que o anual mostra os CPFs de setembro como `pendente`, nao `ok`.
6. So entao iniciar o degrau 1 -> 10 -> 100.

## 18. Correcao aplicada no V2 antes do envio real

Problema real encontrado:

- O frontend/anual estava certo: no tenant `solucoes`, setembro tem 15.917 CPFs S-1210.
- A consulta anterior que falou em `7771 CPFs` veio de base/conexao errada ou incompleta e nao deve ser usada.
- No schema `solucoes`, as tabelas guardam `empresa_id=1` internamente, embora a API/operacao receba SOLUCOES como `empresa_id=2`.
- O Explorador V2 novo guarda XML original em `explorador_eventos.xml_bytes`.
- O motor CICLO100 antigo aceitava apenas `xml_oid`, por isso nao enxergava os XMLs novos.

Correcoes aplicadas em `Easy-eSocial-v2`:

- `envio_teste_100.py`: selecao agora aceita `xml_oid` ou `xml_bytes`.
- `envio_teste_100.py`: leitura do XML original agora usa `xml_bytes` quando existir e cai para `xml_oid` se for legado.
- `envio_teste_100.py`: filtros de `empresa_id` nas tabelas usam `tenant.internal_empresa_id(empresa_id)`.
- `envio_paralelo_v2.py`: conexoes do envio passam `empresa_id=2`, garantindo schema `solucoes`, e os workers tambem usam o tenant correto.
- `explorador.py`: reextracao por `ON CONFLICT` passa a preencher campos ausentes (`zip_id`, `xml_entry_name`, `xml_bytes`, `xml_size_bytes`, `xml_sha256`) sem sobrescrever valores ja existentes.

Validacao sem envio:

- `limite=1`: selecionou 1 CPF.
- `limite=10`: selecionou 10 CPFs.
- `limite=100`: selecionou 100 CPFs.
- Primeiro XML lido via `xml_bytes`: CPF `00001931946`, `per_apur=2025-09`, recibo anterior `1.1.0000000035309810028`.

## 19. Primeiro envio real de setembro - 1 CPF

Execucao real feita em producao, SOLUCOES, `per_apur=2025-09`, `limite=1`, `workers=1`, `batch=1`, `--pular-ja-tentados`.

Resultado:

- `envio_id`: 175.
- CPF: `00001931946`.
- Status: `erro_esocial`.
- Codigo: `401`.
- Mensagem: `Conteudo do evento inválido`.
- Ocorrencia principal: `620 - A folha de pagamento do período 2025-09 já foi fechada, para alterá-la será necessário reabri-la.`
- Recibo anterior usado: `1.1.0000000035309810028`.
- XML enviado salvo em `timeline_envio_item.xml_enviado_oid`.
- XML retorno salvo em `timeline_envio_item.xml_retorno_oid`.

Conclusao operacional:

- A correcao tecnica do V2 funcionou: selecionou, leu XML, assinou, enviou, recebeu protocolo e retorno.
- O bloqueio atual nao e mais base/ZIP/motor; e regra de negocio do eSocial: folha 2025-09 fechada.
- Nao rodar 10 nem 100 enquanto a folha 2025-09 nao for reaberta ou enquanto nao houver decisao explicita sobre tratar erro 620/401.

## 20. Reabertura S-1298 de setembro - 2026-05-13

Autorizacao recebida para reabrir a folha de `2025-09` da SOLUCOES.

Execucao real feita em producao, SOLUCOES, evento `S-1298`, `per_apur=2025-09`, grupo `3`.

Resultado eSocial:

- Evento: `S-1298` / reabertura de eventos periodicos.
- Id evento: `ID1094455020000002026051303032000001`.
- Protocolo: `1.1.202605.0000000013150878121`.
- Codigo lote: `201`.
- Codigo evento: `201`.
- Descricao: `Sucesso.`
- Recibo de reabertura: `1.1.0000000040747878940`.

Persistencia local V2:

- Gravado em `explorador_eventos` com id `3000506`.
- `tipo_evento='S-1298'`, `per_apur='2025-09'`, `cd_resposta='201'`.
- Cache `s1299_fechamento_status` atualizado como `fechado=false`, origem `s1298_envio`.

Validacao do anual V2:

- `2025-09` agora retorna `fechado=false`.
- `nr_recibo_abertura='1.1.0000000040747878940'`.
- `dt_abertura='2026-05-13T03:03:30.310744+00:00'`.
- `fechamento_origem='s1298_envio'`.

Com isso, a folha de setembro esta reaberta para retomar o degrau 10/100 somente quando o usuario autorizar explicitamente.

## 21. Primeiros 100 S-1210 de setembro - 2026-05-13

Autorizacao recebida para retomar o CICLO100 de setembro/2025 da SOLUCOES com trava operacional:

- Enviar os primeiros 100 em blocos de 10.
- Dar feedback a cada 10 CPFs.
- Parar se a taxa de erro de qualquer bloco fosse maior que 20%.

Antes do envio foi corrigido o seletor `--pular-ja-tentados` para nao excluir o CPF do erro antigo `401/620` que ocorreu antes da reabertura S-1298. Esse CPF voltou a ser elegivel como pendente.

Execucao real em producao, SOLUCOES, `per_apur=2025-09`, `empresa_id=2`, blocos de 10, `workers=1`, `batch=10`, com `--pular-ja-tentados`:

| Bloco | envio_id |  OK | Erro | Pendente consulta | Velocidade aprox. |
| ----: | -------: | --: | ---: | ----------------: | ----------------: |
|     1 |      176 |  10 |    0 |                 0 |        75 CPF/min |
|     2 |      177 |  10 |    0 |                 0 |        81 CPF/min |
|     3 |      178 |  10 |    0 |                 0 |        78 CPF/min |
|     4 |      179 |  10 |    0 |                 0 |        55 CPF/min |
|     5 |      180 |  10 |    0 |                 0 |        80 CPF/min |
|     6 |      181 |  10 |    0 |                 0 |        77 CPF/min |
|     7 |      182 |  10 |    0 |                 0 |        54 CPF/min |
|     8 |      183 |  10 |    0 |                 0 |        72 CPF/min |
|     9 |      184 |  10 |    0 |                 0 |        80 CPF/min |
|    10 |      185 |  10 |    0 |                 0 |        56 CPF/min |

Consolidado:

- Envios: `176` a `185`.
- Tentados: `100` CPFs.
- Sucesso: `100`.
- Erro: `0`.
- Pendente consulta: `0`.
- Taxa de erro: `0,0%`.
- Nenhum `543`.
- Nenhum `1089`.

Validacao do anual V2 apos os 100:

- `2025-09` total: `15.917`.
- OK: `100`.
- Erro: `0`.
- Pendente: `15.817`.
- Estado: `pronto_para_processar`.
- Mes permanece aberto com recibo S-1298 `1.1.0000000040747878940`.

## 22. Proximos 100 S-1210 de setembro - envio unico - 2026-05-13

Autorizacao recebida para fazer mais 100 CPFs em uma unica execucao CICLO100, como agosto:

- `limite=100`.
- `workers=5`.
- `batch=50`.
- `progress_every=50`.
- `--pular-ja-tentados`.
- Parada se taxa de erro >20%.

Execucao real em producao, SOLUCOES, `per_apur=2025-09`:

- `timeline_envio.id=186`.
- Selecionados: `100` CPFs.
- Batches: `2` de ate `50` CPFs.
- Protocolos: `1.1.202605.0000000013150938861` e `1.1.202605.0000000013150938864`.
- Sucesso: `99`.
- Erro: `1`.
- Pendente consulta: `0`.
- Taxa de erro: `1,0%`.
- Velocidade final: aproximadamente `152 CPF/min`.
- Histograma: `{'401': 1}`.
- Nenhum `543`.
- Nenhum `1089`.

Erro identificado:

- CPF: `00555440370`.
- Codigo: `401`.
- Mensagem: `Conteudo do evento inválido` / grupo `Plano de saúde coletivo` deve ser preenchido.

Validacao do anual V2 apos o envio `186`:

- `2025-09` total: `15.917`.
- OK: `199`.
- Erro: `1`.
- Pendente: `15.717`.
- Estado: `pronto_para_processar`.
- Mes permanece aberto com recibo S-1298 `1.1.0000000040747878940`.

## 23. Mais 500 S-1210 de setembro - 5 execucoes de 100 - 2026-05-13

Autorizacao recebida para fazer mais `500` CPFs, em `5` execucoes CICLO100 de `100` cada, com feedback apos cada execucao:

- `limite=100`.
- `workers=5`.
- `batch=50`.
- `progress_every=50`.
- `--pular-ja-tentados`.
- Parada se taxa de erro >20%.

Preflight antes da leva:

- Selecionaveis: `500`.
- Primeiro CPF selecionavel: `00560567103`.
- Ultimo CPF selecionavel na janela de 500: `01414329504`.
- Anual antes: total `15.917`, OK `199`, erro `1`, pendente `15.717`.

Execucoes reais em producao:

| Rodada | envio_id |  OK | Erro | Pendente consulta | Taxa erro | Velocidade aprox. | Histograma |
| -----: | -------: | --: | ---: | ----------------: | --------: | ----------------: | ---------- |
|    1/5 |      187 |  99 |    1 |                 0 |      1,0% |       152 CPF/min | `202: 1`   |
|    2/5 |      188 |  99 |    1 |                 0 |      1,0% |       152 CPF/min | `202: 1`   |
|    3/5 |      189 |  98 |    2 |                 0 |      2,0% |       153 CPF/min | `202: 2`   |
|    4/5 |      190 |  99 |    1 |                 0 |      1,0% |       135 CPF/min | `202: 1`   |
|    5/5 |      191 |  99 |    1 |                 0 |      1,0% |       152 CPF/min | `202: 1`   |

Consolidado da leva `187..191`:

- Tentados: `500`.
- Sucesso: `494`.
- Erro: `6`.
- Pendente consulta: `0`.
- Taxa de erro: `1,2%`.
- Histograma: `202: 6`.
- Nenhum `543`.
- Nenhum `1089`.

Os erros `202` sao retornos aceitos com advertencia relacionados a valores de deducao de dependentes, nao falha de infraestrutura nem concorrencia.

Validacao do anual V2 apos a leva:

- `2025-09` total: `15.917`.
- OK: `693`.
- Erro: `7`.
- Pendente: `15.217`.
- Estado: `pronto_para_processar`.
- Mes permanece aberto com recibo S-1298 `1.1.0000000040747878940`.

## 24. Mais 1000 S-1210 de setembro - 10 execucoes de 100 - 2026-05-13

Autorizacao recebida para fazer mais `1000` CPFs, em `10` execucoes CICLO100 de `100` cada, com feedback apos cada execucao e mesmas travas:

- `limite=100`.
- `workers=5`.
- `batch=50`.
- `progress_every=50`.
- `--pular-ja-tentados`.
- Parada se taxa de erro >20%, erro `543`, erro `1089`, falha tecnica ou pendente_consulta relevante.

Preflight antes da leva:

- Selecionaveis: `1000`.
- Primeiro CPF selecionavel: `01414363443`.
- Ultimo CPF selecionavel na janela de 1000: `02821220448`.
- Anual antes: total `15.917`, OK `693`, erro `7`, pendente `15.217`.

Execucoes reais em producao:

| Rodada | envio_id |  OK | Erro | Pendente consulta | Taxa erro | Velocidade aprox. | Histograma       |
| -----: | -------: | --: | ---: | ----------------: | --------: | ----------------: | ---------------- |
|   1/10 |      192 |  98 |    2 |                 0 |      2,0% |       106 CPF/min | `202: 2`         |
|   2/10 |      193 |  99 |    1 |                 0 |      1,0% |       110 CPF/min | `202: 1`         |
|   3/10 |      194 | 100 |    0 |                 0 |      0,0% |       128 CPF/min | `{}`             |
|   4/10 |      195 |  99 |    1 |                 0 |      1,0% |       139 CPF/min | `202: 1`         |
|   5/10 |      196 | 100 |    0 |                 0 |      0,0% |       145 CPF/min | `{}`             |
|   6/10 |      197 |  97 |    3 |                 0 |      3,0% |       173 CPF/min | `202: 3`         |
|   7/10 |      198 |  99 |    1 |                 0 |      1,0% |       171 CPF/min | `401: 1`         |
|   8/10 |      199 |  99 |    1 |                 0 |      1,0% |       146 CPF/min | `202: 1`         |
|   9/10 |      200 |  98 |    2 |                 0 |      2,0% |       146 CPF/min | `202: 2`         |
|  10/10 |      201 |  98 |    2 |                 0 |      2,0% |       148 CPF/min | `202: 1, 401: 1` |

Consolidado da leva `192..201`:

- Tentados: `1000`.
- Sucesso: `987`.
- Erro: `13`.
- Pendente consulta: `0`.
- Taxa de erro: `1,3%`.
- Histograma: `202: 11`, `401: 2`.
- Nenhum `543`.
- Nenhum `1089`.
- Nenhuma falha tecnica.

CPFs com `401` nesta leva:

- `02346385832`: grupo `Plano de saude coletivo` deve ser preenchido.
- `02713285844`: grupo `Plano de saude coletivo` deve ser preenchido.

Os retornos `202` sao aceitos com advertencia, principalmente por valor de deducao de dependente acima de `R$ 189,59` ou dependente `00000000000`.

Validacao do anual V2 apos a leva:

- `2025-09` total: `15.917`.
- OK: `1.680`.
- Erro: `20`.
- Aceito com aviso: `17`.
- Pendente: `14.217`.
- Estado: `pronto_para_processar`.
- Mes permanece aberto com recibo S-1298 `1.1.0000000040747878940`.
- Proximo CPF selecionavel: `02823014292`.

## 25. Mais 2000 S-1210 de setembro - 20 execucoes de 100 - 2026-05-13

Autorizacao recebida para fazer mais `2000` CPFs, em `20` execucoes CICLO100 de `100` cada, com feedback apos cada execucao e mesmas travas:

- `limite=100`.
- `workers=5`.
- `batch=50`.
- `progress_every=50`.
- `--pular-ja-tentados`.
- Parada se taxa de erro >20%, erro `543`, erro `1089`, falha tecnica ou pendente_consulta relevante.

Preflight antes da leva:

- Selecionaveis: `2000`.
- Primeiro CPF selecionavel: `02823014292`.
- Ultimo CPF selecionavel na janela de 2000: `05676572728`.
- Anual antes: total `15.917`, OK `1.680`, erro `20`, pendente `14.217`.

Execucoes reais em producao:

| Rodada | envio_id |  OK | Erro | Pendente consulta | Taxa erro | Velocidade aprox. | Histograma       |
| -----: | -------: | --: | ---: | ----------------: | --------: | ----------------: | ---------------- |
|   1/20 |      202 |  99 |    1 |                 0 |      1,0% |       129 CPF/min | `202: 1`         |
|   2/20 |      203 |  97 |    3 |                 0 |      3,0% |       118 CPF/min | `202: 2, 401: 1` |
|   3/20 |      204 | 100 |    0 |                 0 |      0,0% |       129 CPF/min | `{}`             |
|   4/20 |      205 | 100 |    0 |                 0 |      0,0% |       136 CPF/min | `{}`             |
|   5/20 |      206 |  96 |    4 |                 0 |      4,0% |       154 CPF/min | `202: 4`         |
|   6/20 |      207 |  98 |    2 |                 0 |      2,0% |       150 CPF/min | `202: 2`         |
|   7/20 |      208 |  99 |    1 |                 0 |      1,0% |       152 CPF/min | `202: 1`         |
|   8/20 |      209 |  99 |    1 |                 0 |      1,0% |       178 CPF/min | `202: 1`         |
|   9/20 |      210 | 100 |    0 |                 0 |      0,0% |       151 CPF/min | `{}`             |
|  10/20 |      211 |  97 |    3 |                 0 |      3,0% |       151 CPF/min | `202: 3`         |
|  11/20 |      212 |  95 |    5 |                 0 |      5,0% |       153 CPF/min | `202: 3, 401: 2` |
|  12/20 |      213 | 100 |    0 |                 0 |      0,0% |       152 CPF/min | `{}`             |
|  13/20 |      214 |  98 |    2 |                 0 |      2,0% |       152 CPF/min | `202: 2`         |
|  14/20 |      215 |  98 |    2 |                 0 |      2,0% |       153 CPF/min | `202: 2`         |
|  15/20 |      216 |  99 |    1 |                 0 |      1,0% |       175 CPF/min | `202: 1`         |
|  16/20 |      217 |  99 |    1 |                 0 |      1,0% |       176 CPF/min | `202: 1`         |
|  17/20 |      218 |  99 |    1 |                 0 |      1,0% |       152 CPF/min | `202: 1`         |
|  18/20 |      219 |  99 |    1 |                 0 |      1,0% |       152 CPF/min | `202: 1`         |
|  19/20 |      220 |  96 |    4 |                 0 |      4,0% |       153 CPF/min | `202: 4`         |
|  20/20 |      221 |  99 |    1 |                 0 |      1,0% |       151 CPF/min | `202: 1`         |

Consolidado da leva `202..221`:

- Tentados: `2000`.
- Sucesso: `1967`.
- Erro: `33`.
- Pendente consulta: `0`.
- Taxa de erro: `1,65%`.
- Histograma: `202: 30`, `401: 3`.
- Nenhum `543`.
- Nenhum `1089`.
- Nenhuma falha tecnica.

CPFs com `401` nesta leva:

- `02979332305`: grupo `Plano de saude coletivo` deve ser preenchido.
- `04224010569`: grupo `Plano de saude coletivo` deve ser preenchido.
- `04239333458`: erro `459`, recibo anterior informado nao localizado ou evento anterior excluido/retificado.

Os retornos `202` continuam sendo aceitos com advertencia, principalmente por valor de deducao de dependente acima de `R$ 189,59` ou dependente `00000000000`.

Validacao do anual V2 apos a leva:

- `2025-09` total: `15.917`.
- OK: `3.647`.
- Erro: `53`.
- Aceito com aviso: `47`.
- Pendente: `12.217`.
- Estado: `pronto_para_processar`.
- Mes permanece aberto com recibo S-1298 `1.1.0000000040747878940`.
- Proximo CPF selecionavel: `05677395706`.

## 26. Mais 2000 S-1210 de setembro - segunda leva de 20 execucoes de 100 - 2026-05-13

Autorizacao recebida para fazer mais `2000` CPFs apos a leva anterior, novamente em `20` execucoes CICLO100 de `100` cada, com as mesmas travas:

- `limite=100`.
- `workers=5`.
- `batch=50`.
- `progress_every=50`.
- `--pular-ja-tentados`.
- Parada se taxa de erro >20%, erro `543`, erro `1089`, falha tecnica ou pendente_consulta relevante.

Preflight antes da leva:

- Selecionaveis: `2000`.
- Primeiro CPF selecionavel: `05677395706`.
- Ultimo CPF selecionavel na janela de 2000: `09279109421`.
- Anual antes: total `15.917`, OK `3.647`, erro `53`, aceito com aviso `47`, pendente `12.217`.

Execucoes reais em producao:

| Rodada | envio_id |  OK | Erro | Pendente consulta | Taxa erro | Histograma       |
| -----: | -------: | --: | ---: | ----------------: | --------: | ---------------- |
|   1/20 |      222 |  97 |    3 |                 0 |      3,0% | `202: 3`         |
|   2/20 |      223 | 100 |    0 |                 0 |      0,0% | `{}`             |
|   3/20 |      224 |  99 |    1 |                 0 |      1,0% | `202: 1`         |
|   4/20 |      225 | 100 |    0 |                 0 |      0,0% | `{}`             |
|   5/20 |      226 | 100 |    0 |                 0 |      0,0% | `{}`             |
|   6/20 |      227 | 100 |    0 |                 0 |      0,0% | `{}`             |
|   7/20 |      228 |  97 |    3 |                 0 |      3,0% | `202: 3`         |
|   8/20 |      229 |  96 |    4 |                 0 |      4,0% | `202: 4`         |
|   9/20 |      230 |  98 |    2 |                 0 |      2,0% | `202: 2`         |
|  10/20 |      231 | 100 |    0 |                 0 |      0,0% | `{}`             |
|  11/20 |      232 |  98 |    2 |                 0 |      2,0% | `202: 1, 401: 1` |
|  12/20 |      233 |  99 |    1 |                 0 |      1,0% | `401: 1`         |
|  13/20 |      234 |  94 |    6 |                 0 |      6,0% | `202: 4, 401: 2` |
|  14/20 |      235 |  99 |    1 |                 0 |      1,0% | `202: 1`         |
|  15/20 |      236 | 100 |    0 |                 0 |      0,0% | `{}`             |
|  16/20 |      237 |  97 |    3 |                 0 |      3,0% | `202: 3`         |
|  17/20 |      238 |  98 |    2 |                 0 |      2,0% | `202: 2`         |
|  18/20 |      239 |  99 |    1 |                 0 |      1,0% | `202: 1`         |
|  19/20 |      240 |  99 |    1 |                 0 |      1,0% | `401: 1`         |
|  20/20 |      241 | 100 |    0 |                 0 |      0,0% | `{}`             |

Consolidado da leva `222..241`:

- Tentados: `2000`.
- Sucesso: `1970`.
- Erro: `30`.
- Pendente consulta: `0`.
- Taxa de erro: `1,50%`.
- Histograma: `202: 25`, `401: 5`.
- Nenhum `543`.
- Nenhum `1089`.
- Nenhuma falha tecnica.

CPFs com `401` nesta leva:

- `07463327850`: grupo `Plano de saude coletivo` deve ser preenchido.
- `07634291714`: grupo `Plano de saude coletivo` deve ser preenchido.
- `07863498830`: grupo `Plano de saude coletivo` deve ser preenchido.
- `07863548870`: grupo `Plano de saude coletivo` deve ser preenchido.
- `08865298839`: grupo `Plano de saude coletivo` deve ser preenchido.

Validacao do anual V2 apos a leva:

- `2025-09` total: `15.917`.
- OK: `5.617`.
- Erro: `83`.
- Aceito com aviso: `72`.
- Pendente: `10.217`.
- Estado: `pronto_para_processar`.
- Mes permanece aberto com recibo S-1298 `1.1.0000000040747878940`.
- Proximo CPF selecionavel: `09279699717`.

## 27. Mais 2000 S-1210 de setembro - terceira leva de 20 execucoes de 100 - 2026-05-13

Autorizacao recebida para fazer mais `2000` CPFs apos a segunda leva, novamente em `20` execucoes CICLO100 de `100` cada, com as mesmas travas:

- `limite=100`.
- `workers=5`.
- `batch=50`.
- `progress_every=50`.
- `--pular-ja-tentados`.
- Parada se taxa de erro >20%, erro `543`, erro `1089`, falha tecnica ou pendente_consulta relevante.

Preflight antes da leva:

- Selecionaveis: `2000`.
- Primeiro CPF selecionavel: `09279699717`.
- Ultimo CPF selecionavel na janela de 2000: `13922113796`.
- Anual antes: total `15.917`, OK `5.617`, erro `83`, aceito com aviso `72`, pendente `10.217`.

Execucoes reais em producao:

| Rodada | envio_id |  OK | Erro | Pendente consulta | Taxa erro | Histograma       |
| -----: | -------: | --: | ---: | ----------------: | --------: | ---------------- |
|   1/20 |      242 |  99 |    1 |                 0 |      1,0% | `202: 1`         |
|   2/20 |      243 |  96 |    4 |                 0 |      4,0% | `202: 1, 401: 3` |
|   3/20 |      244 |  99 |    1 |                 0 |      1,0% | `202: 1`         |
|   4/20 |      245 |  98 |    2 |                 0 |      2,0% | `202: 2`         |
|   5/20 |      246 |  97 |    3 |                 0 |      3,0% | `202: 3`         |
|   6/20 |      247 |  99 |    1 |                 0 |      1,0% | `401: 1`         |
|   7/20 |      248 | 100 |    0 |                 0 |      0,0% | `{}`             |
|   8/20 |      249 |  97 |    3 |                 0 |      3,0% | `202: 2, 401: 1` |
|   9/20 |      250 | 100 |    0 |                 0 |      0,0% | `{}`             |
|  10/20 |      251 | 100 |    0 |                 0 |      0,0% | `{}`             |
|  11/20 |      252 |  98 |    2 |                 0 |      2,0% | `202: 2`         |
|  12/20 |      253 |  97 |    3 |                 0 |      3,0% | `202: 2, 401: 1` |
|  13/20 |      254 |  98 |    2 |                 0 |      2,0% | `202: 1, 401: 1` |
|  14/20 |      255 |  96 |    4 |                 0 |      4,0% | `202: 2, 401: 2` |
|  15/20 |      256 |  99 |    1 |                 0 |      1,0% | `401: 1`         |
|  16/20 |      257 |  97 |    3 |                 0 |      3,0% | `202: 1, 401: 2` |
|  17/20 |      258 |  99 |    1 |                 0 |      1,0% | `401: 1`         |
|  18/20 |      259 |  99 |    1 |                 0 |      1,0% | `202: 1`         |
|  19/20 |      260 | 100 |    0 |                 0 |      0,0% | `{}`             |
|  20/20 |      261 |  96 |    4 |                 0 |      4,0% | `401: 4`         |

Consolidado da leva `242..261`:

- Tentados: `2000`.
- Sucesso: `1964`.
- Erro: `36`.
- Pendente consulta: `0`.
- Taxa de erro: `1,80%`.
- Histograma: `202: 19`, `401: 17`.
- Nenhum `543`.
- Nenhum `1089`.
- Nenhuma falha tecnica.

CPFs com `401` nesta leva:

- `09548614855`: grupo `Plano de saude coletivo` deve ser preenchido.
- `09552153824`: grupo `Plano de saude coletivo` deve ser preenchido.
- `09612497656`: grupo `Plano de saude coletivo` deve ser preenchido.
- `10213292823`: grupo `Plano de saude coletivo` deve ser preenchido.
- `10639034837`: grupo `Plano de saude coletivo` deve ser preenchido.
- `11438810873`: grupo `Plano de saude coletivo` deve ser preenchido.
- `11746677880`: grupo `Plano de saude coletivo` deve ser preenchido.
- `11984250833`: grupo `Plano de saude coletivo` deve ser preenchido.
- `11999740807`: grupo `Plano de saude coletivo` deve ser preenchido.
- `12265702838`: grupo `Plano de saude coletivo` deve ser preenchido.
- `12537867718`: grupo `Informacao dos beneficiarios da pensao alimenticia` deve ser preenchido.
- `12601629827`: grupo `Plano de saude coletivo` deve ser preenchido.
- `12611014809`: grupo `Plano de saude coletivo` deve ser preenchido.
- `13660429805`: grupo `Plano de saude coletivo` deve ser preenchido.
- `13696451800`: grupo `Plano de saude coletivo` deve ser preenchido.
- `13705060821`: grupo `Plano de saude coletivo` deve ser preenchido.
- `13711160832`: grupo `Plano de saude coletivo` deve ser preenchido.

Validacao do anual V2 apos a leva:

- `2025-09` total: `15.917`.
- OK: `7.581`.
- Erro: `119`.
- Aceito com aviso: `91`.
- Pendente: `8.217`.
- Estado: `pronto_para_processar`.
- Mes permanece aberto com recibo S-1298 `1.1.0000000040747878940`.
- Proximo CPF selecionavel: `13925917756`.

## 28. Mais 2000 S-1210 de setembro - quarta leva de 20 execucoes de 100 - 2026-05-13

Autorizacao recebida para fazer mais `2000` CPFs apos a terceira leva, novamente em `20` execucoes CICLO100 de `100` cada, com as mesmas travas:

- `limite=100`.
- `workers=5`.
- `batch=50`.
- `progress_every=50`.
- `--pular-ja-tentados`.
- Parada se taxa de erro >20%, erro `543`, erro `1089`, falha tecnica ou pendente_consulta relevante.

Preflight antes da leva:

- Selecionaveis: `2000`.
- Primeiro CPF selecionavel: `13925917756`.
- Ultimo CPF selecionavel na janela de 2000: `28924911856`.
- Anual antes: total `15.917`, OK `7.581`, erro `119`, aceito com aviso `91`, pendente `8.217`.

Execucoes reais em producao:

| Rodada | envio_id |  OK | Erro | Pendente consulta | Taxa erro | Histograma       |
| -----: | -------: | --: | ---: | ----------------: | --------: | ---------------- |
|   1/20 |      262 |  99 |    1 |                 0 |      1,0% | `401: 1`         |
|   2/20 |      263 |  99 |    1 |                 0 |      1,0% | `401: 1`         |
|   3/20 |      264 |  99 |    1 |                 0 |      1,0% | `401: 1`         |
|   4/20 |      265 |  97 |    3 |                 0 |      3,0% | `202: 2, 401: 1` |
|   5/20 |      266 |  99 |    1 |                 0 |      1,0% | `202: 1`         |
|   6/20 |      267 | 100 |    0 |                 0 |      0,0% | `{}`             |
|   7/20 |      268 | 100 |    0 |                 0 |      0,0% | `{}`             |
|   8/20 |      269 |  99 |    1 |                 0 |      1,0% | `202: 1`         |
|   9/20 |      270 |  98 |    2 |                 0 |      2,0% | `202: 1, 401: 1` |
|  10/20 |      271 |  99 |    1 |                 0 |      1,0% | `401: 1`         |
|  11/20 |      272 |  99 |    1 |                 0 |      1,0% | `202: 1`         |
|  12/20 |      273 |  97 |    3 |                 0 |      3,0% | `401: 3`         |
|  13/20 |      274 |  95 |    5 |                 0 |      5,0% | `401: 5`         |
|  14/20 |      275 |  96 |    4 |                 0 |      4,0% | `401: 4`         |
|  15/20 |      276 |  98 |    2 |                 0 |      2,0% | `401: 2`         |
|  16/20 |      277 |  99 |    1 |                 0 |      1,0% | `202: 1`         |
|  17/20 |      278 |  96 |    4 |                 0 |      4,0% | `202: 1, 401: 3` |
|  18/20 |      279 |  96 |    4 |                 0 |      4,0% | `401: 4`         |
|  19/20 |      280 |  98 |    2 |                 0 |      2,0% | `401: 2`         |
|  20/20 |      281 |  99 |    1 |                 0 |      1,0% | `401: 1`         |

Consolidado da leva `262..281`:

- Tentados: `2000`.
- Sucesso: `1962`.
- Erro: `38`.
- Pendente consulta: `0`.
- Taxa de erro: `1,90%`.
- Histograma: `401: 30`, `202: 8`.
- Nenhum `543`.
- Nenhum `1089`.
- Nenhuma falha tecnica.

CPFs com `401` nesta leva: todos por grupo `Plano de saude coletivo` obrigatorio.

- `14193059804`
- `14418818839`
- `15057517805`
- `15509458828`
- `17725269835`
- `18401846803`
- `20315573864`
- `21288302819`
- `21653555831`
- `21777491827`
- `21804920819`
- `21899082808`
- `22229832824`
- `22455023885`
- `22617602800`
- `22617893863`
- `22647816883`
- `22730253866`
- `24945783888`
- `25169797893`
- `26176873843`
- `26349271858`
- `26662467871`
- `26903366857`
- `27156659898`
- `27206786863`
- `27244289863`
- `27984880875`
- `28102078871`
- `28328079844`

Validacao do anual V2 apos a leva:

- `2025-09` total: `15.917`.
- OK: `9.543`.
- Erro: `157`.
- Aceito com aviso: `99`.
- Pendente: `6.217`.
- Estado: `pronto_para_processar`.
- Mes permanece aberto com recibo S-1298 `1.1.0000000040747878940`.
- Proximo CPF selecionavel: `28926436861`.

## 29. Mais 2000 S-1210 de setembro - quinta leva de 20 execucoes de 100 - 2026-05-13

Autorizacao recebida para fazer mais `2000` CPFs apos a quarta leva, novamente em `20` execucoes CICLO100 de `100` cada, com as mesmas travas:

- `limite=100`.
- `workers=5`.
- `batch=50`.
- `progress_every=50`.
- `--pular-ja-tentados`.
- Parada se taxa de erro >20%, erro `543`, erro `1089`, falha tecnica ou pendente_consulta relevante.

Preflight antes da leva:

- Selecionaveis: `2000`.
- Primeiro CPF selecionavel: `28926436861`.
- Ultimo CPF selecionavel na janela de 2000: `43999920858`.
- Anual antes: total `15.917`, OK `9.543`, erro `157`, aceito com aviso `99`, pendente `6.217`.

Execucoes reais em producao:

| Rodada | envio_id |  OK | Erro | Pendente consulta | Taxa erro | Histograma       |
| -----: | -------: | --: | ---: | ----------------: | --------: | ---------------- |
|   1/20 |      282 |  98 |    2 |                 0 |      2,0% | `202: 1, 401: 1` |
|   2/20 |      283 |  96 |    4 |                 0 |      4,0% | `202: 1, 401: 3` |
|   3/20 |      284 |  93 |    7 |                 0 |      7,0% | `202: 1, 401: 6` |
|   4/20 |      285 |  98 |    2 |                 0 |      2,0% | `401: 2`         |
|   5/20 |      286 |  98 |    2 |                 0 |      2,0% | `202: 1, 401: 1` |
|   6/20 |      287 |  97 |    3 |                 0 |      3,0% | `401: 3`         |
|   7/20 |      288 |  97 |    3 |                 0 |      3,0% | `202: 2, 401: 1` |
|   8/20 |      289 |  98 |    2 |                 0 |      2,0% | `202: 1, 401: 1` |
|   9/20 |      290 |  98 |    2 |                 0 |      2,0% | `202: 1, 401: 1` |
|  10/20 |      291 |  97 |    3 |                 0 |      3,0% | `202: 1, 401: 2` |
|  11/20 |      292 | 100 |    0 |                 0 |      0,0% | `{}`             |
|  12/20 |      293 |  98 |    2 |                 0 |      2,0% | `401: 2`         |
|  13/20 |      294 |  97 |    3 |                 0 |      3,0% | `202: 1, 401: 2` |
|  14/20 |      295 |  99 |    1 |                 0 |      1,0% | `401: 1`         |
|  15/20 |      296 |  99 |    1 |                 0 |      1,0% | `401: 1`         |
|  16/20 |      297 |  99 |    1 |                 0 |      1,0% | `202: 1`         |
|  17/20 |      298 |  98 |    2 |                 0 |      2,0% | `401: 2`         |
|  18/20 |      299 |  99 |    1 |                 0 |      1,0% | `202: 1`         |
|  19/20 |      300 |  99 |    1 |                 0 |      1,0% | `401: 1`         |
|  20/20 |      301 |  99 |    1 |                 0 |      1,0% | `401: 1`         |

Consolidado da leva `282..301`:

- Tentados: `2000`.
- Sucesso: `1957`.
- Erro: `43`.
- Pendente consulta: `0`.
- Taxa de erro: `2,15%`.
- Histograma: `401: 31`, `202: 12`.
- Nenhum `543`.
- Nenhum `1089`.
- Nenhuma falha tecnica.

CPFs com `401` nesta leva:

- Plano de saude coletivo obrigatorio: `29014861850`, `29813948353`, `29928815895`, `30516064215`, `30729903877`, `30748912894`, `30761016848`, `30815823851`, `30877919895`, `31268487880`, `31428650806`, `31798008874`, `32394567880`, `32875046810`, `33030723372`, `33387996837`, `33593392828`, `34212228866`, `34917814855`, `35716135897`, `35791396813`, `36984839807`, `37495188820`, `37824282856`, `38072051873`, `38678364858`, `40805764801`, `41190097850`, `42526219841`, `43582114880`.
- Informacao dos beneficiarios da pensao alimenticia obrigatoria: `39428963895`.

Validacao do anual V2 apos a leva:

- `2025-09` total: `15.917`.
- OK: `11.500`.
- Erro: `200`.
- Aceito com aviso: `111`.
- Pendente: `4.217`.
- Estado: `pronto_para_processar`.
- Mes permanece aberto com recibo S-1298 `1.1.0000000040747878940`.
- Proximo CPF selecionavel: `44017889824`.

## 30. Mais 2000 S-1210 de setembro - sexta leva de 20 execucoes de 100 - 2026-05-13

Antes da leva, o backend local foi verificado: `/api/health` respondia, mas `dev-login` retornava `500` por conexao PostgreSQL fechada no processo Uvicorn. O backend foi reiniciado e a validacao por `5174/api/auth/dev-login` + overview anual voltou a responder.

Autorizacao recebida para fazer mais `2000` CPFs apos a quinta leva, novamente em `20` execucoes CICLO100 de `100` cada, com as mesmas travas:

- `limite=100`.
- `workers=5`.
- `batch=50`.
- `progress_every=50`.
- `--pular-ja-tentados`.
- Parada se taxa de erro >20%, erro `543`, erro `1089`, falha tecnica ou pendente_consulta relevante.

Preflight antes da leva:

- Selecionaveis: `2000`.
- Primeiro CPF selecionavel: `44017889824`.
- Ultimo CPF selecionavel na janela de 2000: `72457295149`.
- Anual antes: total `15.917`, OK `11.500`, erro `200`, aceito com aviso `111`, pendente `4.217`.

Execucoes reais em producao:

| Rodada | envio_id |  OK | Erro | Pendente consulta | Taxa erro | Histograma       |
| -----: | -------: | --: | ---: | ----------------: | --------: | ---------------- |
|   1/20 |      302 |  99 |    1 |                 0 |      1,0% | `401: 1`         |
|   2/20 |      303 |  99 |    1 |                 0 |      1,0% | `401: 1`         |
|   3/20 |      304 | 100 |    0 |                 0 |      0,0% | `{}`             |
|   4/20 |      305 | 100 |    0 |                 0 |      0,0% | `{}`             |
|   5/20 |      306 | 100 |    0 |                 0 |      0,0% | `{}`             |
|   6/20 |      307 | 100 |    0 |                 0 |      0,0% | `{}`             |
|   7/20 |      308 | 100 |    0 |                 0 |      0,0% | `{}`             |
|   8/20 |      309 |  98 |    2 |                 0 |      2,0% | `202: 1, 401: 1` |
|   9/20 |      310 | 100 |    0 |                 0 |      0,0% | `{}`             |
|  10/20 |      311 | 100 |    0 |                 0 |      0,0% | `{}`             |
|  11/20 |      312 | 100 |    0 |                 0 |      0,0% | `{}`             |
|  12/20 |      313 | 100 |    0 |                 0 |      0,0% | `{}`             |
|  13/20 |      314 |  99 |    1 |                 0 |      1,0% | `401: 1`         |
|  14/20 |      315 | 100 |    0 |                 0 |      0,0% | `{}`             |
|  15/20 |      316 | 100 |    0 |                 0 |      0,0% | `{}`             |
|  16/20 |      317 |  99 |    1 |                 0 |      1,0% | `401: 1`         |
|  17/20 |      318 | 100 |    0 |                 0 |      0,0% | `{}`             |
|  18/20 |      319 | 100 |    0 |                 0 |      0,0% | `{}`             |
|  19/20 |      320 | 100 |    0 |                 0 |      0,0% | `{}`             |
|  20/20 |      321 | 100 |    0 |                 0 |      0,0% | `{}`             |

Consolidado da leva `302..321`:

- Tentados: `2000`.
- Sucesso: `1994`.
- Erro: `6`.
- Pendente consulta: `0`.
- Taxa de erro: `0,30%`.
- Histograma: `401: 5`, `202: 1`.
- Nenhum `543`.
- Nenhum `1089`.
- Nenhuma falha tecnica.

CPFs com `401` nesta leva: todos por grupo `Plano de saude coletivo` obrigatorio.

- `44752439808`
- `45244860895`
- `51109062893`
- `61623830400`
- `67578284568`

Validacao do anual V2 apos a leva:

- `2025-09` total: `15.917`.
- OK: `13.494`.
- Erro: `206`.
- Aceito com aviso: `112`.
- Pendente: `2.217`.
- Estado: `pronto_para_processar`.
- Mes permanece aberto com recibo S-1298 `1.1.0000000040747878940`.
- Proximo CPF selecionavel: `72462442715`.

## 31. Mais 2000 S-1210 de setembro - setima leva de 20 execucoes de 100 - 2026-05-13

Antes da leva, backend e frontend locais estavam fora do ar nas portas `8000` e `5174`. Foram reiniciados:

- Backend FastAPI em `http://127.0.0.1:8000`.
- Frontend Vite em `http://127.0.0.1:5174`.
- Validacao local: `/api/health` OK, `dev-login` OK, overview anual respondendo com token.

Autorizacao recebida para fazer mais `2000` CPFs apos a sexta leva, novamente em `20` execucoes CICLO100 de `100` cada, com as mesmas travas:

- `limite=100`.
- `workers=5`.
- `batch=50`.
- `progress_every=50`.
- `--pular-ja-tentados`.
- Parada se taxa de erro >20%, erro `543`, erro `1089`, falha tecnica ou pendente_consulta relevante.

Preflight antes da leva:

- Selecionaveis: `2000`.
- Primeiro CPF selecionavel: `72462442715`.
- Ultimo CPF selecionavel na janela de 2000: `95285237734`.
- Anual antes: total `15.917`, OK `13.494`, erro `206`, aceito com aviso `112`, pendente `2.217`.

Execucoes reais em producao:

| Rodada | envio_id |  OK | Erro | Pendente consulta | Taxa erro | Histograma |
| -----: | -------: | --: | ---: | ----------------: | --------: | ---------- |
|   1/20 |      322 |  98 |    2 |                 0 |      2,0% | `401: 2`   |
|   2/20 |      323 |  99 |    1 |                 0 |      1,0% | `202: 1`   |
|   3/20 |      324 | 100 |    0 |                 0 |      0,0% | `{}`       |
|   4/20 |      325 | 100 |    0 |                 0 |      0,0% | `{}`       |
|   5/20 |      326 | 100 |    0 |                 0 |      0,0% | `{}`       |
|   6/20 |      327 | 100 |    0 |                 0 |      0,0% | `{}`       |
|   7/20 |      328 | 100 |    0 |                 0 |      0,0% | `{}`       |
|   8/20 |      329 |  98 |    2 |                 0 |      2,0% | `401: 2`   |
|   9/20 |      330 | 100 |    0 |                 0 |      0,0% | `{}`       |
|  10/20 |      331 | 100 |    0 |                 0 |      0,0% | `{}`       |
|  11/20 |      332 |  99 |    1 |                 0 |      1,0% | `202: 1`   |
|  12/20 |      333 | 100 |    0 |                 0 |      0,0% | `{}`       |
|  13/20 |      334 | 100 |    0 |                 0 |      0,0% | `{}`       |
|  14/20 |      335 | 100 |    0 |                 0 |      0,0% | `{}`       |
|  15/20 |      336 |  99 |    1 |                 0 |      1,0% | `401: 1`   |
|  16/20 |      337 |  97 |    3 |                 0 |      3,0% | `202: 3`   |
|  17/20 |      338 |  99 |    1 |                 0 |      1,0% | `401: 1`   |
|  18/20 |      339 | 100 |    0 |                 0 |      0,0% | `{}`       |
|  19/20 |      340 | 100 |    0 |                 0 |      0,0% | `{}`       |
|  20/20 |      341 |  99 |    1 |                 0 |      1,0% | `202: 1`   |

Consolidado da leva `322..341`:

- Tentados: `2000`.
- Sucesso: `1988`.
- Erro: `12`.
- Pendente consulta: `0`.
- Taxa de erro: `0,60%`.
- Histograma: `202: 6`, `401: 6`.
- Nenhum `543`.
- Nenhum `1089`.
- Nenhuma falha tecnica.

CPFs com `401` nesta leva:

- Plano de saude coletivo obrigatorio: `73425230115`, `73902209372`, `81504411153`, `87041065472`, `90578570904`.
- CPF de dependente invalido no RET/evento: `81529368553` (`09274837500`).

Validacao do anual V2 apos a leva:

- `2025-09` total: `15.917`.
- OK: `15.482`.
- Erro: `218`.
- Aceito com aviso: `118`.
- Pendente: `217`.
- Estado: `pronto_para_processar`.
- Mes permanece aberto com recibo S-1298 `1.1.0000000040747878940`.
- Proximo CPF selecionavel: `95291881534`.
- Ultimo CPF selecionavel restante: `99965402191`.

## 32. Pendentes finais de setembro - 217 CPFs - 2026-05-13

Autorizacao recebida para enviar os `217` CPFs pendentes finais de SOLUCOES `2025-09`.

Preflight antes do envio:

- Painel anual: total `15.917`, OK `15.482`, erro `218`, aceito com aviso `118`, pendente `217`.
- Selecionaveis pelo backend: `217`.
- Primeiro CPF selecionavel: `95291881534`.
- Ultimo CPF selecionavel: `99965402191`.
- Mes aberto com recibo S-1298 `1.1.0000000040747878940`.

Primeira tentativa:

| envio_id | Limite |  OK | Erro | Pendente consulta | Histograma      | Observacao                                                                                        |
| -------: | -----: | --: | ---: | ----------------: | --------------- | ------------------------------------------------------------------------------------------------- |
|      342 |    100 |  50 |   50 |                 0 | `ERRO_LOTE: 50` | Segundo batch retornou XML invalido/retorno tecnico: `Space required after the Public Identifier` |

Como o envio `342` passou da trava de erro tecnico/taxa >20%, a execucao foi pausada. O diagnostico mostrou:

- Os primeiros `50` CPFs do envio `342` foram aceitos com recibo.
- Os outros `50` ficaram com status `falha_rede`, erro `ERRO_LOTE`, mensagem `xml invalido: Space required after the Public Identifier, line 1, column 50`.
- O painel ainda contava esses `50` como pendentes.
- O seletor antigo de `--pular-ja-tentados` bloqueava `falha_rede` como se fosse tentativa final; foi ajustado para permitir retry de `falha_rede` tecnica.

Envios restantes em modo conservador (`workers=1`, `batch=50`):

| envio_id | Limite |  OK | Erro | Pendente consulta | Histograma         |
| -------: | -----: | --: | ---: | ----------------: | ------------------ |
|      343 |     50 |  48 |    2 |                 0 | `202: 1`, `401: 1` |
|      344 |     50 |  50 |    0 |                 0 | `{}`               |
|      345 |     17 |  17 |    0 |                 0 | `{}`               |
|      346 |     50 |  50 |    0 |                 0 | `{}`               |

O envio `346` foi o retry cirurgico dos `50` CPFs que haviam ficado em `falha_rede` no envio `342`.

Consolidado operacional dos `217` CPFs finais:

- CPFs distintos tentados: `217`.
- Sucesso real: `215`.
- Erros funcionais reais: `2`.
- Pendente consulta: `0`.
- Retry tecnico recuperado: `50/50` sucesso no envio `346`.
- Nenhum `543`.
- Nenhum `1089`.
- Selecionaveis restantes pelo backend: `0`.

Erros funcionais reais nesta etapa:

- CPF `98234110187`: `401`, grupo `Plano de saude coletivo` obrigatorio.
- CPF `98397435468`: `202`, advertencia `1863`, valor da deducao da base do dependente `00000000000` invalido/maior que R$ 189,59.

Validacao final do anual V2:

- `2025-09` total: `15.917`.
- OK: `15.697`.
- Erro: `220`.
- Aceito com aviso: `119`.
- Pendente: `0`.
- Estado: `concluido_com_erros`.
- Mes permanece aberto com recibo S-1298 `1.1.0000000040747878940`.
