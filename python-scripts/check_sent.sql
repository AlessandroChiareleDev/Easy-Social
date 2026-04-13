-- Rubricas enviadas recentemente (status enviado ou feito)
SELECT cod_rubrica, envio_status, corrigido, corrigido_em, incid_inss
FROM cruzamento_eb 
WHERE envio_status IN ('enviado', 'feito')
ORDER BY corrigido_em DESC NULLS LAST, cod_rubrica
LIMIT 30;
