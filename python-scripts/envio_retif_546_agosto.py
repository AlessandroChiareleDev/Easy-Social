"""Retificação S-1210 rubrica 546 — AGOSTO/2025 (XLSX 07/05/2026 01:16)."""
import os, sys, json, time
from collections import defaultdict
from datetime import datetime
import requests, psycopg2

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)
from db_config import DB_CONFIG

EMPRESA_ID = 1
API_URL    = "http://localhost:8000/api/s1210-repo/enviar-lote-cpfs"
BATCH_SIZE = 50
TIMEOUT    = 600
OUTDIR     = os.path.join(ROOT, "saida_retif_546")
os.makedirs(OUTDIR, exist_ok=True)

XLSX_PATH = os.path.expanduser(r"~\Downloads\Retificação para correção do Adiantamento - S 1210 (546) 082025 (1).xlsx")
PER_AGOSTO = "2025-08"


def carregar_cpfs():
    import openpyxl
    wb = openpyxl.load_workbook(XLSX_PATH, data_only=True)
    ws = wb['Planilha1']
    out = []
    for r in ws.iter_rows(min_row=2, values_only=True):
        cod_empr, comp, comp_mes, mat, concat, cpf = r
        if not cpf: continue
        cpf_clean = ''.join(c for c in str(cpf) if c.isdigit()).zfill(11)
        out.append(cpf_clean)
    seen=set(); uniq=[]
    for c in out:
        if c not in seen: seen.add(c); uniq.append(c)
    return uniq


def main():
    cpfs = carregar_cpfs()
    print(f"[xlsx] {len(cpfs)} CPFs únicos para {PER_AGOSTO}")

    with psycopg2.connect(**DB_CONFIG) as conn, conn.cursor() as cur:
        # scope
        cur.execute("""
            SELECT cpf, lote_num FROM s1210_cpf_scope
             WHERE empresa_id=%s AND per_apur=%s AND cpf=ANY(%s)
        """, (EMPRESA_ID, PER_AGOSTO, cpfs))
        scope = dict(cur.fetchall())
        # recibo
        cur.execute("""
            SELECT DISTINCT ON (cpf) cpf, nr_recibo_novo
              FROM s1210_cpf_envios
             WHERE empresa_id=%s AND per_apur=%s AND status='ok'
               AND nr_recibo_novo IS NOT NULL AND cpf=ANY(%s)
             ORDER BY cpf, enviado_em DESC
        """, (EMPRESA_ID, PER_AGOSTO, cpfs))
        rec = dict(cur.fetchall())
        # plan_saude (só lote 3)
        cur.execute("""
            SELECT cpf, cnpj_operadora, MAX(reg_ans), SUM(valor)::BIGINT
              FROM s1210_operadoras
             WHERE empresa_id=%s AND lote_num=3 AND per_apur=%s
               AND cpf=ANY(%s) AND cnpj_operadora IS NOT NULL
             GROUP BY cpf, cnpj_operadora
        """, (EMPRESA_ID, PER_AGOSTO, cpfs))
        ps_map = defaultdict(list)
        for cpf, cnpj, ans, cents in cur.fetchall():
            cents = int(cents or 0)
            if cents <= 0: continue
            ps_map[cpf].append({"cnpjOper":cnpj,"regANS":ans or "","vlrSaudeTit":round(cents/100,2)})

    sem_scope = [c for c in cpfs if c not in scope]
    sem_recibo = [c for c in cpfs if c in scope and c not in rec]
    print(f"[scope] {len(scope)}/{len(cpfs)}  sem_scope={len(sem_scope)}")
    print(f"[recibo] {len(rec)}/{len(cpfs)}  sem_recibo={len(sem_recibo)}")
    if sem_scope: print(f"  sem_scope: {sem_scope}")
    if sem_recibo: print(f"  sem_recibo: {sem_recibo}")

    # Agrupar por lote
    grupos = defaultdict(list)
    for cpf in cpfs:
        if cpf not in scope or cpf not in rec: continue
        grupos[scope[cpf]].append(cpf)

    for lote, lst in sorted(grupos.items()):
        print(f"  lote={lote} -> {len(lst)} CPFs")

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    log = open(os.path.join(OUTDIR, f"log_ago_{ts}.txt"), "w", encoding="utf-8")
    def out(m): print(m); log.write(m+"\n"); log.flush()

    g_ok=g_err=0
    for lote, lst in sorted(grupos.items()):
        out(f"\n=== {PER_AGOSTO} lote={lote} ({len(lst)} CPFs) ===")
        for i in range(0, len(lst), BATCH_SIZE):
            blk = lst[i:i+BATCH_SIZE]
            payload = {
                "per_apur": PER_AGOSTO, "lote_num": lote, "cpfs": blk,
                "confirmar_producao": True,
                "recibo_override_por_cpf": {c: rec[c] for c in blk if c in rec},
            }
            if lote == 3:
                ps_slice = {c: ps_map[c] for c in blk if c in ps_map}
                if ps_slice: payload["plan_saude_por_cpf"] = ps_slice
            t0=time.time()
            try:
                r = requests.post(API_URL, json=payload, timeout=TIMEOUT)
                r.raise_for_status()
                body = r.json()
            except Exception as e:
                out(f"  [ERR-NET] bloco {i//BATCH_SIZE+1}: {e}")
                continue
            ok = sum(1 for d in body.get("resultados",[]) if d.get("sucesso"))
            err = len(body.get("resultados",[])) - ok
            g_ok += ok; g_err += err
            out(f"  bloco {i//BATCH_SIZE+1} (cpfs {i+1}-{i+len(blk)}): ok={ok} erro={err} elapsed={round(time.time()-t0,1)}s")
            with open(os.path.join(OUTDIR, f"resp_ago_{ts}_{PER_AGOSTO}_l{lote}_b{i//BATCH_SIZE+1}.json"), "w", encoding="utf-8") as f:
                json.dump(body, f, ensure_ascii=False, indent=2, default=str)
            for d in body.get("resultados",[]):
                if not d.get("sucesso"):
                    out(f"    ERR cpf={d.get('cpf')} cod={d.get('codigo_resposta')} {str(d.get('descricao_resposta') or d.get('erro'))[:120]}")

    out(f"\n=== FIM AGOSTO === ok={g_ok} erro={g_err}")
    log.close()


if __name__ == "__main__":
    main()
