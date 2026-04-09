-- Get COMPLETE S-5002 json for CPF (all fields, not truncated)
SELECT id, LENGTH(dados_json::text) as json_size, dados_json
FROM explorador_eventos
WHERE cpf = '09820037735' AND tipo_evento = 'S-5002'
ORDER BY id DESC LIMIT 1;

-- Check if there are separate mensal vs 13o events
SELECT id, tipo_evento, per_apur, nr_recibo, id_evento,
       SUBSTRING(dados_json::text, 1, 300) as preview
FROM explorador_eventos
WHERE cpf = '09820037735'
ORDER BY tipo_evento, id;

-- Check for any 13o-related S-1200 (look for per_apur patterns)
SELECT id, tipo_evento, per_apur, nr_recibo, dados_json::text
FROM explorador_eventos
WHERE cpf = '09820037735' AND tipo_evento = 'S-1200'
ORDER BY id;
