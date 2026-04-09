"""Consultar protocolo do S-1299 de 2025-01 que ficou em processamento."""
import sys
sys.path.insert(0, "/opt/easy-social/python-scripts")

import psycopg2
from db_config import LOCAL_DB_CONFIG
from esocial.certificate_manager import CertificateManager
from esocial.esocial_client import ESocialClient
from esocial.soap_builder import SOAPEnvelopeBuilder

PROTOCOLO = "1.1.202604.0000000012999904020"

conn = psycopg2.connect(**LOCAL_DB_CONFIG)
cur = conn.cursor()
cur.execute("SELECT cnpj, arquivo_path, senha_encrypted FROM certificados_a1 WHERE ativo = TRUE LIMIT 1")
cnpj, cert_path, senha_enc = cur.fetchone()
cur.close()
conn.close()

senha = CertificateManager.decrypt_password(senha_enc)
with open(cert_path, "rb") as f:
    pfx_data = f.read()

url = SOAPEnvelopeBuilder.url_consulta(producao=True)
result = ESocialClient.consultar_lote(PROTOCOLO, pfx_data, senha, url=url)

print(f"Sucesso: {result.get('sucesso')}")
print(f"Codigo: {result.get('codigo_resposta')}")
print(f"Descricao: {result.get('descricao')}")
for ev in result.get("eventos", []):
    print(f"  Evento: cod={ev.get('codigo_resposta')} desc={ev.get('descricao')} recibo={ev.get('nr_recibo')}")
    for oc in ev.get("ocorrencias", []):
        print(f"    [{oc.get('codigo')}] {oc.get('descricao')}")
