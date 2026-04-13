import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from db_config import LOCAL_DB_CONFIG
from esocial.certificate_manager import CertificateManager
from esocial.esocial_client import ESocialClient
from esocial.soap_builder import SOAPEnvelopeBuilder
import psycopg2

conn = psycopg2.connect(**LOCAL_DB_CONFIG)
cur = conn.cursor()
cur.execute("SELECT cnpj, arquivo_path, senha_encrypted FROM certificados_a1 WHERE ativo = TRUE LIMIT 1")
cnpj, cert_path, senha_enc = cur.fetchone()
conn.close()
senha = CertificateManager.decrypt_password(senha_enc)
with open(cert_path, "rb") as f:
    pfx = f.read()

url = SOAPEnvelopeBuilder.url_consulta(producao=True)
r = ESocialClient.consultar_lote("1.1.202604.0000000013007329947", pfx, senha, url=url)
print("codigo:", r.get("codigo_resposta"))
print("desc:", r.get("descricao"))
for e in r.get("eventos", []):
    print("evt:", e.get("id"), "recibo:", e.get("nr_recibo"), "cod:", e.get("codigo_resposta"))
    if e.get("ocorrencias"):
        for o in e["ocorrencias"]:
            print("  ocorr:", o)
