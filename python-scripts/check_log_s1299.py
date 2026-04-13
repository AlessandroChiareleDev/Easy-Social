"""Consulta RAW no webservice eSocial para ver status do periodo."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import psycopg2
from db_config import LOCAL_DB_CONFIG
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

# Try to SEND a dry S-1299 and see what error we get back
# If period is closed, we'll get an error saying it's already closed
# If open, we'd get acceptance (but we're not actually going to send)
# Instead let's just try S-1298 (reopen) — if already open, error says "already open"
# If closed, it would succeed (but we don't want to reopen!)

# Actually safest: try consultar o ultimo protocolo do S-1299
# Get the protocol from the pipeline progress
import json
with open("/tmp/pipeline_batch_202509_progress.json") as f:
    prog = json.load(f)

print(f"Pipeline run_id: {prog.get('run_id')}")
print(f"s1299_done: {prog.get('s1299_done')}")
print(f"cpfs_ok: {len(prog.get('cpfs_ok',[]))}")
print(f"cpfs_erro: {len(prog.get('cpfs_erro',{}))}")

# Check the log file for S-1299 details
print("\n--- Pipeline log: S-1299 entries ---")
log_file = "/tmp/pipeline_batch_202509.log"
if os.path.exists(log_file):
    with open(log_file) as f:
        lines = f.readlines()
    # Find S-1299 related lines
    for i, line in enumerate(lines):
        if "1299" in line or "fechar" in line.lower() or "STEP 3" in line:
            print(line.rstrip())
    # Also last 20 lines
    print("\n--- Ultimas 30 linhas do log ---")
    for line in lines[-30:]:
        print(line.rstrip())
else:
    print("Log file nao encontrado!")

# Also check the result file for S-1299 details
print("\n--- Result file ---")
result_file = "/tmp/pipeline_batch_202509_result.json"
if os.path.exists(result_file):
    with open(result_file) as f:
        res = json.load(f)
    print(json.dumps(res, indent=2, default=str)[:3000])
