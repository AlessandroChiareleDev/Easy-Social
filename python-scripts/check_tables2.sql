-- Check esocial_envios for this CPF (may be in rubrica_detalhes or xml_enviado)
-- First check pipeline_correcao table for any CPF-related runs
SELECT column_name FROM information_schema.columns WHERE table_name = 'pipeline_correcao' ORDER BY ordinal_position;

-- Check pipeline_audit too
SELECT column_name FROM information_schema.columns WHERE table_name = 'pipeline_audit' ORDER BY ordinal_position;

-- Check if there are downloaded events somewhere  
SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' AND table_name LIKE '%download%' OR table_name LIKE '%evento%' OR table_name LIKE '%s5002%' OR table_name LIKE '%s1200%' OR table_name LIKE '%s1210%' ORDER BY table_name;
