UPDATE cruzamento_eb
SET envio_status = 'feito', corrigido = TRUE, corrigido_em = NOW()
WHERE cod_rubrica = '571';
