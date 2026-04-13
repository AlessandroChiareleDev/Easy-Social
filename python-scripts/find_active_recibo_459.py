"""
Discover the CORRECT active recibo for each of the 44 CPFs with error 459.
Check what the S-3000 excluded to understand which S-1210 recibo is still active.
"""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from db_config import DB_CONFIG
import psycopg2, psycopg2.extras
from lxml import etree

conn = psycopg2.connect(**DB_CONFIG)
cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

# Get the 44 CPFs with their wrong recibo
cur.execute("""
    SELECT cpf, nr_recibo_original
    FROM pipeline_cpf_results
    WHERE run_id = 1 AND erro_descricao LIKE '%%[459]%%'
    ORDER BY cpf
""")
cpfs_459 = cur.fetchall()
cpf_list = [r['cpf'] for r in cpfs_459]
recibo_pipeline = {r['cpf']: r['nr_recibo_original'] for r in cpfs_459}

print(f"Total CPFs: {len(cpf_list)}")

# Get ALL events for these CPFs (S-1210, S-3000, S-5002)
cur.execute("""
    SELECT cpf, tipo_evento, nr_recibo, arquivo_origem, dados_json, id
    FROM explorador_eventos
    WHERE cpf = ANY(%s) AND per_apur = '2025-09'
    ORDER BY cpf, id
""", (cpf_list,))
all_events = cur.fetchall()

from collections import defaultdict
by_cpf = defaultdict(list)
for e in all_events:
    by_cpf[e['cpf']].append(e)

# For each CPF, figure out the correct active recibo
results = []
for cpf in cpf_list:
    events = by_cpf[cpf]
    wrong_recibo = recibo_pipeline[cpf]
    
    s1210s = [e for e in events if e['tipo_evento'] == 'S-1210']
    s3000s = [e for e in events if e['tipo_evento'] == 'S-3000']
    
    # Get recibos from S-1210
    s1210_recibos = [e['nr_recibo'] for e in s1210s if e['nr_recibo']]
    
    # Check S-3000 dados_json to see which recibo was excluded
    excluded_recibos = set()
    for s3 in s3000s:
        dj = s3.get('dados_json') or {}
        if isinstance(dj, dict):
            # S-3000 might have nrRecEvt in dados_json
            nr_rec_evt = dj.get('nrRecEvt', '')
            if nr_rec_evt:
                excluded_recibos.add(nr_rec_evt)
    
    # Active recibos = all S-1210 recibos minus excluded ones
    active = [r for r in s1210_recibos if r not in excluded_recibos and r != wrong_recibo]
    
    # If active is empty, the non-pipeline recibo might be active
    other_recibos = [r for r in s1210_recibos if r != wrong_recibo]
    
    results.append({
        'cpf': cpf,
        'wrong': wrong_recibo,
        's1210_recibos': s1210_recibos,
        'excluded': list(excluded_recibos),
        'active': active,
        'other': other_recibos,
    })

# Print analysis
print(f"\n=== ANALYSIS (first 5 CPFs) ===")
for r in results[:5]:
    print(f"\nCPF: {r['cpf']}")
    print(f"  Pipeline used (wrong): {r['wrong']}")
    print(f"  All S-1210 recibos: {r['s1210_recibos']}")
    print(f"  S-3000 excluded: {r['excluded']}")
    print(f"  Possible active: {r['active']}")
    print(f"  Other (not pipeline): {r['other']}")

# Summary
has_other = sum(1 for r in results if r['other'])
has_active = sum(1 for r in results if r['active'])
print(f"\n=== SUMMARY ===")
print(f"CPFs with another S-1210 recibo: {has_other}")
print(f"CPFs with active recibo (excluding S-3000): {has_active}")

# Check S-3000 dados_json to see if nrRecEvt is there
print(f"\n=== S-3000 SAMPLE ===")
for e in all_events:
    if e['tipo_evento'] == 'S-3000':
        dj = e.get('dados_json') or {}
        if isinstance(dj, dict):
            print(f"CPF={e['cpf']} nr_recibo={e['nr_recibo']} dados_json keys={list(dj.keys())}")
            print(f"  dados_json sample: {json.dumps(dj, ensure_ascii=False)[:300]}")
        break

conn.close()
