"""Consulta identificadores S-1298 e S-1299 direto no eSocial webservice."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import psycopg2
from db_config import LOCAL_DB_CONFIG
from esocial.certificate_manager import CertificateManager
from esocial.esocial_client import ESocialClient

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

for tp in ["S-1299", "S-1298"]:
    print(f"\n{'='*60}")
    print(f"  CONSULTA IDENTIFICADORES: {tp} em 2025-09")
    print(f"{'='*60}")
    try:
        result = ESocialClient.consultar_identificadores_empregador(
            tp_evt=tp,
            per_apur="2025-09",
            pfx_data=pfx_data,
            password=senha,
            empregador=empregador,
            producao=True,
        )
        print(f"Sucesso: {result.get('sucesso')}")
        print(f"Codigo: {result.get('codigo_resposta')}")
        print(f"Descricao: {result.get('descricao')}")
        
        if result.get("eventos"):
            print(f"Eventos: {len(result['eventos'])}")
            for evt in result["eventos"]:
                print(f"  {evt}")
        
        if result.get("xml_resposta"):
            xml = result["xml_resposta"]
            # Print relevant part
            print(f"\nXML resposta ({len(xml)} chars):")
            print(xml[:3000])
        
        print(f"Keys: {list(result.keys())}")
    except Exception as e:
        print(f"ERRO: {e}")
        import traceback
        traceback.print_exc()
