"""Quick test: send S-1299 only to homologação — verify schema fix."""
import sys, os, time
sys.path.insert(0, os.path.dirname(__file__))

import psycopg2
from db_config import LOCAL_DB_CONFIG
from esocial.certificate_manager import CertificateManager
from esocial.xml_s1299 import S1299XMLGenerator
from esocial.xml_signer import S1010XMLSigner
from esocial.soap_builder import SOAPEnvelopeBuilder
from esocial.esocial_client import ESocialClient

TP_AMB = "2"
CNPJ_RAIZ = "05969071"
CNPJ_FULL = "05969071000110"
PER_APUR = "2026-02"
EMPREGADOR = {"tpInsc": 1, "nrInsc": CNPJ_RAIZ}
TRANSMISSOR = {"tpInsc": 1, "nrInsc": CNPJ_FULL}

# Load cert
conn = psycopg2.connect(**LOCAL_DB_CONFIG)
cur = conn.cursor()
cur.execute("SELECT arquivo_path, senha_encrypted FROM certificados_a1 WHERE ativo = TRUE LIMIT 1")
row = cur.fetchone()
cur.close()
conn.close()
senha = CertificateManager.decrypt_password(row[1])
with open(row[0], "rb") as f:
    pfx_data = f.read()

# Generate S-1299 — evt_remun/evt_pgtos = N because no events exist in homologação
xml_bytes = S1299XMLGenerator.gerar(EMPREGADOR, PER_APUR, ind_apuracao="1", tp_amb=TP_AMB,
                                     evt_remun="N", evt_pgtos="N")

# Print XML
from lxml import etree
print("=== XML S-1299 ===")
print(etree.tostring(etree.fromstring(xml_bytes), pretty_print=True).decode())

# Sign
xml_assinado = S1010XMLSigner.assinar(xml_bytes, pfx_data, senha)
soap = SOAPEnvelopeBuilder.montar_envio([xml_assinado], EMPREGADOR, TRANSMISSOR, grupo="3")
url_envio = SOAPEnvelopeBuilder.url_envio(producao=False)

print(f"Enviando para {url_envio}...")
resultado = ESocialClient.enviar_lote(soap, pfx_data, senha, url=url_envio)
print(f"Envio: sucesso={resultado.get('sucesso')} cod={resultado.get('codigo_resposta')} prot={resultado.get('protocolo')}")

protocolo = resultado.get("protocolo")
if protocolo:
    url_consulta = SOAPEnvelopeBuilder.url_consulta(producao=False)
    for i in range(5):
        time.sleep(8)
        print(f"Consulta {i+1}/5...", end=" ")
        consulta = ESocialClient.consultar_lote(protocolo, pfx_data, senha, url=url_consulta)
        cod = consulta.get("codigo_resposta")
        print(f"cod={cod}")
        if consulta.get("eventos"):
            for ev in consulta["eventos"]:
                print(f"  [{ev.get('codigo_resposta')}] recibo={ev.get('nr_recibo')} desc={ev.get('descricao', '')[:100]}")
                for oc in ev.get("ocorrencias", []):
                    print(f"    OC: cod={oc.get('codigo')} desc={oc.get('descricao', '')[:200]}")
        if cod != "101":
            break
