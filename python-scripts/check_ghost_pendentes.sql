-- Rubricas que foram consultadas com sucesso mas estão pendentes
SELECT ce.cod_rubrica, ce.envio_status, ce.corrigido,
       ee.status AS envio_tbl_status, 
       (ee.recibo_consulta::json->>'sucesso')::text AS consulta_ok,
       ee.nr_recibo
FROM cruzamento_eb ce
JOIN esocial_envios ee ON ce.cod_rubrica = ANY(
    ARRAY(SELECT jsonb_array_elements_text(ee.rubrica_ids::jsonb))
)
WHERE ce.envio_status = 'pendente'
  AND ee.nr_recibo IS NOT NULL
LIMIT 20;
