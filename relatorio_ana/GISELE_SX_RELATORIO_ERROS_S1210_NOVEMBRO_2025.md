# Relatório Gisele SX — Erros S-1210 Novembro/2025

Gerado em: 2026-05-20T08:25:50

## Resumo executivo

- Empresa: SOLUÇÕES Serviços Terceirizados
- Período: 2025-11
- Total S-1210 tentados no ciclo: 16.254
- Aceitos com recibo: 16.140
- Erros eSocial 401: 114
- Pendente de consulta/transmissão: 0
- XML enviado e retorno armazenados: 16.254/16.254

## Que significa o erro 401

No retorno do eSocial, `401` significa `Conteúdo do evento inválido`. Não é falha de login nem queda de transmissão: o eSocial recebeu o XML S-1210, validou o conteúdo e recusou por regra de layout/dados.

## Quebras por causa

| Causa | Quantidade | Percentual dos 114 |
|---|---:|---:|
| Plano de saúde coletivo ausente | 105 | 92.11% |
| Recibo anterior não localizado/retificado | 6 | 5.26% |
| Beneficiário de pensão alimentícia ausente | 2 | 1.75% |
| CPF de dependente inválido | 1 | 0.88% |

## Interpretação operacional

- A maior concentração está em plano de saúde coletivo ausente: o evento possui condição que exige o grupo de plano de saúde no S-1210, mas o grupo não veio preenchido.
- Os casos de recibo anterior não localizado/retificado são retificações apontando para recibo que o eSocial não considera ativo.
- Os casos de pensão alimentícia indicam rubrica/dado que exige beneficiário da pensão, mas o grupo não veio preenchido.
- O caso de CPF de dependente inválido indica dependente não reconhecido no RET/eSocial ou não informado corretamente no próprio evento.

## CPFs por causa

### Beneficiário de pensão alimentícia ausente (2)

08551918486, 08617192984

### CPF de dependente inválido (1)

81529368553

### Plano de saúde coletivo ausente (105)

00555440370, 02346385832, 02713285844, 02979332305, 03476711102, 04205280599, 04224010569, 05104134555, 07463327850, 07634291714, 07863548870, 08865298839
09552153824, 09555377898, 09612497656, 10213292823, 10639034837, 11438810873, 11746677880, 11746946881, 11984250833, 11999740807, 12007949822, 12265702838
12601629827, 12611014809, 13660429805, 13696451800, 13705060821, 13711160832, 14129552899, 14193059804, 14418818839, 15057517805, 15509458828, 17725269835
18401846803, 20178870803, 20315573864, 21288302819, 21777491827, 21804920819, 21899082808, 22229832824, 22455023885, 22617602800, 22730253866, 23357036843
25169797893, 26176873843, 26534955890, 26662467871, 26903366857, 27156659898, 27206786863, 27244289863, 27984880875, 28102078871, 28328079844, 29813948353
29928815895, 30516064215, 30622848895, 30729903877, 30748912894, 30761016848, 30815823851, 30877919895, 31268487880, 31428650806, 31798008874, 32706842822
32875046810, 32945497840, 33030723372, 33387996837, 33593392828, 34228705120, 34917814855, 35716135897, 35747949837, 35791396813, 36969401863, 36984839807
37495188820, 37824282856, 38678364858, 40191479810, 41190097850, 42526219841, 44987210800, 49107771134, 51109062893, 51773791168, 61623830400, 73425230115
73902209372, 79204775149, 84195940168, 84378093120, 85400360378, 85472026172, 87041065472, 90578570904, 93707908100

### Recibo anterior não localizado/retificado (6)

00426401646, 00548440298, 01556900350, 03568399237, 04380956776, 06553932182

## Distribuição por envio

| Envio | Erros |
|---:|---:|
| 980 | 3 |
| 986 | 1 |
| 992 | 1 |
| 995 | 1 |
| 997 | 1 |
| 1000 | 1 |
| 1001 | 1 |
| 1006 | 2 |
| 1007 | 1 |
| 1012 | 1 |
| 1021 | 1 |
| 1026 | 1 |
| 1027 | 1 |
| 1029 | 1 |
| 1032 | 1 |
| 1033 | 1 |
| 1034 | 1 |
| 1037 | 1 |
| 1038 | 2 |
| 1041 | 1 |
| 1043 | 1 |
| 1048 | 1 |
| 1049 | 2 |
| 1050 | 3 |
| 1051 | 1 |
| 1052 | 2 |
| 1056 | 4 |
| 1057 | 2 |
| 1058 | 1 |
| 1060 | 1 |
| 1061 | 1 |
| 1066 | 1 |
| 1067 | 1 |
| 1069 | 3 |
| 1070 | 4 |
| 1071 | 3 |
| 1072 | 1 |
| 1073 | 1 |
| 1074 | 2 |
| 1075 | 5 |
| 1076 | 1 |
| 1077 | 2 |
| 1079 | 2 |
| 1080 | 7 |
| 1081 | 2 |
| 1082 | 1 |
| 1083 | 4 |
| 1084 | 2 |
| 1085 | 1 |
| 1087 | 1 |
| 1088 | 3 |
| 1089 | 2 |
| 1090 | 1 |
| 1091 | 1 |
| 1092 | 1 |
| 1094 | 1 |
| 1095 | 1 |
| 1097 | 1 |
| 1100 | 1 |
| 1104 | 1 |
| 1106 | 2 |
| 1112 | 1 |
| 1120 | 2 |
| 1124 | 1 |
| 1126 | 1 |
| 1129 | 2 |
| 1130 | 2 |
| 1133 | 1 |
| 1135 | 1 |
| 1138 | 1 |

## Arquivo analítico

CSV detalhado: `GISELE_SX_ERROS_S1210_NOVEMBRO_2025.csv`

## Próxima ação sugerida

Corrigir as bases de plano de saúde/pensão/dependentes e os 6 recibos anteriores antes de nova tentativa desses 114 CPFs. O fechamento S-1299 pode seguir com os eventos aceitos; estes 114 ficam como exceções de dados para tratamento posterior.
