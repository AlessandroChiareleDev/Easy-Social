-- Check if CPF has events in 2025-01 (potential blocker period)
SELECT id, tipo_evento, per_apur, nr_recibo, cd_resposta, dt_processamento
FROM explorador_eventos
WHERE cpf = '09820037735' AND per_apur = '2025-01'
ORDER BY tipo_evento;

-- Get S-1200 data (most recent, id 364624)
SELECT dados_json FROM explorador_eventos WHERE id = 364624;

-- Get S-1210 data (most recent, id 379964)
SELECT dados_json FROM explorador_eventos WHERE id = 379964;

-- Get S-5002 data (most recent, id 290228)
SELECT dados_json FROM explorador_eventos WHERE id = 290228;
