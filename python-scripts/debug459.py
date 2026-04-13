import sys, subprocess, os, glob
sys.path.insert(0, "/opt/easy-social/python-scripts")

# 1. Verificar se ha outros logs com protocolo
print("=== OUTROS LOGS/SAIDAS DO PIPELINE ===")
for path in ["/tmp/nohup.out", "/var/log/pipeline*", "/opt/easy-social/python-scripts/*.log"]:
    files = glob.glob(path)
    for f in files:
        if os.path.isfile(f):
            size = os.path.getsize(f)
            print(f"  {f} ({size} bytes)")

# 2. Verificar se pipeline_batch_set2025.py salva protocolo
print("\n=== PIPELINE: TRECHO QUE ENVIA LOTE ===")
result = subprocess.run(
    ["grep", "-n", "-iE", "protocolo|enviar_lote|consultar_lote", 
     "/opt/easy-social/python-scripts/pipeline_batch_set2025.py"],
    capture_output=True, text=True
)
print(result.stdout[:3000] if result.stdout else "Nada")

# 3. Testar se endpoint de ENVIO e CONSULTA regular funcionam (diferente do download cirurgico)
print("\n=== TESTE ENDPOINTS ===")
import requests, urllib3
urllib3.disable_warnings()
from esocial.esocial_client import ESocialClient
from esocial.certificate_manager import CertificateManager
from db_config import LOCAL_DB_CONFIG
import psycopg2

conn_local = psycopg2.connect(**LOCAL_DB_CONFIG)
with conn_local.cursor() as cur:
    cur.execute("SELECT cnpj, arquivo_path, senha_encrypted FROM certificados_a1 WHERE ativo = TRUE LIMIT 1")
    row = cur.fetchone()
conn_local.close()

with open(row[1], "rb") as f:
    pfx_data = f.read()
senha = CertificateManager.decrypt_password(row[2])

# Testar download cirurgico URL diretamente
urls_to_test = [
    ("DOWNLOAD (producao)", "https://webservices.download.esocial.gov.br/servicos/empregador/dwlcirurgico/WsConsultarIdentificadoresEventos.svc"),
    ("CONSULTA (producao)", "https://webservices.consulta.esocial.gov.br/servicos/empregador/consultarloteeventos/WsConsultarLoteEventos.svc"),
    ("ENVIO (producao)", "https://webservices.envio.esocial.gov.br/servicos/empregador/enviarloteeventos/WsEnviarLoteEventos.svc"),
    ("DOWNLOAD (homolog)", "https://webservices.producaorestrita.esocial.gov.br/servicos/empregador/dwlcirurgico/WsConsultarIdentificadoresEventos.svc"),
]

cert_pem, key_pem = ESocialClient._extrair_pem(pfx_data, senha)
import tempfile
tc = tempfile.NamedTemporaryFile(mode="wb", delete=False, suffix=".pem")
tk = tempfile.NamedTemporaryFile(mode="wb", delete=False, suffix=".pem")
tc.write(cert_pem); tc.flush(); tc.close()
tk.write(key_pem); tk.flush(); tk.close()

for name, url in urls_to_test:
    try:
        r = requests.get(url, cert=(tc.name, tk.name), verify=False, timeout=10)
        print(f"  {name}: HTTP {r.status_code} ({len(r.text)} bytes)")
    except Exception as e:
        print(f"  {name}: ERRO - {e}")

os.unlink(tc.name)
os.unlink(tk.name)
