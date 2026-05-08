"""Reabertura S-1298 em lote para os meses fechados que serão retificados.
Endpoint: POST /api/esocial/s1298/enviar  (ambiente=1, ind_apuracao=1)
"""
import argparse, json, time, sys
import requests

API = "http://localhost:8000/api/esocial/s1298/enviar"

# Meses fechados que precisam ser reabertos para a retif rubrica 546
MESES_DEFAULT = [
    "2025-03", "2025-04", "2025-05", "2025-06", "2025-07",
    "2025-09", "2025-10", "2025-11", "2025-12",
]

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--meses", nargs="+", default=None, help="lista AAAA-MM")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    meses = args.meses or MESES_DEFAULT
    print(f"Reabrindo {len(meses)} meses (ambiente=1 produção): {meses}")
    if args.dry_run:
        print("[dry-run] sem envio"); return

    res = []
    for per in meses:
        body = {"per_apur": per, "ind_apuracao": "1", "ambiente": "1"}
        print(f"\n→ S-1298 {per} ...", end=" ", flush=True)
        t0 = time.time()
        try:
            r = requests.post(API, json=body, timeout=120)
            r.raise_for_status()
            j = r.json()
        except Exception as e:
            print(f"ERRO rede: {e}")
            res.append({"per": per, "erro_rede": str(e)})
            continue
        dt = time.time() - t0
        print(f"sucesso={j.get('sucesso')} cod={j.get('codigo_resposta')} {dt:.1f}s  proto={j.get('protocolo')}")
        if j.get("ocorrencias"):
            for o in j["ocorrencias"]:
                print(f"    [{o.get('codigo')}] {o.get('descricao')[:160]}")
        res.append({"per": per, "resp": j})
        time.sleep(1.0)  # respiro entre envios

    print("\n=== RESUMO ===")
    ok = sum(1 for r in res if r.get("resp", {}).get("sucesso"))
    print(f"OK: {ok}/{len(res)}")
    with open("_resultado_s1298_lote.json", "w", encoding="utf-8") as f:
        json.dump(res, f, ensure_ascii=False, indent=2, default=str)

if __name__ == "__main__":
    main()
