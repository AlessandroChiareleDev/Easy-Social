import psycopg2, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from db_config import DB_CONFIG

conn = psycopg2.connect(**DB_CONFIG, keepalives=1, keepalives_idle=30, keepalives_interval=10, keepalives_count=3)
cur = conn.cursor()

# cruzamento_eb columns
cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'cruzamento_eb' ORDER BY ordinal_position")
print('cruzamento_eb columns:')
for r in cur.fetchall(): print(f'  {r[0]}')

# Check sample data for 571, 572
cur.execute("SELECT * FROM cruzamento_eb WHERE cod_rubrica IN ('571','572')")
if cur.description:
    cols = [desc[0] for desc in cur.description]
    for r in cur.fetchall():
        print(f'\ncod_rubrica={r[cols.index("cod_rubrica")]}:')
        for c, v in zip(cols, r):
            print(f'  {c}: {v}')

# Also check explorador_rubricas - what's the source of tpRubr?
print("\n\n=== explorador_rubricas for 571, 572 ===")
cur.execute("""
    SELECT DISTINCT er.cod_rubr, er.tp_rubr, er.nat_rubr, er.cod_inc_irrf
    FROM explorador_rubricas er
    WHERE er.cod_rubr IN ('571','572') AND er.tp_rubr IS NOT NULL
""")
for r in cur.fetchall():
    print(f'  codRubr={r[0]}: tpRubr={r[1]}, natRubr={r[2]}, codIncIRRF={r[3]}')

# Check depara for tpRubr
print("\n\n=== esocial_depara for tpRubr of 571, 572 ===")
cur.execute("""
    SELECT * FROM esocial_depara WHERE campo = 'tpRubr' AND cod_rubrica IN ('571','572')
""")
if cur.description:
    cols = [desc[0] for desc in cur.description]
    for r in cur.fetchall():
        print(f'  {dict(zip(cols, r))}')

# Check rubricas-pendentes query
print("\n\n=== rubricas-pendentes data for 571, 572 ===")
cur.execute("""
    SELECT ce.cod_rubrica, ce.descricao, ce.incid_irrf, 
           ce.incid_base_legal_irrf, ce.envio_status,
           dp_tp.valor_novo as tprubr_depara
    FROM cruzamento_eb ce
    LEFT JOIN esocial_depara dp_tp 
        ON ce.cod_rubrica = dp_tp.cod_rubrica AND dp_tp.campo = 'tpRubr'
    WHERE ce.cod_rubrica IN ('571','572')
""")
if cur.description:
    cols = [desc[0] for desc in cur.description]
    for r in cur.fetchall():
        print(f'  {dict(zip(cols, r))}')

conn.close()
