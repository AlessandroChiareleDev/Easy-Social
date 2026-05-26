# Relatorio dos 893 erros reais atuais - S-1210 SOLUCOES

## Universo analisado

Foram analisados os erros reais atuais de S-1210 da SOLUCOES, empresa_id=2, em todos os meses existentes na timeline. O criterio foi latest por CPF x mes x evento: se um CPF teve erro antigo mas depois foi corrigido, ele nao entra no universo atual.

Ficaram fora da conta: status `sucesso` e codigo `202`, porque `202` e evento aceito com advertencia, nao erro operacional bloqueante.

Total do universo: **893 erros reais atuais**.

## Categorias do grafico

| Categoria | Quantidade | Percentual |
|---|---:|---:|
| Plano de saude coletivo ausente | 754 | 84.4% |
| Pensao alimenticia - beneficiarios ausentes | 106 | 11.9% |
| Dependente/IRRF - CPF dependente invalido ou sem infoDep | 21 | 2.4% |
| Recibo anterior nao localizado | 12 | 1.3% |

## Distribuicao por mes

| Mes | Quantidade | Percentual do total |
|---|---:|---:|
| 2025-02 | 114 | 12.8% |
| 2025-03 | 150 | 16.8% |
| 2025-04 | 109 | 12.2% |
| 2025-05 | 106 | 11.9% |
| 2025-06 | 109 | 12.2% |
| 2025-07 | 108 | 12.1% |
| 2025-09 | 101 | 11.3% |
| 2025-10 | 96 | 10.8% |

## Texto explicando a imagem

A pizza mostra que o universo atual de erros e muito concentrado: **860 de 893 erros (96.3%)** estao nos dois blocos esperados, plano de saude e pensao alimenticia.

O maior grupo e **Plano de saude coletivo ausente**, com **754 ocorrencias (84.4%)**. O segundo e **Pensao alimenticia - beneficiarios ausentes**, com **106 ocorrencias (11.9%)**.

Os outros erros existem, mas sao minoritarios: dependente/IRRF e recibo anterior nao localizado. Eles devem ser tratados em uma frente separada, porque nao sao o mesmo tipo de correcao de plano/pensao.
