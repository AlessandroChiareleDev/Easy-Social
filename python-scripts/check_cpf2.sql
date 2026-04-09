SELECT id, tipo_evento, modo, per_apur, protocolo_envio, nr_recibo, codigo_resposta, created_at
FROM esocial_envios
WHERE cpf = '09820037735'
ORDER BY id;
