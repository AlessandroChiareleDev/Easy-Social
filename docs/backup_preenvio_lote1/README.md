# Backup Pre-envio Lote 1 (Estado 0)

Este diretorio guarda o backup operacional do preparo do Lote 1 por mes, antes de qualquer envio.

## O que tem aqui

- Resumo geral do preparo por mes:
  - [lote1_resumo_geral.json](lote1_resumo_geral.json)
- Resumo geral do estado 0 por mes:
  - [lote1_estado0_resumo_geral.json](lote1_estado0_resumo_geral.json)
- Resumos por mes:
  - [lote1_2025-02_resumo.json](lote1_2025-02_resumo.json)
  - [lote1_2025-03_resumo.json](lote1_2025-03_resumo.json)
  - [lote1_2025-04_resumo.json](lote1_2025-04_resumo.json)
- Manifests de estado 0 por mes:
  - [lote1_2025-02_estado0_manifest.json](lote1_2025-02_estado0_manifest.json)
  - [lote1_2025-03_estado0_manifest.json](lote1_2025-03_estado0_manifest.json)
  - [lote1_2025-04_estado0_manifest.json](lote1_2025-04_estado0_manifest.json)

## Para que serve

- Prova de estado pre-envio por mes.
- Referencia de rollback operacional.
- Base para processamento em batches de 50 sem misturar meses.

## Observacao

Os arquivos grandes (base completa, snapshots detalhados e batches) ficam no armazenamento local de trabalho para nao inflar o repositorio.
