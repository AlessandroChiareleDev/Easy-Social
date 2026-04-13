SELECT id, rubrica_ids, resultado, created_at
FROM esocial_lotes
WHERE resultado::text LIKE '%571%'
ORDER BY created_at DESC
LIMIT 5;
