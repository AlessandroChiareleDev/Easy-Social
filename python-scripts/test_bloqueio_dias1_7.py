"""Testa se o bloqueio dos dias 1-7 do eSocial ainda está ativo e registra no banco."""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import psycopg2
from db_config import DB_CONFIG, LOCAL_DB_CONFIG
from esocial.certificate_manager import CertificateManager
from esocial.esocial_client import ESocialClient
from esocial.envio_tracker import registrar_consulta

# Certificado vem do banco local
local_conn = psycopg2.connect(**LOCAL_DB_CONFIG)
cur = local_conn.cursor()
cur.execute("SELECT cnpj, arquivo_path, senha_encrypted FROM certificados_a1 WHERE ativo = TRUE LIMIT 1")
row = cur.fetchone()
local_conn.close()

# Tracker usa Supabase (banco principal)
conn = psycopg2.connect(**DB_CONFIG)

cnpj, arquivo_path, senha_enc = row
senha = CertificateManager.decrypt_password(senha_enc)
with open(arquivo_path, "rb") as f:
    pfx_data = f.read()

empregador = {"tpInsc": 1, "nrInsc": cnpj[:8]}

print("=" * 60)
print("  TESTE BLOQUEIO DIAS 1-7 DO ESOCIAL")
print("  Consulta Identificadores Trabalhador (Producao)")
print("=" * 60)

result = ESocialClient.consultar_identificadores_trabalhador(
    cpf="08132588983",
    dt_ini="2024-12-01T00:00:00",
    dt_fim="2024-12-28T23:59:59",
    pfx_data=pfx_data,
    password=senha,
    empregador=empregador,
    producao=True,
)

result_clean = {k: v for k, v in result.items() if k != "xml_resposta"}
print(json.dumps(result_clean, indent=2, ensure_ascii=False, default=str))

# Registrar no banco usando o tracker
envio_id = registrar_consulta(
    conn,
    tipo_consulta="CONSULTA-IDENT",
    ambiente="1",
    resultado=result,
    cpf="08132588983",
    per_apur="2024-12",
    xml_resposta=result.get("xml_resposta"),
    origem="test_bloqueio_dias1_7",
)
print(f"\n>>> Registrado no banco como envio #{envio_id} <<<")

descricao = str(result.get("descricao", ""))
if "dias 1 e 7" in descricao:
    print(">>> BLOQUEIO DIAS 1-7 DETECTADO - PROVA REGISTRADA! <<<")
elif result.get("sucesso"):
    eventos = result.get("eventos", [])
    print(f">>> Consulta FUNCIONOU - {len(eventos)} eventos encontrados <<<")
    print(">>> O bloqueio dias 1-7 ja acabou (dia 8) <<<")
else:
    print(f">>> Resultado: {descricao} <<<")

conn.close()
