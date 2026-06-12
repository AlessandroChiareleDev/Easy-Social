# Relatorio Execucao Objetiva Jun-Nov 2025

Fluxo executado em producao com S-1298 de reabertura e S-1210 de retificacao por XML original. Nao foram usadas consultas de download ou identificadores.

## Resumo final por CPF

| per_apur |           recibo S-1298 |         envios | CPFs finais | aceitos | erros finais | pendente_consulta | principais categorias                                              |
| -------- | ----------------------: | -------------: | ----------: | ------: | -----------: | ----------------: | ------------------------------------------------------------------ |
| 2025-06  | 1.1.0000000040946564210 |         21, 63 |         996 |     996 |            0 |                 0 | corrigido e fechado em 2026-05-28                                  |
| 2025-07  | 1.1.0000000040946772638 |         22, 64 |         995 |     995 |            0 |                 0 | corrigido e fechado em 2026-05-28                                  |
| 2025-08  | 1.1.0000000040946973523 |         23, 65 |        1057 |    1057 |            0 |                 0 | corrigido e fechado em 2026-05-28                                  |
| 2025-09  | 1.1.0000000040947177208 | 24, 66, 70, 72 |        1059 |    1059 |            0 |                 0 | corrigido e fechado apos resolver S-3000/S-1210 do CPF 06701349960 |
| 2025-10  | 1.1.0000000040947418526 |         25, 67 |        1226 |    1226 |            0 |                 0 | corrigido e fechado em 2026-05-28                                  |
| 2025-11  | 1.1.0000000040948191770 |     26, 27, 68 |        1284 |    1284 |            0 |                 0 | corrigido e fechado em 2026-05-28                                  |

## Totais Jun-Nov

- CPFs finais analisados: 6617
- Aceitos: 6617
- Erros finais de dados: 0
- Pendentes tecnicos: 0

## Correcao complementar - Junho/2025

- Gerados 87 XMLs S-1210 assinados em `2025-06/xmls_junho_87_corrigidos`.
- Sem fallback: todos os valores de `planSaude` vieram de S-1200 local por CPF + `ideDmDev`.
- Protocolos S-1210: `1.1.202605.0000000013221815660`, `1.1.202605.0000000013221816509`, `1.1.202605.0000000013221817417`.
- Resultado S-1210: 87/87 aceitos, V2 final `996 ok`, `0 erro`.
- S-1299 fechamento aceito: protocolo `1.1.202605.0000000013221818201`, recibo `1.1.0000000041100417148`.

## Correcao complementar - Julho/2025

- Gerados 87 XMLs S-1210 assinados em `2025-07/xmls_julho_87_corrigidos`.
- Um CPF usou fallback explicito do S-1210 aceito de junho (`47200725854`, recibo fonte `1.1.0000000041100412121`).
- Protocolos S-1210: `1.1.202605.0000000013221824396`, `1.1.202605.0000000013221825070`, `1.1.202605.0000000013221825870`.
- Resultado S-1210: 87/87 aceitos, V2 final `995 ok`, `0 erro`.
- S-1299 fechamento aceito: protocolo `1.1.202605.0000000013221826511`, recibo `1.1.0000000041100466416`.

## Correcao complementar - Agosto/2025

- Gerados 96 XMLs S-1210 assinados em `2025-08/xmls_agosto_96_corrigidos`.
- Dois CPFs usaram fonte rescisoria local S-2299 para `detVerbas` (`37478883800`, `51622669819`); sem fallback por S-1210 anterior.
- Protocolos S-1210: `1.1.202605.0000000013221840679`, `1.1.202605.0000000013221841693`, `1.1.202605.0000000013221842493`.
- Resultado S-1210: 96/96 aceitos, V2 final `1057 ok`, `0 erro`.
- S-1299 fechamento aceito: protocolo `1.1.202605.0000000013221843473`, recibo `1.1.0000000041100538978`.

## Correcao complementar - Setembro/2025

- Gerados 82 XMLs S-1210 assinados em `2025-09/xmls_setembro_82_corrigidos`.
- CPF de recibo `06701349960` ficou pendente inicialmente porque o S-1210 local havia sido excluido por S-3000.
- Dois CPFs usaram fonte rescisoria local S-2299/S-2399 para `detVerbas` (`15867162800`, `53902278838`); sem fallback por S-1210 anterior.
- Protocolos S-1210: `1.1.202605.0000000013221851751`, `1.1.202605.0000000013221853136`, `1.1.202605.0000000013221854766`.
- Resultado S-1210 planSaude: 82/82 aceitos, V2 parcial `1058 ok`, `1 erro`.
- Recibo informado para o CPF `06701349960` (`1.1.0000000035183951429`) era um S-3000 que excluiu o S-1210 local `1.1.0000000035182530057`; a retificacao com esse recibo voltou `401/157`, corretamente.
- Foi enviada nova inclusao S-1210 `indRetif=1` para o CPF `06701349960`; protocolo `1.1.202605.0000000013221940347`, recibo `1.1.0000000041100992863`.
- V2 final setembro: `1059 ok`, `0 erro`.
- S-1299 fechamento aceito: protocolo `1.1.202605.0000000013221942257`, recibo `1.1.0000000041101000922`.

## Correcao complementar - Outubro/2025

- Gerados 93 XMLs S-1210 assinados em `2025-10/xmls_outubro_93_corrigidos`.
- A fonte mensal tinha 80 linhas; foi usado o CSV consolidado filtrado por `2025-10`, batendo com os 93 erros vivos no V2.
- Dois CPFs usaram fonte rescisoria local S-2299/S-2399 para `detVerbas` (`27157534894`, `37622574856`); sem fallback por S-1210 anterior.
- Protocolos S-1210: `1.1.202605.0000000013221863880`, `1.1.202605.0000000013221865009`, `1.1.202605.0000000013221866118`.
- Resultado S-1210: 93/93 aceitos, V2 final `1226 ok`, `0 erro`.
- S-1299 fechamento aceito: protocolo `1.1.202605.0000000013221867451`, recibo `1.1.0000000041100640007`.

## Correcao complementar - Novembro/2025

- Gerados 91 XMLs S-1210 assinados em `2025-11/xmls_novembro_91_corrigidos`.
- Foi usado o CSV consolidado filtrado por `2025-11`; o CSV mensal continha erros antigos de folha fechada ja superados pelo retry/reabertura.
- Sem fallback e sem fonte rescisoria: todas as rubricas vieram de S-1200 local.
- Protocolos S-1210: `1.1.202605.0000000013221875083`, `1.1.202605.0000000013221875966`, `1.1.202605.0000000013221877059`.
- Resultado S-1210: 91/91 aceitos, V2 final `1284 ok`, `0 erro`.
- S-1299 fechamento aceito: protocolo `1.1.202605.0000000013221877950`, recibo `1.1.0000000041100699587`.

## Pendencia residual

Nao ha pendencia residual em junho-novembro. Setembro foi zerado e fechado apos identificar que o recibo informado era S-3000 de exclusao e reenviar o S-1210 como inclusao.

## Artefatos

- CSV consolidado de erros finais: C:\Users\xandao\Documents\GitHub\Easy-Social\relatorio_ana\OBJETIVA_JUN_NOV_2025\erros_s1210_objetiva_jun_nov_2025.csv
- XMLs de dry-run e JSONs mensais: pasta OBJETIVA_JUN_NOV_2025.
