"""Tenta consultar status da folha de forma indireta.
Se mandar S-1299 dry (sem assinar/enviar), posso ao menos ver
o que o consultar_identificadores retorna."""
import sys, os, json
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

# Consultar identificadores do empregador para S-1299 no periodo 2025-09
# Se retornar eventos = existem S-1299 ativos = fechado
# Se retornar vazio = nenhum S-1299 ativo = aberto
for tp in ["S-1299", "S-1298"]:
    print(f"\n{'='*60}")
    print(f"Consultando {tp} para 2025-09")
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
        print(f"Result keys: {list(result.keys())}")
        for k, v in result.items():
            if k == 'xml_resposta':
                print(f"  xml_resposta ({len(v)} chars):")
                print(v[:2000])
            else:
                print(f"  {k}: {v}")
    except Exception as e:
        import traceback
        print(f"ERRO: {e}")
        traceback.print_exc()

# Also try consultar o protocolo do combo lote da 774
print(f"\n{'='*60}")
print("Consultando protocolo combo 774: 1.1.202604.0000000013009230046")
print(f"{'='*60}")
try:
    url = SOAPEnvelopeBuilder.url_consulta(producao=True)
    result = ESocialClient.consultar_lote(
        "1.1.202604.0000000013009230046",
        pfx_data, senha, url=url
    )
    print(f"Sucesso: {result.get('sucesso')}")
    print(f"Codigo: {result.get('codigo_resposta')}")
    print(f"Descricao: {result.get('descricao')}")
    if result.get("eventos"):
        for evt in result["eventos"]:
            print(f"  id={evt.get('id')} recibo={evt.get('nr_recibo')} "
                  f"cod={evt.get('codigo_resposta')} desc={evt.get('descricao','')[:150]}")
except Exception as e:
    print(f"ERRO: {e}")
