"""Retificação S-1210 rubrica 546 (IR cód 9 → 11) — XLSX da Ana 07/05/2026.

Estratégia:
- 825 (cpf, per_apur) únicos → para cada par:
  - lote_num: buscar de s1210_cpf_scope (cpf, per_apur)
  - recibo_override: último nr_recibo_novo do envio OK (cpf, per_apur)
  - plan_saude_override: de s1210_operadoras (apenas se lote=3)
- Agrupar por (per_apur, lote_num) e enviar em batches de 50.
- Pular: 36383238892 set/2025 (já feito ontem).

Uso:
  python envio_retif_546.py --dry-run
  python envio_retif_546.py --max 1
  python envio_retif_546.py --per 2025-12
  python envio_retif_546.py
"""
import argparse, json, os, sys, time
from collections import defaultdict
from datetime import datetime
import requests
import psycopg2
from psycopg2.extras import RealDictCursor

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)
from db_config import DB_CONFIG

EMPRESA_ID = 1
API_URL    = "http://localhost:8000/api/s1210-repo/enviar-lote-cpfs"
BATCH_SIZE = 50
TIMEOUT    = 600
OUTDIR     = os.path.join(ROOT, "saida_retif_546")
os.makedirs(OUTDIR, exist_ok=True)

XLSX_PATH = os.path.expanduser(r"~\Downloads\Retificação para correção do Adiantamento - S 1210 (546).xlsx")

# Já feito ontem manualmente
JA_FEITO = {("36383238892", "2025-09")}

# Pers sem fonte indexada no backend (FONTES) — pular
PERS_SEM_FONTE = {"2025-01"}

# Blocos (per, lote) já enviados na execução anterior 07/05/2026 — pular para evitar duplicação.
# fev/L1+L3, mar/L3, abr/L1+L3, mai/L1 = 100% OK. mar/L1 e mai/L3 ficaram com erros 401 — tratamos depois.
BLOCOS_FEITOS = {
    ("2025-02", 1), ("2025-02", 3),
    ("2025-03", 1), ("2025-03", 3),  # mar/L1 tem 11 erros pendentes (tratar depois)
    ("2025-04", 1), ("2025-04", 3),
    ("2025-05", 1), ("2025-05", 3),  # mai/L3 tem 26 erros pendentes (tratar depois)
}


def comp_to_per(comp_int) -> str:
    s = f"{int(comp_int):06d}"
    return f"{s[2:]}-{s[:2]}"


def carregar_xlsx() -> list[tuple[str, str]]:
    import openpyxl
    wb = openpyxl.load_workbook(XLSX_PATH, data_only=True)
    ws = wb['Planilha2']
    out = []
    for r in ws.iter_rows(min_row=2, values_only=True):
        cod_empr, comp, comp_mes, mat, concat, cpf = r
        if not cpf or not comp: continue
        cpf_clean = ''.join(c for c in str(cpf) if c.isdigit()).zfill(11)
        per = comp_to_per(comp)
        out.append((cpf_clean, per))
    # dedup mantendo ordem
    seen = set(); uniq = []
    for x in out:
        if x not in seen:
            seen.add(x); uniq.append(x)
    return uniq


def carregar_lote_por_cpf_per(pares: list[tuple[str,str]]) -> dict[tuple[str,str], int]:
    """Lote_num do scope por (cpf, per_apur)."""
    cpfs = sorted({c for c, _ in pares})
    pers = sorted({p for _, p in pares})
    out: dict[tuple[str,str], int] = {}
    with psycopg2.connect(**DB_CONFIG) as c, c.cursor() as cur:
        cur.execute("""
            SELECT cpf, per_apur, lote_num
              FROM s1210_cpf_scope
             WHERE empresa_id=%s AND cpf = ANY(%s) AND per_apur = ANY(%s)
        """, (EMPRESA_ID, cpfs, pers))
        for cpf, per, lote in cur.fetchall():
            out[(cpf, per)] = lote
    return out


