"""Retry das 15 rubricas que falharam com Internal Server Error (IRRF=67 fix)"""
import urllib.request
import json
import time

API = "http://localhost:8000"
RUBRICAS = ["516","522","537","605","606","607","615","619","621","631","638","774","775","779","895"]

def api_get(path):
    resp = urllib.request.urlopen(f"{API}{path}", timeout=30)
    return json.loads(resp.read())

def api_post(path, body):
    data = json.dumps(body).encode()
    req = urllib.request.Request(f"{API}{path}", data=data, headers={"Content-Type": "application/json"}, method="POST")
    try:
        resp = urllib.request.urlopen(req, timeout=120)
        return json.loads(resp.read()), resp.status
    except urllib.error.HTTPError as e:
        body_err = e.read().decode() if e.fp else ""
        try:
            return json.loads(body_err), e.code
        except:
            return {"erro": body_err}, e.code

def consultar(protocolo, max_t=12):
    for i in range(max_t):
        time.sleep(4)
        try:
            r = api_get(f"/api/esocial/s1010/consultar/{protocolo}?ambiente=1")
            cod = r.get("codigo_resposta","")
            evts = r.get("eventos",[])
            if cod == "201" and evts: return r
            if cod and cod not in ("101","201","202"): return r
            if evts and any(e.get("codigo_resposta") for e in evts): return r
        except: pass
    return {"codigo_resposta":"timeout","eventos":[]}

print("="*60)
print(f"RETRY 15 RUBRICAS (IRRF=67 fix)")
print("="*60)

sucesso, falha = [], []
for i, cod in enumerate(RUBRICAS, 1):
    print(f"\n  [{i}/15] #{cod}")
    body = {"rubrica_ids":[cod],"ini_valid":"","modo":"alteracao","ambiente":"1"}
    try:
        resp, sc = api_post("/api/esocial/s1010/enviar", body)
        if resp.get("sucesso") and resp.get("protocolo"):
            prot = resp["protocolo"]
            print(f"    ✓ Protocolo: {prot}")
            print(f"    ⏳ Aguardando...")
            result = consultar(prot)
            evts = result.get("eventos",[])
            if evts:
                evt = evts[0]
                rec = evt.get("nr_recibo","")
                if rec:
                    print(f"    ✅ SUCESSO — Recibo: {rec}")
                    sucesso.append(cod)
                else:
                    occ = "; ".join(o.get("descricao","") for o in evt.get("ocorrencias",[]))
                    print(f"    ❌ REJEITADO — {evt.get('codigo_resposta')}: {occ[:80]}")
                    falha.append((cod, f"{evt.get('codigo_resposta')}: {occ[:80]}"))
            else:
                print(f"    ⏱️ TIMEOUT")
                falha.append((cod, "timeout"))
        else:
            erro = resp.get("erro") or resp.get("detail") or str(resp)
            print(f"    ❌ ERRO: {str(erro)[:80]}")
            falha.append((cod, str(erro)[:80]))
    except Exception as e:
        print(f"    ❌ EXCEÇÃO: {e}")
        falha.append((cod, str(e)[:80]))
    if i < len(RUBRICAS): time.sleep(1)

print(f"\n{'='*60}")
print(f"RESULTADO: {len(sucesso)} sucesso, {len(falha)} falha")
if falha:
    print("FALHAS:")
    for c,e in falha: print(f"  #{c}: {e}")
