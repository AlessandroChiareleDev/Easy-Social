# S1210 Anual Perfeito - Arquitetura de Escala (11 meses x 4 lotes)

Data: 2026-04-22
Escopo deste documento: estudo e desenho tecnico. Nao implementa codigo.

## 1. Objetivo de produto

Construir uma pagina unica do S1210 anual que permita:

- Operar 11 meses (fev a dez, sem janeiro).
- Operar 4 lotes por mes com o mesmo padrao de controle ja validado no projeto atual.
- Aceitar carga parcial de dados (ex.: usuario envia apenas Lote 1 de 3 meses no inicio).
- Manter trilha de validacao/vigilancia em tempo real: status por CPF, contadores consistentes, erro explicito, retry controlado.
- Nao povoar meses/lotes sem dados ainda (ficam visiveis, mas em estado sem dados).

## 2. O que ja foi provado e deve ser preservado

Com base no que ja foi construido e testado:

- Modelo por per_apur + lote_num funciona bem para escopo e contadores.
- Batch de 50 CPFs por envelope SOAP aumentou throughput de forma forte e reduziu ruido operacional.
- Fonte de contadores precisa vir de historico de envio (s1210_cpf_envios / view consolidada), nao de tabela auxiliar isolada.
- Nem todo CPF no escopo teorico e enviavel no lote do mes (caso sem operadora / blocklist / nao aplicavel).
- Erros de negocio do eSocial (ex.: buscar recibo sem S-1210 no ZIP) devem ficar explicitamente classificados, nao mascarados como falha tecnica da API.

## 3. Diferenca de input (ponto central)

Sim, a diferenca de input foi entendida e incorporada no desenho:

- O sistema anual NAO pode exigir "11 meses completos" para iniciar.
- O sistema deve aceitar ingestao incremental e incompleta:
  - mes com apenas Lote 1,
  - mes com Lote 1 e 2,
  - mes sem nenhum dado ainda,
  - lote com dados parciais (faltando parte de CPFs),
  - lotes recebidos em datas diferentes.

Regra de ouro:

- O que chegou e valido: entra.
- O que nao chegou: permanece sem dados.
- O que chegou parcial: fica como parcial e auditavel.

## 4. Pagina alvo (UX funcional)

## 4.1 Visao macro anual

Grade 11 x 4:

- Linhas: meses (2025-02 ... 2025-12).
- Colunas: L1, L2, L3, L4.
- Cada celula com estado:
  - sem_dados
  - pronto_para_processar
  - processando
  - concluido
  - concluido_com_erros
  - bloqueado

Cada celula mostra KPIs:

- total_escopo
- ok
- erro
- enviando
- pendente
- nao_aplicavel
- ultimo_processamento
- velocidade media (s/cpf)

## 4.2 Drill-down por celula

Ao clicar em um mes+lote:

- Lista de CPFs com filtros (status, erro, rubrica, tem_operadora, blocklist, data envio).
- Acao em lote: processar pendentes.
- Acao pontual: reenviar CPF.
- Painel de erros por causa raiz.
- Painel de qualidade de dados (faltas de operadora, recibo, rubrica inconsistente).

## 5. Modelo de dados recomendado (evolucao sem quebrar o atual)

A base atual ja esta muito proxima do ideal. O desenho anual precisa formalizar 3 niveis:

## 5.1 Nivel calendario/controle

Tabela nova: s1210_periodo_lote_status

Chave: empresa_id, per_apur, lote_num

Campos sugeridos:

- estado_operacional (sem_dados, pronto, processando, concluido, erro)
- fonte_input (xlsx_ana, carga_manual, import_api)
- cobertura_input (completo, parcial)
- total_escopo
- total_enviavel
- total_nao_aplicavel
- ok
- erro
- enviando
- pendente
- dt_primeira_carga
- dt_ultima_carga
- hash_versao_input
- observacoes

Objetivo: separar "estado do periodo+lote" de "linhas CPF".

## 5.2 Nivel escopo CPF

Reaproveitar s1210_cpf_scope como fonte de universo por mes+lote.

Acrescentar (se nao existir):

- origem_carga (nome do arquivo/fonte)
- carga_id
- escopo_status (ativo, removido, substituido)
- motivo_exclusao (quando aplicavel)

## 5.3 Nivel historico de execucao

Reaproveitar s1210_cpf_envios como trilha oficial de resultado por tentativa.

Acrescentar (se necessario):

- classificacao_erro (dados, regra_esocial, tecnico, timeout, sem_recibo)
- retry_elegivel (bool)
- nao_aplicavel (bool)
- motivo_nao_aplicavel
- correlacao_execucao_id (id da rodada/lote executado)

## 6. Contrato de ingestao anual

Endpoint alvo (conceitual):

- POST /api/s1210-anual/ingest

Payload aceitando lotes e meses misturados:

- empresa_id
- cargas[]
  - per_apur
  - lote_num
  - tipo_input (xlsx, json, csv)
  - arquivo ou dados
  - metadata opcional (versao, origem)

Comportamento:

1. Valida formato e chave de periodo/lote.
2. Gera carga_id.
3. Faz parse para escopo padrao CPF.
4. Upsert em s1210_cpf_scope sem apagar historico de envios.
5. Recalcula s1210_periodo_lote_status.
6. Marca cobertura_input:
   - completo: lote integral do mes presente
   - parcial: lote incompleto
   - sem_dados: nada carregado

Regra critica:

- Nao derrubar dados de meses/lotes ja consolidados ao receber nova carga parcial.
- Versionar entrada por hash para detectar reenvio do mesmo arquivo.

## 7. Execucao anual (orquestracao)

## 7.1 Unidade de execucao

Unidade = (empresa_id, per_apur, lote_num, batch_id)

Cada unidade:

