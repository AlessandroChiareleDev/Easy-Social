"""Complete analysis: for CPF 00140303570, compute the [1955] balance per incidence."""
import sys, os, json, re, glob
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from db_config import DB_CONFIG
import psycopg2, psycopg2.extras

conn = psycopg2.connect(**DB_CONFIG, keepalives=1, keepalives_idle=30, keepalives_interval=10, keepalives_count=3)
cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

# 1) Build a proper rubrica map from explorador_rubricas (prefer non-null values)
print("=== Building rubrica map ===")
cur.execute("""
    SELECT cod_rubr, tp_rubr, cod_inc_irrf, nat_rubr
    FROM explorador_rubricas
    WHERE tp_rubr IS NOT NULL
    ORDER BY cod_rubr, id DESC
""")
rubrica_map = {}
for r in cur.fetchall():
    cod = r['cod_rubr']
    if cod not in rubrica_map:
        rubrica_map[cod] = r
    elif rubrica_map[cod]['cod_inc_irrf'] is None and r['cod_inc_irrf'] is not None:
        rubrica_map[cod] = r

# Show all rubricas with codIncIRRF
ir_rubrs = {k: v for k, v in rubrica_map.items() if v['cod_inc_irrf'] and v['cod_inc_irrf'] in ('31','32','33','34')}
print(f"Rubricas with codIncIRRF 31-34: {len(ir_rubrs)}")
for k, v in sorted(ir_rubrs.items()):
    print(f"  codRubr={k}: tpRubr={v['tp_rubr']}, codIncIRRF={v['cod_inc_irrf']}, natRubr={v['nat_rubr']}")

# 2) Get CPF info
CPF = '00140303570'
print(f"\n=== CPF {CPF} ===")

# Get S-1210 data
cur.execute("""
    SELECT dados_json
    FROM explorador_eventos
    WHERE tipo_evento = 'S-1210' AND cpf = %s AND per_apur = '2025-09'
    ORDER BY id DESC LIMIT 1
""", (CPF,))
s1210 = cur.fetchone()
d1210 = s1210['dados_json']
if isinstance(d1210, str): d1210 = json.loads(d1210)
pagamentos = d1210.get('pagamentos', [])
print(f"S-1210 pagamentos ({len(pagamentos)}):")
for p in pagamentos:
    print(f"  ideDmDev={p.get('ideDmDev')}, perRef={p.get('perRef')}, dtPgto={p.get('dtPgto')}, vrLiq={p.get('vrLiq')}")

# 3) For each demonstrativo, find its S-1200 and extract rubricas
all_rubricas_with_values = []  # list of (codRubr, vrRubr, tpRubr, codIncIRRF)
xml_dir = "/opt/easy-social/xmls_set2025"

for pgto in pagamentos:
    ide_dm_dev = pgto.get('ideDmDev')
    per_ref = pgto.get('perRef')
    print(f"\n--- Demo {ide_dm_dev} (perRef={per_ref}) ---")
    
    # Search for S-1200 with this ideDmDev
    cur.execute("""
        SELECT arquivo_origem, dados_json, per_apur
        FROM explorador_eventos
        WHERE tipo_evento = 'S-1200' AND cpf = %s
          AND dados_json::text LIKE %s
        ORDER BY id DESC
    """, (CPF, f'%{ide_dm_dev}%'))
    s1200_events = cur.fetchall()
    print(f"  S-1200 events containing {ide_dm_dev}: {len(s1200_events)}")
    
    for evt in s1200_events:
        fname = evt['arquivo_origem']
        fpath = f"{xml_dir}/{fname}"
        print(f"  File: {fname} (perApur={evt['per_apur']})")
        
        if not os.path.exists(fpath):
            print(f"    FILE NOT FOUND")
            continue
        
        with open(fpath, 'r', encoding='utf-8') as f:
            xml = f.read()
        
        # This S-1200 may have multiple demonstrativos. We need to find the one matching ide_dm_dev
        # Parse per-demonstrativo rubrica blocks
        # Look for: <dmDev> ... <ideDmDev>X</ideDmDev> ... (rubricas) ... </dmDev>
        # or just find all itensRemun that are within the matching ideDmDev block
        
        # Split by dmDev blocks
        dm_blocks = re.split(r'<dmDev>', xml)
        for block in dm_blocks[1:]:  # skip first (before first dmDev)
            dm_id_match = re.search(r'<ideDmDev>(.*?)</ideDmDev>', block)
            if not dm_id_match:
                continue
            block_dm_id = dm_id_match.group(1)
            
            if block_dm_id == ide_dm_dev:
                # Found our demonstrativo - extract rubricas
                rubr_items = re.findall(
                    r'<codRubr>(\d+)</codRubr>.*?<vrRubr>([\d.]+)</vrRubr>',
                    block, re.DOTALL
                )
                print(f"    Demo {block_dm_id}: {len(rubr_items)} rubricas")
                for cod, vr in rubr_items:
                    info = rubrica_map.get(cod, {})
                    tp = info.get('tp_rubr', '?')
                    inc = info.get('cod_inc_irrf', '?')
                    nat = info.get('nat_rubr', '?')
                    all_rubricas_with_values.append((cod, float(vr), tp, inc))
                    marker = " <<<" if str(inc) in ('31','32','33','34') else ""
                    print(f"      codRubr={cod}, vrRubr={vr}, tpRubr={tp}, codIncIRRF={inc}, natRubr={nat}{marker}")
                break

