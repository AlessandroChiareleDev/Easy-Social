SELECT COALESCE(envio_status,'pendente') as st, COUNT(*)
FROM cruzamento_eb
WHERE (incid_inss != SPLIT_PART(incid_base_legal_inss,' - ',1)
    OR incid_irrf != SPLIT_PART(incid_base_legal_irrf,' - ',1)
    OR incid_fgts != SPLIT_PART(incid_base_legal_fgts,' - ',1))
  AND COALESCE(envio_status,'pendente') != 'enviado'
GROUP BY 1;
