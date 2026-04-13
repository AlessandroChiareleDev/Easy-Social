"""Quick schema check for batch fix script planning."""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from db_config import DB_CONFIG
import psycopg2, psycopg2.extras

conn = psycopg2.connect(**DB_CONFIG, keepalives=1, keepalives_idle=30, keepalives_interval=10, keepalives_count=3)
cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

# 1) explorador_rubricas columns
cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'explorador_rubricas' ORDER BY ordinal_position")
print("EXPLORADOR cols:", [r['column_name'] for r in cur.fetchall()])

# Sample 571 and 509
for cod in ['571', '509', '843']:
    cur.execute("SELECT * FROM explorador_rubricas WHERE cod_rubr = %s LIMIT 1", (cod,))
    r = cur.fetchone()
    if r:
        print(f"\nExplorador {cod}:", json.dumps({k: str(v) for k,v in dict(r).items() if v is not None}, indent=2, ensure_ascii=False))
    else:
        print(f"\nExplorador {cod}: NOT FOUND")

# 2) cruzamento_eb columns  
cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'cruzamento_eb' ORDER BY ordinal_position")
print("\nCRUZAMENTO cols:", [r['column_name'] for r in cur.fetchall()])

# Sample wrong rubricas from cruzamento_eb
for cod in ['509', '516', '843']:
    cur.execute("SELECT * FROM cruzamento_eb WHERE cod_rubrica = %s LIMIT 1", (cod,))
    r = cur.fetchone()
    if r:
        d = {k: str(v) for k,v in dict(r).items() if v is not None}
        print(f"\nCruzamento {cod}:", json.dumps(d, indent=2, ensure_ascii=False))
    else:
        print(f"\nCruzamento {cod}: NOT FOUND")

# 3) Check esocial_depara for iniValid info
cur.execute("SELECT DISTINCT campo FROM esocial_depara LIMIT 20")
print("\nDepara campos:", [r['campo'] for r in cur.fetchall()])

# 4) Get detail from explorador for wrong rubricas
cur.execute("""
    SELECT er.cod_rubr, er.tp_rubr, er.nat_rubr,
           er.cod_inc_cp, er.cod_inc_irrf, er.cod_inc_fgts, er.ide_tab_rubr
    FROM explorador_rubricas er
    WHERE er.cod_rubr IN ('509','516','843','580')
""")
for r in cur.fetchall():
    print(f"\nExpl detail {r['cod_rubr']}: tpRubr={r['tp_rubr']}, nat={r['nat_rubr']}, cp={r['cod_inc_cp']}, irrf={r['cod_inc_irrf']}, fgts={r['cod_inc_fgts']}")

# 5) Check cruzamento_eb for iniValid or similar
cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'esocial_envios' ORDER BY ordinal_position")
print("\nENVIOS cols:", [r['column_name'] for r in cur.fetchall()])

# 6) Check tabela_marcos for iniValid-like info and description 
cur.execute("SELECT codigo, tipo_rb, tipo, descricao, nat_rb FROM tabela_marcos WHERE codigo IN ('509','516','843','580') LIMIT 10")
for r in cur.fetchall():
    print(f"\nMarcos {r['codigo']}: tipo_rb={r['tipo_rb']}, tipo={r['tipo']}, nat={r['nat_rb']}, desc={r['descricao']}")

# 7) How many explorador rubricas match the 76 wrong ones?
wrong_codes = ['509','516','520','521','522','524','526','530','537','544','546','547','550','552','554','555','556','558','566','575','580','582','585','586','587','590','594','595','596','600','605','606','607','610','615','616','619','621','627','631','638','640','641','656','657','658','659','667','677','686','698','701','702','703','709','715','716','724','729','730','733','748','767','772','774','775','779','790','838','842','843','895','899','964','971','1112']
cur.execute("SELECT cod_rubr FROM explorador_rubricas WHERE cod_rubr = ANY(%s)", (wrong_codes,))
found = [r['cod_rubr'] for r in cur.fetchall()]
not_found = [c for c in wrong_codes if c not in found]
print(f"\n--- Match explorador: {len(found)}/{len(wrong_codes)} ---")
if not_found:
    print(f"NOT in explorador (need depara): {not_found}")

conn.close()
print("\nDONE")
