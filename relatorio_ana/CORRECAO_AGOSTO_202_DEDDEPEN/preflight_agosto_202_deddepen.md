# Preflight Agosto/2025 - aviso 202/1863 dedDepen

Gerado em: 2026-05-18T22:40:01

## Regra aplicada

- Corrigir apenas `dedDepen` dos avisos 202/1863.
- Usar dependentes reais confirmados em Julho/2025 e/ou Setembro/2025.
- Ignorar `cpfDep=00000000000`, pois e totalizador/erro de parser.
- Usar valor por dependente limitado a R$ 189,59.
- Nao misturar com plano de saude, pensao alimenticia ou S-1200.

## Resultado local

- CPFs atuais com codigo 202: 105.
- Com `dedDepen` reconstruido por julho/setembro: 35.
- Alta confianca (julho e setembro iguais): 35.
- Media confianca (somente um mes vizinho): 0.
- Divergente/manual: 0.
- Sem prova em julho/setembro: 70.
- Com recibo ativo local ja disponivel: 105.
- Com recibo vindo do front/S-1210 HEAD XML: 105.
- Prontos para XML/envio sem consultar eSocial: 35.

## Fonte de recibo local

Para codigo 202 a timeline nao gravou `nr_recibo_novo`, mas a tela S-1210 anual/lista do mes expoe `nr_recibo_xml` do S-1210 HEAD. Esse valor foi usado como recibo ativo local, amarrado ao XML local importado, sem consulta ao eSocial.

Conclusao apos envio: essa fonte foi suficiente para montar o XML local, mas nao confirmou recibo ativo perante o eSocial. O envio corrigido retornou `401/459` para os 35 CPFs: o recibo informado nao foi localizado como evento ativo ou ja foi excluido/retificado.

## Checagem do mes seguinte

Em 2026-05-18, os ZIPs locais `SOLUCOES_2025-08*.zip` e `SOLUCOES_2025-09*.zip` foram varridos para os 35 CPFs de alta confianca, lendo apenas entradas S-1210 e filtrando `perApur=2025-08`.

- CPFs encontrados nos ZIPs: 35/35.
- Arquivo de auditoria: `relatorio_ana/CORRECAO_AGOSTO_202_DEDDEPEN/scan_zip_recibos_2025_08.json`.
- Resultado: o ZIP do mes seguinte existe e confirma o mesmo recibo historico do HEAD local, por exemplo CPF `02254091786` com `1.1.0000000034695365779` em `SOLUCOES_2025-09(16-30).zip`.
- Esse recibo historico e exatamente o que o eSocial rejeitou nas tentativas 916/917. Portanto, para estes 35 CPFs, o ZIP original do mes seguinte nao contem o recibo ativo gerado apos o envio 202 de maio/2026.

## Causa raiz do recibo ativo ausente

Os itens 202 originais dos 35 CPFs apontam para `xml_retorno_oid`, mas os Large Objects antigos nao existem mais no banco atual. Exemplo: item `1883` do CPF `02254091786` aponta `xml_retorno_oid=319624`, porem o LO nao existe.

O bug de origem estava nos motores `app/envio_teste_100.py` e `app/envio_paralelo_v2.py`: retorno de evento com `cdResposta=202` era gravado como `erro_esocial`, sem preencher `nr_recibo_novo`, mesmo o eSocial emitindo recibo em sucesso com advertencia. Ambos os motores foram corrigidos para tratar `201` e `202` como sucesso com `nr_recibo_novo`; em `202`, a advertencia fica preservada em `erro_codigo/erro_mensagem`.

O sender `python-scripts/enviar_correcao_agosto_202_deddepen.py` tambem foi travado para nao reenviar manifesto baseado em `front_s1210_cpfs_do_mes.nr_recibo_xml`, fonte ja provada invalida para estes CPFs.

## V2 / front / protocolos

Checagem direta no V2 (`empresa_id=2`, schema `solucoes`) em 2026-05-18:

- `s1210_cpf_recibo`: 0 linhas.
- `s1210_cpf_envios`: 0 linhas.
- A tela S-1210 mensal usa `s1210_cpfs_do_mes`; para SOLUCOES ela cai em `explorador_eventos` + `timeline_envio_item`.
- O modal de detalhe tenta `s1210_cpf_recibo`, mas como a tabela esta vazia, tambem cai no recibo mais recente do `explorador_eventos`.
- Para CPF `02254091786`, o V2 mostra `explorador_eventos.id=219047`, recibo `1.1.0000000034695365779`, `cd_resposta=202`, vindo do XML `ID1094455020000002025091819102200012.S-1210.xml`. Esse e o mesmo recibo historico rejeitado em 916/917.

A busca local nos logs do V2 encontrou os protocolos dos envios originais dos 35 CPFs. Arquivo gerado:

