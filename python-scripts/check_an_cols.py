import psycopg2

conn = psycopg2.connect(host='localhost', port=5432, dbname='easy_social_db', user='easy_social_user', password='sua_senha_segura')
cur = conn.cursor()

# Cabecalho real (row_number=1)
cur.execute("SELECT col_a, col_b, col_c, col_d, col_e, col_f, col_g, col_h, col_i, col_j FROM analise_natureza WHERE row_number = 1 LIMIT 3")
rows = cur.fetchall()
print("=== CABECALHOS analise_natureza (row_number=1) ===")
for r in rows:
    for i, name in enumerate(['a','b','c','d','e','f','g','h','i','j']):
        print(f"  col_{name} = {repr(r[i])}")
    print()

# 5 VERIFICAR com TODOS os campos
cur.execute("SELECT col_a, col_b, col_c, col_d, col_e, col_f, col_g, col_h, col_i, col_j FROM analise_natureza WHERE UPPER(TRIM(col_d)) = 'VERIFICAR' LIMIT 5")
print("=== 5 VERIFICAR em analise_natureza (TODAS as colunas) ===")
for r in cur.fetchall():
    for i, name in enumerate(['a','b','c','d','e','f','g','h','i','j']):
        val = r[i]
        if val and str(val).strip():
            print(f"  col_{name} = {repr(val)}")
    print("  ---")

# col_f da analise_natureza: quantos VERIFICAR tem col_f preenchida?
cur.execute("SELECT COUNT(*) FROM analise_natureza WHERE UPPER(TRIM(col_d)) = 'VERIFICAR' AND col_f IS NOT NULL AND TRIM(col_f) != '' AND TRIM(col_f) != '-'")
print(f"\nVERIFICAR com col_f preenchida (AN): {cur.fetchone()[0]}")

# Exemplos de col_f em VERIFICAR
cur.execute("SELECT col_a, col_b, col_f FROM analise_natureza WHERE UPPER(TRIM(col_d)) = 'VERIFICAR' AND col_f IS NOT NULL AND TRIM(col_f) != '' AND TRIM(col_f) != '-' LIMIT 10")
rows = cur.fetchall()
print(f"\nExemplos col_f VERIFICAR (AN):")
for r in rows:
    print(f"  cod {r[0]} | {r[1]} | col_f = {repr(r[2])}")

# col_f DISTINTOS nos VERIFICAR
cur.execute("SELECT DISTINCT TRIM(col_f), COUNT(*) FROM analise_natureza WHERE UPPER(TRIM(col_d)) = 'VERIFICAR' GROUP BY TRIM(col_f) ORDER BY COUNT(*) DESC")
print(f"\n=== VALORES DISTINTOS de col_f nos VERIFICAR (AN) ===")
for r in cur.fetchall():
    print(f"  {repr(r[0])} ({r[1]}x)")

# Agora comparar: col_e e col_f da AN vs col_e e col_f da dinamica para mesmo codigo
print("\n=== COMPARACAO AN vs DIN para 5 VERIFICAR ===")
cur.execute("""
    SELECT an.col_a, an.col_b, 
           an.col_e as an_e, an.col_f as an_f,
           d.col_e as din_e, d.col_f as din_f
    FROM analise_natureza an
    JOIN dinamica d ON an.col_a = d.col_b
    WHERE UPPER(TRIM(an.col_d)) = 'VERIFICAR'
    LIMIT 10
""")
for r in cur.fetchall():
    print(f"  cod {r[0]} | {r[1]}")
    print(f"    AN.col_e  = {repr(r[2])}")
    print(f"    AN.col_f  = {repr(r[3])}")
    print(f"    DIN.col_e = {repr(r[4])}")
    print(f"    DIN.col_f = {repr(r[5])}")
    print()

cur.close()
conn.close()
