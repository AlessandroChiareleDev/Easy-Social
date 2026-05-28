# Relatorio - APPA e Chain Walk legado

Data: 2026-05-28

## Resumo executivo

APPA e a primeira empresa do sistema: `empresa_id=1`, CNPJ `05.969.071/0001-10`, identificada nos documentos como APPA Servicos Temporarios e Efetivos LTDA.

A APPA nao aparece no Chain Walk V2 (`timeline_mes`, `timeline_envio`, `timeline_envio_item`) porque o fluxo dela foi construido antes do modelo novo. O historico operacional da APPA vive no repositorio S-1210 legado, principalmente em `s1210_cpf_scope`, `s1210_cpf_envios`, `s1210_xlsx`, `s1210_operadoras`, `pipeline_runs`, `pipeline_cpf_results` e no cache em memoria/ZIP do `bot_api` antigo.

Nao foi feita nenhuma chamada ao eSocial nesta investigacao. A analise foi somente leitura em codigo e banco.

## Evidencias de banco

Conexao usada pelo V2 para APPA: `search_path = appa, public`.

Contagem de tabelas no schema `appa`:

| Tabela                 |  Linhas | Leitura                                                          |
| ---------------------- | ------: | ---------------------------------------------------------------- |
| `timeline_mes`         |       0 | Chain Walk V2 nao foi populado para APPA                         |
| `timeline_envio`       |       0 | Sem bolinhas/envios V2                                           |
| `timeline_envio_item`  |       0 | Sem status por CPF no modelo V2                                  |
| `empresa_zips_brutos`  |       0 | Nao ha ZIP bruto no modelo V2                                    |
| `explorador_eventos`   | 375.985 | Existe explorador antigo/importado, mas sem vinculo por `zip_id` |
| `s1210_cpf_scope`      | 110.651 | Escopo legado vivo por CPF/mes/lote                              |
| `s1210_cpf_envios`     | 223.837 | Historico legado vivo de envios/recibos/status                   |
| `s1210_cpf_recibo`     |       0 | Cache planejado, nao usado como fonte real                       |
| `s1210_xlsx`           |      32 | Planilhas oficiais/virtuais ingeridas                            |
| `s1210_operadoras`     |  18.434 | Dados de plano por CPF/rubrica/operadora                         |
| `pipeline_runs`        |      29 | Execucoes antigas do pipeline                                    |
| `pipeline_cpf_results` | 113.025 | Cadeias antigas por recibo/pagamentos                            |

Ponto critico: `appa.explorador_eventos` tem eventos, mas a consulta mostrou `zip_id` nulo para os eventos principais analisados. Ja `empresa_zips_brutos` tem zero linhas. O backfill V2 (`backfill_chain.py`) depende do join `explorador_eventos -> empresa_zips_brutos` por `zip_id`, portanto nao encontra grupos para criar `timeline_mes`.

Exemplos do explorador antigo sem `zip_id`:

| Evento | Periodo | Linhas |   CPFs | Com `zip_id` |
| ------ | ------- | -----: | -----: | -----------: |
| S-1210 | 2025-01 | 22.684 | 11.290 |            0 |
| S-5002 | 2025-01 | 34.081 | 11.290 |            0 |
| S-1210 | 2025-02 | 21.603 | 10.800 |            0 |
| S-5002 | 2025-02 | 32.406 | 10.800 |            0 |
| S-1210 | 2025-09 | 15.542 |  7.771 |            0 |
| S-5002 | 2025-09 | 23.313 |  7.771 |            0 |

## Evidencias do escopo legado

APPA tem escopo por mes e lote em `s1210_cpf_scope`. Alguns exemplos:

| Periodo | Lote |   CPFs |
| ------- | ---: | -----: |
| 2025-01 |    1 | 11.290 |
| 2025-02 |    1 |  9.471 |
| 2025-02 |    2 |  1.390 |
| 2025-02 |    3 |    737 |
| 2025-02 |    4 |      2 |
| 2025-03 |    1 |  8.164 |
| 2025-03 |    2 |  1.395 |
| 2025-03 |    3 |  1.624 |
| 2025-04 |    1 |  7.142 |
| 2025-04 |    2 |  1.376 |
| 2025-04 |    3 |  1.498 |
| 2025-12 |    1 |  5.083 |
| 2025-12 |    2 |  1.001 |
| 2025-12 |    3 |  1.339 |

O estado atual por CPF/lote e calculado no V2 anual por uma compatibilidade especial: se `empresa_id=1`, o backend primeiro le `s1210_cpf_scope` e `s1210_cpf_envios`. So se esse caminho nao retornar dados ele tenta o fallback V2 por `timeline_mes`.

## Como o Chain Walk da APPA funcionava

Existem dois mecanismos legados, ambos fora de `timeline_*`:

1. `bot_api` / `/api/s1210-repo/enviar-lote-cpfs`
   - Indexa ZIP local em memoria por periodo (`_CACHE_RECIBOS`).
   - Busca o S-1210 original do CPF no ZIP (`_buscar_s1210_unico`).
   - Usa o recibo do ZIP como base.
   - Tenta encadear para o recibo ativo via `_buscar_recibo_ativo`.
   - Permite `recibo_override_por_cpf`, que bypassa o chain walk quando a Ana fornece recibo ativo.
   - Persiste resultado em `s1210_cpf_envios`.

