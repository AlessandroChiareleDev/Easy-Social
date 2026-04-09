-- Get S-1210 data for FIRST CPF to compare
SELECT id, tipo_evento, per_apur, nr_recibo,
       SUBSTRING(dados_json::text, 1, 500) as dados
FROM explorador_eventos
WHERE cpf = '08132588983' AND tipo_evento = 'S-1210' AND per_apur = '2024-12'
ORDER BY id;

-- How many S-1200 dmDevs does second CPF have? Check the S-5002 XML for dmDev detail
-- Get S-5002 with id 290228 (most recent, after retif) full dados
SELECT dados_json::text FROM explorador_eventos WHERE id = 290228;

-- Also get S-5002 from first CPF for comparison
SELECT id, dados_json::text FROM explorador_eventos WHERE cpf = '08132588983' AND tipo_evento = 'S-5002' AND per_apur = '2024-12' LIMIT 1;
