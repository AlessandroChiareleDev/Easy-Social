# Objetiva - Dezembro/2025 - Ciclo 100 S-1210

Data da execucao: 2026-05-27

Empresa: Objetiva, CNPJ 10.874.523/0001-10, V2 `empresa_id=3`, schema `objetiva`.

## Resumo executivo

O ciclo de 100 CPFs foi executado em producao e parou exatamente no limite combinado.

Resultado final:

- Reabertura S-1298 de dezembro confirmada com recibo antes do S-1210.
- S-1210 tentados: 100 CPFs.
- Sucesso: 98.
- Erros: 2.
- Pendente de consulta: 0.
- Taxa de nao-sucesso: 2,00%.
- Trava de 20%: nao acionada.
- CPFs restantes no escopo dezembro: 1.184.

Conclusao: o ciclo 100 passou com folga em relacao a trava de erro. Nao avancei para 500 porque a instrucao era parar no 100 e reportar velocidade/taxa.

## Reabertura S-1298

Antes do S-1210 foi enviado S-1298 para `2025-12`.

- Evento: `ID1108745230000002026052702233800001`
- Protocolo: `1.1.202605.0000000013210362404`
- Codigo: `201`
- Descricao: `Sucesso.`
- Recibo S-1298: `1.1.0000000041038424835`
- Tentativas de consulta do protocolo: 1

Isso evitou repetir o problema de novembro, quando parte dos S-1210 foi enviada antes de a reabertura estar efetivamente confirmada e voltou com folha fechada.

## Envio S-1210

Configuracao usada:

- `workers=1`
- `batch_size=50`
- `pular_ja_tentados=True`
- Trava: parar se taxa acumulada de nao-sucesso ultrapassar 20%.

### Bloco 1

- `timeline_envio_id=29`
- Protocolo: `1.1.202605.0000000013210363011`
- Tentados: 50
- Sucesso: 48
- Erro: 2
- Pendente de consulta: 0
- Tempo: 66,6s
- Velocidade: ~45,6 CPFs/min
- Taxa do bloco: 4,00%

### Bloco 2

- `timeline_envio_id=30`
- Protocolo: `1.1.202605.0000000013210364295`
- Tentados: 50
- Sucesso: 50
- Erro: 0
- Pendente de consulta: 0
- Tempo: 67,9s
- Velocidade: ~44,7 CPFs/min
- Taxa do bloco: 0,00%

### Consolidado S-1210

- Tempo S-1210 aproximado: 134,5s
- Velocidade S-1210 aproximada: 44,6 CPFs/min
- Tempo total incluindo S-1298: 151,1s
- Velocidade total incluindo S-1298: 39,7 CPFs/min
- Sucesso consolidado: 98/100
- Nao-sucesso consolidado: 2/100
- Taxa consolidada: 2,00%

## Erros encontrados

### CPF 00257694307 - plano de saude coletivo obrigatorio

- `timeline_envio_id=29`
- `item_id=12131`
- `versao_anterior_id=178123`
- Evento original/head: `ID1108745230000002026011911251000005`
- Recibo usado: `1.1.0000000037276575466`
- Erro: `401 / 8`
- Mensagem: grupo `Plano de saude coletivo` deve ser preenchido.

Auditoria do XML original/head:

- `planSaude`: ausente.
- `infoDepSau`: ausente.
- `infoIRCR`: existe com `tpCR=056107`.
- Pagamentos preservados:
  - `2025-12-05`, `perRef=2025-11`, `ideDmDev=00003351`, `vrLiq=1501.19`
  - `2025-12-19`, `perRef=2025-12`, `ideDmDev=00003445`, `vrLiq=760.56`
  - `2025-12-19`, `perRef=2025`, `ideDmDev=00003390`, `vrLiq=781.27`

Leitura: o XML original que usamos como fonte nao traz `planSaude`. O eSocial, ao validar a retificacao, exige esse grupo para esse CPF. O motor nao tem como inventar CNPJ da operadora, registro ANS e valores por titular/dependente sem fonte externa. Esse e o mesmo tipo de sobra comum nos finais de lote: nao e falha de envio, e ausencia de dado obrigatorio no XML/fonte.

### CPF 00831605588 - recibo nao localizado/ativo

- `timeline_envio_id=29`
- `item_id=12152`
- `versao_anterior_id=176154`
- Evento original/head: `ID1108745230000002026012013152400001`
- Recibo usado: `1.1.0000000037295806756`
- Erro: `401 / 459`
- Mensagem: nao foi localizado evento ativo para o recibo informado, ou o evento foi excluido/retificado.

Auditoria do XML original/head:

- O XML original/head ja e `indRetif=2`.
- O proprio XML traz `nrReciboAtual=1.1.0000000037295806756`.
- O eSocial respondeu que esse recibo nao esta ativo.

Leitura: o banco/ZIP local tem um recibo, mas o Ambiente Nacional considera outro evento como ativo, ou esse recibo foi retificado/excluido depois do ZIP. Para resolver, precisa fonte de recibo ativo posterior: novo ZIP, retorno mais recente, ou consulta autorizada especifica. Nao rodei Download nem ConsultarIdentificadores.

## Por que e comum sobra no final

Depois que o motor esta certo, os erros finais tendem a concentrar em casos que dependem de informacao externa ou estado atualizado do Ambiente Nacional:

- Plano de saude: o eSocial exige `cnpjOper`, `regANS`, `vlrSaudeTit` e, se houver dependente, `cpfDep/vlrSaudeDep`. Se o XML original nao tem esse grupo, o reenvio preserva a ausencia e o eSocial pode rejeitar.
- Recibo ativo: se o recibo do ZIP local nao e mais o ativo no Ambiente Nacional, a retificacao volta `459`.
- Folha fechada: se S-1298 nao estiver confirmado com recibo antes do S-1210, volta `620`. Neste ciclo isso foi prevenido.
- Retornos assíncronos: se o protocolo demora, pode aparecer `pendente_consulta`; neste ciclo nao apareceu.

## Preparacao para 500

Como o ciclo 100 fechou com 2,00% de nao-sucesso e zero pendente, a execucao esta apta tecnicamente para um ciclo maior. A recomendacao conservadora para o proximo passo e:

- Rodar 500 em blocos internos de 50, mantendo guarda de taxa apos cada bloco.
- Manter `workers=1` se a prioridade for menor risco operacional.
- Velocidade esperada com `workers=1`: cerca de 44 a 45 CPFs/min.
- Tempo estimado para 500 S-1210: aproximadamente 11 a 12 minutos, mais overhead.
- Parar imediatamente se a taxa acumulada de nao-sucesso passar de 20%.
- Gerar auditoria dos erros ao final, separando plano de saude, recibo `459`, folha fechada e pendente de consulta.

O estudo de plano de saude deve continuar durante/proximo ao ciclo de 500, comparando CPFs rejeitados contra o XML original/head e verificando se existe `planSaude` ou apenas `infoIRCR`. Neste ciclo, o caso rejeitado por plano nao tinha `planSaude` no XML original.

## Artefatos

- Resultado JSON: `relatorio_ana/OBJETIVA_DEZEMBRO_2025_CICLO100_RESULTADO.json`
- Executor usado: `python-scripts/envio_objetiva_dezembro_ciclo100.py`
