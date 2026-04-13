"""Debug consulta identificadores - test with 1 CPF to see raw response."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from db_config import DB_CONFIG, LOCAL_DB_CONFIG
import psycopg2
import psycopg2.extras
from esocial.esocial_client import ESocialClient
from esocial.certificate_manager import CertificateManager

# Load cert
conn_local = psycopg2.connect(**LOCAL_DB_CONFIG)
cur_local = conn_local.cursor()
cur_local.execute("SELECT cnpj, arquivo_path, senha_encrypted FROM certificados_a1 WHERE ativo=TRUE LIMIT 1")
row = cur_local.fetchone()
conn_local.close()

cnpj = row[0]
with open(row[1], 'rb') as f:
    pfx_data = f.read()
senha = CertificateManager.decrypt_password(row[2])
empregador = {"tpInsc": 1, "nrInsc": cnpj}

print(f"CNPJ: {cnpj}")
print(f"Testing consulta for CPF 03638157164...")

result = ESocialClient.consultar_identificadores_trabalhador(
    cpf="03638157164",
    dt_ini="2025-09-01",
    dt_fim="2025-09-30",
    pfx_data=pfx_data,
    password=senha,
    empregador=empregador,
    producao=True,
)

print(f"\nsucesso: {result.get('sucesso')}")
print(f"codigo_resposta: {result.get('codigo_resposta')}")
print(f"descricao: {result.get('descricao')}")
print(f"erro: {result.get('erro')}")
print(f"eventos: {result.get('eventos')}")

xml_resp = result.get('xml_resposta', '')
if xml_resp:
    print(f"\nXML resposta (primeiros 2000 chars):")
    print(xml_resp[:2000])
else:
    print("\nNenhum XML de resposta retornado")