- seleciona apenas CPFs elegiveis (status pendente + enviavel + fora de blocklist + dados minimos ok).
- processa em batch de 50 no padrao atual validado.
- persiste resultado por CPF com idempotencia.

## 7.2 Sequenciamento

Padrao recomendado para estabilidade:

- Paralelismo por mes+lote controlado (max 2 unidades simultaneas por empresa).
- Dentro da unidade: 1 envelope por vez (mantem baixo risco de ocorrencias de concorrencia no eSocial).
- Polling com backoff adaptativo.

## 7.3 Politica de retry

- Retry automatico apenas para erros tecnicos/transitorios.
- Erro de dados fica em fila de correcao (nao martelar eSocial).
- Limite de tentativas por CPF por dia.

## 8. Padrao de validacao e vigilancia (mantido e ampliado)

O sistema anual deve manter 3 camadas de vigilancia:

## 8.1 Validacao de entrada (antes de enviar)

- CPF valido.
- per_apur coerente.
- lote_num valido.
- requisitos por lote:
  - L2/L3 exigem campos de operadora quando aplicavel.
- deduplicacao por CPF+mes+lote.

## 8.2 Validacao de processamento (durante envio)

- checkpoint por etapa (build XML, assinatura, envio SOAP, consulta lote, parse retorno, persistencia).
- medicao de duracao por CPF e por batch.
- classificacao de erro obrigatoria.

## 8.3 Validacao pos-processamento (auditoria)

- reconciliacao de contadores (escopo vs envios vs dashboard).
- amostragem de XML/recibo para qualidade.
- alarme de anomalia (ex.: pico abrupto de erro por rubrica, como visto em abril com rubrica 775).

## 9. Estados sem dados e nao aplicavel (ponto que evita falso pendente)

Para meses/lotes sem input ainda:

- estado = sem_dados
- contadores zerados
- sem pendente artificial

Para CPF no escopo teorico mas nao enviavel no lote do mes:

- status = nao_aplicavel
- motivo obrigatorio (sem_operadora, blocklist, regra_negocio, etc.)
- nao contar como pendente de execucao

Isso evita distorcoes do tipo "pendente eterno".

## 10. API de leitura para o frontend anual

Endpoints alvo (conceituais):

- GET /api/s1210-anual/overview?ano=2025
  - retorna 11 meses x 4 lotes com estado e KPIs
- GET /api/s1210-anual/mes/{per_apur}
  - detalhe dos 4 lotes do mes
- GET /api/s1210-anual/lote/{per_apur}/{lote_num}/cpfs
  - grade de CPFs com filtros
- GET /api/s1210-anual/lote/{per_apur}/{lote_num}/erros
  - distribuicao por causa raiz/rubrica

## 11. Compatibilidade com o que sera enviado depois ("3 meses so Lote 1")

Quando voce enviar dados de 3 meses apenas do Lote 1, o sistema anual deve reagir assim:

- Fev/Mar/Abr L1: populados e processaveis.
- Fev/Mar/Abr L2-L4: sem_dados (ou pronto apenas se ja existir base historica valida).
- Meses restantes (mai..dez): sem_dados.
- Nenhum bloqueio de UI por falta dos 11 meses completos.
- Validacao e vigilancia continuam identicas para o que existir.

Ou seja: input parcial nao quebra o padrao; apenas muda cobertura.

## 12. Migracao em fases (sem big bang)

Fase 0 - Preparacao

- Introduzir s1210_periodo_lote_status e enum de estados.
- Ajustar view de contadores para incluir nao_aplicavel e sem_dados.

Fase 1 - Leitura anual

- Montar endpoint overview anual consumindo dados atuais.
- Renderizar grade 11x4 no frontend (somente leitura).

Fase 2 - Ingestao incremental

- Novo endpoint de ingestao anual (mes/lote parciais).
- Versionamento por hash e carga_id.

Fase 3 - Execucao anual

- Reuso do motor batch50 por unidade mes+lote.
- Fila e scheduler com limites de concorrencia.

Fase 4 - Vigilancia avancada

- Painel de anomalias por rubrica/erro.
- SLA por lote e alerta de regressao.

## 13. Riscos tecnicos e mitigacoes

Risco: mistura de contadores historicos antigos com novo estado anual.
Mitigacao: camada de reconciliacao por view/materialized view com regra unica.

Risco: reingestao parcial apagar escopo antigo indevidamente.
Mitigacao: upsert versionado por carga_id e soft-delete, nunca truncate cego por mes.

Risco: crescimento de volume (11 meses x 4 lotes) gerar lentidao em grid.
Mitigacao: agregacoes precomputadas por periodo+lote e pagina por CPF com cursor.

Risco: erro de classificacao de rubrica inflar taxa de erro operacional.
Mitigacao: etapa de quality gate pre-envio por rubrica/categoria antes de disparar lote.

## 14. Criterios de pronto do S1210 anual perfeito

- Consegue operar 11 meses sem exigir completude inicial.
- Aceita input parcial por mes/lote sem quebrar fluxo.
- Mostra sem_dados e nao_aplicavel corretamente (sem falso pendente).
- Mantem 4 lotes com mesmo controle operacional atual.
- Mantem rastreabilidade por CPF e por tentativa.
- Mantem vigilancia de qualidade e alertas de anomalia.

## 15. Decisao final deste estudo

Sim, e totalmente viavel montar o S1210 anual com o padrao que ja foi construido.

A diferenca de input foi entendida e coberta:

- voce pode mandar primeiro apenas Lote 1 de 3 meses,
- o sistema anual continua consistente,
- e os demais meses/lotes ficam somente como sem_dados ate nova carga.

Isso preserva o padrao de validacao/vigilancia e permite evolucao sem retrabalho estrutural.
