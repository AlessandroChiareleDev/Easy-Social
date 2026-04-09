-- Get ALL S-1200 events for this CPF with full JSON
SELECT id, nr_recibo, dados_json
FROM explorador_eventos
WHERE cpf = '09820037735' AND tipo_evento = 'S-1200'
ORDER BY id;

-- Get ALL S-1210 events for this CPF with full JSON
SELECT id, nr_recibo, dados_json
FROM explorador_eventos
WHERE cpf = '09820037735' AND tipo_evento = 'S-1210'
ORDER BY id;

-- Get ALL S-5002 events for this CPF with full JSON
SELECT id, dados_json
FROM explorador_eventos
WHERE cpf = '09820037735' AND tipo_evento = 'S-5002'
ORDER BY id;
