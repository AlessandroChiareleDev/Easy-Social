"""Check if there are S-1210 events from other periods referencing  
demonstrativo 01511303 from September's S-1200."""
import sys, os, subprocess
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from db_config import DB_CONFIG
import psycopg2, psycopg2.extras

CPF = "31381951805"

# Check explorador_eventos for ALL S-1210 events (any period)
conn = psycopg2.connect(**DB_CONFIG, keepalives=1, keepalives_idle=30,
                        keepalives_interval=10, keepalives_count=3)
cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

cur.execute("""
    SELECT id, cpf, per_apur, tipo_evento, nr_recibo, dados_json
    FROM explorador_eventos
    WHERE cpf = %s AND tipo_evento = 'S-1210'
    ORDER BY per_apur, id
""", (CPF,))
rows = cur.fetchall()
print(f"ALL S-1210 events for CPF {CPF} in explorador_eventos:")
for r in rows:
    dados = r.get("dados_json", {}) or {}
    pagamentos = dados.get("pagamentos", [])
    dm_devs = [p.get("ideDmDev") for p in pagamentos]
    print(f"  id={r['id']} per_apur={r['per_apur']} nr_recibo={r['nr_recibo']}")
    print(f"    pagamentos: {len(pagamentos)}, dmDevs: {dm_devs}")

# Check ALL S-1210 XML files for reference to demonstrativo 01511303
print("\n--- Searching all S-1210 XMLs for demonstrativo 01511303 ---")
result = subprocess.run(
    ["grep", "-rl", "01511303", "/opt/easy-social/xmls_set2025/"],
    capture_output=True, text=True, timeout=60
)
files = result.stdout.strip().split("\n") if result.stdout.strip() else []
for f in files:
    event_type = "S-1200" if "S-1200" in f else "S-1210" if "S-1210" in f else "OTHER"
    print(f"  [{event_type}] {f}")

# Also check for S-1200 events
print(f"\nALL S-1200 events for CPF {CPF}:")
cur.execute("""
    SELECT id, cpf, per_apur, tipo_evento, nr_recibo
    FROM explorador_eventos
    WHERE cpf = %s AND tipo_evento = 'S-1200'
    ORDER BY per_apur, id
""", (CPF,))
for r in cur.fetchall():
    print(f"  id={r['id']} per_apur={r['per_apur']} nr_recibo={r['nr_recibo']}")

# Check pipeline_cpf_results for ALL CPFs
print(f"\nPipeline CPF results for {CPF}:")
cur.execute("""
    SELECT id, cpf, status, nr_recibo_original, nr_recibo_novo
    FROM pipeline_cpf_results
    WHERE cpf = %s ORDER BY id
""", (CPF,))
for r in cur.fetchall():
    print(f"  id={r['id']} status={r['status']} orig={r['nr_recibo_original']} novo={r['nr_recibo_novo']}")

conn.close()
