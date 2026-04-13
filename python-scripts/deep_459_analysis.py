"""
Deep analysis of error 459 CPFs.
Need to understand the full event chain and find the ACTIVE S-1210 recibo.

Each CPF has:
- S-1210 original (recibo A) 
- S-3000 exclusion (recibo B) - this excluded some event
- S-1210 from lote 28 (recibo C) - pipeline wrongly used this

The question is: which recibo corresponds to the ACTIVE S-1210?
After S-3000 excluded one S-1210, another was sent. We need to find which one
was NOT excluded and is still active.
"""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from db_config import DB_CONFIG
import psycopg2, psycopg2.extras
from lxml import etree

conn = psycopg2.connect(**DB_CONFIG)
cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

# Get the 44 CPFs
cur.execute("""
    SELECT cpf, nr_recibo_original
    FROM pipeline_cpf_results
    WHERE run_id = 1 AND status = 'erro' AND erro_descricao LIKE '%%459%%'
    ORDER BY cpf
""")
cpfs_459 = cur.fetchall()
cpf_list = [r['cpf'] for r in cpfs_459]
recibo_pipeline = {r['cpf']: r['nr_recibo_original'] for r in cpfs_459}

# Get ALL events for these CPFs, ORDERED BY ID (chronological)
cur.execute("""
    SELECT cpf, tipo_evento, nr_recibo, arquivo_origem, dados_json, id, cd_resposta
    FROM explorador_eventos
    WHERE cpf = ANY(%s) AND per_apur = '2025-09'
    ORDER BY cpf, id
""", (cpf_list,))
all_events = cur.fetchall()

from collections import defaultdict
by_cpf = defaultdict(list)
for e in all_events:
    by_cpf[e['cpf']].append(e)

# Deep analysis of first 3 CPFs
for cpf in cpf_list[:3]:
    events = by_cpf[cpf]
    wrong_recibo = recibo_pipeline[cpf]
    
    print(f"\n{'='*70}")
    print(f"CPF: {cpf}")
    print(f"Pipeline recibo (wrong): {wrong_recibo}")
    print(f"{'='*70}")
    
    for e in events:
        tipo = e['tipo_evento']
        rec = e['nr_recibo'] or '(none)'
        arq = e['arquivo_origem'] or ''
        cd = e.get('cd_resposta', '?')
        dj = e.get('dados_json') or {}
        if isinstance(dj, str):
            dj = json.loads(dj)
        
        extra = ''
        if tipo == 'S-3000' and isinstance(dj, dict):
            extra = f" keys={list(dj.keys())}"
        if tipo == 'S-1210' and isinstance(dj, dict):
            ind = dj.get('indRetif', '?')
            nrRecArqBase = dj.get('nrRecArqBase', '')
            extra = f" indRetif={ind} nrRecArqBase={nrRecArqBase}"
        
        marker = " <<<WRONG" if rec == wrong_recibo else ""
        print(f"  [{e['id']}] {tipo} recibo={rec} cd={cd} arq={arq}{extra}{marker}")

# Now check: what does the S-3000 XML actually contain?
# The S-3000 arquivo_origem has an ID that includes the recibo being excluded
print(f"\n{'='*70}")
print("ANALYZING S-3000 arquivo_origem pattern...")
print(f"{'='*70}")

# S-3000 filename pattern: ID1059690710000002025102412392600002.S-3000.xml
# The number after the CNPJ might encode info about which event was excluded

# Let's check the XML files directly to see what nrRecEvt is in S-3000
sample_cpf = cpf_list[0]
sample_events = by_cpf[sample_cpf]
s3000_events = [e for e in sample_events if e['tipo_evento'] == 'S-3000']
if s3000_events:
    s3 = s3000_events[0]
    print(f"\nS-3000 for {sample_cpf}:")
    print(f"  nr_recibo: {s3['nr_recibo']}")
    print(f"  arquivo: {s3['arquivo_origem']}")
    print(f"  dados_json: {json.dumps(s3.get('dados_json'), indent=2, ensure_ascii=False)[:500]}")

# Critical insight: Look at S-5002 events. The S-5002 filename includes the recibo 
# of the event it's a response to.
print(f"\n{'='*70}")
print("ANALYZING S-5002 (retorno) correlation...")
print(f"{'='*70}")

for cpf in cpf_list[:3]:
    events = by_cpf[cpf]
    s5002s = [e for e in events if e['tipo_evento'] == 'S-5002']
    s1210s = [e for e in events if e['tipo_evento'] == 'S-1210']
    s3000s = [e for e in events if e['tipo_evento'] == 'S-3000']
    
    print(f"\nCPF {cpf}:")
    
    # S-5002 arquivo has format: ID002...{recibo}.S-5002.xml
    # The recibo embedded in the filename tells us which event this S-5002 responds to
    all_recibos = set()
    for s in s1210s:
        if s['nr_recibo']:
            all_recibos.add(s['nr_recibo'])
    for s in s3000s:
        if s['nr_recibo']:
            all_recibos.add(s['nr_recibo'])
    
    print(f"  All recibos: {all_recibos}")
    
    for s5 in s5002s:
        arq = s5['arquivo_origem'] or ''
        # Check which recibo this S-5002 matches
        matched = None
        for rec in all_recibos:
            clean_rec = rec.replace('.', '')
            if clean_rec in arq:
                matched = rec
                break
        print(f"  S-5002 arq={arq} -> matches recibo {matched}")

conn.close()
