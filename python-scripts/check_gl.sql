-- Check tabela_eventos_gl schema and data for this CPF
SELECT column_name FROM information_schema.columns WHERE table_name = 'tabela_eventos_gl' ORDER BY ordinal_position;
