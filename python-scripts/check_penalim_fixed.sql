-- CPFs com codIncIRRF=51 (pensão alimentícia) que tinham erro [8]
-- Verificar se dados_json agora tem penAlim
SELECT e.id, e.cpf, e.arquivo_origem,
       e.dados_json::text LIKE '%penAlim%' AS tem_penalim,
       e.dados_json::text LIKE '%dedDepen%' AS tem_deddepen
FROM explorador_eventos e
JOIN explorador_rubricas r ON r.evento_id = e.id
WHERE e.tipo_evento = 'S-1210'
  AND r.cod_inc_irrf = '51'
GROUP BY e.id, e.cpf, e.arquivo_origem, e.dados_json
ORDER BY e.cpf
LIMIT 10;
