SELECT cod_rubrica, envio_status, corrigido, incid_inss, incid_base_legal_inss
FROM cruzamento_eb
WHERE cod_rubrica IN ('571', '572')
ORDER BY cod_rubrica;
