SELECT cod_rubrica, envio_status, corrigido,
       incid_inss, incid_irrf, incid_fgts,
       incid_base_legal_inss, incid_base_legal_irrf, incid_base_legal_fgts
FROM cruzamento_eb
WHERE cod_rubrica = '571';
