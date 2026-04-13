"""
Investigate error 459 via local XMLs and explorador data.
Strategy: Check if these CPFs already have retification events in the explorador
          or XML files that succeeded after lote 28.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from db_config import DB_CONFIG
import psycopg2
import psycopg2.extras

conn = psycopg2.connect(**DB_CONFIG)
cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

# Get the 44 CPFs
cur.execute("""
    SELECT cpf, nr_recibo_original
    FROM pipeline_cpf_results
    WHERE run_id = 1 AND erro_descricao LIKE '%%[459]%%'
    ORDER BY cpf
""")
cpfs_459 = cur.fetchall()
cpf_list = [r['cpf'] for r in cpfs_459]
recibo_map = {r['cpf']: r['nr_recibo_original'] for r in cpfs_459}

print(f"Total CPFs com erro 459: {len(cpf_list)}")

# For each CPF, check ALL events in explorador
cur.execute("""
    SELECT e.cpf, e.tipo_evento, e.nr_recibo, e.cd_resposta, e.arquivo_origem, e.dados_json,
           e.id as evento_id
    FROM explorador_eventos e
    WHERE e.cpf = ANY(%s) AND e.per_apur = '2025-09'
    ORDER BY e.cpf, e.id
""", (cpf_list,))
all_events = cur.fetchall()

# Group by CPF
from collections import defaultdict
by_cpf = defaultdict(list)
for e in all_events:
    by_cpf[e['cpf']].append(e)

print(f"\nTotal events across all 44 CPFs: {len(all_events)}")

# Analyze each CPF
already_retified = 0
needs_retif = 0
unclear = 0

for cpf in cpf_list[:5]:  # Sample first 5
    events = by_cpf[cpf]
    old_recibo = recibo_map[cpf]
    
    print(f"\n{'='*60}")
    print(f"CPF: {cpf}")
    print(f"Recibo original (pipeline): {old_recibo}")
    print(f"Events in explorador:")
    
    s1210_events = []
    for e in events:
        tipo = e['tipo_evento']
        rec = e['nr_recibo'] or '(none)'
        arq = e['arquivo_origem']
        dj = e.get('dados_json') or {}
        ind_retif = dj.get('indRetif', '?') if isinstance(dj, dict) else '?'
        nrRecArqBase = dj.get('nrRecArqBase', '') if isinstance(dj, dict) else ''
        cd = e.get('cd_resposta', '?')
        
        if tipo == 'S-1210':
            s1210_events.append(e)
            print(f"  {tipo} indRetif={ind_retif} recibo={rec} nrRecArqBase={nrRecArqBase} cd={cd} arq={arq}")
        elif tipo in ('S-3000', 'S-5002'):
            print(f"  {tipo} recibo={rec} cd={cd} arq={arq}")
    
    # Check if any S-1210 has indRetif=2 referencing the old recibo
    for e in s1210_events:
        dj = e.get('dados_json') or {}
        if isinstance(dj, dict):
            nrRecArqBase = dj.get('nrRecArqBase', '')
            if nrRecArqBase == old_recibo:
                print(f"  >>> Found retification referencing our recibo! New recibo: {e['nr_recibo']}")

# Count S-1210 events per CPF
print(f"\n{'='*60}")
print("SUMMARY: S-1210 count per CPF:")
counts = {}
for cpf in cpf_list:
    events = by_cpf[cpf]
    s1210_count = sum(1 for e in events if e['tipo_evento'] == 'S-1210')
    counts.setdefault(s1210_count, 0)
    counts[s1210_count] += 1
for cnt, num in sorted(counts.items()):
    print(f"  {num} CPFs have {cnt} S-1210 events")

# Check if any S-1210 has nrRecArqBase matching our old recibos
print(f"\nChecking for retifications in dados_json...")
retif_found = 0
for cpf in cpf_list:
    events = by_cpf[cpf]
    old_recibo = recibo_map[cpf]
    for e in events:
        if e['tipo_evento'] != 'S-1210':
            continue
        dj = e.get('dados_json') or {}
        if isinstance(dj, dict):
            nrRecArqBase = dj.get('nrRecArqBase', '')
            if nrRecArqBase == old_recibo:
                retif_found += 1
                print(f"  CPF {cpf}: retif found! nrRecArqBase={old_recibo[:30]}... newRecibo={e['nr_recibo']}")

print(f"\nTotal retifications found in explorador: {retif_found} / {len(cpf_list)}")

# Also check: search for XML files on disk that might contain these recibos
# We'll do that in a follow-up

conn.close()
