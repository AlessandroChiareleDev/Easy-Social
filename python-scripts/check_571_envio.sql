SELECT id, rubrica_ids, status, protocolo, created_at
FROM esocial_envios
WHERE rubrica_ids::text LIKE '%571%'
ORDER BY created_at DESC
LIMIT 5;
