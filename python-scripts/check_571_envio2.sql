SELECT * FROM esocial_envios
WHERE rubrica_ids::text LIKE '%571%'
ORDER BY created_at DESC
LIMIT 3;
