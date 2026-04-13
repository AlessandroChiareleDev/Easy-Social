"""Ordem REAL dos eventos de periodo por numero de recibo (sequencial no eSocial)."""
import psycopg2, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from db_config import DB_CONFIG

conn = psycopg2.connect(**DB_CONFIG, keepalives=1, keepalives_idle=30,
                        keepalives_interval=10, keepalives_count=3)
cur = conn.cursor()

# S-1298 e S-1299 ordenados por recibo (ordem real eSocial)
cur.execute("""
    SELECT tipo_evento, nr_recibo
    FROM explorador_eventos
    WHERE per_apur='2025-09' AND tipo_evento IN ('S-1298','S-1299')
    ORDER BY nr_recibo
""")
rows = cur.fetchall()
print("ORDEM REAL (por nr_recibo crescente):")
print("-" * 60)
for i, r in enumerate(rows, 1):
    print(f"  {i}. {r[0]}  recibo={r[1]}")

ultimo = rows[-1] if rows else None
if ultimo:
    print(f"\n>>> ULTIMO EVENTO: {ultimo[0]}")
    if ultimo[0] == 'S-1299':
        print(">>> STATUS: PERIODO FECHADO")
    else:
        print(">>> STATUS: PERIODO ABERTO !!!")

# Also check: do reenvio scripts have their own S-1298?
# Check ALL S-1298 recibos
print("\n\nTodos S-1298 em 2025-09:")
cur.execute("""
    SELECT nr_recibo, dados_json FROM explorador_eventos
    WHERE per_apur='2025-09' AND tipo_evento='S-1298'
    ORDER BY nr_recibo
""")
for r in cur.fetchall():
    print(f"  recibo={r[0]}")

print("\nTodos S-1299 em 2025-09:")
cur.execute("""
    SELECT nr_recibo, dados_json FROM explorador_eventos
    WHERE per_apur='2025-09' AND tipo_evento='S-1299'
    ORDER BY nr_recibo
""")
for r in cur.fetchall():
    print(f"  recibo={r[0]}")

# CRITICAL: check the reenvio scripts - did they send additional S-1298 that might not be in DB?
# Check reenvio log files
print("\n\n--- Checking reenvio logs ---")
import glob
for logf in sorted(glob.glob("/tmp/reenvio*.log") + glob.glob("/tmp/pipeline*.log")):
    print(f"\nFile: {logf}")
    with open(logf) as f:
        lines = f.readlines()
    for line in lines:
        if "1298" in line or "1299" in line or "reabr" in line.lower() or "fech" in line.lower():
            print(f"  {line.rstrip()}")

conn.close()
