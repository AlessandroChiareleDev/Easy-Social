"""Envio Lote 2 Setembro/2025 APPA."""
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
from db_config import DB_CONFIG

PER_APUR = "2025-09"
LOTE_NUM = 2
EMPRESA_ID = 1
API_URL = "http://localhost:8000/api/s1210-repo/enviar-lote-cpfs"
BATCH_SIZE = 50
TIMEOUT = 600
OUTDIR = os.path.join(ROOT, "saida_lote2_setembro")
os.makedirs(OUTDIR, exist_ok=True)


def carregar_cpfs_pendentes() -> list[str]:
    with psycopg2.connect(**DB_CONFIG) as conn, conn.cursor() as cur:
        cur.execute(
            """
            WITH lv AS (
              SELECT DISTINCT ON (cpf) cpf, status
                FROM s1210_cpf_envios
               WHERE empresa_id=%s AND per_apur=%s AND lote_num=%s
               ORDER BY cpf, enviado_em DESC NULLS LAST, id DESC
            )
            SELECT s.cpf
              FROM s1210_cpf_scope s
              LEFT JOIN lv ON lv.cpf=s.cpf
             WHERE s.empresa_id=%s AND s.per_apur=%s AND s.lote_num=%s
               AND (lv.status IS NULL OR lv.status NOT IN ('ok', 'na'))
             ORDER BY s.cpf
            """,
            (EMPRESA_ID, PER_APUR, LOTE_NUM, EMPRESA_ID, PER_APUR, LOTE_NUM),
        )
        return [row[0] for row in cur.fetchall()]


def filtrar_cpfs_por_erro(cpfs: list[str], modo: str | None) -> list[str]:
    if not modo:
        return cpfs
    with psycopg2.connect(**DB_CONFIG) as conn, conn.cursor() as cur:
        cur.execute(
            """
            WITH lv AS (
              SELECT DISTINCT ON (cpf) cpf, codigo_resposta, erro_descricao
                FROM s1210_cpf_envios
               WHERE empresa_id=%s AND per_apur=%s AND lote_num=%s
                 AND cpf=ANY(%s)
               ORDER BY cpf, enviado_em DESC NULLS LAST, id DESC
            )
            SELECT cpf
              FROM lv
             WHERE (%s='timeout' AND COALESCE(erro_descricao,'') ILIKE '%%timeout%%')
                OR (%s='401' AND codigo_resposta='401')
                OR (%s='sem_codigo' AND codigo_resposta IS NULL)
             ORDER BY cpf
            """,
            (EMPRESA_ID, PER_APUR, LOTE_NUM, cpfs, modo, modo, modo),
        )
        return [row[0] for row in cur.fetchall()]


def carregar_plan_saude_db() -> dict[str, list[dict]]:
    sql = """
        SELECT cpf, cnpj_operadora, MAX(reg_ans) AS reg_ans, SUM(valor)::BIGINT AS centavos
          FROM s1210_operadoras
         WHERE empresa_id=%s AND per_apur=%s AND lote_num=%s
           AND cnpj_operadora IS NOT NULL
         GROUP BY cpf, cnpj_operadora
         ORDER BY cpf, cnpj_operadora
    """
    out: dict[str, list[dict]] = {}
    with psycopg2.connect(**DB_CONFIG) as conn, conn.cursor() as cur:
        cur.execute(sql, (EMPRESA_ID, PER_APUR, LOTE_NUM))
        for cpf, cnpj, ans, centavos in cur.fetchall():
            cents = int(centavos or 0)
            if cents <= 0:
                continue
            out.setdefault(cpf, []).append({
                "cnpjOper": cnpj,
                "regANS": ans or "",
                "vlrSaudeTit": f"{cents / 100:.2f}",
            })
    return out


