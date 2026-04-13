#!/usr/bin/env python3
"""Consulta UNICA do protocolo S-1210 Adriana."""
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

protocolo = "1.1.202604.0000000013009591836"
url = SOAPEnvelopeBuilder.url_consulta(producao=True)
soap = SOAPEnvelopeBuilder.montar_consulta(protocolo)
ret = ESocialClient.consultar_lote(soap, pfx, senha, url=url)
print("RESULTADO:", ret)

# Se tiver eventos, mostrar detalhes
for ev in ret.get("eventos", []):
    nr = ev.get("nr_recibo")
    if nr:
        print(f"ACEITO! Recibo: {nr}")
    else:
        ocorr = ev.get("ocorrencias", [])
        for o in ocorr:
            print(f"  [{o.get('codigo')}] {o.get('descricao','')[:300]}")
