"""Consultar resultado de protocolo pendente."""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

import psycopg2
from db_config import LOCAL_DB_CONFIG
from esocial.certificate_manager import CertificateManager
from esocial.esocial_client import ESocialClient
from esocial.soap_builder import SOAPEnvelopeBuilder
import json

PROTOCOLO = "1.1.202604.0000000012969859327"

# Load cert
conn = psycopg2.connect(**LOCAL_DB_CONFIG)
with conn.cursor() as cur:
    cur.execute("SELECT cnpj, arquivo_path, senha_encrypted FROM certificados_a1 WHERE ativo = TRUE LIMIT 1")
    row = cur.fetchone()
conn.close()

cnpj, arquivo_path, senha_enc = row
senha = CertificateManager.decrypt_password(senha_enc)
with open(arquivo_path, "rb") as f:
    pfx_data = f.read()

url_consulta = SOAPEnvelopeBuilder.url_consulta(producao=True)
print(f"Consultando protocolo: {PROTOCOLO}")
print(f"URL: {url_consulta}")
print()

resultado = ESocialClient.consultar_lote(PROTOCOLO, pfx_data, senha, url=url_consulta)
print(json.dumps(resultado, indent=2, default=str, ensure_ascii=False))
