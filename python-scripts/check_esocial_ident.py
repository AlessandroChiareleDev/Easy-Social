"""Consultar identificadores de eventos no eSocial para CPF 31381951805 (set/2025)."""
import sys, os, logging
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from db_config import LOCAL_DB_CONFIG
from esocial.certificate_manager import CertificateManager
from esocial.esocial_client import ESocialClient
from esocial.soap_builder import SOAPEnvelopeBuilder
from esocial.xml_signer import S1010XMLSigner as XMLSigner
import psycopg2

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("ident")

CPF = "31381951805"

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

def main():
    cnpj_full, pfx_data, senha = _load_cert()
    empregador = {"tpInsc": 1, "nrInsc": cnpj_full}

    # Query multiple date ranges
    date_ranges = [
        ("2025-10-01T00:00:00", "2025-10-31T23:59:59"),
        ("2026-04-01T00:00:00", "2026-04-11T23:59:59"),
    ]

    # Send
    url = SOAPEnvelopeBuilder.url_identificadores(producao=True)
    headers = SOAPEnvelopeBuilder.headers_ident_trabalhador()

    import requests
    from cryptography.hazmat.primitives.serialization import pkcs12, Encoding, PrivateFormat, NoEncryption
    import tempfile

    private_key, certificate, _ = pkcs12.load_key_and_certificates(pfx_data, senha.encode("utf-8"))
    cert_pem = certificate.public_bytes(Encoding.PEM)
    key_pem = private_key.private_bytes(Encoding.PEM, PrivateFormat.TraditionalOpenSSL, NoEncryption())

    with tempfile.NamedTemporaryFile(suffix=".pem", delete=False) as cf:
        cf.write(cert_pem)
        cert_file = cf.name
    with tempfile.NamedTemporaryFile(suffix=".pem", delete=False) as kf:
        kf.write(key_pem)
        key_file = kf.name

    for dt_ini, dt_fim in date_ranges:
        log.info(f"\n=== Consultando {dt_ini} a {dt_fim} ===")
        inner_xml = SOAPEnvelopeBuilder.inner_consulta_ident_trabalhador(
            empregador=empregador,
            cpf=CPF,
            dt_ini=dt_ini,
            dt_fim=dt_fim,
        )

        inner_signed = XMLSigner.assinar(inner_xml.encode("utf-8"), pfx_data, senha)
        inner_signed_str = inner_signed.decode("utf-8") if isinstance(inner_signed, bytes) else inner_signed
        soap = SOAPEnvelopeBuilder.montar_consulta_ident_trabalhador(inner_signed_str)

        resp = requests.post(url, data=soap.encode("utf-8"), headers=headers,
                             cert=(cert_file, key_file), timeout=60, verify=False)
        log.info(f"HTTP {resp.status_code}")
        try:
            from lxml import etree
            root = etree.fromstring(resp.content)
            print(etree.tostring(root, pretty_print=True, encoding="unicode")[:10000])
        except:
            print(resp.text[:10000])

    os.unlink(cert_file)
    os.unlink(key_file)

if __name__ == "__main__":
    main()
