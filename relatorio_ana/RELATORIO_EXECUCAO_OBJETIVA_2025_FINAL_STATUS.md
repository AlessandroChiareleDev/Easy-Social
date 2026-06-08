# Objetiva - S-1210 2025 - Status final

Atualizado em 2026-05-28 local / 2026-05-29 UTC.

## Resumo executivo

A correcao S-1210 da Objetiva em 2025 foi zerada no V2. Todos os erros de `planSaude` e os dois residuais de recibo foram resolvidos, e todos os meses de janeiro a dezembro foram fechados com S-1299 aceito.

Nao houve chamada de Download, SolicitarDownload ou ConsultarIdentificadores nesta consolidacao. As acoes usaram base local/V2 e envio S-1210/S-1299 quando aplicavel.

## Validacao V2 por competencia

| Competencia | Total V2 | OK | Erro | Pendente | Situacao |
| ----------- | -------: | -: | ---: | -------: | -------- |
| 2025-01 | 806 | 806 | 0 | 0 | Zerado/fechado |
| 2025-02 | 887 | 887 | 0 | 0 | Zerado/fechado |
| 2025-03 | 982 | 982 | 0 | 0 | Zerado/fechado |
| 2025-04 | 986 | 986 | 0 | 0 | Zerado/fechado |
| 2025-05 | 840 | 840 | 0 | 0 | Zerado/fechado |
| 2025-06 | 996 | 996 | 0 | 0 | Zerado/fechado |
| 2025-07 | 995 | 995 | 0 | 0 | Zerado/fechado |
| 2025-08 | 1057 | 1057 | 0 | 0 | Zerado/fechado |
| 2025-09 | 1059 | 1059 | 0 | 0 | Zerado/fechado |
| 2025-10 | 1226 | 1226 | 0 | 0 | Zerado/fechado |
| 2025-11 | 1284 | 1284 | 0 | 0 | Zerado/fechado |
| 2025-12 | 1275 | 1275 | 0 | 0 | Zerado/fechado |

## Recibos residuais resolvidos

| Competencia | CPF | Caminho adotado | Recibo S-1210 novo | Fechamento S-1299 |
| ----------- | --- | -------------- | ----------------- | ---------------- |
| 2025-09 | `06701349960` | Recibo informado `1.1.0000000035183951429` era S-3000 excluindo o S-1210 antigo; foi feita nova inclusao `indRetif=1` | `1.1.0000000041100992863` | `1.1.0000000041101000922` |
| 2025-12 | `00831605588` | Retificacao `indRetif=2` com recibo ativo informado `1.1.0000000037296094083` | `1.1.0000000041100973111` | `1.1.0000000041101004200` |

Evidencia consolidada: `relatorio_ana/OBJETIVA_RECIBOS_459_SET_DEZ_2025/resultado_final_recibos_459_set_dez_2025.json`.

## Dezembro - correcao final de planSaude

Antes da correcao, dezembro tinha 73 erros no V2: 72 de plano de saude e 1 recibo 459. Foram gerados e enviados 72 XMLs S-1210 de retificacao com `planSaude`; todos foram aceitos.

- `timeline_envio_id=69`
- Protocolo `1.1.202605.0000000013221886030`: 40 eventos aceitos
- Protocolo `1.1.202605.0000000013221887079`: 32 eventos aceitos
- Recibos novos: de `1.1.0000000041100738194` a `1.1.0000000041100745142`
- Resultado: `relatorio_ana/OBJETIVA_DEZEMBRO_2025_CORRECAO_72_RESULTADO.json`

## Fechamentos

Todos os meses de 2025 constam fechados no V2. Os ultimos fechamentos aceitos foram:

- Setembro/2025: protocolo `1.1.202605.0000000013221942257`, recibo `1.1.0000000041101000922`
- Dezembro/2025: protocolo `1.1.202605.0000000013221942818`, recibo `1.1.0000000041101004200`
