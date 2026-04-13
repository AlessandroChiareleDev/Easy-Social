-- Status do endpoint de download cirúrgico do eSocial
-- Os 44 CPFs do erro [459] dependem desse endpoint funcionar
-- Verificar se há recibos recuperados desde a última tentativa
SELECT count(*) AS total_erro_459
FROM explorador_eventos e
WHERE e.tipo_evento = 'S-1210'
  AND e.cd_resposta IS NULL
  AND e.nr_recibo IS NULL;
