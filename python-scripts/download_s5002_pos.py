"""Tentar download S-5002 pós-pipeline - abril 2026."""
import sys, os, json, re
sys.path.insert(0, os.path.dirname(__file__))

import psycopg2
from db_config import LOCAL_DB_CONFIG
from esocial.certificate_manager import CertificateManager
from esocial.esocial_client import ESocialClient

CPF = "08132588983"

# Carregar certificado
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
print("  TENTATIVA DE DOWNLOAD S-5002 PÓS-PIPELINE")
print(f"  CPF: {CPF} | CNPJ: {cnpj}")
print("=" * 60)

# Tentar download por nrRecibo dos S-1210 retificados
# O S-5002 é gerado automaticamente pelo S-1299, vinculado ao S-1210
# Mas podemos tentar baixar pelo nrRecibo do S-1210

# PRIMEIRO: tentar consultar identificadores
for per in ["2024-12", "2025-01"]:
    print(f"\n--- Período: {per} ---")
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
        if result.get("sucesso"):
            eventos = result.get("eventos", [])
            print(f"  OK! {len(eventos)} eventos encontrados")
            
            # Classificar por tipo
            por_tipo = {}
            for ev in eventos:
                tp = ev.get("tipo", "?")
                por_tipo.setdefault(tp, []).append(ev)
            
            for tp, evs in sorted(por_tipo.items()):
                print(f"    {tp}: {len(evs)}")
                for e in evs:
                    print(f"      id={e.get('id','?')[:40]}... nrRec={e.get('nrRec','?')}")
            
            # Download S-5002
            s5002 = [e for e in eventos if e.get("tipo") == "S-5002"]
            if s5002:
                ids = [e["id"] for e in s5002 if e.get("id")]
                print(f"\n  Baixando {len(ids)} S-5002...")
                dl = ESocialClient.solicitar_download_por_id(
                    ids=ids,
                    pfx_data=pfx_data,
                    password=senha,
                    empregador=empregador,
                    producao=True,
                )
                if dl.get("sucesso"):
                    for i, arq in enumerate(dl.get("arquivos", [])):
                        xml = arq.get("evento_xml") or arq.get("xml_evento") or ""
                        nr = arq.get("nr_recibo", "?")
                        print(f"\n  === S-5002 #{i+1} (recibo: {nr}) ===")
                        
                        if xml:
                            # Extrair dados
                            nm = re.findall(r'<nmTrab>([^<]+)</nmTrab>', xml)
                            if nm:
                                print(f"  NOME: {nm[0]}")
                            
                            cpf_b = re.findall(r'<cpfBenef>([^<]+)</cpfBenef>', xml)
                            rec_base = re.findall(r'<nrRecArqBase>([^<]+)</nrRecArqBase>', xml)
                            print(f"  cpfBenef: {cpf_b}")
                            print(f"  nrRecArqBase: {rec_base}")
                            
                            # infoIR
                            infos = re.findall(r'<infoIR><tpInfoIR>(\d+)</tpInfoIR><valor>([^<]+)</valor></infoIR>', xml)
                            print(f"  infoIR:")
                            for tp, val in infos:
                                print(f"    tpInfoIR={tp} valor={val}")
                            
                            # totApurMen
                            tots = re.findall(r'<CRMen>(\d+)</CRMen><vlrCRMen>([^<]+)</vlrCRMen>', xml)
                            if tots:
                                print(f"  totApurMen:")
                                for cr, vl in tots:
                                    print(f"    CRMen={cr} vlrCRMen={vl}")
                            
                            # Salvar
                            fname = f"s5002_pos_pipeline_{per}_{i+1}.xml"
                            with open(fname, "w", encoding="utf-8") as f:
                                f.write(xml)
                            print(f"  Salvo: {fname}")
                        else:
                            print(f"  Sem XML! Keys: {arq.keys()}")
                else:
                    print(f"  Download falhou: {dl.get('descricao','?')}")
            else:
                print("  Nenhum S-5002 encontrado!")
        else:
            cod = result.get("codigo_resposta", "?")
            desc = result.get("descricao", "?")
            print(f"  FALHA ({cod}): {desc}")
            print(f"  Result completo: {json.dumps(result, indent=2, default=str)[:800]}")
    except Exception as e:
        print(f"  ERRO: {e}")

print("\n" + "=" * 60)
print("  FIM")
print("=" * 60)
