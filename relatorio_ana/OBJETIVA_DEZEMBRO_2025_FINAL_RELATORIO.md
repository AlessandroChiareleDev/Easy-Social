# Objetiva - S-1210 Dezembro/2025 - Resultado final

## Resumo executivo

Dezembro/2025 foi processado ate o fim para a Objetiva, usando somente a base local/ZIP ja importada. Nao houve chamada de Download, SolicitarDownload ou ConsultarIdentificadores.

- Empresa: Objetiva (`empresa_id=3`, schema `objetiva`, CNPJ `10874523000110`)
- Competencia: `2025-12`
- Escopo head por CPF: 1.284 CPFs
- S-1298: ja estava reaberto e confirmado antes da rodada final
  - Protocolo: `1.1.202605.0000000013210362404`
  - Recibo: `1.1.0000000041038424835`
- Resultado S-1210 final: 1.284 tentados, 1.211 sucessos, 73 erros, 0 pendentes
- Taxa final de erro: 5,69%
- Trava operacional: limite era 20%; nao foi acionada
- Restantes elegiveis pelo seletor do motor: 0

## Execucao

| Fase              | Envios | Tentados | Sucesso | Erro | Taxa de erro | Observacao                      |
| ----------------- | -----: | -------: | ------: | ---: | -----------: | ------------------------------- |
| Ciclo 100         |  29-30 |      100 |      98 |    2 |        2,00% | Rodada inicial autorizada       |
| Restante dezembro |  31-54 |    1.184 |   1.113 |   71 |        6,00% | 23 blocos de 50 + 1 bloco de 34 |
| Total dezembro    |  29-54 |    1.284 |   1.211 |   73 |        5,69% | Sem pendente_consulta           |

A rodada final usou `workers=1`, `batch_size=50`, blocos de 50 CPFs e ultimo bloco parcial de 34 CPFs. O tempo da rodada final foi 1.998,7s, cerca de 33m19s, com media aproximada de 35,5 CPFs/min.

## Erros finais

Todos os 73 erros ficaram como `erro_esocial` codigo `401`.

| Motivo                                                                    | Qtde | Leitura                                                                        |
| ------------------------------------------------------------------------- | ---: | ------------------------------------------------------------------------------ |
| `8: Grupo 'Plano de saude coletivo' deve ser preenchido`                  |   72 | O eSocial exigiu `planSaude`, mas o XML head local nao tinha grupo `planSaude` |
| `459: Nao foi localizado um evento para o recibo de entrega informado...` |    1 | Recibo local nao era mais o evento ativo no Ambiente Nacional                  |

Auditoria contra os XMLs head locais dos 73 CPFs com erro:

- 73/73 tinham `infoIRComplem` no XML original/head.
- 0/73 tinham `planSaude` no XML original/head.
- 0 falhas de extracao local.

Ou seja: a geracao preservou o que existia na origem. Os 72 erros de plano de saude nao sao perda do motor nesta rodada; faltam dados obrigatorios de plano no XML base para esses CPFs.

CPF do erro de recibo `459`:

| CPF           | Recibo local usado        | Observacao                                                                            |
| ------------- | ------------------------- | ------------------------------------------------------------------------------------- |
| `00831605588` | `1.1.0000000037295806756` | eSocial informou que esse recibo nao localiza evento ativo ou foi excluido/retificado |

Exemplos de CPFs com erro de plano de saude:

`00257694307`, `03906984583`, `04599304514`, `04959319500`, `06192861560`, `06359217821`, `09699573864`, `11255263865`, `12067551809`, `12073149863`, `13361896819`.

## Evidencias locais

- `timeline_mes_id=13`
- `zip_inicial`: envio 28, 2.431 XMLs S-1210, 1.284 heads por CPF
- Envios reais S-1210: 29 a 54, todos `concluido`
- Agregado local: `sucesso=1211`, `erro_esocial=73`
- `pendente_consulta=0` em todos os blocos
- Mesmo seletor usado pelo motor (`_carregar_eventos_alvo(..., pular_ja_tentados=True)`) retornou `0` CPFs restantes

## Arquivos gerados/alterados

- `python-scripts/envio_objetiva_dezembro_ciclo100.py`: parametrizado para aceitar `--meta-total`, `--report-json`, ultimo bloco parcial e rotulo de parada.
- `relatorio_ana/OBJETIVA_DEZEMBRO_2025_RESTANTE_RESULTADO.json`: resultado bruto redigido da rodada final.
- `relatorio_ana/OBJETIVA_DEZEMBRO_2025_FINAL_RELATORIO.md`: este relatorio.

## Proxima acao tecnica

Para os 72 CPFs de plano de saude, e necessario obter ou montar dados por CPF: CNPJ da operadora, registro ANS, valor do titular e, se houver, CPF/valor dos dependentes. Para o CPF `00831605588`, e necessario obter um recibo ativo valido antes de retificar novamente.
