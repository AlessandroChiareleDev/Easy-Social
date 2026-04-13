"""Check: algum S-3000 excluiu um S-1299? E verificar recibos reais do eSocial."""
import psycopg2, json, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from db_config import DB_CONFIG

conn = psycopg2.connect(**DB_CONFIG, keepalives=1, keepalives_idle=30,
                        keepalives_interval=10, keepalives_count=3)
cur = conn.cursor()

# Check S-3000 dados_json to see what they deleted
print("S-3000 sample (first 5):")
cur.execute("""
    SELECT nr_recibo, dados_json, cpf
    FROM explorador_eventos
    WHERE per_apur='2025-09' AND tipo_evento='S-3000'
    LIMIT 5
""")
for r in cur.fetchall():
    dados = r[1] if isinstance(r[1], dict) else json.loads(r[1] or '{}')
    print(f"  recibo={r[0]} cpf={r[2]}")
    print(f"  dados: {json.dumps(dados, indent=2)[:300]}")

# Check if any S-3000 has nrRecEvt referencing S-1299 or S-1298
print("\n\nChecking S-3000 for S-1299/S-1298 references:")
cur.execute("""
    SELECT nr_recibo, dados_json
    FROM explorador_eventos
    WHERE per_apur='2025-09' AND tipo_evento='S-3000'
      AND (dados_json::text LIKE '%1299%' OR dados_json::text LIKE '%1298%')
""")
rows = cur.fetchall()
print(f"  Found: {len(rows)} S-3000 referencing 1298/1299")
for r in rows:
    print(f"  recibo={r[0]} dados={r[1]}")

# Check the S-3000 that were part of the explorador import
# The 7771 S-3000 — what type of events did they delete?
print("\n\nS-3000 - what events did they reference?")
cur.execute("""
    SELECT 
        CASE 
            WHEN dados_json->>'nrRecEvt' IS NOT NULL THEN 'has_nrRecEvt'
            ELSE 'no_nrRecEvt'
        END as has_ref,
        COUNT(*)
    FROM explorador_eventos
    WHERE per_apur='2025-09' AND tipo_evento='S-3000'
    GROUP BY 1
""")
for r in cur.fetchall():
    print(f"  {r[0]}: {r[1]}")

# Get a sample of S-3000 nrRecEvt values  
cur.execute("""
    SELECT dados_json->>'nrRecEvt' as ref, COUNT(*)
    FROM explorador_eventos
    WHERE per_apur='2025-09' AND tipo_evento='S-3000'
      AND dados_json->>'nrRecEvt' IS NOT NULL
    GROUP BY 1
    LIMIT 5
""")
print("\nSample nrRecEvt values from S-3000:")
for r in cur.fetchall():
    print(f"  {r[0]}: {r[1]}")

# Cross-reference: check if any S-3000 deleted events are S-1299
cur.execute("""
    SELECT s3.nr_recibo as s3000_recibo, s3.dados_json->>'nrRecEvt' as deleted_recibo,
           ee.tipo_evento as deleted_type
    FROM explorador_eventos s3
    LEFT JOIN explorador_eventos ee ON ee.nr_recibo = s3.dados_json->>'nrRecEvt'
    WHERE s3.per_apur='2025-09' AND s3.tipo_evento='S-3000'
      AND ee.tipo_evento IN ('S-1299','S-1298')
""")
rows = cur.fetchall()
print(f"\nS-3000 that deleted S-1298/S-1299: {len(rows)}")
for r in rows:
    print(f"  S-3000 {r[0]} deleted {r[2]} {r[1]}")

conn.close()
