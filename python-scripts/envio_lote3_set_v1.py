"""
Envio Lote 3 Setembro/2025 APPA — 156 INCLUSOES PENDENTES.

Origem:
  - CPFs: XLSX '09 Setembro_lote 003_APPA_Inclusão Pendencias.xlsx' (aba 'Pendencia Lote 3')
  - CNPJ+ANS: tabela s1210_operadoras (operadora histórica do CPF — todos têm 63554067000198/368253)
  - Valor: XLSX aba 'Assistencia Medica' col 'ValorEvento' (centavos), rubrica 619
  - Sem recibo_override → incNovo (primeiro envio do CPF no L3 set/2025)

Uso:
  python envio_lote3_set_v1.py --dry-run-1   # mostra payload do 1º
  python envio_lote3_set_v1.py --max 1       # envia 1 CPF
  python envio_lote3_set_v1.py --batch 50    # envia em lotes de 50 (default)
"""
from __future__ import annotations
import argparse, json, os, sys, time
from datetime import datetime
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

import requests

ROOT = os.path.dirname(os.path.abspath(__file__))
PER_APUR = "2025-09"
LOTE_NUM = 3
EMPRESA_ID = 1
API_URL = "http://localhost:8000/api/s1210-repo/enviar-lote-cpfs"
TIMEOUT = 600

OUTDIR = os.path.join(ROOT, "saida_lote3_set_v1")
os.makedirs(OUTDIR, exist_ok=True)


def carregar():
    with open(os.path.join(ROOT, '_l3_cpfs.json')) as f:
        cpfs = sorted(json.load(f))
    with open(os.path.join(ROOT, '_l3_plan_saude_final.json')) as f:
        plan = json.load(f)
    return cpfs, plan


def enviar(cpfs, plan):
    payload = {
        "per_apur": PER_APUR,
        "lote_num": LOTE_NUM,
        "cpfs": cpfs,
        "confirmar_producao": True,
        "plan_saude_por_cpf": {c: plan[c] for c in cpfs if c in plan},
    }
    t0 = time.time()
    r = requests.post(API_URL, json=payload, timeout=TIMEOUT)
    r.raise_for_status()
    body = r.json()
    body["_client_elapsed_s"] = round(time.time()-t0, 1)
    return body


def resumir(body):
    ok = err = 0
    erros = []
    for det in body.get("resultados", []):
        if det.get("sucesso"): ok += 1
        else:
            err += 1
            ocorr = det.get("ocorrencias") or []
            ocstr = "; ".join(f'{o.get("codigo")}:{(o.get("descricao") or "")[:120]}' for o in ocorr)
            erros.append((det.get("cpf",""), str(det.get("codigo_resposta","")), ocstr))
    return ok, err, erros


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--max", type=int, default=None)
    ap.add_argument("--batch", type=int, default=50)
    ap.add_argument("--dry-run-1", action="store_true")
    ap.add_argument("--cpf", default=None)
    args = ap.parse_args()

    cpfs, plan = carregar()
    print(f"[scope] {len(cpfs)} CPFs L3 set/2025")
    print(f"[plan]  {len(plan)} CPFs com plan_saude")
    falt = [c for c in cpfs if c not in plan]
    if falt:
        print(f"[ERRO] sem plan_saude: {falt}"); return

    if args.cpf:
        cpfs = [args.cpf]
    elif args.max:
        cpfs = cpfs[:args.max]

    if args.dry_run_1:
        c = cpfs[0]
        payload = {"per_apur":PER_APUR, "lote_num":LOTE_NUM, "cpfs":[c],
                   "confirmar_producao":True,
                   "plan_saude_por_cpf":{c:plan[c]}}
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        return

    total_ok = total_err = 0
    todos_resultados = []
    n = len(cpfs)
    for i in range(0, n, args.batch):
        chunk = cpfs[i:i+args.batch]
        print(f"\n=== Lote {i//args.batch+1} ({len(chunk)} CPFs) [{i+1}-{i+len(chunk)}/{n}] ===")
        try:
            body = enviar(chunk, plan)
        except Exception as e:
            print(f"  FALHA HTTP: {e}")
            continue
        ok, err, erros = resumir(body)
        total_ok += ok; total_err += err
        print(f"  ok={ok} err={err} elapsed={body.get('_client_elapsed_s')}s")
        for c, cod, oc in erros[:10]:
            print(f"    {c} cod={cod} {oc}")
        if len(erros) > 10:
            print(f"    ... +{len(erros)-10} erros")
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        out = os.path.join(OUTDIR, f"resp_b{i//args.batch+1:02d}_{ts}.json")
        with open(out, "w", encoding="utf-8") as f:
            json.dump(body, f, indent=2, ensure_ascii=False)
        todos_resultados.extend(body.get("resultados", []))
    
    print(f"\n=== TOTAL: ok={total_ok} err={total_err} de {n} ===")
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    cons = os.path.join(OUTDIR, f"consolidado_{ts}.json")
    with open(cons, "w", encoding="utf-8") as f:
        json.dump({"total_ok":total_ok,"total_err":total_err,"resultados":todos_resultados}, f, indent=2, ensure_ascii=False)
    print(f"consolidado: {cons}")


if __name__ == "__main__":
    main()
