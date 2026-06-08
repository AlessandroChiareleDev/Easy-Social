# Objetiva - Execucao S-1210 Jan-Mai/2025

Operacao em producao concluida em 2026-05-28. Nao foram feitas consultas de Download/Identificadores; apenas envio de lotes S-1210/S-1299 e consulta dos protocolos enviados.

## Resultado final no V2

| Periodo | CPFs | OK | Erro | Fechado | Recibo S-1299 |
|---|---:|---:|---:|---:|---:|
| 2025-01 | 806 | 806 | 0 | sim | 1.1.0000000041099163346 |
| 2025-02 | 887 | 887 | 0 | sim | 1.1.0000000041099250033 |
| 2025-03 | 982 | 982 | 0 | sim | 1.1.0000000041099341018 |
| 2025-04 | 986 | 986 | 0 | sim | 1.1.0000000041099479782 |
| 2025-05 | 840 | 840 | 0 | sim | 1.1.0000000041099502997 |

## Envios corretivos S-1210

| Periodo | XMLs corretivos | Protocolos | Resultado |
|---|---:|---|---|
| 2025-01 | 70 | 1.1.202605.0000000013221570765; 1.1.202605.0000000013221604564 | 70 aceitos |
| 2025-02 | 67 | 1.1.202605.0000000013221622926; 1.1.202605.0000000013221623984 | 67 aceitos |
| 2025-03 | 72 | 1.1.202605.0000000013221642355; 1.1.202605.0000000013221643079 | 72 aceitos |
| 2025-04 | 90 | 1.1.202605.0000000013221667954; 1.1.202605.0000000013221668827; 1.1.202605.0000000013221669713 | 90 aceitos |
| 2025-05 | 60 | 1.1.202605.0000000013221672288; 1.1.202605.0000000013221673050 | 60 aceitos |

## Fechamentos S-1299

| Periodo | Protocolo | Recibo | Resultado |
|---|---|---|---|
| 2025-01 | 1.1.202605.0000000013221609172 | 1.1.0000000041099163346 | aceito |
| 2025-02 | 1.1.202605.0000000013221626051 | 1.1.0000000041099250033 | aceito |
| 2025-03 | 1.1.202605.0000000013221644041 | 1.1.0000000041099341018 | aceito |
| 2025-04 | 1.1.202605.0000000013221670404 | 1.1.0000000041099479782 | aceito |
| 2025-05 | 1.1.202605.0000000013221673990 | 1.1.0000000041099502997 | aceito |

## Regras aplicadas

- `dtPgto` e `infoPgto` foram preservados do S-1210 local.
- `planSaude` foi montado a partir do S-1200 local por CPF + `ideDmDev`.
- Rubricas: `516/605/775` = SB Saude `28633372000174` / ANS `421154`; `522/619/774` = NEW LEADER `02127779000136` / ANS `364592`.
- Fallback local usado apenas quando o S-1200 exato nao existia: `17730608804` em marco; `30063798883` e `36136987813` em abril.

Artefatos principais: `xmls_janeiro_70_corrigidos`, `xmls_fevereiro_67_corrigidos`, `xmls_marco_72_corrigidos`, `xmls_abril_90_corrigidos`, `xmls_maio_60_corrigidos`.
