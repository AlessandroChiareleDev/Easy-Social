-- 1) Rubrica 1026: update to match eSocial (00, 09, 00) and natureza 1299, mark enviado
UPDATE cruzamento_eb
SET incid_base_legal_inss = '00',
    incid_base_legal_irrf = '09',
    incid_base_legal_fgts = '00',
    incid_inss = '00',
    incid_irrf = '09',
    incid_fgts = '00',
    cod_natureza = '1299',
    envio_status = 'enviado',
    corrigido = TRUE
WHERE cod_rubrica = '1026';

-- 2) All other pending/feito rubricas: mark as enviado
UPDATE cruzamento_eb
SET envio_status = 'enviado',
    corrigido = TRUE
WHERE (incid_inss != SPLIT_PART(incid_base_legal_inss,' - ',1)
    OR incid_irrf != SPLIT_PART(incid_base_legal_irrf,' - ',1)
    OR incid_fgts != SPLIT_PART(incid_base_legal_fgts,' - ',1))
  AND COALESCE(envio_status,'pendente') != 'enviado';

-- 3) Verify: should return 0 rows
SELECT COUNT(*) as restantes
FROM cruzamento_eb
WHERE (incid_inss != SPLIT_PART(incid_base_legal_inss,' - ',1)
    OR incid_irrf != SPLIT_PART(incid_base_legal_irrf,' - ',1)
    OR incid_fgts != SPLIT_PART(incid_base_legal_fgts,' - ',1))
  AND COALESCE(envio_status,'pendente') != 'enviado';

-- 4) Verify 1026
SELECT cod_rubrica, LEFT(descricao,40), cod_natureza, envio_status,
       incid_inss, incid_irrf, incid_fgts,
       incid_base_legal_inss, incid_base_legal_irrf, incid_base_legal_fgts
FROM cruzamento_eb WHERE cod_rubrica = '1026';
