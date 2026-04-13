"""Check August S-1200 and cross-period references for [1955] CPFs."""
import sys, os, json, re, glob
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from db_config import DB_CONFIG
import psycopg2, psycopg2.extras

conn = psycopg2.connect(**DB_CONFIG, keepalives=1, keepalives_idle=30, keepalives_interval=10, keepalives_count=3)
cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

# 1) Check all perRef values across the 87 CPFs
print("=== Demo references across all [1955] CPFs ===")
cur.execute("""
    SELECT ee.cpf, ee.dados_json
    FROM explorador_eventos ee
    JOIN pipeline_cpf_results pcr ON ee.cpf = pcr.cpf
    WHERE ee.tipo_evento = 'S-1210' AND ee.per_apur = '2025-09'
      AND pcr.status = 'erro' AND pcr.erro_descricao LIKE '%%1955%%'
      AND ee.nr_recibo = pcr.nr_recibo_original
    ORDER BY cpf
""")
# Count how many reference August
aug_count = 0
sep_only_count = 0
total = 0
sample_cpfs = []
for r in cur.fetchall():
    total += 1
    d = r['dados_json']
    if isinstance(d, str): d = json.loads(d)
    pagamentos = d.get('pagamentos', [])
    per_refs = [p.get('perRef') for p in pagamentos]
    has_aug = any('2025-08' in (ref or '') for ref in per_refs)
    if has_aug:
        aug_count += 1
        if len(sample_cpfs) < 3:
            sample_cpfs.append(r['cpf'])
    else:
        sep_only_count += 1

print(f"Total [1955] CPFs com S-1210: {total}")
print(f"  Com referência agosto: {aug_count}")
print(f"  Somente setembro: {sep_only_count}")

# 2) For a sample CPF, check the error value vs rubrica 571 value
print("\n=== Checking error value vs rubrica 571 value ===")
# First, get rubrica 571 values from S-1200 for sample CPFs
CPF = '00140303570'
xml_dir = "/opt/easy-social/xmls_set2025"

cur.execute("""
    SELECT arquivo_origem
    FROM explorador_eventos
    WHERE tipo_evento = 'S-1200' AND cpf = %s AND per_apur = '2025-09'
    ORDER BY id LIMIT 1
""", (CPF,))
r = cur.fetchone()
if r:
    fpath = f"{xml_dir}/{r['arquivo_origem']}"
    if os.path.exists(fpath):
        with open(fpath) as f:
            xml = f.read()
        # Find ALL occurrences of rubrica 571
        rubr_571 = re.findall(r'<codRubr>571</codRubr>.*?<vrRubr>([\d.]+)</vrRubr>', xml, re.DOTALL)
        print(f"CPF {CPF}: rubrica 571 values in S-1200 Sep = {rubr_571}")

# 3) Check reenvio log for this CPF's error value
log_files = glob.glob("/tmp/reenvio_erro1955_*.log")
if log_files:
    latest = sorted(log_files)[-1]
    print(f"\nReenvio log: {latest}")
    with open(latest) as f:
        for line in f:
            if CPF in line and '1955' in line:
                print(f"  {line.strip()[:200]}")
            elif CPF in line and 'somatório' in line.lower():
                print(f"  {line.strip()[:200]}")

# 4) For first 3 CPFs with [1955], check rubrica 571 value and error somatório
print("\n=== Rubrica 571 value vs error somatório for sample CPFs ===")
cur.execute("""
    SELECT cpf FROM pipeline_cpf_results
    WHERE status = 'erro' AND erro_descricao LIKE '%%1955%%'
    ORDER BY cpf LIMIT 5
""")
sample = [r['cpf'] for r in cur.fetchall()]

