"""Dry-run: carrega dados das 76 rubricas e mostra preview sem enviar."""
import sys, os, json, logging
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from db_config import DB_CONFIG
import psycopg2, psycopg2.extras

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("dryrun")

WRONG_CODES = [
    '509','516','520','521','522','524','526','530','537','544',
    '546','547','550','552','554','555','556','558','566','575',
    '580','582','585','586','587','590','594','595','596','600',
    '605','606','607','610','615','616','619','621','627','631',
    '638','640','641','656','657','658','659','667','677','686',
    '698','701','702','703','709','715','716','724','729','730',
    '733','748','767','772','774','775','779','790','838','842',
    '843','895','899','964','971','1112',
]

def _extract_code(base_legal_str):
    if not base_legal_str:
        return "0"
    s = str(base_legal_str).strip()
    if " - " in s:
        return s.split(" - ")[0].strip()
    try:
        int(s)
        return s
    except ValueError:
        return "0"

conn = psycopg2.connect(**DB_CONFIG, keepalives=1, keepalives_idle=30, keepalives_interval=10, keepalives_count=3)
cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

# 1) cruzamento_eb
cur.execute("""
    SELECT cod_rubrica, descricao, cod_natureza,
           incid_base_legal_inss, incid_base_legal_irrf, incid_base_legal_fgts,
           ini_valid_esocial, envio_status
    FROM cruzamento_eb
    WHERE cod_rubrica = ANY(%s) AND envio_status IN ('enviado', 'feito')
""", (WRONG_CODES,))
cruzamento = {r['cod_rubrica']: dict(r) for r in cur.fetchall()}
print(f"Cruzamento: {len(cruzamento)}/{len(WRONG_CODES)}")
not_in_cruz = [c for c in WRONG_CODES if c not in cruzamento]
if not_in_cruz:
    print(f"  NOT in cruzamento: {not_in_cruz}")

# 2) explorador tp_rubr
cur.execute("""
    SELECT DISTINCT cod_rubr, tp_rubr
    FROM explorador_rubricas
    WHERE cod_rubr = ANY(%s) AND tp_rubr IS NOT NULL
""", (WRONG_CODES,))
expl_tp = {}
for r in cur.fetchall():
    expl_tp[r['cod_rubr']] = int(r['tp_rubr'])
print(f"Explorador tpRubr: {len(expl_tp)}")

# 3) depara tp
cur.execute("""
    SELECT cod_rubrica, valor_novo FROM esocial_depara
    WHERE campo = 'tpRubr' AND cod_rubrica = ANY(%s)
""", (WRONG_CODES,))
depara_tp = {str(r['cod_rubrica']): r['valor_novo'] for r in cur.fetchall()}
print(f"Depara tpRubr: {len(depara_tp)}")

# 4) marcos tp
cur.execute("""
    SELECT codigo, tipo_rb FROM tabela_marcos WHERE codigo = ANY(%s)
""", (WRONG_CODES,))
marcos_tp = {str(r['codigo']): r['tipo_rb'] for r in cur.fetchall()}
print(f"Marcos tpRubr: {len(marcos_tp)}")

# 5) depara pis
cur.execute("""
    SELECT cod_rubrica, valor_novo FROM esocial_depara
    WHERE campo = 'codIncPisPasep' AND cod_rubrica = ANY(%s)
""", (WRONG_CODES,))
depara_pis = {str(r['cod_rubrica']): r['valor_novo'] for r in cur.fetchall()}
print(f"Depara PIS: {len(depara_pis)}")

# Montar
print(f"\n{'Cod':>5} {'tpRubr':>6} {'Fonte':>10} {'nat':>5} {'cp':>3} {'irrf':>4} {'fgts':>4} {'pis':>3} {'iniValid':>10} Descrição")
print("=" * 120)

ok_count = 0
for cod in sorted(WRONG_CODES, key=lambda x: int(x)):
    c = cruzamento.get(cod)
    if not c:
        print(f"{cod:>5} *** NÃO ENCONTRADO EM CRUZAMENTO ***")
        continue
    
    # tpRubr resolution
    tp = expl_tp.get(cod)
    fonte = "explorador"
    if tp is None:
        v = depara_tp.get(cod)
        if v:
            tp = int(v)
            fonte = "depara"
    if tp is None:
        v = marcos_tp.get(cod)
        if v:
            tp = int(v)
            fonte = "marcos"
    if tp is None:
        tp = "?"
        fonte = "???"
    
    nat = c.get('cod_natureza') or '?'
    cp = _extract_code(c.get('incid_base_legal_inss'))
    irrf = _extract_code(c.get('incid_base_legal_irrf'))
    fgts = _extract_code(c.get('incid_base_legal_fgts'))
    pis = depara_pis.get(cod, '00')
    ini = c.get('ini_valid_esocial') or '?'
    desc = (c.get('descricao') or '?')[:45]
    
    flag = "" if tp != "?" and tp != 1 else " ⚠"
    print(f"{cod:>5} {str(tp):>6} {fonte:>10} {str(nat):>5} {cp:>3} {irrf:>4} {fgts:>4} {pis:>3} {str(ini):>10} {desc}{flag}")
    if tp != "?" and tp != 1:
        ok_count += 1

print(f"\n{'='*120}")
print(f"Prontas para envio: {ok_count}/{len(WRONG_CODES)}")
conn.close()
