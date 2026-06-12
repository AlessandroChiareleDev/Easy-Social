# Objetiva - S-1210 Dezembro/2025 - Resultado final

## Resumo executivo

Atualizacao final: os 72 erros de plano de saude foram retificados com `planSaude`, enviados em producao e aceitos pelo eSocial. O CPF residual `00831605588` tambem foi resolvido com o recibo ativo informado pelo usuario, e dezembro foi fechado com S-1299 aceito.

- Correcao S-1210 planSaude: 72 XMLs assinados, 72 aceitos, 0 erro/pendente
- Protocolos S-1210 da correcao:
  - `1.1.202605.0000000013221886030` (40 eventos)
  - `1.1.202605.0000000013221887079` (32 eventos)
- V2 final: 1.275 CPFs no seletor atual, 1.275 ok, 0 erro
- CPF residual resolvido: `00831605588`, recibo ativo informado `1.1.0000000037296094083`, recibo novo `1.1.0000000041100973111`
- Fechamento S-1299: protocolo `1.1.202605.0000000013221942818`, recibo `1.1.0000000041101004200`
- Evidencia: `relatorio_ana/OBJETIVA_DEZEMBRO_2025_CORRECAO_72_RESULTADO.json`

Dezembro/2025 foi processado ate o fim para a Objetiva, usando somente a base local/ZIP ja importada. Nao houve chamada de Download, SolicitarDownload ou ConsultarIdentificadores.

- Empresa: Objetiva (`empresa_id=3`, schema `objetiva`, CNPJ `10874523000110`)
- Competencia: `2025-12`
- Escopo head por CPF: 1.284 CPFs
- S-1298: ja estava reaberto e confirmado antes da rodada final
  - Protocolo: `1.1.202605.0000000013210362404`
  - Recibo: `1.1.0000000041038424835`
- Resultado S-1210 antes da correcao de plano: 1.284 tentados, 1.211 sucessos, 73 erros, 0 pendentes
- Resultado V2 apos resolver recibo: 1.275 ok, 0 erro, 0 pendentes
- Taxa residual atual no seletor V2: 0,00%
- Trava operacional: limite era 20%; nao foi acionada
- Restantes elegiveis pelo seletor do motor: 0

## Execucao

| Fase              | Envios | Tentados | Sucesso | Erro | Taxa de erro | Observacao                      |
| ----------------- | -----: | -------: | ------: | ---: | -----------: | ------------------------------- |
| Ciclo 100         |  29-30 |      100 |      98 |    2 |        2,00% | Rodada inicial autorizada       |
| Restante dezembro |  31-54 |    1.184 |   1.113 |   71 |        6,00% | 23 blocos de 50 + 1 bloco de 34 |
| Total dezembro    |  29-54 |    1.284 |   1.211 |   73 |        5,69% | Sem pendente_consulta           |

A rodada final usou `workers=1`, `batch_size=50`, blocos de 50 CPFs e ultimo bloco parcial de 34 CPFs. O tempo da rodada final foi 1.998,7s, cerca de 33m19s, com media aproximada de 35,5 CPFs/min.

## Erros antes da correcao de plano

Todos os 73 erros ficaram como `erro_esocial` codigo `401`.

| Motivo                                                                    | Qtde | Leitura                                                                        |
| ------------------------------------------------------------------------- | ---: | ------------------------------------------------------------------------------ |
| `8: Grupo 'Plano de saude coletivo' deve ser preenchido`                  |   72 | O eSocial exigiu `planSaude`, mas o XML head local nao tinha grupo `planSaude` |
| `459: Nao foi localizado um evento para o recibo de entrega informado...` |    1 | Recibo local nao era mais o evento ativo no Ambiente Nacional                  |

Auditoria contra os XMLs head locais dos 73 CPFs com erro:

- 73/73 tinham `infoIRComplem` no XML original/head.
- 0/73 tinham `planSaude` no XML original/head.
- 0 falhas de extracao local.

Ou seja: a geracao preservou o que existia na origem. Depois desta auditoria, os 72 casos de plano foram corrigidos usando rubricas locais de plano e reenviados com sucesso.

## Correcao planSaude 2026-05-29

Foram gerados 72 XMLs S-1210 de retificacao `indRetif=2` com `planSaude` para dezembro/2025.

