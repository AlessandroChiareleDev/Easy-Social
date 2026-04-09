SELECT cod_rubrica, LEFT(descricao,35) as desc, COALESCE(envio_status,'pendente') as status,
       SPLIT_PART(incid_base_legal_inss,' - ',1) as inss,
       SPLIT_PART(incid_base_legal_irrf,' - ',1) as irrf,
       SPLIT_PART(incid_base_legal_fgts,' - ',1) as fgts
FROM cruzamento_eb
WHERE (incid_inss != SPLIT_PART(incid_base_legal_inss,' - ',1)
    OR incid_irrf != SPLIT_PART(incid_base_legal_irrf,' - ',1)
    OR incid_fgts != SPLIT_PART(incid_base_legal_fgts,' - ',1))
  AND COALESCE(envio_status,'pendente') != 'enviado'
ORDER BY cod_rubrica::int;
