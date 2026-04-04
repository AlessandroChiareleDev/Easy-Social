"""Quick test: send S-1010 ALTERAÇÃO to homologação — validate cert/XML/SOAP/mTLS.

RESULTADO da INCLUSÃO (rodado em 02/04/2026 22:29):
  - Rubrica 566, codIncIRRF=41, natRubr=9201
  - SUCESSO: recibo=1.2.0000000000306683496
  - A rubrica 566 agora EXISTE em homologação
"""
import sys, os, time
sys.path.insert(0, os.path.dirname(__file__))

import psycopg2
from db_config import DB_CONFIG, LOCAL_DB_CONFIG
from esocial.certificate_manager import CertificateManager
from esocial.xml_generator import S1010XMLGenerator
from esocial.xml_signer import S1010XMLSigner
from esocial.soap_builder import SOAPEnvelopeBuilder
from esocial.esocial_client import ESocialClient

TP_AMB = "2"
CNPJ_RAIZ = "05969071"
CNPJ_FULL = "05969071000110"
EMPREGADOR = {"tpInsc": 1, "nrInsc": CNPJ_RAIZ}
TRANSMISSOR = {"tpInsc": 1, "nrInsc": CNPJ_FULL}

# Load cert
lconn = psycopg2.connect(**LOCAL_DB_CONFIG)
cur = lconn.cursor()
cur.execute("SELECT arquivo_path, senha_encrypted FROM certificados_a1 WHERE ativo = TRUE LIMIT 1")
row = cur.fetchone()
cur.close()
lconn.close()
senha = CertificateManager.decrypt_password(row[1])
with open(row[0], "rb") as f:
    pfx_data = f.read()
print(f"Cert OK: {len(pfx_data)} bytes")

# Get rubrica 566 — a rubrica-problema principal (codIncIRRF 11→41)
conn = psycopg2.connect(**DB_CONFIG)
cur = conn.cursor()
cur.execute("""SELECT cod_rubrica, descricao, cod_natureza, incid_inss, incid_irrf, incid_fgts,
               ini_valid_esocial FROM cruzamento_eb WHERE cod_rubrica = '566'""")
row = cur.fetchone()
cur.close()
conn.close()

nat_rubr = (row[2] or "").split(" - ")[0].strip() if row[2] else ""
rubrica = {
    "codRubr": row[0], "ideTabRubr": "1",
    "iniValid": row[6] or "2025-01",
    "dscRubr": (row[1] or "RUBRICA")[:100],
    "natRubr": nat_rubr, "tpRubr": "1",
    "codIncCP": row[3] or "00",
    "codIncIRRF": "41",  # CORRETO: 41 (era 11)
    "codIncFGTS": row[5] or "00",
}
print(f"Rubrica: cod={rubrica['codRubr']} irrf={rubrica['codIncIRRF']} nat={rubrica['natRubr']}")

# Generate XML — INCLUSÃO (homologação não tem essa rubrica)
xml_bytes = S1010XMLGenerator.gerar_inclusao(EMPREGADOR, rubrica, seq=1, tp_amb=TP_AMB)
print(f"XML gerado: {len(xml_bytes)} bytes")
print("--- XML CONTENT ---")
print(xml_bytes.decode())
print("--- END XML ---")

# Sign
xml_assinado = S1010XMLSigner.assinar(xml_bytes, pfx_data, senha)
print(f"XML assinado: {len(xml_assinado)} bytes")

# SOAP
soap = SOAPEnvelopeBuilder.montar_envio([xml_assinado], EMPREGADOR, TRANSMISSOR, grupo="1")
print(f"SOAP: {len(soap)} bytes")

# Send
url_envio = SOAPEnvelopeBuilder.url_envio(producao=False)
print(f"URL: {url_envio}")
print("Enviando...")
resultado = ESocialClient.enviar_lote(soap, pfx_data, senha, url=url_envio)
print(f"Resultado envio:")
for k, v in resultado.items():
    print(f"  {k}: {v}")

protocolo = resultado.get("protocolo")
if protocolo:
    url_consulta = SOAPEnvelopeBuilder.url_consulta(producao=False)
    print(f"\nPolling consulta (protocolo={protocolo})...")
    for i in range(5):
        time.sleep(8)
        print(f"  tentativa {i+1}...", end=" ")
        consulta = ESocialClient.consultar_lote(protocolo, pfx_data, senha, url=url_consulta)
        cod = consulta.get("codigo_resposta")
        print(f"cod={cod} desc={consulta.get('descricao', '')[:80]}")
        if consulta.get("eventos"):
            for ev in consulta["eventos"]:
                print(f"    EVENTO: cod={ev.get('codigo_resposta')} recibo={ev.get('nr_recibo')} desc={ev.get('descricao', '')[:120]}")
                if ev.get("ocorrencias"):
                    for oc in ev["ocorrencias"]:
                        print(f"      OC: cod={oc.get('codigo')} tipo={oc.get('tipo')} loc={oc.get('localizacao', '')[:80]} desc={oc.get('descricao', '')[:120]}")
            import json
            print(f"    RAW: {json.dumps(consulta, indent=2, ensure_ascii=False)[:2000]}")
        if cod != "101":
            break
else:
    print("Sem protocolo - nao eh possivel consultar")
