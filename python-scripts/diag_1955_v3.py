"""Deep dive into [1955] - understand rubrica 571, 572, and the incidence 33 balance."""
import sys, os, json, re, glob
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from db_config import DB_CONFIG
import psycopg2, psycopg2.extras

conn = psycopg2.connect(**DB_CONFIG, keepalives=1, keepalives_idle=30, keepalives_interval=10, keepalives_count=3)
cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

# 1) What are rubricas 570, 571, 572 in S-1010?
print("=== Rubricas 570, 571, 572 (explorador_rubricas) ===")
cur.execute("""
    SELECT DISTINCT cod_rubr, tp_rubr, nat_rubr, cod_inc_irrf, cod_inc_cp
    FROM explorador_rubricas
    WHERE cod_rubr IN ('570','571','572')
    ORDER BY cod_rubr
""")
for r in cur.fetchall():
    print(f"  codRubr={r['cod_rubr']}: tpRubr={r['tp_rubr']}, natRubr={r['nat_rubr']}, "
          f"codIncIRRF={r['cod_inc_irrf']}, codIncCP={r['cod_inc_cp']}")

# 2) All rubricas with codIncIRRF in (31,32,33,34)
print("\n=== Todas rubricas com codIncIRRF 31-34 ===")
cur.execute("""
    SELECT DISTINCT cod_rubr, tp_rubr, nat_rubr, cod_inc_irrf
    FROM explorador_rubricas
    WHERE cod_inc_irrf IN ('31','32','33','34')
    ORDER BY cod_inc_irrf, cod_rubr
""")
for r in cur.fetchall():
    print(f"  codRubr={r['cod_rubr']}: tpRubr={r['tp_rubr']}, natRubr={r['nat_rubr']}, codIncIRRF={r['cod_inc_irrf']}")

# 3) S-1210 original XML files for affected CPFs
print("\n=== Finding S-1210 XML for CPF 00140303570 ===")
cur.execute("""
    SELECT arquivo_origem
    FROM explorador_eventos
    WHERE tipo_evento = 'S-1210' AND cpf = '00140303570' AND per_apur = '2025-09'
    ORDER BY id
""")
for r in cur.fetchall():
    fname = r['arquivo_origem']
    print(f"  arquivo: {fname}")
    fpath = f"/opt/easy-social/xmls_set2025/{fname}"
    if os.path.exists(fpath):
        with open(fpath) as f:
            xml = f.read()
        print(f"  XML size: {len(xml)} bytes")
        # This is S-1210 - show the structure
        print(f"  XML snippet (first 2000 chars):")
        print(f"  {xml[:2000]}")
    else:
        print(f"  FILE NOT FOUND: {fpath}")

# 4) Find corresponding S-1200 events for this CPF
print("\n=== S-1200 events for CPF 00140303570 ===")
cur.execute("""
    SELECT id, nr_recibo, arquivo_origem, dados_json
    FROM explorador_eventos
    WHERE tipo_evento = 'S-1200' AND cpf = '00140303570' AND per_apur = '2025-09'
    ORDER BY id
""")
for r in cur.fetchall():
    print(f"  id={r['id']}, recibo={r['nr_recibo']}, arquivo={r['arquivo_origem']}")
    d = r['dados_json']
    if isinstance(d, str): d = json.loads(d)
    print(f"  dados_json: {json.dumps(d, ensure_ascii=False)[:500]}")

# 5) Find S-1200 XML files and extract rubricas
print("\n=== S-1200 XML rubricas for CPF 00140303570 ===")
cur.execute("""
    SELECT arquivo_origem
    FROM explorador_eventos
    WHERE tipo_evento = 'S-1200' AND cpf = '00140303570' AND per_apur = '2025-09'
    ORDER BY id
""")
for r in cur.fetchall():
    fname = r['arquivo_origem']
    fpath = f"/opt/easy-social/xmls_set2025/{fname}"
    if os.path.exists(fpath):
        with open(fpath) as f:
            xml = f.read()
        # Extract ideDmDev
        dm_devs = re.findall(r'<ideDmDev>(.*?)</ideDmDev>', xml)
        print(f"\n  File: {fname}")
        print(f"  ideDmDev: {dm_devs}")
        
        # Extract rubricas
        rubrs = re.findall(
            r'<codRubr>(\d+)</codRubr>.*?<vrRubr>([\d.]+)</vrRubr>',
            xml, re.DOTALL
        )
        print(f"  Rubricas: {len(rubrs)}")
        for cod, vr in rubrs:
            # look up in explorador_rubricas
            cur.execute("""
                SELECT DISTINCT tp_rubr, cod_inc_irrf, nat_rubr
                FROM explorador_rubricas WHERE cod_rubr = %s LIMIT 1
            """, (cod,))
            info = cur.fetchone()
            tp = info['tp_rubr'] if info else '?'
            inc = info['cod_inc_irrf'] if info else '?'
            nat = info['nat_rubr'] if info else '?'
            marker = " <<<" if inc in ('31','32','33','34') else ""
            print(f"    codRubr={cod}, vrRubr={vr}, tpRubr={tp}, codIncIRRF={inc}, natRubr={nat}{marker}")
    else:
        print(f"  FILE NOT FOUND: {fpath}")

# 6) Also check: what does the S-1210 reference? (ideDmDev)
print("\n=== S-1210 references (ideDmDev) ===")
cur.execute("""
    SELECT dados_json
    FROM explorador_eventos
    WHERE tipo_evento = 'S-1210' AND cpf = '00140303570' AND per_apur = '2025-09'
      AND nr_recibo = '1.1.0000000035299455626'
""")
r = cur.fetchone()
if r:
    d = r['dados_json']
    if isinstance(d, str): d = json.loads(d)
    pagamentos = d.get('pagamentos', [])
    for p in pagamentos:
        print(f"  ideDmDev={p.get('ideDmDev')}, dtPgto={p.get('dtPgto')}, vrLiq={p.get('vrLiq')}")

conn.close()
