-- Fix rubrica 258: set correct incidence values and mark as enviado
UPDATE cruzamento_eb
SET incid_base_legal_inss = '0',
    incid_base_legal_irrf = '75',
    incid_base_legal_fgts = '0',
    envio_status = 'enviado',
    corrigido = TRUE
WHERE cod_rubrica = '258';

-- Verify
SELECT cod_rubrica, LEFT(descricao,40), envio_status,
       incid_base_legal_inss, incid_base_legal_irrf, incid_base_legal_fgts
FROM cruzamento_eb WHERE cod_rubrica = '258';