def carregar_recibos_override(pares: list[tuple[str,str]]) -> dict[tuple[str,str], str]:
    """Último nr_recibo_novo do envio OK por (cpf, per_apur)."""
    cpfs = sorted({c for c, _ in pares})
    pers = sorted({p for _, p in pares})
    out: dict[tuple[str,str], str] = {}
    with psycopg2.connect(**DB_CONFIG) as c, c.cursor() as cur:
        cur.execute("""
            SELECT DISTINCT ON (cpf, per_apur)
                   cpf, per_apur, nr_recibo_novo
              FROM s1210_cpf_envios
             WHERE empresa_id=%s AND status='ok'
               AND cpf = ANY(%s) AND per_apur = ANY(%s)
               AND nr_recibo_novo IS NOT NULL
             ORDER BY cpf, per_apur, enviado_em DESC
        """, (EMPRESA_ID, cpfs, pers))
        for cpf, per, rec in cur.fetchall():
            out[(cpf, per)] = rec
    return out


def carregar_plan_saude(pers: list[str]) -> dict[tuple[str,str], list[dict]]:
    """plan_saude_por_cpf de s1210_operadoras (lote 3 sempre — lote 1 não tem)."""
    out: dict[tuple[str,str], list[dict]] = defaultdict(list)
    with psycopg2.connect(**DB_CONFIG) as c, c.cursor() as cur:
        cur.execute("""
            SELECT cpf, per_apur, cnpj_operadora,
                   MAX(reg_ans), SUM(valor)::BIGINT
              FROM s1210_operadoras
             WHERE empresa_id=%s AND lote_num=3 AND per_apur = ANY(%s)
               AND cnpj_operadora IS NOT NULL
             GROUP BY cpf, per_apur, cnpj_operadora
        """, (EMPRESA_ID, pers))
        for cpf, per, cnpj, ans, cents in cur.fetchall():
            cents = int(cents or 0)
            if cents <= 0: continue
            out[(cpf, per)].append({
                "cnpjOper": cnpj,
                "regANS": ans or "",
                "vlrSaudeTit": round(cents/100, 2),
            })
    return dict(out)


