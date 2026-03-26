import psycopg2

conn = psycopg2.connect(host='localhost', port=5432, dbname='easy_social_db', user='easy_social_user', password='sua_senha_segura')
cur = conn.cursor()

# Colunas
cur.execute("SELECT column_name, ordinal_position FROM information_schema.columns WHERE table_name = 'dinamica' ORDER BY ordinal_position")
print("=== COLUNAS DA DINAMICA ===")
for r in cur.fetchall():
    print(f"  {r[1]}: {r[0]}")

# 5 VERIFICAR
cur.execute("SELECT col_a, col_b, col_c, col_d, col_e, col_f, col_g, col_h, col_i, col_j FROM dinamica WHERE UPPER(TRIM(col_d)) = 'VERIFICAR' LIMIT 5")
print("\n=== 5 VERIFICAR NA DINAMICA (todas as cols) ===")
for r in cur.fetchall():
    for i, name in enumerate(['a','b','c','d','e','f','g','h','i','j']):
        print(f"  col_{name} = {repr(r[i])}")
    print("  ---")

# Contar col_f preenchida
cur.execute("SELECT COUNT(*) FROM dinamica WHERE UPPER(TRIM(col_d)) = 'VERIFICAR' AND col_f IS NOT NULL AND TRIM(col_f) != '' AND TRIM(col_f) != '-'")
print(f"\nVERIFICAR com col_f preenchida (nao vazia, nao '-'): {cur.fetchone()[0]}")

cur.execute("SELECT COUNT(*) FROM dinamica WHERE UPPER(TRIM(col_d)) = 'VERIFICAR'")
print(f"Total VERIFICAR na dinamica: {cur.fetchone()[0]}")

# Tambem ver o que o frontend mostra - checar table routes
cur.execute("SELECT COUNT(*) FROM dinamica")
print(f"\nTotal registros dinamica: {cur.fetchone()[0]}")

# Ver cabeçalhos row_number=1
cur.execute("SELECT col_a, col_b, col_c, col_d, col_e, col_f FROM dinamica WHERE row_number = 1 LIMIT 3")
rows = cur.fetchall()
print(f"\nrow_number=1 (possiveis cabecalhos): {len(rows)} rows")
for r in rows:
    print(f"  a={repr(r[0])} b={repr(r[1])} c={repr(r[2])} d={repr(r[3])} e={repr(r[4])} f={repr(r[5])}")

cur.close()
conn.close()
