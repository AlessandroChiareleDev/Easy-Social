# SOLUCOES - Agosto/2025 - Pendencias finais para Jaque

Atualizado em: 18/05/2026

## Situacao apos envio das correcoes

Foram processadas as correcoes de Agosto/2025 recebidas da Jaque.

Resultado consolidado dos 99 S-1210 corrigiveis:

| Situacao             | Quantidade |
| -------------------- | ---------: |
| Aceitos pelo eSocial |         98 |
| Pendentes para Jaque |          5 |

## Pendencias que ainda dependem da Jaque

| Grupo                   | Quantidade | O que falta                                                       |
| ----------------------- | ---------: | ----------------------------------------------------------------- |
| Plano de saude coletivo |          4 | Informar CNPJ operadora, registro ANS e valor descontado em folha |
| Pensao alimenticia      |          1 | Informar o CPF correto do beneficiario/alimentando da pensao      |
| Total                   |          5 | Dados externos para nova retificacao S-1210                       |

## Plano de saude coletivo - 4 CPFs

| CPF         | Nome                       | Pendencia                         |
| ----------- | -------------------------- | --------------------------------- |
| 14193059804 | ELIANE CONCEICAO DE SOUSA  | Preencher dados do plano de saude |
| 25585996827 | CLEIA ANTONUCI DE SA SIMON | Preencher dados do plano de saude |
| 30729903877 | NILZA LIMA SEVERO DA SILVA | Preencher dados do plano de saude |
| 38870126404 | MARIA DE FATIMA LIMA       | Preencher dados do plano de saude |

## Pensao alimenticia - 1 CPF

| CPF trabalhador | Nome                        | Pendencia                                                                                                                                                             |
| --------------- | --------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 39428963895     | VANESSA APARECIDA DE MATTOS | Informar CPF correto do beneficiario/alimentando da pensao. O CPF enviado anteriormente era igual ao CPF da propria trabalhadora, e o eSocial rejeitou com 1745/1861. |

## Observacao tecnica

Nao misturar estas pendencias com o aviso 202/1863 de `dedDepen`. Aqui o problema pendente e somente:

- 4 CPFs sem dados de `planSaude`.
- 1 CPF de `penAlim` com CPF do beneficiario incorreto.

O arquivo de agosto na pasta de envio para Jaque foi atualizado para conter somente esses 5 CPFs.
