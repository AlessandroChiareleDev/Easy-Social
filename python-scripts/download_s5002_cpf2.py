"""
Download S-1210 XML por nrRecibo para CPF 09820037735 — extrair ideDmDev correto.
Usa 1 cota de download (WsSolicitarDownloadEventos).
"""
import sys, os, json, re
sys.path.insert(0, "/opt/easy-social/python-scripts")

import psycopg2
from db_config import LOCAL_DB_CONFIG
from esocial.certificate_manager import CertificateManager
from esocial.esocial_client import ESocialClient

# S-1210 mais recente do CPF 09820037735 (retif, com pagamento correto)
S1210_NRRECIBO = "1.1.0000000030328699934"

# Carregar certificado
conn = psycopg2.connect(**LOCAL_DB_CONFIG)
cur = conn.cursor()
cur.execute("SELECT cnpj, arquivo_path, senha_encrypted FROM certificados_a1 WHERE ativo = TRUE LIMIT 1")
row = cur.fetchone()
cur.close()
conn.close()

if not row:
    print("ERRO: Nenhum certificado A1 ativo!")
    sys.exit(1)

cnpj, cert_path, senha_enc = row
senha = CertificateManager.decrypt_password(senha_enc)

with open(cert_path, "rb") as f:
    pfx_data = f.read()

empregador = {"tpInsc": 1, "nrInsc": cnpj[:8]}

print(f"Baixando S-1210 por nrRecibo: {S1210_NRRECIBO}")
print(f"CNPJ: {cnpj}")
print(f"Empregador: {empregador}")

# Download por nrRecibo (1 cota)
resultado = ESocialClient.solicitar_download_por_nrrecibo(
    nr_recibos=[S1210_NRRECIBO],
    pfx_data=pfx_data,
    password=senha,
    empregador=empregador,
    producao=True,
)

print(f"\nSucesso: {resultado.get('sucesso')}")
print(f"Código: {resultado.get('codigo_resposta')}")
print(f"Descrição: {resultado.get('descricao')}")
if resultado.get("erro"):
    print(f"Erro: {resultado.get('erro')}")

arquivos = resultado.get("arquivos", [])
print(f"Arquivos retornados: {len(arquivos)}")

if arquivos:
    for i, arq in enumerate(arquivos):
        xml_content = arq.get("evento_xml", "")
        if xml_content:
            fname = f"/tmp/s1210_cpf2_{i}.xml"
            with open(fname, "w") as f:
                f.write(xml_content)
            print(f"\nXML salvo em {fname}")

            # Extrair ideDmDev
            dm_devs = re.findall(r"<ideDmDev>([^<]+)</ideDmDev>", xml_content)
            per_refs = re.findall(r"<perRef>([^<]+)</perRef>", xml_content)
            dt_pgtos = re.findall(r"<dtPgto>([^<]+)</dtPgto>", xml_content)
            tp_pgtos = re.findall(r"<tpPgto>([^<]+)</tpPgto>", xml_content)
            vr_liqs = re.findall(r"<vrLiq>([^<]+)</vrLiq>", xml_content)

            print(f"\n=== ideDmDev encontrados no S-1210 ===")
            for j, dm in enumerate(dm_devs):
                per = per_refs[j] if j < len(per_refs) else "?"
                dt = dt_pgtos[j] if j < len(dt_pgtos) else "?"
                tp = tp_pgtos[j] if j < len(tp_pgtos) else "?"
                vr = vr_liqs[j] if j < len(vr_liqs) else "?"
                print(f"  [{j}] ideDmDev={dm}, perRef={per}, dtPgto={dt}, tpPgto={tp}, vrLiq={vr}")

            # Print full XML
            print(f"\n=== XML completo ===")
            print(xml_content[:5000])
        else:
            print(f"\nArquivo {i}: sem evento_xml")
            print(f"  Keys: {list(arq.keys())}")
else:
    print("\nNenhum arquivo retornado!")
    xml_resp = resultado.get("xml_resposta", "")
    if xml_resp:
        print(f"\n=== XML resposta (primeiros 5000 chars) ===")
        print(xml_resp[:5000])
