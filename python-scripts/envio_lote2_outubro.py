"""
Envio Lote 2 Outubro/2025 APPA (empresa_id=1).

Fluxo:
1. Le CPFs de s1210_cpf_scope (populado por ingest_lote2_outubro.py).
2. Filtra CPFs que ainda NAO tem envio OK (via DISTINCT ON ult status).
3. Carrega planSaude de s1210_operadoras (CNPJ + ANS por CPF).
4. Fatia em blocos de BATCH_SIZE (50) e faz POST sequencial no endpoint
   /api/s1210-repo/enviar-lote-cpfs, 1 POST por bloco.
5. Salva JSON de resposta em saida_lote2_outubro/resp_<ts>.json.

Uso:
  python envio_lote2_outubro.py --dry-run
  python envio_lote2_outubro.py --max 1
  python envio_lote2_outubro.py --max 10
  python envio_lote2_outubro.py
  python envio_lote2_outubro.py --workers 3
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

PER_APUR   = "2025-10"
LOTE_NUM   = 2
EMPRESA_ID = 1
API_URL    = "http://localhost:8000/api/s1210-repo/enviar-lote-cpfs"
BATCH_SIZE = 50
TIMEOUT    = 600
OUTDIR     = os.path.join(ROOT, "saida_lote2_outubro")
os.makedirs(OUTDIR, exist_ok=True)


def carregar_cpfs_pendentes() -> list[str]:
    """CPFs no scope que ainda NAO tem envio com status='ok' ou 'na'."""
    with psycopg2.connect(**DB_CONFIG) as c:
        with c.cursor() as cur:
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
    """Monta plan_saude_por_cpf a partir de s1210_operadoras (per_apur+lote_num).
    1 entrada por CNPJ — rubricas diferentes do mesmo CNPJ sao SOMADAS.
    eSocial nao aceita dois <planSaude> com o mesmo cnpjOper."""
    sql = """
        SELECT cpf,
               cnpj_operadora,
               MAX(reg_ans) AS reg_ans,
               SUM(valor)::BIGINT AS soma_centavos
          FROM s1210_operadoras
         WHERE empresa_id=%s AND per_apur=%s AND lote_num=%s
           AND cnpj_operadora IS NOT NULL
      GROUP BY cpf, cnpj_operadora
      ORDER BY cpf, cnpj_operadora
    """
    out: dict[str, list[dict]] = {}
    with psycopg2.connect(**DB_CONFIG) as c, c.cursor() as cur:
        cur.execute(sql, (EMPRESA_ID, PER_APUR, LOTE_NUM))
        for cpf, cnpj, ans, centavos in cur.fetchall():
            cents = int(centavos or 0)
            if cents <= 0:
                continue
            out.setdefault(cpf, []).append({
                "cnpjOper": cnpj,
                "regANS":   ans or "",
                "vlrSaudeTit": f"{cents / 100:.2f}",
            })
    return out


def carregar_recibos_override_db() -> dict[str, str]:
    """Para cada CPF, pega o nr_recibo_novo do ULTIMO envio OK no mesmo per_apur.
    Cobre o caso de lote anterior ja ter retificado esse CPF."""
    sql = """
        SELECT DISTINCT ON (cpf) cpf, nr_recibo_novo
          FROM s1210_cpf_envios
         WHERE empresa_id=%s AND per_apur=%s AND status IN ('ok', 'ok_recuperado')
           AND nr_recibo_novo IS NOT NULL
         ORDER BY cpf, enviado_em DESC
    """
    with psycopg2.connect(**DB_CONFIG) as c, c.cursor() as cur:
        cur.execute(sql, (EMPRESA_ID, PER_APUR))
        return {cpf: rec for cpf, rec in cur.fetchall()}


def enviar_bloco(
    cpfs: list[str],
    recibos_override: dict[str, str],
    plan_saude_override: dict[str, list[dict]],
) -> dict:
    payload: dict = {
        "per_apur": PER_APUR,
        "lote_num": LOTE_NUM,
        "cpfs":     cpfs,
        "confirmar_producao": True,
    }
    override_slice = {c: recibos_override[c] for c in cpfs if c in recibos_override}
    if override_slice:
        payload["recibo_override_por_cpf"] = override_slice

    ps_slice = {c: plan_saude_override[c] for c in cpfs if c in plan_saude_override}
    if ps_slice:
        payload["plan_saude_por_cpf"] = ps_slice

    t0 = time.time()
    r  = requests.post(API_URL, json=payload, timeout=TIMEOUT)
    r.raise_for_status()
    dt   = time.time() - t0
    body = r.json()
    body["_client_elapsed_s"] = round(dt, 1)
    return body


def resumir(body: dict) -> tuple[int, int, list[tuple[str, str, str]]]:
    ok = err = 0
    erros: list[tuple[str, str, str]] = []
    for det in body.get("resultados", []):
        cpf = det.get("cpf", "")
        if det.get("sucesso"):
            ok += 1
        else:
            err += 1
            erros.append((
                cpf,
                str(det.get("codigo_resposta", "")),
                str(det.get("descricao_resposta") or det.get("erro") or "")[:120],
            ))
    return ok, err, erros


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--max",        type=int, default=None, help="Limite de CPFs (debug)")
    ap.add_argument("--dry-run",    action="store_true")
    ap.add_argument("--batch",      type=int, default=BATCH_SIZE)
    ap.add_argument("--workers",    type=int, default=1,
                    help="Workers paralelos — manter em 1 ou 3 MAX")
    args = ap.parse_args()

    if args.workers > 3:
        print(f"[AVISO] workers={args.workers} excede o limite seguro de 3 — reduzindo para 3")
        args.workers = 3

    cpfs = carregar_cpfs_pendentes()
    print(f"[scope pendente] {len(cpfs)} CPFs em {PER_APUR} lote={LOTE_NUM}")
    if not cpfs:
        print("nada a enviar"); return

    if args.max:
        cpfs = cpfs[: args.max]
        print(f"[--max] reduzido a {len(cpfs)} CPFs")

    recibos_override = carregar_recibos_override_db()
    print(f"[override DB] {len(recibos_override)} recibos vindos de s1210_cpf_envios")

    plan_saude_override = carregar_plan_saude_db()
    print(f"[plan_saude DB] {len(plan_saude_override)} CPFs com CNPJ+ANS de s1210_operadoras")

    if args.dry_run:
        print("[dry-run] primeiros 5 CPFs:", cpfs[:5])
        for c in cpfs[:5]:
            ps = plan_saude_override.get(c)
            print(f"  {c}  planSaude={ps}")
        return

    total_ok = total_err = 0
    batches  = [cpfs[i : i + args.batch] for i in range(0, len(cpfs), args.batch)]
    t_global = time.time()

    if args.workers > 1:
        from concurrent.futures import ThreadPoolExecutor, as_completed
        import threading
        lock = threading.Lock()

        def _job(idx_bloco):
            i, bloco = idx_bloco
            try:
                body = enviar_bloco(bloco, recibos_override, plan_saude_override)
            except requests.exceptions.RequestException as e:
                return (i, None, f"REDE {type(e).__name__}: {e}")
            ok, err, erros = resumir(body)
            ts = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            with open(os.path.join(OUTDIR, f"resp_bloco{i:03d}_{ts}.json"), "w", encoding="utf-8") as f:
                json.dump(body, f, ensure_ascii=False, indent=2)
            return (i, (ok, err, erros, body.get("_client_elapsed_s", 0)), None)

        with ThreadPoolExecutor(max_workers=args.workers) as ex:
            futs = {ex.submit(_job, (i, b)): i for i, b in enumerate(batches, 1)}
            for fut in as_completed(futs):
                i, res, err_msg = fut.result()
                if err_msg:
                    print(f"[bloco {i}] FALHA REDE: {err_msg}")
                    continue
                ok, err, erros, dt_b = res
                with lock:
                    total_ok  += ok
                    total_err += err
                    print(f"[bloco {i:>3}] ok={ok} err={err} tempo={dt_b}s "
                          f"| acumulado ok={total_ok} err={total_err}")
                    for cpf, cod, desc in erros[:3]:
                        print(f"   ERR {cpf} cod={cod} desc={desc[:80]}")
    else:
        for idx, bloco in enumerate(batches, 1):
            print(f"\n=== bloco {idx}/{len(batches)} — {len(bloco)} CPFs ===")
            try:
                body = enviar_bloco(bloco, recibos_override, plan_saude_override)
            except requests.exceptions.RequestException as e:
                print(f"[ERRO REDE] {type(e).__name__}: {e}")
                break

            ok, err, erros = resumir(body)
            total_ok  += ok
            total_err += err

            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            outfile = os.path.join(OUTDIR, f"resp_bloco{idx:03d}_{ts}.json")
            with open(outfile, "w", encoding="utf-8") as f:
                json.dump(body, f, ensure_ascii=False, indent=2)

            dt_b = body.get("_client_elapsed_s", "?")
            print(f"  ok={ok} err={err} tempo={dt_b}s | acumulado ok={total_ok} err={total_err}")
            for cpf, cod, desc in erros[:5]:
                print(f"   ERR {cpf} cod={cod} desc={desc[:100]}")

            if err > 0 and ok == 0:
                print("[AVISO] bloco com 100% erros — parando")
                break

    dt_total = time.time() - t_global
    print(f"\n=== CONCLUIDO === ok={total_ok} err={total_err} "
          f"tempo_total={dt_total:.1f}s")


if __name__ == "__main__":
    main()
