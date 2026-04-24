-- ════════════════════════════════════════════════════════════════════
-- Adiciona status 'na' (Não Aplica) para CPFs que não devem ser enviados
-- ao eSocial (ex.: demitidos, sem base IRRF, folha paga em outra
-- competência, etc.) — análise feita pela Ana fora do sistema.
-- ════════════════════════════════════════════════════════════════════

CREATE OR REPLACE VIEW public.v_s1210_contadores AS
WITH ult AS (
    SELECT DISTINCT ON (empresa_id, per_apur, cpf)
           empresa_id, per_apur, cpf, lote_num, status
      FROM public.s1210_cpf_envios
     ORDER BY empresa_id, per_apur, cpf, enviado_em DESC
)
SELECT s.empresa_id,
       s.per_apur,
       s.lote_num,
       COUNT(*)                                                                                  AS total,
       COUNT(*) FILTER (WHERE u.status = 'ok')                                                   AS ok,
       COUNT(*) FILTER (WHERE u.status = 'erro')                                                 AS erro,
       COUNT(*) FILTER (WHERE u.status = 'enviando')                                             AS enviando,
       COUNT(*) FILTER (WHERE u.status = 'na')                                                   AS na,
       COUNT(*) FILTER (WHERE u.status IS NULL OR u.status NOT IN ('ok','erro','enviando','na')) AS pendente
  FROM public.s1210_cpf_scope s
  LEFT JOIN ult u
         ON u.empresa_id = s.empresa_id
        AND u.per_apur   = s.per_apur
        AND u.cpf        = s.cpf
 GROUP BY s.empresa_id, s.per_apur, s.lote_num;

COMMENT ON VIEW public.v_s1210_contadores IS
    'Contadores por (empresa,per_apur,lote_num). Status na = CPF marcado como Não Aplica (não deve ser transmitido).';