- CSV de origem atual: `relatorio_ana/OBJETIVA_DEZEMBRO_2025_ERROS_V2_ATUAL_2026-05-28.csv`
- Manifest: `relatorio_ana/OBJETIVA_DEZEMBRO_2025/xmls_dezembro_72_corrigidos/manifest_72_xmls_corrigidos.json`
- ZIP assinado: `relatorio_ana/OBJETIVA_DEZEMBRO_2025/xmls_dezembro_72_corrigidos/OBJETIVA_2025-12_72_XMLS_CORRIGIDOS_ASSINADOS.zip`
- Resultado bruto do envio: `relatorio_ana/OBJETIVA_DEZEMBRO_2025/xmls_dezembro_72_corrigidos/retorno_envio_72_dezembro/resultado_envio_72_dezembro.json`
- Resultado resumido: `relatorio_ana/OBJETIVA_DEZEMBRO_2025_CORRECAO_72_RESULTADO.json`

Resumo da geracao:

- XMLs assinados: 72/72
- Fallback para S-1210 anterior: 0
- Fontes rescisorias S-2299/S-2399: 19 CPFs
- Rubricas usadas: `516` (63), `619` (10), `774` (8), `775` (2)

Resumo do envio:

| Lote | Protocolo                        | Eventos | Resultado  |
| ---- | -------------------------------- | ------: | ---------- |
| 1    | `1.1.202605.0000000013221886030` |      40 | 40 aceitos |
| 2    | `1.1.202605.0000000013221887079` |      32 | 32 aceitos |

Validacao V2 apos envio:

| Status | Qtde |
| ------ | ---: |
| ok     | 1274 |
| erro   |    1 |

Depois da correcao de plano, o unico erro restante era o CPF `00831605588`, categoria `recibo_459_nao_localizado_excluido_retificado`. Ele foi resolvido com retificacao `indRetif=2` usando o recibo ativo informado `1.1.0000000037296094083`.

## Correcao recibo 459 e fechamento

- S-1210 CPF `00831605588`: protocolo `1.1.202605.0000000013221934866`, recibo novo `1.1.0000000041100973111`.
- V2 apos recibo: `1275 ok`, `0 erro`, `0 pendente`.
- S-1299 dezembro: protocolo `1.1.202605.0000000013221942818`, recibo `1.1.0000000041101004200`.

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
- Agregado local final: `sucesso=1275`, `erro_esocial=0`
- `pendente_consulta=0` em todos os blocos
- Mesmo seletor usado pelo motor (`_carregar_eventos_alvo(..., pular_ja_tentados=True)`) retornou `0` CPFs restantes

## Arquivos gerados/alterados

- `python-scripts/envio_objetiva_dezembro_ciclo100.py`: parametrizado para aceitar `--meta-total`, `--report-json`, ultimo bloco parcial e rotulo de parada.
- `relatorio_ana/OBJETIVA_DEZEMBRO_2025_RESTANTE_RESULTADO.json`: resultado bruto redigido da rodada final.
- `relatorio_ana/OBJETIVA_DEZEMBRO_2025_ERROS_V2_ATUAL_2026-05-28.csv`: snapshot V2 dos 73 erros antes da correcao, separando 72 plano e 1 recibo.
- `relatorio_ana/gerar_xmls_dezembro_72_corrigidos.py`: wrapper para gerar os 72 S-1210 de correcao.
- `relatorio_ana/enviar_72_dezembro_persistir_v2.py`: wrapper para enviar e persistir os 72 S-1210 no V2.
- `relatorio_ana/OBJETIVA_DEZEMBRO_2025_CORRECAO_72_RESULTADO.json`: resumo da correcao e validacao final.
- `relatorio_ana/OBJETIVA_RECIBOS_459_SET_DEZ_2025/resultado_resolucao_recibos_459.json`: tentativa de retificacao dos recibos informados; dezembro aceito, setembro identificado como S-3000.
- `relatorio_ana/OBJETIVA_RECIBOS_459_SET_DEZ_2025/resultado_final_recibos_459_set_dez_2025.json`: consolidado final dos recibos de setembro e dezembro.
- `relatorio_ana/OBJETIVA_DEZEMBRO_2025/fechamento_dezembro_s1299/manifest_fechamento_s1299_dezembro_objetiva.json`: fechamento S-1299 aceito.
- `relatorio_ana/OBJETIVA_DEZEMBRO_2025_FINAL_RELATORIO.md`: este relatorio.

## Proxima acao tecnica

Nenhuma acao tecnica pendente para dezembro/2025 no V2: S-1210 zerado e S-1299 fechado.
