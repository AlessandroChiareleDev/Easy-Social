"""Investigar CPF 31381951805 - parte 2."""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from db_config import DB_CONFIG
import psycopg2, psycopg2.extras

conn = psycopg2.connect(**DB_CONFIG, keepalives=1, keepalives_idle=30,
                        keepalives_interval=10, keepalives_count=3)
cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

CPF = "31381951805"

# 1. esocial_envios columns
cur.execute("""
    SELECT column_name FROM information_schema.columns 
    WHERE table_name = 'esocial_envios' ORDER BY ordinal_position
""")
print("=== esocial_envios columns ===")
print([r['column_name'] for r in cur.fetchall()])

# 2. esocial_envios for this CPF (find by searching xml_enviado or xml_retorno)
cur.execute("""
    SELECT id, tipo_evento, modo, status, protocolo_envio, nr_recibo, created_at,
           LEFT(xml_enviado::text, 300) as xml_preview
    FROM esocial_envios 
    WHERE xml_enviado::text LIKE %s OR xml_retorno::text LIKE %s
    ORDER BY id DESC LIMIT 10
""", (f'%{CPF}%', f'%{CPF}%'))
rows = cur.fetchall()
print(f"\n=== esocial_envios matching CPF ({len(rows)}) ===")
for r in rows:
    d = dict(r)
    print(d)
    print()

# 3. explorador_rubricas for this CPF (check if 774 appears)
cur.execute("""
    SELECT er.cod_rubr, er.tp_rubr, er.nat_rubr, er.vr_rubr, er.ide_tab_rubr,
           ee.tipo_evento, ee.per_apur, ee.nr_recibo
    FROM explorador_rubricas er
    JOIN explorador_eventos ee ON er.evento_id = ee.id
    WHERE ee.cpf = %s AND er.cod_rubr IN ('774', '607')
    ORDER BY er.cod_rubr
""", (CPF,))
rows = cur.fetchall()
print(f"\n=== explorador_rubricas for CPF: 774/607 ({len(rows)}) ===")
for r in rows:
    print(dict(r))

# 4. ALL rubricas for this CPF from explorador
cur.execute("""
    SELECT er.cod_rubr, er.tp_rubr, er.vr_rubr, ee.tipo_evento, ee.per_apur
    FROM explorador_rubricas er
    JOIN explorador_eventos ee ON er.evento_id = ee.id
    WHERE ee.cpf = %s AND ee.per_apur = '2025-09'
    ORDER BY ee.tipo_evento, er.cod_rubr
""", (CPF,))
rows = cur.fetchall()
print(f"\n=== ALL rubricas CPF 2025-09 ({len(rows)}) ===")
for r in rows:
    print(f"  {r['tipo_evento']} {r['cod_rubr']} tp={r['tp_rubr']} vr={r['vr_rubr']}")

# 5. Pipeline correcao for this CPF
cur.execute("SELECT * FROM pipeline_correcao WHERE cpf = %s ORDER BY id DESC LIMIT 3", (CPF,))
rows = cur.fetchall()
print(f"\n=== pipeline_correcao ({len(rows)}) ===")
for r in rows:
    d = dict(r)
    if d.get('steps_log'):
        d['steps_log'] = f"[{len(d['steps_log'])} steps]"
    print(d)

conn.close()
