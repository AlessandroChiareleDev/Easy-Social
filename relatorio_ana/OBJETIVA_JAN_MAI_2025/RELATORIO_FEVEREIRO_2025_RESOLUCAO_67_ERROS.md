# Objetiva - Fevereiro/2025 - resolucao dos 67 erros

## Entregaveis finais

- `xmls_fevereiro_67_corrigidos/OBJETIVA_2025-02_67_XMLS_CORRIGIDOS_ASSINADOS.zip`: pacote final com 67 XMLs S-1210 assinados.
- `xmls_fevereiro_67_corrigidos/01_plano_saude_retificacao/`: 67 XMLs de retificacao com `indRetif=2`, `nrRecibo` original e `planSaude` inserido.
- `xmls_fevereiro_67_corrigidos/manifest_67_xmls_corrigidos.json`: manifesto de auditoria com CPF, caminho do XML, `dtPgto`, rubricas usadas, origem local S-1200 e hash SHA-256.
- `xmls_fevereiro_67_corrigidos/retorno_envio_67_fevereiro/resultado_envio_67_fevereiro.json`: retorno parseado do envio em producao e persistencia no V2.
- `fechamento_fevereiro_s1299/manifest_fechamento_s1299_fevereiro_objetiva.json`: manifesto do S-1299 de fechamento de fevereiro aceito em producao.
- `gerar_xmls_fevereiro_67_corrigidos.py`: script local reproduzivel que gerou o pacote.
- `enviar_67_fevereiro_persistir_v2.py`: script que enviou os 67 XMLs e persistiu os resultados no V2.
- `enviar_fechamento_fevereiro_objetiva_s1299.py`: wrapper de fechamento S-1299 de fevereiro.

## Resultado validado

- Total original de erros em fevereiro: 67.
- Categoria dos 67 erros: `plano_saude_coletivo_obrigatorio`.
- XMLs finais gerados: 67.
- XMLs parseados com sucesso: 67.
- XMLs com exatamente uma assinatura XMLDSig: 67.
- Retificacoes de plano de saude: 67.
- XMLs dentro do zip final: 67, mais o manifesto.
- SHA-256 do zip final: `392D04AC14878CBF40F8D6F71D851C182AADC4EEF38ADC8796B6B9B0E5279DC1`.
- Na geracao dos XMLs nao houve consulta, download ou envio ao eSocial; depois, por autorizacao explicita, foram feitos os envios em producao e o fechamento de fevereiro.

## Resultado em producao

- `timeline_envio_id`: `59`.
- Lote 1: 40 XMLs aceitos.
- Protocolo lote 1: `1.1.202605.0000000013221622926`.
- Lote 2: 27 XMLs aceitos.
- Protocolo lote 2: `1.1.202605.0000000013221623984`.
- Total enviado em fevereiro: 67.
- Total aceito em fevereiro: 67.
- Total erro/pendente: 0.
- Front/V2 apos o envio: `887 ok`, `0 erro` em `s1210_anual_overview(2025, 3)` e `s1210_cpfs_do_mes('2025-02', 3, 1)`.

## Fechamento S-1299

- Preflight antes do fechamento: `887` S-1210 com status `sucesso`, `0` pendencias.
- Envio do S-1299: `201 - Lote Recebido com Sucesso.`
- Protocolo S-1299: `1.1.202605.0000000013221626051`.
- Consulta do lote: `201 - Lote processado com sucesso.`
- Resultado do evento: `201 - Sucesso.`
- Recibo de fechamento: `1.1.0000000041099250033`.
- Status persistido no V2: `s1299_fechamento_status.fechado=true`, `origem=s1299_envio`.

## Regra aplicada

- Cada S-1210 foi reconstruido a partir do XML local correspondente ao `nr_recibo_anterior` do erro.
- O `dtPgto` e o bloco `infoPgto` do S-1210 original foram preservados.
- O `planSaude` foi montado com as rubricas locais do S-1200 que batem com o `ideDmDev` do S-1210.
- Periodos S-1200 usados na busca local: `2025-01` e `2025-02`, sempre escolhendo por `ideDmDev` do S-1210.

## Mapeamento aplicado

| Rubrica | Operadora  | CNPJ           | ANS    |
| ------- | ---------- | -------------- | ------ |
| 516     | SB SAUDE   | 28633372000174 | 421154 |
| 605     | SB SAUDE   | 28633372000174 | 421154 |
| 775     | SB SAUDE   | 28633372000174 | 421154 |
| 619     | NEW LEADER | 02127779000136 | 364592 |
| 774     | NEW LEADER | 02127779000136 | 364592 |

## Amostras conferidas

| CPF         | Acao        | dtPgto     | Resultado                                   |
| ----------- | ----------- | ---------- | ------------------------------------------- |
| 01369448503 | Retificacao | 2025-02-06 | SB SAUDE, rubrica 516, `vlrSaudeTit=11.24`. |
| 32540823890 | Retificacao | 2025-02-28 | SB SAUDE, rubrica 516, `vlrSaudeTit=23.00`. |
| 53902278838 | Retificacao | 2025-02-06 | SB SAUDE, rubrica 516, `vlrSaudeTit=27.20`. |
