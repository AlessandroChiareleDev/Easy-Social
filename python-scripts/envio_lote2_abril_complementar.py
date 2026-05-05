"""
Envio Lote 2 Abril/2025 APPA — Complementar (106 CPFs pendentes).
Todos sao declaratorios (sem detPlanSaud) conforme confirmado pela cliente.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from datetime import datetime

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

import requests

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)

import psycopg2
import psycopg2.extras
from db_config import DB_CONFIG

PER_APUR   = "2025-04"
LOTE_NUM   = 2
EMPRESA_ID = 1
API_URL    = "http://localhost:8000/api/s1210-repo/enviar-lote-cpfs"
BATCH_SIZE = 30
TIMEOUT    = 600
OUTDIR     = os.path.join(ROOT, "saida_lote2_abril_complementar")
os.makedirs(OUTDIR, exist_ok=True)


def carregar_cpfs_pendentes() -> list[str]:
    """CPFs no scope lote=2 que ainda NAO tem OK/NA neste lote_num=2."""
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
              AND (lv.status IS NULL OR lv.status NOT IN ('ok', 'na'))
            ORDER BY s.cpf
            """,
            (EMPRESA_ID, PER_APUR, LOTE_NUM, EMPRESA_ID, PER_APUR, LOTE_NUM),
        )
        return [r[0] for r in cur.fetchall()]


def carregar_plan_saude_db() -> dict[str, list[dict]]:
    """planSaude por CPF — agrupa por CNPJ (1 planSaude por cnpjOper)."""
    sql = """
        SELECT cpf, cnpj_operadora,
               MAX(reg_ans) AS reg_ans,
               SUM(valor)::BIGINT AS soma
          FROM s1210_operadoras
         WHERE empresa_id=%s AND per_apur=%s AND lote_num=%s
           AND cnpj_operadora IS NOT NULL
      GROUP BY cpf, cnpj_operadora
      ORDER BY cpf, cnpj_operadora
    """
    out: dict[str, list[dict]] = {}
    with psycopg2.connect(**DB_CONFIG) as c, c.cursor() as cur:
        cur.execute(sql, (EMPRESA_ID, PER_APUR, LOTE_NUM))
        for cpf, cnpj, ans, cents in cur.fetchall():
            cents = int(cents or 0)
            if cents <= 0:
                continue
            out.setdefault(cpf, []).append({
                "cnpjOper": cnpj,
                "regANS":   ans or "",
                "vlrSaudeTit": f"{cents/100:.2f}",
            })
    return out


def carregar_recibos_override_db() -> dict[str, str]:
    """Pega ultimo recibo OK por CPF em qualquer lote do mesmo per_apur (retificacao)."""
    sql = """
        SELECT DISTINCT ON (cpf) cpf, nr_recibo_novo
          FROM s1210_cpf_envios
         WHERE empresa_id=%s AND per_apur=%s
           AND status IN ('ok', 'ok_recuperado')
           AND nr_recibo_novo IS NOT NULL
           AND nr_recibo_novo NOT LIKE 'MARCADO%%'
           AND nr_recibo_novo NOT LIKE 'RECIBO_PERDIDO%%'
         ORDER BY cpf, enviado_em DESC
    """
    with psycopg2.connect(**DB_CONFIG) as c, c.cursor() as cur:
        cur.execute(sql, (EMPRESA_ID, PER_APUR))
        return {cpf: rec for cpf, rec in cur.fetchall()}


def enviar_bloco(cpfs, recibos, plan_saude) -> dict:
    payload = {
        "per_apur": PER_APUR,
        "lote_num": LOTE_NUM,
        "cpfs":     cpfs,
        "confirmar_producao": True,
    }
    rec_slice = {c: recibos[c] for c in cpfs if c in recibos}
    if rec_slice:
        payload["recibo_override_por_cpf"] = rec_slice
    ps_slice = {c: plan_saude[c] for c in cpfs if c in plan_saude}
    if ps_slice:
        payload["plan_saude_por_cpf"] = ps_slice
    t0 = time.time()
    r = requests.post(API_URL, json=payload, timeout=TIMEOUT)
    r.raise_for_status()
    body = r.json()
    body["_client_elapsed_s"] = round(time.time() - t0, 1)
    return body


