# SOLUCOES Agosto/2025 - fechamento tecnico 543/1089

Gerado em: 18/05/2026 15:41

## Rodada executada

- Escopo: somente S-1210 de Agosto/2025, empresa SOLUCOES, producao.
- Nao foi feita consulta Download/Identificadores; apenas EnviarLoteEventos e polling dos protocolos dos envios executados.
- S-1200 nao foi tocado.

| Envio | Itens | Sucesso | Nao sucesso | Protocolos |
|---:|---:|---:|---:|---|
| 902 | 1 | 1 | 0 | 1.1.202605.0000000013176686331 |
| 903 | 10 | 10 | 0 | 1.1.202605.0000000013176700095 |
| 904 | 44 | 43 | 1 | 1.1.202605.0000000013176712677, 1.1.202605.0000000013176714318, 1.1.202605.0000000013176717205, 1.1.202605.0000000013176719831, 1.1.202605.0000000013176722775 |
| 905 | 1 | 1 | 0 | 1.1.202605.0000000013176763242 |
| 906 | 10 | 10 | 0 | 1.1.202605.0000000013176772628 |
| 907 | 103 | 103 | 0 | 1.1.202605.0000000013176782696, 1.1.202605.0000000013176784724, 1.1.202605.0000000013176786697, 1.1.202605.0000000013176788694, 1.1.202605.0000000013176790654, 1.1.202605.0000000013176792429, 1.1.202605.0000000013176794137, 1.1.202605.0000000013176796641, 1.1.202605.0000000013176800267, 1.1.202605.0000000013176804129, 1.1.202605.0000000013176805749 |

## Resultado

- 1089: zerado. Foram 54 sucessos; 1 CPF virou 459 por recibo antigo/stale.
- 543: resolvidos 114 CPFs seguros; restaram 3 CPFs com problema real de dependente/cpfDep.
- Total de sucessos nesta rodada: 168 S-1210.
- Painel atual Agosto: ok=15005, erro=213, aceito_com_aviso=105, na=277.

## Falhas da rodada

| Envio | CPF | Status | Codigo | Recibo usado | Mensagem curta |
|---:|---|---|---|---|---|
| 904 | 02521004502 | erro_esocial | 401 | 1.1.0000000034695408170 | 401: Conteudo do evento inválido. / - 459: Não foi localizado um evento para o recibo de entrega informado ou o mesmo foi excluído/retificado. Ação Sugerida: Deverá existir um Evento já recebido, "Ativo" (não excluído ou |

## Pendencias atuais

| Grupo | Quantidade | Observacao |
|---|---:|---|
| Plano de saude | 99 | Aguardando dados da Jaque. |
| Pensao alimenticia | 4 | Aguardando dados da Jaque. |
| Aviso 202/1863 | 105 | XML e ajuste local existem, mas falta recibo ativo; 105/105 xml_retorno_oid apontam para large objects ausentes. |
| 543 remanescente | 3 | CPFs com cpfDep/dedDepen problematica: 02077635185, 02165214165, 02170925198. |
| 1089 | 0 | Zerado. |
| 459 novo | 1 | CPF 02521004502; ZIP latest tem recibo que voltou stale. |
| Dependente invalido 1861 | 1 | CPF 81529368553; precisa CPF dependente correto/cadastro. |

## Proximo passo seguro

- Nao insistir nos 202 sem recibo ativo; isso vira 459.
- Nao reenviar os 3 de 543 sem corrigir cpfDep/dedDepen.
- Para limpar o restante tecnico, precisamos de fonte de recibo ativo para 202 e para o CPF 02521004502, ou autorizacao explicita para consulta pontual de recibos no eSocial.
