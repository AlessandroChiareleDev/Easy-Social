import psycopg2

conn = psycopg2.connect(
    host='localhost', port=5432, dbname='easy_social_db',
    user='easy_social_user', password='sua_senha_segura'
)
cur = conn.cursor()

# Agrupar rubricas por natRubr expirado e mostrar descricoes
for nat in [2920, 1020, 1021, 9290]:
    cur.execute("""
        SELECT rc.cod_rubrica, LEFT(rc.descricao, 60)
        FROM rubrica_corrections rc
        LEFT JOIN tabela_eventos_gl te ON te.raw_data->>'Código' = rc.cod_rubrica
        LEFT JOIN esocial_tabela3_natureza t3 ON t3.codigo = (te.raw_data->>'Cód. Natureza')::int
        WHERE rc.status = 'pendente' AND (te.raw_data->>'Cód. Natureza')::int = %s
        ORDER BY rc.cod_rubrica::int
    """, (nat,))
    rows = cur.fetchall()
    print(f"\n=== natRubr {nat} ({len(rows)} rubricas) ===")
    for r in rows:
        print(f"  {r[0]:>5} - {r[1]}")

conn.close()