# 4) Compute [1955] balance per incidence
print(f"\n\n=== [1955] Balance ===")
sums = {}
for cod, vr, tp, inc in all_rubricas_with_values:
    if str(inc) in ('31','32','33','34'):
        k = str(inc)
        if k not in sums:
            sums[k] = {'tipo_1_3': 0.0, 'tipo_2_4': 0.0, 'details_1_3': [], 'details_2_4': []}
        if str(tp) in ('1','3'):
            sums[k]['tipo_1_3'] += vr
            sums[k]['details_1_3'].append((cod, vr))
        elif str(tp) in ('2','4'):
            sums[k]['tipo_2_4'] += vr
            sums[k]['details_2_4'].append((cod, vr))

for inc, vals in sorted(sums.items()):
    diff_desconto_minus_provento = vals['tipo_2_4'] - vals['tipo_1_3']
    diff_provento_minus_desconto = vals['tipo_1_3'] - vals['tipo_2_4']
    print(f"\nIncidência {inc}:")
    print(f"  Sum(tipo 1,3 / proventos): {vals['tipo_1_3']:.2f} → {vals['details_1_3']}")
    print(f"  Sum(tipo 2,4 / descontos): {vals['tipo_2_4']:.2f} → {vals['details_2_4']}")
    print(f"  deduções - proventos = {diff_desconto_minus_provento:.2f}")
    print(f"  proventos - deduções = {diff_provento_minus_desconto:.2f}")
    if diff_desconto_minus_provento >= 0:
        print(f"  → Rule (desc >= prov): PASS")
    else:
        print(f"  → Rule (desc >= prov): FAIL")
    if diff_provento_minus_desconto >= 0:
        print(f"  → Rule (prov >= desc): PASS")
    else:
        print(f"  → Rule (prov >= desc): FAIL")

# 5) Also show ALL rubricas with their tpRubr and codIncIRRF
print(f"\n=== ALL unique rubricas used in these S-1200 demonstrativos ===")
used_rubrs = set(cod for cod, _, _, _ in all_rubricas_with_values)
for cod in sorted(used_rubrs, key=int):
    info = rubrica_map.get(cod, {})
    print(f"  codRubr={cod}: tpRubr={info.get('tp_rubr','?')}, "
          f"codIncIRRF={info.get('cod_inc_irrf','?')}, natRubr={info.get('nat_rubr','?')}")

# 6) Check if there are S-1200 for August 2025 for this CPF
print(f"\n=== S-1200 for August 2025, CPF {CPF} ===")
cur.execute("""
    SELECT id, dados_json, arquivo_origem, per_apur
    FROM explorador_eventos
    WHERE tipo_evento = 'S-1200' AND cpf = %s AND per_apur = '2025-08'
    ORDER BY id
""", (CPF,))
for r in cur.fetchall():
    print(f"  id={r['id']}, perApur={r['per_apur']}, arquivo={r['arquivo_origem']}")
    d = r['dados_json']
    if isinstance(d, str): d = json.loads(d)
    print(f"  ideDmDev={d.get('ideDmDev')}, indRetif={d.get('indRetif')}")

conn.close()
