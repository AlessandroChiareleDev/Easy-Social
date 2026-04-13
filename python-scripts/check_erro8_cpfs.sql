-- Buscar CPFs com erro [8] do último pipeline run
SELECT cpf, erro_descricao, nr_recibo_original
FROM pipeline_cpf_results
WHERE status = 'erro'
  AND erro_descricao LIKE '%[8]%'
ORDER BY cpf
LIMIT 60;
