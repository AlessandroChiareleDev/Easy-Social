"""Download S-5002 pós-pipeline com retry robusto."""
import sys, os, json, re, time
sys.path.insert(0, os.path.dirname(__file__))

import psycopg2
from db_config import LOCAL_DB_CONFIG
from esocial.certificate_manager import CertificateManager
from esocial.esocial_client import ESocialClient

CPF = "08132588983"
MAX_RETRIES = 5
RETRY_DELAY = 15

conn = psycopg2.connect(**LOCAL_DB_CONFIG)
cur = conn.cursor()
cur.execute("SELECT cnpj, arquivo_path, senha_encrypted FROM certificados_a1 WHERE ativo = TRUE LIMIT 1")
cnpj, arquivo_path, senha_enc = cur.fetchone()
conn.close()

senha = CertificateManager.decrypt_password(senha_enc)
with open(arquivo_path, "rb") as f:
    pfx_data = f.read()

empregador = {"tpInsc": 1, "nrInsc": cnpj[:8]}

print("=" * 60)
print("  DOWNLOAD S-5002 PÓS-PIPELINE (com retry)")
print(f"  CPF: {CPF} | Data: 2026-04-04")
print("=" * 60)

for per in ["2024-12"]:
    print(f"\n--- Período: {per} ---")
    
    for attempt in range(1, MAX_RETRIES + 1):
        print(f"\n  Tentativa {attempt}/{MAX_RETRIES}...")
        try:
            result = ESocialClient.consultar_identificadores_trabalhador(
                cpf=CPF,
                dt_ini=f"{per}-01T00:00:00",
                dt_fim=f"{per}-28T23:59:59",
                pfx_data=pfx_data,
                password=senha,
                empregador=empregador,
                producao=True,
            )
            
            erro = result.get("erro", "")
            if "Connection" in str(erro) or "Remote" in str(erro):
                print(f"  Conexão caiu. Aguardando {RETRY_DELAY}s...")
                time.sleep(RETRY_DELAY)
                continue
            
            if result.get("sucesso"):
                eventos = result.get("eventos", [])
                print(f"  OK! {len(eventos)} eventos encontrados")
                
                por_tipo = {}
                for ev in eventos:
                    tp = ev.get("tipo", "?")
                    por_tipo.setdefault(tp, []).append(ev)
                
                for tp, evs in sorted(por_tipo.items()):
                    print(f"    {tp}: {len(evs)}")
                    for e in evs:
                        eid = e.get('id', '?')
                        print(f"      id={eid}")
                
                s5002 = por_tipo.get("S-5002", [])
                if s5002:
                    ids = [e["id"] for e in s5002 if e.get("id")]
                    print(f"\n  Baixando {len(ids)} S-5002...")
                    
                    for dl_attempt in range(1, MAX_RETRIES + 1):
                        dl = ESocialClient.solicitar_download_por_id(
                            ids=ids,
                            pfx_data=pfx_data,
                            password=senha,
                            empregador=empregador,
                            producao=True,
                        )
                        dl_erro = dl.get("erro", "")
                        if "Connection" in str(dl_erro):
                            print(f"  Download tentativa {dl_attempt} - conexão caiu. Aguardando...")
                            time.sleep(RETRY_DELAY)
                            continue
                        break
                    
                    if dl.get("sucesso"):
                        for i, arq in enumerate(dl.get("arquivos", [])):
                            xml = arq.get("evento_xml") or arq.get("xml_evento") or ""
                            nr = arq.get("nr_recibo", "?")
                            print(f"\n  === S-5002 #{i+1} (recibo: {nr}) ===")
                            
                            if xml:
                                nm = re.findall(r'<nmTrab>([^<]+)</nmTrab>', xml)
                                if nm:
                                    print(f"  NOME: {nm[0]}")
                                
                                rec_base = re.findall(r'<nrRecArqBase>([^<]+)</nrRecArqBase>', xml)
                                print(f"  nrRecArqBase: {rec_base}")
                                
                                infos = re.findall(r'<infoIR><tpInfoIR>(\d+)</tpInfoIR><valor>([^<]+)</valor></infoIR>', xml)
                                print(f"  infoIR:")
                                for tp, val in infos:
                                    desc_map = {"11": "Rend. tributável", "12": "Rend. 13º", "31": "IRRF retido", "7900": "Contrib. previd.", "41": "Ded. INSS", "42": "Ded. INSS 13º", "9": "Isento"}
                                    print(f"    tpInfoIR={tp} ({desc_map.get(tp, '?')}) = R$ {val}")
                                
                                fname = f"s5002_POS_pipeline_{per}_{i+1}.xml"
                                with open(fname, "w", encoding="utf-8") as f:
                                    f.write(xml)
                                print(f"  Salvo: {fname}")
                    else:
                        print(f"  Download falhou: {dl.get('descricao') or dl.get('erro')}")
                else:
                    print("  Nenhum S-5002 encontrado!")
                break
            else:
                cod = result.get("codigo_resposta", "?")
                desc = result.get("descricao", "?")
                print(f"  FALHA ({cod}): {desc}")
                if "dias 1 e 7" in str(desc):
                    print("\n  ** DOWNLOAD BLOQUEADO DIAS 1-7 DO MÊS **")
                    print("  ** Hoje é dia 4 de abril. Tentar após dia 8. **")
                break
        except Exception as e:
            print(f"  ERRO: {e}")
            time.sleep(RETRY_DELAY)

print("\n" + "=" * 60)
