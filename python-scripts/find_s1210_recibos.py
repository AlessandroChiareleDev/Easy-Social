"""Find all S-1210 records for CPF 31381951805"""
import psycopg2, psycopg2.extras, sys, subprocess
sys.path.insert(0, '/opt/easy-social/python-scripts')
from db_config import DB_CONFIG

conn = psycopg2.connect(**DB_CONFIG, keepalives=1, keepalives_idle=30,
                        keepalives_interval=10, keepalives_count=3)
cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

CPF = "31381951805"

cur.execute("""
    SELECT id, cpf, per_apur, tipo_evento, nr_recibo, created_at
    FROM explorador_eventos
    WHERE cpf = %s AND per_apur = '2025-09' AND tipo_evento = 'S-1210'
    ORDER BY id
""", (CPF,))
rows = cur.fetchall()
print("S-1210 records in explorador_eventos:")
for r in rows:
    print(f"  id={r['id']} nr_recibo={r['nr_recibo']} created={r['created_at']}")

cur.execute("""
    SELECT * FROM pipeline_cpf_results
    WHERE cpf = %s ORDER BY id
""", (CPF,))
rows = cur.fetchall()
print("\npipeline_cpf_results:")
for r in rows:
    for k, v in r.items():
        if v is not None:
            print(f"  {k}: {v}")
    print()

# XML files on disk
result = subprocess.run(
    ["grep", "-rl", CPF, "/opt/easy-social/xmls_set2025/"],
    capture_output=True, text=True, timeout=60
)
files = [f for f in result.stdout.strip().split("\n") if f and "S-1210" in f]
print("\nS-1210 XML files on disk:")
for f in files:
    print(f"  {f}")

conn.close()