2. `s1210_batch._buscar_recibo_ativo`
   - Le `pipeline_cpf_results` por CPF, apenas status `ok`.
   - Compara a lista de `ideDmDev` dos pagamentos do ZIP com a lista persistida nos resultados anteriores.
   - Monta mapa `nr_recibo_original -> nr_recibo_novo`.
   - Anda pela cadeia ate achar o ultimo recibo conhecido.
   - Se nao encontra cadeia compativel, volta para o recibo do ZIP.

Ou seja: para APPA, o chain walk historico e um encadeamento por `pipeline_cpf_results`/`s1210_cpf_envios` + ZIP local/cache, nao por `timeline_mes`/`timeline_envio`.

## Por que o Chain Walk V2 nao enxerga APPA

O backfill V2 atual faz:

1. Agrupa `explorador_eventos` S-1210 por `empresa_zips_brutos.empresa_id` e `per_apur`.
2. Cria `timeline_mes`.
3. Cria `timeline_envio` sequencia 0, tipo `zip_inicial`.
4. Preenche `origem_envio_id` em `explorador_eventos`.
5. Conecta retificacoes internas por `referenciado_recibo -> nr_recibo`.

Na APPA isso nao roda porque falta o requisito inicial: nao ha `empresa_zips_brutos` e os eventos antigos nao tem `zip_id`. Portanto o join inicial do backfill retorna zero grupos.

## Estado tecnico atual

- APPA tem dados operacionais completos no legado.
- APPA nao tem bolinhas Chain Walk V2.
- A tela anual V2 ja tem desvio intencional para APPA: usa `s1210_cpf_scope` e `s1210_cpf_envios` antes do fallback `timeline_*`.
- A regua do Chain Walk V2 (`/api/explorador/timeline/meses`) vai retornar vazio para APPA, porque ela depende exclusivamente de `timeline_mes`.
- `s1210_cpf_recibo` foi planejada como cache de recibo, mas esta vazia e nao deve ser tratada como fonte atual da verdade.

## Riscos de migrar APPA para `timeline_*`

Nao e seguro simplesmente rodar `backfill_chain.backfill_empresa(1)` esperando resolver, porque:

- o backfill atual depende de `empresa_zips_brutos`, que esta vazio;
- `explorador_eventos` antigo nao tem `zip_id`;
- o escopo oficial da APPA e XLSX/lote, nao apenas XML bruto;
- APPA tem quatro lotes operacionais e o Chain Walk V2 MVP trabalha como um fluxo mensal unico, com lote dinamico simples;
- APPA usa historico de tentativas em `s1210_cpf_envios`, inclusive `na`, `ok`, `erro`, override de recibo e resultados duplicados por tentativa;
- `pipeline_cpf_results` nao e equivalente direto a `timeline_envio_item`.

## Caminhos possiveis

### Caminho A - manter APPA no legado com adaptador de leitura

Recomendado para curto prazo.

- Manter APPA fora do backfill V2.
- Criar/ajustar endpoints de Chain Walk para, quando `empresa_id=1`, ler `s1210_cpf_scope` + ultimo estado em `s1210_cpf_envios`.
- Exibir no frontend como `Chain Walk legado APPA` ou `Repositorio APPA`, sem fingir que ha `timeline_mes` real.
- Preserva todos os numeros atuais sem migração destrutiva.

### Caminho B - materializar APPA em `timeline_*` sintetico

Possivel, mas exige um script especifico.

Etapas sugeridas:

1. Criar `timeline_mes` para cada `per_apur` presente em `s1210_cpf_scope`.
2. Criar `timeline_envio` sequencia 0 por mes/lote ou por mes com resumo por lote.
3. Converter o ultimo estado por CPF de `s1210_cpf_envios` para `timeline_envio_item`.
4. Definir como mapear os 4 lotes APPA em um modelo que hoje nao tem lote como dimensao nativa em `timeline_mes`.
5. Preservar `nr_recibo_usado`, `nr_recibo_novo`, `codigo_resposta`, `descricao_resposta`, XML enviado/resposta quando existir.
6. Marcar a origem como `legacy_appa_import` para nao misturar com envios V2 reais.

Esse caminho e bom se a meta for unificar visualmente APPA/SOLUCOES/CTE/OBJETIVA, mas precisa de desenho antes de escrever dados.

### Caminho C - reimportar ZIPs APPA no modelo V2

Nao recomendado como primeira opcao.

- Exigiria localizar ZIPs originais, subir em `empresa_zips_brutos` e reextrair.
- Pode gerar divergencia entre XML bruto e escopo oficial da Ana.
- Nao recupera automaticamente `s1210_cpf_envios`/tentativas antigas.

## Conclusao

APPA nao esta sem historia. Ela esta sem `timeline_*` porque nasceu antes do Chain Walk V2 e o fluxo dela foi projetado ao redor de XLSX oficial, lotes 1/2/3/4, ZIP local/cache e tabelas `s1210_*`/`pipeline_*`.

Para nao quebrar a missao APPA, o caminho seguro e tratar APPA como `Chain Walk legado` no curto prazo e so migrar para `timeline_*` com um script de materializacao controlado, sem apagar nem sobrescrever as tabelas legadas.
