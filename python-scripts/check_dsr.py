import psycopg2

conn = psycopg2.connect(host='localhost', port=5432, dbname='easy_social_db', user='easy_social_user', password='sua_senha_segura')
cur = conn.cursor()

# DSR rubricas col_f
print("=== DSR RUBRICAS (VERIFICAR) ===")
cur.execute("""SELECT col_a, col_b, col_f FROM analise_natureza 
WHERE UPPER(TRIM(col_d)) = 'VERIFICAR' AND (col_b ILIKE '%DSR%' OR col_b ILIKE '%D.S.R%') 
ORDER BY col_a""")
for row in cur.fetchall():
    print(f"cod={row[0]:6s} | {row[1]}")
    print(f"  col_f: {row[2]}")

# Check natureza 1020, 1002, 1012 status
print("\n=== NATUREZAS DSR/FERIAS ===")
cur.execute("SELECT codigo, nome, data_fim FROM naturezas_esocial WHERE codigo IN ('1002','1012','1020') ORDER BY codigo")
for row in cur.fetchall():
    status = "INATIVA" if row[2] else "ATIVA"
    print(f"  {row[0]} - {row[1]} [{status}] (fim={row[2]})")

conn.close()
