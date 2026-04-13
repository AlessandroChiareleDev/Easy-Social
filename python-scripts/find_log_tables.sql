SELECT table_name FROM information_schema.tables
WHERE table_schema = 'public' AND table_name LIKE '%lote%' OR table_name LIKE '%envio%' OR table_name LIKE '%s1010%'
ORDER BY table_name;