def enviar_bloco(per: str, lote: int, cpfs: list[str],
                 rec_map: dict, ps_map: dict) -> dict:
    payload = {
        "per_apur": per,
        "lote_num": lote,
        "cpfs": cpfs,
        "confirmar_producao": True,
    }
    rec_slice = {c: rec_map[(c, per)] for c in cpfs if (c, per) in rec_map}
    if rec_slice: payload["recibo_override_por_cpf"] = rec_slice
    if lote == 3:
        ps_slice = {c: ps_map[(c, per)] for c in cpfs if (c, per) in ps_map}
        if ps_slice: payload["plan_saude_por_cpf"] = ps_slice

    t0 = time.time()
    r = requests.post(API_URL, json=payload, timeout=TIMEOUT)
    r.raise_for_status()
    body = r.json()
    body["_client_elapsed_s"] = round(time.time()-t0, 1)
    return body


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--max", type=int, default=None, help="limite total")
    ap.add_argument("--per", default=None, help="só essa per_apur (ex 2025-12)")
    ap.add_argument("--lote", type=int, default=None, help="só esse lote_num (1 ou 3)")
    args = ap.parse_args()

    pares = carregar_xlsx()
    print(f"[xlsx] {len(pares)} pares (cpf, per_apur) únicos")

    # filtrar JA_FEITO
    pares = [p for p in pares if p not in JA_FEITO]
    print(f"[skip ja-feito] {len(pares)} restantes (removeu {len(JA_FEITO)})")

    lote_map = carregar_lote_por_cpf_per(pares)
    print(f"[scope] {len(lote_map)} pares com lote_num definido")

    sem_scope = [p for p in pares if p not in lote_map]
    if sem_scope:
        print(f"[WARN] {len(sem_scope)} pares SEM scope (não serão enviados)")
        with open(os.path.join(OUTDIR, "sem_scope.json"), "w", encoding="utf-8") as f:
            json.dump(sem_scope, f, ensure_ascii=False, indent=2)

    rec_map = carregar_recibos_override(pares)
    print(f"[recibo] {len(rec_map)} pares com recibo override")

    pers_unicas = sorted({p for _, p in pares})
    ps_map = carregar_plan_saude(pers_unicas)
    print(f"[plan_saude] {len(ps_map)} pares com plan_saude (lote 3)")

    # Agrupar por (per, lote)
    grupos: dict[tuple[str, int], list[str]] = defaultdict(list)
    sem_recibo: list[tuple[str,str,int]] = []
    for cpf, per in pares:
        if per in PERS_SEM_FONTE: continue
        lote = lote_map.get((cpf, per))
        if lote is None: continue
        if (per, lote) in BLOCOS_FEITOS: continue
        if (cpf, per) not in rec_map:
            sem_recibo.append((cpf, per, lote))
            continue
        if args.per and per != args.per: continue
        if args.lote and lote != args.lote: continue
        grupos[(per, lote)].append(cpf)

    if sem_recibo:
        print(f"[WARN] {len(sem_recibo)} pares SEM recibo override (chain walk pode falhar)")
        with open(os.path.join(OUTDIR, "sem_recibo.json"), "w", encoding="utf-8") as f:
            json.dump(sem_recibo, f, ensure_ascii=False, indent=2)

    print(f"\n[grupos] (per, lote) => qtd:")
    total = 0
    for (per, lote), cpfs in sorted(grupos.items()):
        print(f"  ({per}, lote={lote}) → {len(cpfs)} CPFs")
        total += len(cpfs)
    print(f"TOTAL a enviar: {total}")

    if args.max:
        # achatar e cortar
        chato = []
        for k, lst in sorted(grupos.items()):
            for cpf in lst: chato.append((k, cpf))
        chato = chato[:args.max]
        novo: dict = defaultdict(list)
        for k, cpf in chato: novo[k].append(cpf)
        grupos = novo
        print(f"[--max {args.max}] reduzido para {sum(len(v) for v in grupos.values())} CPFs")

    if args.dry_run:
        amostra_per, amostra_lote = next(iter(grupos.keys())) if grupos else (None, None)
        if amostra_per:
            cpfs_am = grupos[(amostra_per, amostra_lote)][:3]
            print(f"\n[dry-run] amostra payload {amostra_per} lote={amostra_lote}:")
            payload = {
                "per_apur": amostra_per,
                "lote_num": amostra_lote,
                "cpfs": cpfs_am,
                "confirmar_producao": True,
            }
            rec_slice = {c: rec_map[(c, amostra_per)] for c in cpfs_am if (c, amostra_per) in rec_map}
            if rec_slice: payload["recibo_override_por_cpf"] = rec_slice
            if amostra_lote == 3:
                ps_slice = {c: ps_map[(c, amostra_per)] for c in cpfs_am if (c, amostra_per) in ps_map}
                if ps_slice: payload["plan_saude_por_cpf"] = ps_slice
            print(json.dumps(payload, indent=2, ensure_ascii=False))
        return

    # Envio
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_path = os.path.join(OUTDIR, f"log_{ts}.txt")
    log = open(log_path, "w", encoding="utf-8")
    def out(msg):
        print(msg); log.write(msg + "\n"); log.flush()

    g_total_ok = g_total_err = 0
    for (per, lote), cpfs in sorted(grupos.items()):
        out(f"\n=== {per} lote={lote} ({len(cpfs)} CPFs) ===")
        for i in range(0, len(cpfs), BATCH_SIZE):
            blk = cpfs[i:i+BATCH_SIZE]
            try:
                body = enviar_bloco(per, lote, blk, rec_map, ps_map)
            except requests.exceptions.RequestException as e:
                out(f"  [ERR-NET] bloco {i//BATCH_SIZE+1} ({per} l{lote}): {e} — pulando bloco")
                continue
            ok = sum(1 for d in body.get("resultados", []) if d.get("sucesso"))
            err = len(body.get("resultados", [])) - ok
            g_total_ok += ok; g_total_err += err
            out(f"  bloco {i//BATCH_SIZE+1} (cpfs {i+1}-{i+len(blk)}): ok={ok} erro={err} elapsed={body.get('_client_elapsed_s')}s")
            # salvar resp
            resp_path = os.path.join(OUTDIR, f"resp_{ts}_{per}_l{lote}_b{i//BATCH_SIZE+1}.json")
            with open(resp_path, "w", encoding="utf-8") as f:
                json.dump(body, f, ensure_ascii=False, indent=2, default=str)
            # listar erros
            for d in body.get("resultados", []):
                if not d.get("sucesso"):
                    out(f"    ERR cpf={d.get('cpf')} cod={d.get('codigo_resposta')} {str(d.get('descricao_resposta') or d.get('erro'))[:120]}")

    out(f"\n=== FIM === total ok={g_total_ok} erro={g_total_err}")
    log.close()


if __name__ == "__main__":
    main()
