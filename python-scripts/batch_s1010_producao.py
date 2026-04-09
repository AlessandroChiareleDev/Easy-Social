"""
Batch S-1010 Alteração em Produção
- Busca todas as rubricas pendentes
- Envia uma por uma como ALTERAÇÃO em PRODUÇÃO (ambiente=1)
- Se der erro, pula pro próximo
- No final, mostra resumo
"""
import urllib.request
import json
import time
import sys

API = "http://localhost:8000"

def api_get(path):
    resp = urllib.request.urlopen(f"{API}{path}", timeout=30)
    return json.loads(resp.read())

def api_post(path, body):
    data = json.dumps(body).encode()
    req = urllib.request.Request(
        f"{API}{path}",
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    try:
        resp = urllib.request.urlopen(req, timeout=120)
        return json.loads(resp.read()), resp.status
    except urllib.error.HTTPError as e:
        body_err = e.read().decode() if e.fp else ""
        try:
            return json.loads(body_err), e.code
        except:
            return {"erro": body_err}, e.code

def consultar_protocolo(protocolo, max_tentativas=12):
    """Consulta protocolo até ter resultado ou timeout"""
    for i in range(max_tentativas):
        time.sleep(4)
        try:
            result = api_get(f"/api/esocial/s1010/consultar/{protocolo}?ambiente=1")
            # Check if lote was processed (codigo_resposta=201 means processed)
            cod_resp = result.get("codigo_resposta", "")
            eventos = result.get("eventos", [])
            if cod_resp == "201" and eventos:
                return result
            # Also check for rejection at lote level
            if cod_resp and cod_resp not in ("101", "201", "202"):
                return result
            # If eventos have results, we're done
            if eventos and any(e.get("codigo_resposta") for e in eventos):
                return result
        except Exception as e:
            pass
    return {"codigo_resposta": "timeout", "eventos": [], "erro": "Timeout aguardando processamento"}

def main():
    print("=" * 70)
    print("BATCH S-1010 ALTERAÇÃO — PRODUÇÃO")
    print("=" * 70)
    
    # 1) Buscar pendentes
    print("\n[1] Buscando rubricas pendentes...")
    data = api_get("/api/esocial/rubricas-pendentes?filtro=pendentes")
    rubricas = data.get("rubricas", [])
    print(f"    Total pendentes: {len(rubricas)}")
    
    if not rubricas:
        print("    Nenhuma rubrica pendente. Nada a fazer.")
        return
    
    # 2) Filtrar válidas (excluir "Rubrica não encontrada")
    validas = []
    invalidas = []
    for r in rubricas:
        campos = [r.get("inss_correto",""), r.get("irrf_correto",""), r.get("fgts_correto","")]
        if any("não encontrada" in str(c).lower() for c in campos):
            invalidas.append(r)
        else:
            validas.append(r)
    
    print(f"    Válidas (enviaveis): {len(validas)}")
    print(f"    Inválidas (puladas): {len(invalidas)}")
    
    if not validas:
        print("    Nenhuma rubrica válida para enviar.")
        return
    
    # 3) Enviar uma por uma
    print(f"\n[2] Enviando {len(validas)} rubricas como ALTERAÇÃO em PRODUÇÃO...")
    print("-" * 70)
    
    sucesso = []
    falha = []
    
    for i, r in enumerate(validas, 1):
        cod = r["cod_rubrica"]
        desc = r.get("descricao", "?")[:40]
        print(f"\n  [{i}/{len(validas)}] #{cod} — {desc}")
        print(f"    INSS: {r.get('incid_inss','?')} -> {r.get('inss_correto','?')}")
        print(f"    IRRF: {r.get('incid_irrf','?')} -> {r.get('irrf_correto','?')}")
        print(f"    FGTS: {r.get('incid_fgts','?')} -> {r.get('fgts_correto','?')}")
        
        # Enviar
        body = {
            "rubrica_ids": [cod],
            "ini_valid": "",  # auto-detect
            "modo": "alteracao",
            "ambiente": "1"   # PRODUÇÃO
        }
        
        try:
            resp, status_code = api_post("/api/esocial/s1010/enviar", body)
            
            if resp.get("sucesso") and resp.get("protocolo"):
                protocolo = resp["protocolo"]
                print(f"    ✓ Enviado! Protocolo: {protocolo}")
                
                # Consultar resultado
                print(f"    ⏳ Aguardando processamento...")
                result = consultar_protocolo(protocolo)
                
                eventos = result.get("eventos", [])
                cod_lote = result.get("codigo_resposta", "")
                if eventos:
                    evt = eventos[0]
                    nr_recibo = evt.get("nr_recibo", "")
                    cod_evt = evt.get("codigo_resposta", "")
                    desc_evt = (evt.get("descricao", "") or "")[:60]
                    ocorrencias = evt.get("ocorrencias", [])
                    
                    if nr_recibo:
                        print(f"    ✅ SUCESSO — Recibo: {nr_recibo}")
                        sucesso.append({"cod": cod, "desc": desc, "recibo": nr_recibo, "protocolo": protocolo})
                    else:
                        ocorr_txt = "; ".join(o.get("descricao","") for o in ocorrencias if o.get("descricao")) if ocorrencias else desc_evt
                        print(f"    ❌ REJEITADO — {cod_evt}: {ocorr_txt[:80]}")
                        falha.append({"cod": cod, "desc": desc, "erro": f"{cod_evt}: {ocorr_txt[:100]}", "protocolo": protocolo})
                else:
                    if cod_lote == "timeout":
                        print(f"    ⏱️ TIMEOUT — protocolo: {protocolo}")
                        falha.append({"cod": cod, "desc": desc, "erro": f"timeout (protocolo: {protocolo})", "protocolo": protocolo})
                    else:
                        erro_txt = result.get("erro", result.get("descricao", "sem detalhes"))
                        print(f"    ❌ {cod_lote}: {erro_txt}")
                        falha.append({"cod": cod, "desc": desc, "erro": f"{cod_lote}: {erro_txt}", "protocolo": protocolo})
            else:
                erro = resp.get("erro") or resp.get("detail") or resp.get("descricao") or str(resp)
                print(f"    ❌ ERRO no envio: {erro[:80]}")
                falha.append({"cod": cod, "desc": desc, "erro": str(erro)[:100]})
        
        except Exception as e:
            print(f"    ❌ EXCEÇÃO: {e}")
            falha.append({"cod": cod, "desc": desc, "erro": str(e)[:100]})
        
        # Pequena pausa entre envios para não sobrecarregar
        if i < len(validas):
            time.sleep(1)
    
    # 4) Resumo final
    print("\n" + "=" * 70)
    print("RESUMO FINAL")
    print("=" * 70)
    print(f"  Total enviadas:  {len(validas)}")
    print(f"  ✅ Sucesso:      {len(sucesso)}")
    print(f"  ❌ Falha:        {len(falha)}")
    print(f"  ⏭️ Puladas:      {len(invalidas)}")
    
    if sucesso:
        print(f"\n  === SUCESSO ({len(sucesso)}) ===")
        for s in sucesso:
            print(f"    #{s['cod']:<5} {s['desc']:<40} recibo: {s['recibo']}")
    
    if falha:
        print(f"\n  === FALHA ({len(falha)}) ===")
        for f in falha:
            print(f"    #{f['cod']:<5} {f['desc']:<40} erro: {f['erro']}")
    
    if invalidas:
        print(f"\n  === PULADAS ({len(invalidas)}) ===")
        for inv in invalidas:
            print(f"    #{inv['cod_rubrica']:<5} {inv.get('descricao','?')[:40]}")
    
    # Salvar resultado em JSON
    resultado = {
        "sucesso": sucesso,
        "falha": falha,
        "puladas": [inv["cod_rubrica"] for inv in invalidas],
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    }
    with open("/tmp/batch_s1010_resultado.json", "w") as f:
        json.dump(resultado, f, indent=2, ensure_ascii=False)
    print(f"\n  Resultado salvo em /tmp/batch_s1010_resultado.json")

if __name__ == "__main__":
    main()
