import psycopg2

conn = psycopg2.connect(
    host='localhost', port=5432, dbname='easy_social_db',
    user='easy_social_user', password='sua_senha_segura'
)
cur = conn.cursor()

# Rubricas pendentes com natRubr expirado ou inexistente
cur.execute("""
SELECT rc.cod_rubrica, te.raw_data->>'Cód. Natureza' AS nat,
  CASE WHEN t3.codigo IS NULL THEN 'NAO_EXISTE'
       WHEN t3.dt_fim IS NOT NULL THEN 'EXPIRADO'
       ELSE 'OK' END AS st
FROM rubrica_corrections rc
LEFT JOIN tabela_eventos_gl te ON te.raw_data->>'Código' = rc.cod_rubrica
LEFT JOIN esocial_tabela3_natureza t3 ON t3.codigo = (te.raw_data->>'Cód. Natureza')::int
WHERE rc.status = 'pendente' AND (t3.codigo IS NULL OR t3.dt_fim IS NOT NULL)
ORDER BY rc.cod_rubrica::int
""")
print("=== RUBRICAS COM natRubr PROBLEMATICO ===")
problemas = cur.fetchall()
for row in problemas:
    print(f"Rubrica {row[0]:>5} | natRubr={row[1]} | {row[2]}")
print(f"\nTotal com problema: {len(problemas)}")

# Resumo por natRubr
cur.execute("""
SELECT te.raw_data->>'Cód. Natureza' AS nat, t3.dt_fim,
  COUNT(*) as qtd
FROM rubrica_corrections rc
LEFT JOIN tabela_eventos_gl te ON te.raw_data->>'Código' = rc.cod_rubrica
LEFT JOIN esocial_tabela3_natureza t3 ON t3.codigo = (te.raw_data->>'Cód. Natureza')::int
WHERE rc.status = 'pendente' AND (t3.codigo IS NULL OR t3.dt_fim IS NOT NULL)
GROUP BY te.raw_data->>'Cód. Natureza', t3.dt_fim
ORDER BY qtd DESC
""")
print("\n=== RESUMO POR natRubr ===")
for row in cur.fetchall():
    print(f"natRubr={row[0]} | expirou={row[1]} | {row[2]} rubricas")

# Total de pendentes OK
cur.execute("""
SELECT COUNT(*) FROM rubrica_corrections rc
LEFT JOIN tabela_eventos_gl te ON te.raw_data->>'Código' = rc.cod_rubrica
LEFT JOIN esocial_tabela3_natureza t3 ON t3.codigo = (te.raw_data->>'Cód. Natureza')::int
WHERE rc.status = 'pendente' AND t3.codigo IS NOT NULL AND t3.dt_fim IS NULL
""")
ok = cur.fetchone()[0]
print(f"\nTotal pendentes com natRubr OK: {ok}")

cur.execute("SELECT COUNT(*) FROM rubrica_corrections WHERE status = 'pendente'")
total = cur.fetchone()[0]
print(f"Total pendentes: {total}")

conn.close()
