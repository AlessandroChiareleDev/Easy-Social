"""Check which CPFs in lote 28 area are still pendente after crash."""
import psycopg2

conn = psycopg2.connect(
    host='aws-1-us-east-2.pooler.supabase.com',
    port=5432,
    dbname='postgres',
    user='postgres.zpizibafccwsjgvplcum',
    password='6.18.13.1.8Supa',
    sslmode='require'
)
cur = conn.cursor()

# Count total pendente
cur.execute("SELECT COUNT(*) FROM pipeline_cpf_results WHERE run_id=1 AND status='pendente'")
print(f"Total pendente: {cur.fetchone()[0]}")

# Count by status
cur.execute("SELECT status, COUNT(*) FROM pipeline_cpf_results WHERE run_id=1 GROUP BY status ORDER BY status")
for r in cur.fetchall():
    print(f"  {r[0]}: {r[1]}")

# Check CPFs around lote 28 - from the log, lote 28 starts with CPF 03628162556
print("\n--- CPFs around lote 28 boundary ---")
cur.execute("""
    SELECT cpf, status, lote_num, nr_recibo_novo 
    FROM pipeline_cpf_results 
    WHERE run_id=1 AND cpf >= '03625147556' AND cpf <= '03699999999' 
    ORDER BY cpf LIMIT 20
""")
for r in cur.fetchall():
    print(f"CPF={r[0]}  status={r[1]}  lote={r[2]}  recibo={r[3]}")

# Find the specific CPF that crashed
print("\n--- CPF 03635806544 (crash point) ---")
cur.execute("SELECT cpf, status, lote_num, nr_recibo_novo FROM pipeline_cpf_results WHERE run_id=1 AND cpf='03635806544'")
r = cur.fetchone()
if r:
    print(f"CPF={r[0]}  status={r[1]}  lote={r[2]}  recibo={r[3]}")
else:
    print("NOT FOUND")

conn.close()
