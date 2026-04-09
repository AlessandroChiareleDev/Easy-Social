-- All events for CPF 09820037735 in explorador_eventos
SELECT id, tipo_evento, per_apur, nr_recibo, cd_resposta, dt_processamento
FROM explorador_eventos
WHERE cpf = '09820037735'
ORDER BY tipo_evento, per_apur;
