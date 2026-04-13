"""Debug SOAP envelope for S-3000."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from db_config import LOCAL_DB_CONFIG
from esocial.certificate_manager import CertificateManager
from esocial.soap_builder import SOAPEnvelopeBuilder
from esocial.xml_s3000 import S3000XMLGenerator
from esocial.xml_signer import S1010XMLSigner as XMLSigner
import psycopg2

def _load_cert():
    conn = psycopg2.connect(**LOCAL_DB_CONFIG)
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT cnpj, arquivo_path, senha_encrypted "
                "FROM certificados_a1 WHERE ativo = TRUE LIMIT 1"
            )
            row = cur.fetchone()
    finally:
        conn.close()
    cnpj, cert_path, senha_enc = row
    senha = CertificateManager.decrypt_password(senha_enc)
    with open(cert_path, "rb") as f:
        pfx_data = f.read()
    return cnpj, pfx_data, senha

cnpj_full, pfx_data, senha = _load_cert()
cnpj_raiz = cnpj_full[:8]

xml_bytes = S3000XMLGenerator.gerar(
    empregador={"tpInsc": 1, "nrInsc": cnpj_raiz},
    tp_evento="S-1210",
    nr_rec_evt="1.1.0000000035299436298",
    cpf_trab="31381951805",
    per_apur="2025-09",
    ind_apuracao="1",
    tp_amb="1",
)

xml_str = xml_bytes.decode("utf-8")
print("=== S-3000 Event XML ===")
print(xml_str[:800])
print()

xml_assinado = XMLSigner.assinar(xml_bytes, pfx_data, senha)
emp_soap = {"tpInsc": 1, "nrInsc": cnpj_full}

# Try different grupos
for grupo in [3, 4, "3", "4"]:
    soap = SOAPEnvelopeBuilder.montar_envio(
        [xml_assinado], emp_soap, emp_soap, grupo=grupo
    )
    # Find grupo in SOAP
    idx = soap.find("grupo=")
    snippet = soap[idx:idx+20] if idx >= 0 else "NOT FOUND"
    print(f"Grupo={grupo} (type={type(grupo).__name__}): {snippet}")
    if grupo == 3:
        print("  SOAP (first 1500 chars):")
        print(soap[:1500])