for cpf in sample:
    # Get S-1200 file
    cur.execute("""
        SELECT arquivo_origem FROM explorador_eventos
        WHERE tipo_evento = 'S-1200' AND cpf = %s AND per_apur = '2025-09'
        ORDER BY id LIMIT 1
    """, (cpf,))
    r = cur.fetchone()
    rubr_571_val = None
    if r:
        fpath = f"{xml_dir}/{r['arquivo_origem']}"
        if os.path.exists(fpath):
            with open(fpath) as f:
                xml = f.read()
            vals = re.findall(r'<codRubr>571</codRubr>.*?<vrRubr>([\d.]+)</vrRubr>', xml, re.DOTALL)
            if vals:
                rubr_571_val = sum(float(v) for v in vals)
    
    # Get error somatório from log
    error_som = None
    if log_files:
        with open(sorted(log_files)[-1]) as f:
            capture_next = False
            for line in f:
                if cpf in line and '1955' in line:
                    capture_next = True
                elif capture_next and 'somatório' in line.lower():
                    m = re.search(r'somatório\s+([-\d.]+)', line)
                    if m:
                        error_som = float(m.group(1))
                    capture_next = False
    
    print(f"CPF {cpf}: rubrica_571_value={rubr_571_val}, error_somatório={error_som}, "
          f"match={'YES' if rubr_571_val and error_som and abs(rubr_571_val + error_som) < 0.01 else 'NO/partial'}")

# 5) Check if there's ANY S-1200 for August for any of these CPFs  
print("\n=== Any August S-1200 for [1955] CPFs? ===")
cur.execute("""
    SELECT count(*) as cnt
    FROM explorador_eventos ee
    JOIN pipeline_cpf_results pcr ON ee.cpf = pcr.cpf
    WHERE ee.tipo_evento = 'S-1200' AND ee.per_apur = '2025-08'
      AND pcr.status = 'erro' AND pcr.erro_descricao LIKE '%%1955%%'
""")
print(f"August S-1200 events for [1955] CPFs: {cur.fetchone()['cnt']}")

# 6) Check: what % of ALL 7771 CPFs have rubrica 571 in S-1200?
print("\n=== Rubrica 571 prevalence ===")
cur.execute("""
    SELECT count(DISTINCT cpf) as cnt
    FROM explorador_eventos
    WHERE tipo_evento = 'S-1200' AND per_apur = '2025-09'
""")
total_s1200 = cur.fetchone()['cnt']
print(f"Total CPFs with S-1200 Sep 2025: {total_s1200}")

# Check by scanning XML files for rubrica 571 presence (sample)
print("(Checking prevalence by scanning S-1200 XMLs for a sample...)")
cur.execute("""
    SELECT DISTINCT ee.cpf, ee.arquivo_origem, 
           CASE WHEN pcr.status = 'erro' AND pcr.erro_descricao LIKE '%%1955%%' THEN true ELSE false END as is_1955
    FROM explorador_eventos ee
    LEFT JOIN pipeline_cpf_results pcr ON ee.cpf = pcr.cpf
    WHERE ee.tipo_evento = 'S-1200' AND ee.per_apur = '2025-09'
    ORDER BY ee.cpf
    LIMIT 200
""")
rows = cur.fetchall()
has_571_and_ok = 0
has_571_and_1955 = 0
no_571_and_ok = 0
no_571_and_1955 = 0
for r in rows:
    fpath = f"{xml_dir}/{r['arquivo_origem']}"
    has_571 = False
    if os.path.exists(fpath):
        with open(fpath) as f:
            xml = f.read()
        has_571 = '<codRubr>571</codRubr>' in xml
    
    if has_571 and r['is_1955']:
        has_571_and_1955 += 1
    elif has_571 and not r['is_1955']:
        has_571_and_ok += 1
    elif not has_571 and r['is_1955']:
        no_571_and_1955 += 1
    else:
        no_571_and_ok += 1

print(f"  Has rubrica 571 AND [1955] error: {has_571_and_1955}")
print(f"  Has rubrica 571 AND OK: {has_571_and_ok}")
print(f"  No rubrica 571 AND [1955] error: {no_571_and_1955}")
print(f"  No rubrica 571 AND OK: {no_571_and_ok}")

conn.close()
