"""Consulta direta no webservice eSocial: verificar status real do periodo 2025-09.
Faz download do último S-1299 aceito e verifica se está ativo."""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import psycopg2
from db_config import DB_CONFIG, LOCAL_DB_CONFIG
from esocial.certificate_manager import CertificateManager
from esocial.esocial_client import ESocialClient
from esocial.soap_builder import SOAPEnvelopeBuilder

# Load cert
conn_local = psycopg2.connect(**LOCAL_DB_CONFIG)
cur_local = conn_local.cursor()
cur_local.execute("SELECT cnpj, arquivo_path, senha_encrypted FROM certificados_a1 WHERE ativo=TRUE LIMIT 1")
cert_row = cur_local.fetchone()
conn_local.close()
cnpj = cert_row[0]
with open(cert_row[1], "rb") as f:
    pfx_data = f.read()
senha = CertificateManager.decrypt_password(cert_row[2])
empregador = {"tpInsc": 1, "nrInsc": cnpj}

# Get last S-1299 recibo from DB
conn = psycopg2.connect(**DB_CONFIG, keepalives=1, keepalives_idle=30, keepalives_interval=10, keepalives_count=3)
cur = conn.cursor()
cur.execute("""
    SELECT nr_recibo, created_at FROM explorador_eventos
    WHERE per_apur='2025-09' AND tipo_evento='S-1299'
    ORDER BY created_at DESC LIMIT 1
""")
ultimo_s1299 = cur.fetchone()
print(f"Ultimo S-1299 no banco: recibo={ultimo_s1299[0]} em {ultimo_s1299[1]}")

# Also get last S-1298
cur.execute("""
    SELECT nr_recibo, created_at FROM explorador_eventos
    WHERE per_apur='2025-09' AND tipo_evento='S-1298'
    ORDER BY created_at DESC LIMIT 1
""")
ultimo_s1298 = cur.fetchone()
print(f"Ultimo S-1298 no banco: recibo={ultimo_s1298[0]} em {ultimo_s1298[1]}")
conn.close()

# Download the last S-1299 from eSocial to see if it's really there
print("\n--- Consultando eSocial: download S-1299 por recibo ---")
try:
    result = ESocialClient.solicitar_download_por_nrrecibo(
        empregador=empregador,
        nr_recibos=[ultimo_s1299[0]],
        pfx_data=pfx_data,
        password=senha,
        producao=True,
    )
    print(f"Sucesso: {result.get('sucesso')}")
    print(f"Codigo: {result.get('codigo_resposta')}")
    print(f"Descricao: {result.get('descricao')}")
    if result.get("eventos"):
        for evt in result["eventos"]:
            print(f"  Evento: tipo={evt.get('tipo_evento')} id={evt.get('id')}")
            if evt.get("xml"):
                xml_str = evt["xml"][:1000]
                print(f"  XML (trecho): {xml_str}")
    else:
        print("  Nenhum evento retornado")
except Exception as e:
    print(f"ERRO download: {e}")

# Also download the last S-1298 to compare timestamps
print("\n--- Consultando eSocial: download S-1298 por recibo ---")
try:
    result2 = ESocialClient.solicitar_download_por_nrrecibo(
        empregador=empregador,
        nr_recibos=[ultimo_s1298[0]],
        pfx_data=pfx_data,
        password=senha,
        producao=True,
    )
    print(f"Sucesso: {result2.get('sucesso')}")
    print(f"Codigo: {result2.get('codigo_resposta')}")
    print(f"Descricao: {result2.get('descricao')}")
    if result2.get("eventos"):
        for evt in result2["eventos"]:
            print(f"  Evento: tipo={evt.get('tipo_evento')} id={evt.get('id')}")
            if evt.get("xml"):
                xml_str = evt["xml"][:1000]
                print(f"  XML (trecho): {xml_str}")
    else:
        print("  Nenhum evento retornado")
except Exception as e:
    print(f"ERRO download: {e}")

# Try consulting via identifier query for S-1299 events
print("\n--- Consultando identificadores S-1299 em 2025-09 ---")
try:
    result3 = ESocialClient.consultar_identificadores_empregador(
        empregador=empregador,
        tipo_evento="S-1299",
        per_apur="2025-09",
        pfx_data=pfx_data,
        password=senha,
        producao=True,
    )
    print(f"Sucesso: {result3.get('sucesso')}")
    print(f"Codigo: {result3.get('codigo_resposta')}")
    print(f"Descricao: {result3.get('descricao')}")
    if result3.get("identificadores"):
        for ident in result3["identificadores"]:
            print(f"  ID: {ident}")
    elif result3.get("eventos"):
        for evt in result3["eventos"]:
            print(f"  Evento: {evt}")
    print(f"  Raw keys: {list(result3.keys())}")
except Exception as e:
    print(f"ERRO: {e}")

print("\n--- Consultando identificadores S-1298 em 2025-09 ---")
try:
    result4 = ESocialClient.consultar_identificadores_empregador(
        empregador=empregador,
        tipo_evento="S-1298",
        per_apur="2025-09",
        pfx_data=pfx_data,
        password=senha,
        producao=True,
    )
    print(f"Sucesso: {result4.get('sucesso')}")
    print(f"Codigo: {result4.get('codigo_resposta')}")
    print(f"Descricao: {result4.get('descricao')}")
    if result4.get("identificadores"):
        for ident in result4["identificadores"]:
            print(f"  ID: {ident}")
    elif result4.get("eventos"):
        for evt in result4["eventos"]:
            print(f"  Evento: {evt}")
    print(f"  Raw keys: {list(result4.keys())}")
except Exception as e:
    print(f"ERRO: {e}")
