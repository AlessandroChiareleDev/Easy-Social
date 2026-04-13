import psycopg2, psycopg2.extras, json, sys, os, re, glob
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from db_config import DB_CONFIG

conn = psycopg2.connect(**DB_CONFIG, keepalives=1, keepalives_idle=30, keepalives_interval=10, keepalives_count=3)
cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

# 1) explorador_rubricas schema and data
cur.execute("SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'explorador_rubricas' ORDER BY ordinal_position")
print("=== explorador_rubricas columns ===")
for r in cur.fetchall(): print(f"  {r['column_name']}: {r['data_type']}")

cur.execute("SELECT count(*) as cnt FROM explorador_rubricas")
print(f"\nTotal rubricas: {cur.fetchone()['cnt']}")

cur.execute("SELECT * FROM explorador_rubricas LIMIT 3")
rows = cur.fetchall()
print("\nSample rubricas:")
for r in rows:
    print(f"  {dict(r)}")

# 2) Get all rubricas with codIncIRRF info
cur.execute("SELECT * FROM explorador_rubricas WHERE cod_inc_irrf IS NOT NULL LIMIT 20")
rows = cur.fetchall()
print(f"\nRubricas com codIncIRRF ({len(rows)}):")
for r in rows:
    print(f"  {dict(r)}")

# 3) Check S-1010 events dados_json
cur.execute("SELECT dados_json FROM explorador_eventos WHERE tipo_evento = 'S-1010' LIMIT 3")
rows = cur.fetchall()
print("\nSample S-1010 dados_json:")
for r in rows:
    d = r["dados_json"]
    if isinstance(d, str): d = json.loads(d)
    print(f"  {json.dumps(d, ensure_ascii=False)[:300]}")

# 4) Get first CPF with 1955 error
cur.execute("""
    SELECT cpf, nr_recibo_original
    FROM pipeline_cpf_results
    WHERE status = 'erro' AND erro_descricao LIKE '%%1955%%'
    ORDER BY cpf LIMIT 1
""")
cpf_row = cur.fetchone()
cpf = cpf_row["cpf"]
recibo = cpf_row["nr_recibo_original"]
print(f"\n\n=== Diagnóstico CPF: {cpf} (recibo: {recibo}) ===")

# 5) S-1210 dados_json for this CPF
cur.execute("""
    SELECT id, nr_recibo, dados_json, arquivo_origem
    FROM explorador_eventos
    WHERE tipo_evento = 'S-1210' AND per_apur = '2025-09' AND cpf = %s
    ORDER BY id
""", (cpf,))
events = cur.fetchall()
print(f"\nEventos S-1210: {len(events)}")
for evt in events:
    d = evt["dados_json"]
    if isinstance(d, str): d = json.loads(d)
    print(f"  id={evt['id']}, recibo={evt['nr_recibo']}, arquivo={evt['arquivo_origem']}")
    print(f"  dados_json keys: {list(d.keys())}")
    print(f"  pagamentos: {json.dumps(d.get('pagamentos', []), ensure_ascii=False)[:500]}")
    print()

# 6) Read actual XML file from disk for this CPF
print("\n=== XML files on disk ===")
xml_dir = "/opt/easy-social/xmls_set2025"
# Find files for this CPF
matching_files = glob.glob(f"{xml_dir}/*S-1210*{cpf}*") + glob.glob(f"{xml_dir}/*s1210*{cpf}*")
if not matching_files:
    # Try broader search
    matching_files = glob.glob(f"{xml_dir}/*{cpf}*S-1210*") + glob.glob(f"{xml_dir}/*{cpf}*")

print(f"Files matching CPF {cpf}: {len(matching_files)}")
for f in matching_files[:5]:
    print(f"  {f}")

# 7) If we have files, read and parse them
for fpath in matching_files[:3]:
    if not fpath.endswith('.xml'):
        continue
    print(f"\n--- {os.path.basename(fpath)} ---")
    with open(fpath, 'r', encoding='utf-8') as fobj:
        xml = fobj.read()
    
    # Tipo do evento
    tipo_match = re.search(r'<evtPgtos|<evtTabRubrica|<evtExclusao|<evtReaworberturaPer', xml)
    if 'evtPgtos' not in xml and 'S-1210' not in fpath:
        print(f"  (not S-1210, skipping)")
        continue
    
    # Extract detalhes
    rubr_blocks = re.findall(r'<itensRemun>(.*?)</itensRemun>', xml, re.DOTALL)
    print(f"  itensRemun blocks: {len(rubr_blocks)}")
    for i, blk in enumerate(rubr_blocks):
        cod = re.search(r'<codRubr>(\d+)</codRubr>', blk)
        vr = re.search(r'<vrRubr>([\d.]+)</vrRubr>', blk)
        if cod and vr:
            c = cod.group(1)
            v = vr.group(1)
            # Get rubrica info
            cur.execute("SELECT tp_rubr, cod_inc_irrf, dsc_rubr FROM explorador_rubricas WHERE cod_rubr = %s LIMIT 1", (c,))
            rinfo = cur.fetchone()
            if rinfo:
                print(f"    codRubr={c}, vrRubr={v}, tpRubr={rinfo['tp_rubr']}, codIncIRRF={rinfo['cod_inc_irrf']}, dsc={rinfo['dsc_rubr'][:50]}")
            else:
                print(f"    codRubr={c}, vrRubr={v}, (rubrica NOT in explorador_rubricas)")

conn.close()
