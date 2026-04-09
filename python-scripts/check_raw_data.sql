-- Get raw XML from explorador for S-5002 events of this CPF (they might have full XML)
-- Also check if there's a raw_xml or similar field in explorador_eventos
SELECT id, tipo_evento, 
       SUBSTRING(dados_json::text, 1, 2000) as dados_preview
FROM explorador_eventos
WHERE cpf = '09820037735' AND tipo_evento IN ('S-1210', 'S-1200')
ORDER BY id;

-- Check if there's an "arquivo_origem" field that points to a file
SELECT id, tipo_evento, arquivo_origem, nr_recibo
FROM explorador_eventos
WHERE cpf = '09820037735'
ORDER BY id;