- `relatorio_ana/CORRECAO_AGOSTO_202_DEDDEPEN/protocolos_reconsulta_202_deddepen.json`

Resumo desse mapa:

- 35/35 CPFs mapeados para envio, item, batch e protocolo.
- 29 protocolos unicos.
- Exemplo: CPF `02254091786`, envio `20`, item `1883`, rank `311`, batch `B07`, protocolo `1.1.202605.0000000013127100357`.
- Os logs contem os protocolos, mas nao contem os `retornoEvento` completos nem os recibos novos por CPF.

Tambem foi gerada a lista de recibos candidatos locais:

- `relatorio_ana/CORRECAO_AGOSTO_202_DEDDEPEN/recibos_candidatos_locais_202_deddepen.json`
- 35/35 CPFs possuem recibos locais no `explorador_eventos`/ZIP.
- Maximo de 2 recibos por CPF, 67 recibos unicos no total.
- O recibo local mais recente de cada CPF ja foi usado nas tentativas 916/917 e voltou `401/459`.
- O recibo local anterior e versao velha da cadeia, ja retificada pelo recibo mais recente; nao e candidato seguro para novo envio.
- Exemplo CPF `02254091786`: candidatos locais `1.1.0000000034695365779` e `1.1.0000000034619869899`; o primeiro foi testado em 916/917 e rejeitado, o segundo e a versao anterior retificada.

## XMLs gerados

- XMLs unsigned gerados: 35.
- Pasta: `relatorio_ana/CORRECAO_AGOSTO_202_DEDDEPEN/xml_correcao_202_deddepen_unsigned`.
- Manifesto JSON: `relatorio_ana/CORRECAO_AGOSTO_202_DEDDEPEN/manifest_correcao_202_deddepen.json`.
- Manifesto CSV: `relatorio_ana/CORRECAO_AGOSTO_202_DEDDEPEN/manifest_correcao_202_deddepen.csv`.
- Validacao estrutural: 35/35 OK; `indRetif=2`, `perApur=2025-08`, `nrRecibo` do HEAD XML, sem `Signature`, sem `cpfDep=00000000000`, `vlrDedDep <= 189.59`.
- Validacao XSD completa nao executada porque `evtPgtos.xsd` referencia `tipos.xsd`, que nao esta disponivel localmente.

Nenhum envio, download ou consulta ao eSocial foi executado neste preflight.

## Resultado dos envios

- Tentativas 913, 914 e 915: 35/35 rejeitados por `402` devido a XML gerado inicialmente com namespace/envelope de download. Nenhum recibo novo emitido.
- Gerador corrigido e validado em 2026-05-19: 35/35 XMLs agora saem como `<eSocial>` do namespace `evtPgtos`, sem wrapper `retornoProcessamentoDownload`, sem namespace de download, sem `Signature`.
- Tentativa 916, protocolo `1.1.202605.0000000013178500774`: 0 sucesso, 35 erros `401/459`.
- Tentativa 917, protocolo `1.1.202605.0000000013178501058`: 0 sucesso, 35 erros `401/459`.
- Mensagem comum: `Nao foi localizado um evento para o recibo de entrega informado ou o mesmo foi excluido/retificado`.
- Estado local: envios 913 a 917 finalizados como `concluido`; os itens preservam os erros retornados pelo eSocial.

## Teste de recibo informado pelo usuario

Em 2026-05-19 foi feito teste isolado, com 1 CPF, usando recibo informado manualmente pelo usuario:

- CPF: `02254091786`.
- Recibo testado em `nrRecibo`: `1.1.0000000040581570546`.
- Envio local: `918`.
- Protocolo eSocial: `1.1.202605.0000000013178594002`.
- Resultado: `sucesso` 1/1.
- Recibo novo emitido: `1.1.0000000040883704639`.
- Arquivo de resultado: `relatorio_ana/CORRECAO_AGOSTO_202_DEDDEPEN/teste_recibo_override/resultado_teste_recibo_02254091786.json`.

Conclusao: o recibo `1.1.0000000040581570546` era o recibo ativo correto para o CPF `02254091786`; a correcao dedDepen desse CPF foi aceita e agora o novo recibo ativo e `1.1.0000000040883704639`.

## Bloqueio atual

Os 35 XMLs de conteudo estao estruturalmente corretos, mas nao devem ser reenviados com os recibos do S-1210 HEAD local nem com o ZIP original do mes seguinte, pois ambos apontam para o mesmo recibo historico rejeitado. Para destravar, o proximo passo tecnico e reconsultar os 29 protocolos mapeados em `protocolos_reconsulta_202_deddepen.json` e extrair os recibos novos dos retornos `202`; isso chama eSocial e so deve ser feito com autorizacao explicita do usuario.