def resumir(body):
    ok = err = 0
    erros = []
    for det in body.get("resultados", []):
        if det.get("sucesso"):
            ok += 1
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
    ap.add_argument("--workers", type=int, default=1)
    args = ap.parse_args()

    if args.workers > 3:
        print(f"[AVISO] workers={args.workers} > 3, limitando a 3")
        args.workers = 3

    cpfs = carregar_cpfs_pendentes()
    print(f"[scope pendente] {len(cpfs)} CPFs em {PER_APUR} lote={LOTE_NUM}")
    if not cpfs:
        print("nada a enviar"); return

    if args.max:
        cpfs = cpfs[:args.max]
        print(f"[--max] {len(cpfs)}")

    recibos = carregar_recibos_override_db()
    print(f"[recibos override] {len(recibos)}")

    plan_saude = carregar_plan_saude_db()
    print(f"[plan_saude] {len(plan_saude)} CPFs")

    if args.dry_run:
        print("primeiros 5:", cpfs[:5])
        for c in cpfs[:5]:
            print(f"  {c} ps={plan_saude.get(c)} rec={recibos.get(c)}")
        return

    total_ok = total_err = 0
    batches = [cpfs[i:i+args.batch] for i in range(0, len(cpfs), args.batch)]
    t0 = time.time()

    if args.workers > 1:
        from concurrent.futures import ThreadPoolExecutor, as_completed
        import threading
        lock = threading.Lock()

        def _job(item):
            i, b = item
            try:
                body = enviar_bloco(b, recibos, plan_saude)
            except requests.exceptions.RequestException as e:
                return (i, None, f"REDE {type(e).__name__}: {e}")
            ok, err, erros = resumir(body)
            ts = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            with open(os.path.join(OUTDIR, f"resp_bloco{i:03d}_{ts}.json"), "w", encoding="utf-8") as f:
                json.dump(body, f, ensure_ascii=False, indent=2)
            return (i, (ok, err, erros, body.get("_client_elapsed_s",0)), None)

        with ThreadPoolExecutor(max_workers=args.workers) as ex:
            futs = {ex.submit(_job, (i, b)): i for i, b in enumerate(batches, 1)}
            for fut in as_completed(futs):
                i, res, msg = fut.result()
                if msg:
                    print(f"[bloco {i}] FALHA: {msg}")
                    continue
                ok, err, erros, dt = res
                with lock:
                    total_ok += ok; total_err += err
                    print(f"[bloco {i:>3}/{len(batches)}] ok={ok} err={err} t={dt}s "
                          f"| acum ok={total_ok} err={total_err}")
                    for cpf, cod, desc in erros[:3]:
                        print(f"   ERR {cpf} cod={cod} {desc[:80]}")
    else:
        for i, b in enumerate(batches, 1):
            print(f"\n=== bloco {i}/{len(batches)} ({len(b)} CPFs) ===")
            try:
                body = enviar_bloco(b, recibos, plan_saude)
            except requests.exceptions.RequestException as e:
                print(f"[ERRO REDE] {e}"); break
            ok, err, erros = resumir(body)
            total_ok += ok; total_err += err
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            with open(os.path.join(OUTDIR, f"resp_bloco{i:03d}_{ts}.json"), "w", encoding="utf-8") as f:
                json.dump(body, f, ensure_ascii=False, indent=2)
            dt = body.get("_client_elapsed_s","?")
            print(f"  ok={ok} err={err} t={dt}s | acum ok={total_ok} err={total_err}")
            for cpf, cod, desc in erros[:5]:
                print(f"   ERR {cpf} cod={cod} {desc[:100]}")
            if err > 0 and ok == 0:
                print("[AVISO] bloco 100% erro — parando"); break

    print(f"\n=== FIM === ok={total_ok} err={total_err} t={time.time()-t0:.1f}s")


if __name__ == "__main__":
    main()
