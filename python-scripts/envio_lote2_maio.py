"""Envio Lote 2 Maio/2025 APPA - copia de envio_lote2_outubro.py com PER_APUR=2025-05."""
from __future__ import annotations
import argparse, json, os, sys, time
from datetime import datetime
try: sys.stdout.reconfigure(encoding="utf-8")
except Exception: pass
import requests, psycopg2, psycopg2.extras
ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)
from db_config import DB_CONFIG

PER_APUR   = "2025-05"
LOTE_NUM   = 2
EMPRESA_ID = 1
API_URL    = "http://localhost:8000/api/s1210-repo/enviar-lote-cpfs"
BATCH_SIZE = 15
TIMEOUT    = 600
OUTDIR     = os.path.join(ROOT, "saida_lote2_maio")
os.makedirs(OUTDIR, exist_ok=True)


def carregar_cpfs_pendentes():
    with psycopg2.connect(**DB_CONFIG) as c, c.cursor() as cur:
        cur.execute(
            """
            WITH lv AS (
              SELECT DISTINCT ON (cpf) cpf, status
              FROM s1210_cpf_envios
              WHERE empresa_id=%s AND per_apur=%s AND lote_num=%s
              ORDER BY cpf, enviado_em DESC NULLS LAST
            )
            SELECT s.cpf
            FROM s1210_cpf_scope s
            LEFT JOIN lv ON lv.cpf = s.cpf
            WHERE s.empresa_id=%s AND s.per_apur=%s AND s.lote_num=%s
              AND (lv.status IS NULL OR lv.status NOT IN ('ok','na'))
            ORDER BY s.cpf
            """,
            (EMPRESA_ID, PER_APUR, LOTE_NUM, EMPRESA_ID, PER_APUR, LOTE_NUM),
        )
        return [r[0] for r in cur.fetchall()]


def carregar_plan_saude_db():
    sql = """
        SELECT cpf, cnpj_operadora, MAX(reg_ans), SUM(valor)::BIGINT
          FROM s1210_operadoras
         WHERE empresa_id=%s AND per_apur=%s AND lote_num=%s
           AND cnpj_operadora IS NOT NULL
      GROUP BY cpf, cnpj_operadora
      ORDER BY cpf, cnpj_operadora
    """
    out = {}
    with psycopg2.connect(**DB_CONFIG) as c, c.cursor() as cur:
        cur.execute(sql, (EMPRESA_ID, PER_APUR, LOTE_NUM))
        for cpf, cnpj, ans, cents in cur.fetchall():
            cents = int(cents or 0)
            if cents <= 0: continue
            out.setdefault(cpf, []).append({
                "cnpjOper": cnpj, "regANS": ans or "",
                "vlrSaudeTit": f"{cents/100:.2f}",
            })
    return out


def carregar_recibos_override_db():
    sql = """
        SELECT DISTINCT ON (cpf) cpf, nr_recibo_novo
          FROM s1210_cpf_envios
         WHERE empresa_id=%s AND per_apur=%s AND status IN ('ok','ok_recuperado')
           AND nr_recibo_novo IS NOT NULL
         ORDER BY cpf, enviado_em DESC
    """
    with psycopg2.connect(**DB_CONFIG) as c, c.cursor() as cur:
        cur.execute(sql, (EMPRESA_ID, PER_APUR))
        return {cpf: rec for cpf, rec in cur.fetchall()}


def enviar_bloco(cpfs, recibos_override, plan_saude_override):
    payload = {"per_apur": PER_APUR, "lote_num": LOTE_NUM,
               "cpfs": cpfs, "confirmar_producao": True}
    ov = {c: recibos_override[c] for c in cpfs if c in recibos_override}
    if ov: payload["recibo_override_por_cpf"] = ov
    ps = {c: plan_saude_override[c] for c in cpfs if c in plan_saude_override}
    if ps: payload["plan_saude_por_cpf"] = ps
    t0 = time.time()
    r = requests.post(API_URL, json=payload, timeout=TIMEOUT)
    r.raise_for_status()
    body = r.json()
    body["_client_elapsed_s"] = round(time.time()-t0, 1)
    return body


def resumir(body):
    ok = err = 0; erros = []
    for det in body.get("resultados", []):
        if det.get("sucesso"): ok += 1
        else:
            err += 1
            erros.append((det.get("cpf",""), str(det.get("codigo_resposta","")),
                          str(det.get("descricao_resposta") or det.get("erro") or "")[:120]))
    return ok, err, erros


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--max", type=int, default=None)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--batch", type=int, default=BATCH_SIZE)
    args = ap.parse_args()

    cpfs = carregar_cpfs_pendentes()
    print(f"[scope pendente] {len(cpfs)} CPFs em {PER_APUR} lote={LOTE_NUM}")
    if not cpfs:
        print("nada a enviar"); return
    if args.max: cpfs = cpfs[:args.max]; print(f"[--max] {len(cpfs)} CPFs")

    rec_ov = carregar_recibos_override_db()
    print(f"[recibos override] {len(rec_ov)}")
    ps_ov = carregar_plan_saude_db()
    print(f"[plan_saude] {len(ps_ov)} CPFs com operadora")

    if args.dry_run:
        for c in cpfs[:5]:
            print(f"  {c} ps={ps_ov.get(c)}")
        return

    tot_ok = tot_err = 0
    batches = [cpfs[i:i+args.batch] for i in range(0, len(cpfs), args.batch)]
    t0 = time.time()
    for i, bloco in enumerate(batches, 1):
        print(f"\n--- Bloco {i}/{len(batches)}: {len(bloco)} CPFs ---")
        try:
            body = enviar_bloco(bloco, rec_ov, ps_ov)
        except requests.exceptions.RequestException as e:
            print(f"  REDE FALHOU: {e}"); break
        ok, err, erros = resumir(body)
        tot_ok += ok; tot_err += err
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        with open(os.path.join(OUTDIR, f"resp_bloco{i:03d}_{ts}.json"), "w", encoding="utf-8") as f:
            json.dump(body, f, ensure_ascii=False, indent=2)
        print(f"  OK={ok} ERR={err} elapsed={body.get('_client_elapsed_s')}s")
        for cpf, cod, desc in erros[:5]:
            print(f"    ERR {cpf} cod={cod} {desc}")

    print(f"\n=== TOTAL: ok={tot_ok} err={tot_err} tempo={time.time()-t0:.0f}s ===")


if __name__ == "__main__":
    main()
