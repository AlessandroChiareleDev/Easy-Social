# Objetiva - Janeiro/2025 - resolucao dos 70 erros

## Entregaveis finais

- `xmls_janeiro_70_corrigidos/OBJETIVA_2025-01_70_XMLS_CORRIGIDOS_ASSINADOS.zip`: pacote final com 70 XMLs S-1210 assinados.
- `xmls_janeiro_70_corrigidos/OBJETIVA_2025-01_69_XMLS_RESTANTES_APOS_PILOTO.zip`: pacote atualizado para envio dos 69 restantes, sem o CPF piloto ja aceito.
- `xmls_janeiro_70_corrigidos/01_plano_saude_retificacao/`: 69 XMLs de retificacao com `indRetif=2`, `nrRecibo` original e `planSaude` inserido.
- `xmls_janeiro_70_corrigidos/02_recibo_459_inclusao/`: 1 XML de inclusao com `indRetif=1`, sem `nrRecibo`, para o caso de recibo 459.
- `xmls_janeiro_70_corrigidos/manifest_70_xmls_corrigidos.json`: manifesto de auditoria com CPF, caminho do XML, `dtPgto`, rubricas usadas, origem local S-1200 e hash SHA-256.
- `xmls_janeiro_70_corrigidos/manifest_69_restantes_apos_piloto.json`: manifesto atualizado dos 69 XMLs restantes.
- `xmls_janeiro_70_corrigidos/retorno_envio_piloto/10477639828/resultado_envio_piloto.json`: retorno parseado do envio piloto em producao.
- `xmls_janeiro_70_corrigidos/retorno_envio_008_retif_recibo_informado.json`: retorno parseado da retificacao final do CPF `00820996777` com recibo informado pelo usuario.
- `fechamento_janeiro_s1299/manifest_fechamento_s1299_janeiro_objetiva.json`: manifesto do S-1299 de fechamento de janeiro aceito em producao.
- `gerar_xmls_janeiro_70_corrigidos.py`: script local reproduzivel que gerou o pacote.

Os rascunhos JSON/XLSX anteriores foram substituidos. A entrega valida agora e o pacote de XMLs assinados acima.

## Resultado validado

- Total original de erros em janeiro: 70.
- XMLs finais gerados: 70.
- XMLs parseados com sucesso: 70.
- XMLs com exatamente uma assinatura XMLDSig: 70.
- Retificacoes de plano de saude: 69.
- Inclusao para recibo 459: 1.
- XMLs dentro do zip final: 70, mais o manifesto.
- SHA-256 do zip final: `AAD123360B2EA276A8D66618D7B27833D21A8638F4B245B575339BFA4FE7C6BC`.
- Na geracao dos XMLs nao houve consulta, download ou envio ao eSocial; depois, por autorizacao explicita, foram feitos envios em producao para resolver os 70 erros e fechar janeiro.
- Estado final no V2 para janeiro/2025: `806 ok`, `0 erro`, `fechado=true`.

## Resultado final em producao

- Envio piloto CPF `10477639828`: aceito com recibo novo `1.1.0000000041098951355`.
- Envio dos 69 restantes: 68 aceitos de primeira e 1 CPF (`00820996777`) retornou duplicidade quando enviado como inclusao.
- CPF `00820996777`: retificado com o recibo ativo informado pelo usuario, `1.1.0000000039559372733`.
- Resultado do CPF `00820996777`: `201 - Sucesso`, protocolo `1.1.202605.0000000013221604564`, recibo novo `1.1.0000000041099143046`.
- Front/V2 apos a retificacao final: `806 ok`, `0 erro` em `s1210_anual_overview(2025, 3)` e `s1210_cpfs_do_mes('2025-01', 3, 1)`.
- Fechamento S-1299 de janeiro: `201 - Sucesso`, protocolo `1.1.202605.0000000013221609172`, recibo `1.1.0000000041099163346`.
- Status de fechamento persistido em `s1299_fechamento_status`: `fechado=true`, `origem=s1299_envio`.

## Envio piloto em producao

- CPF enviado: `10477639828`.
- XML enviado: `S1210_2025-01_10477639828_plano_saude_retificacao_assinado.xml`.
- Envio do lote: `201 - Lote Recebido com Sucesso.`
- Protocolo: `1.1.202605.0000000013221570765`.
- Consulta do lote: `201 - Lote processado com sucesso.`
- Resultado do evento: `201 - Sucesso.`
- Recibo novo: `1.1.0000000041098951355`.
- Ocorrencias: nenhuma.
- Retornos brutos salvos em `xmls_janeiro_70_corrigidos/retorno_envio_piloto/10477639828/xml_bruto/`.
- A partir deste piloto, nao reenviar o XML do CPF `10477639828` dentro do pacote de 70. Usar o pacote dos 69 restantes.
- SHA-256 do zip dos 69 restantes: `AC6DD03A624AEEE6F5FA32014B0789ED7A5389D8224CDB1608C9FB8587D3CC83`.

## Regra aplicada

- Cada S-1210 foi reconstruido a partir do XML local correspondente ao `nr_recibo_anterior` do erro.
- O `dtPgto` e o bloco `infoPgto` do S-1210 original foram preservados.
- O `planSaude` foi montado com as rubricas locais do S-1200 que batem com o `ideDmDev` do S-1210.
- O erro 459 inicialmente foi gerado como inclusao (`indRetif=1`) em pasta separada; o eSocial retornou duplicidade. A solucao final foi retificar com o recibo ativo informado pelo usuario: `1.1.0000000039559372733`.

## Mapeamento aplicado

| Rubrica | Operadora  | CNPJ           | ANS    |
| ------- | ---------- | -------------- | ------ |
| 516     | SB SAUDE   | 28633372000174 | 421154 |
| 605     | SB SAUDE   | 28633372000174 | 421154 |
| 775     | SB SAUDE   | 28633372000174 | 421154 |
| 619     | NEW LEADER | 02127779000136 | 364592 |
| 774     | NEW LEADER | 02127779000136 | 364592 |

## Amostras conferidas

| CPF         | Acao              | dtPgto     | Resultado                                                                                           |
| ----------- | ----------------- | ---------- | --------------------------------------------------------------------------------------------------- |
| 10477639828 | Retificacao       | 2025-01-06 | SB SAUDE, rubrica 516, `vlrSaudeTit=54.40`.                                                         |
| 32540823890 | Retificacao       | 2025-01-31 | SB SAUDE, rubrica 516, `vlrSaudeTit=23.00`.                                                         |
| 00820996777 | Retificacao final | 2025-01-06 | `indRetif=2`, `nrRecibo=1.1.0000000039559372733`, aceito com recibo novo `1.1.0000000041099143046`. |
