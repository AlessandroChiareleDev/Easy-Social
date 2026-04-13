"""Investigar CPF 31381951805 - full S-1200 reconstruction data."""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from db_config import DB_CONFIG
import psycopg2, psycopg2.extras

conn = psycopg2.connect(**DB_CONFIG, keepalives=1, keepalives_idle=30,
                        keepalives_interval=10, keepalives_count=3)
cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

CPF = "31381951805"
PER = "2025-09"

# 1. Get the most recent S-1200 event (highest nr_recibo = most recent)
cur.execute("""
    SELECT id, tipo_evento, cpf, per_apur, nr_recibo, id_evento, 
           dados_json, dt_processamento
    FROM explorador_eventos
    WHERE cpf = %s AND per_apur = %s AND tipo_evento = 'S-1200'
    ORDER BY nr_recibo DESC LIMIT 1
""", (CPF, PER))
s1200 = cur.fetchone()
print("=== Most recent S-1200 ===")
print(f"  id={s1200['id']} recibo={s1200['nr_recibo']} evento={s1200['id_evento']}")
print(f"  dados_json: {json.dumps(s1200['dados_json'], indent=2, default=str)}")

# 2. Get ALL explorador_rubricas for this S-1200 event
cur.execute("""
    SELECT id, cod_rubr, ide_tab_rubr, nat_rubr, tp_rubr, 
           cod_inc_cp, cod_inc_irrf, cod_inc_fgts, vr_rubr, ind_ap_ir
    FROM explorador_rubricas 
    WHERE evento_id = %s
    ORDER BY id
""", (s1200['id'],))
rubricas = cur.fetchall()
print(f"\n=== explorador_rubricas for S-1200 event {s1200['id']} ({len(rubricas)} rows) ===")
for r in rubricas:
    print(f"  {dict(r)}")

# 3. Get the most recent S-1210 event (which was retified by pipeline)
cur.execute("""
    SELECT id, tipo_evento, cpf, per_apur, nr_recibo, id_evento, 
           dados_json
    FROM explorador_eventos
    WHERE cpf = %s AND per_apur = %s AND tipo_evento = 'S-1210'
    ORDER BY nr_recibo DESC LIMIT 1
""", (CPF, PER))
s1210 = cur.fetchone()
print(f"\n=== Most recent S-1210 (pre-pipeline) ===")
print(f"  id={s1210['id']} recibo={s1210['nr_recibo']}")
print(f"  dados_json: {json.dumps(s1210['dados_json'], indent=2, default=str)}")

# 4. Get ALL S-1200 versions to understand retification chain
cur.execute("""
    SELECT id, nr_recibo, id_evento, dados_json->>'indRetif' as ind_retif,
           dados_json->>'matricula' as matricula,
           dados_json->>'codCateg' as cod_categ,
           dados_json->>'ideDmDev' as ide_dm_dev
    FROM explorador_eventos
    WHERE cpf = %s AND per_apur = %s AND tipo_evento = 'S-1200'
    ORDER BY nr_recibo DESC
""", (CPF, PER))
s1200_versions = cur.fetchall()
print(f"\n=== All S-1200 versions ===")
for v in s1200_versions:
    print(f"  {dict(v)}")

# 5. Get pipeline_cpf_results to know the current S-1210 recibo
cur.execute("""
    SELECT nr_recibo_original, nr_recibo_novo, pagamentos, info_ir_cr
    FROM pipeline_cpf_results WHERE cpf = %s
""", (CPF,))
pcr = cur.fetchone()
print(f"\n=== pipeline_cpf_results ===")
if pcr:
    print(f"  S-1210 original: {pcr['nr_recibo_original']}")
    print(f"  S-1210 retified: {pcr['nr_recibo_novo']}")
    print(f"  pagamentos: {json.dumps(pcr['pagamentos'], indent=2, default=str) if pcr['pagamentos'] else 'NULL'}")
    print(f"  info_ir_cr: {json.dumps(pcr['info_ir_cr'], indent=2, default=str) if pcr['info_ir_cr'] else 'NULL'}")

# 6. Check explorador_rubricas columns/structure
cur.execute("""
    SELECT column_name, data_type FROM information_schema.columns 
    WHERE table_name = 'explorador_rubricas' ORDER BY ordinal_position
""")
print(f"\n=== explorador_rubricas schema ===")
for r in cur.fetchall():
    print(f"  {r['column_name']}: {r['data_type']}")

conn.close()