def carregar_recibos_override_db() -> dict[str, str]:
    sql = """
        SELECT DISTINCT ON (cpf) cpf, nr_recibo_novo
          FROM s1210_cpf_envios
         WHERE empresa_id=%s AND per_apur=%s AND status IN ('ok', 'ok_recuperado')
           AND nr_recibo_novo IS NOT NULL
         ORDER BY cpf, enviado_em DESC NULLS LAST, id DESC
    """
    with psycopg2.connect(**DB_CONFIG) as conn, conn.cursor() as cur:
        cur.execute(sql, (EMPRESA_ID, PER_APUR))
        return {cpf: recibo for cpf, recibo in cur.fetchall()}


def enviar_bloco(cpfs: list[str], recibos: dict[str, str], planos: dict[str, list[dict]], forcar_inclusao: bool) -> dict:
    payload: dict = {
        "per_apur": PER_APUR,
        "lote_num": LOTE_NUM,
        "cpfs": cpfs,
        "confirmar_producao": True,
    }
    if forcar_inclusao:
        payload["forcar_inclusao"] = True
    else:
        override_slice = {cpf: recibos[cpf] for cpf in cpfs if cpf in recibos}
        if override_slice:
            payload["recibo_override_por_cpf"] = override_slice
    ps_slice = {cpf: planos[cpf] for cpf in cpfs if cpf in planos}
    if ps_slice:
        payload["plan_saude_por_cpf"] = ps_slice

    t0 = time.time()
    response = requests.post(API_URL, json=payload, timeout=TIMEOUT)
    response.raise_for_status()
    body = response.json()
    body["_client_elapsed_s"] = round(time.time() - t0, 1)
    return body


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--max", type=int, default=None)
    ap.add_argument("--batch", type=int, default=BATCH_SIZE)
    ap.add_argument("--continuar-com-erros", action="store_true")
    ap.add_argument("--somente-erro", choices=["timeout", "401", "sem_codigo"], default=None)
    ap.add_argument("--forcar-inclusao", action="store_true")
    args = ap.parse_args()

    cpfs = carregar_cpfs_pendentes()
    cpfs = filtrar_cpfs_por_erro(cpfs, args.somente_erro)
    if args.max:
        cpfs = cpfs[:args.max]
    planos = carregar_plan_saude_db()
    recibos = carregar_recibos_override_db()
    sem_plano = [cpf for cpf in cpfs if cpf not in planos]

    print(f"[scope pendente] {len(cpfs)} CPFs em {PER_APUR} lote={LOTE_NUM}")
    print(f"[plan_saude DB] {len(planos)} CPFs com plano")
    print(f"[override DB] {len(recibos)} recibos")
    print(f"[sem plano entre pendentes] {len(sem_plano)}")
    if sem_plano:
        print("  amostra:", sem_plano[:20])
    for cpf in cpfs[:5]:
        print(f"  {cpf} planSaude={planos.get(cpf)} override={recibos.get(cpf)}")

    if args.dry_run:
        print("[dry-run] nenhum envio realizado")
        return
    if sem_plano:
        raise SystemExit("Abortado: ha CPFs pendentes sem planSaude")

    total_ok = total_err = 0
    batches = [cpfs[i:i + args.batch] for i in range(0, len(cpfs), args.batch)]
    for idx, bloco in enumerate(batches, start=1):
        print(f"\n=== bloco {idx}/{len(batches)} - {len(bloco)} CPFs ===")
        body = enviar_bloco(bloco, recibos, planos, args.forcar_inclusao)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        with open(os.path.join(OUTDIR, f"resp_bloco{idx:03d}_{ts}.json"), "w", encoding="utf-8") as f:
            json.dump(body, f, ensure_ascii=False, indent=2)
        ok = sum(1 for item in body.get("resultados", []) if item.get("sucesso"))
        err = sum(1 for item in body.get("resultados", []) if not item.get("sucesso"))
        total_ok += ok
        total_err += err
        print(f"ok={ok} err={err} tempo={body.get('_client_elapsed_s')}s acumulado ok={total_ok} err={total_err}")
        if err and not ok and not args.continuar_com_erros:
            print("[AVISO] bloco 100% erro - parando")
            break


if __name__ == "__main__":
    main()