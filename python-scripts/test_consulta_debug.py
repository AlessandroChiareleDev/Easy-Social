"""Debug script for eSocial consultation"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

import requests, tempfile
from cryptography.hazmat.primitives.serialization import pkcs12, Encoding, PrivateFormat, NoEncryption
from cryptography.hazmat.backends import default_backend
import urllib3
urllib3.disable_warnings()
import psycopg2
from esocial.certificate_manager import CertificateManager

# Load cert
conn = psycopg2.connect(host='localhost', port=5432, database='easy_social_db', user='easy_social_user', password='sua_senha_segura')
cur = conn.cursor()
cur.execute('SELECT arquivo_path, senha_encrypted FROM certificados_a1 WHERE ativo=TRUE LIMIT 1')
row = cur.fetchone()
conn.close()

arquivo_path, senha_enc = row
senha = CertificateManager.decrypt_password(senha_enc)

with open(arquivo_path, 'rb') as f:
    pfx_data = f.read()

pk, cert, _ = pkcs12.load_key_and_certificates(pfx_data, senha.encode(), default_backend())
cert_pem = cert.public_bytes(Encoding.PEM)
key_pem = pk.private_bytes(Encoding.PEM, PrivateFormat.TraditionalOpenSSL, NoEncryption())

tc = tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.pem')
tk = tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.pem')
tc.write(cert_pem); tc.close()
tk.write(key_pem); tk.close()

protocolo = '1.2.202603.0000000000205430968'

soap = (
    '<?xml version="1.0" encoding="UTF-8"?>\n'
    '<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" '
    'xmlns:v1="http://www.esocial.gov.br/servicos/empregador/lote/eventos/'
    'envio/consulta/retornoProcessamento/v1_0_0">\n'
    '  <soapenv:Header/>\n'
    '  <soapenv:Body>\n'
    '    <v1:ConsultarLoteEventos>\n'
    f'      <v1:protocoloEnvio>{protocolo}</v1:protocoloEnvio>\n'
    '    </v1:ConsultarLoteEventos>\n'
    '  </soapenv:Body>\n'
    '</soapenv:Envelope>'
)

url = 'https://webservices.producaorestrita.esocial.gov.br/servicos/empregador/consultarloteeventos/WsConsultarLoteEventos.svc'
headers = {
    'Content-Type': 'text/xml; charset=utf-8',
    'SOAPAction': ('http://www.esocial.gov.br/servicos/empregador/lote/eventos/'
                   'envio/consulta/retornoProcessamento/v1_1_0/'
                   'ServicoConsultarLoteEventos/ConsultarLoteEventos'),
}

print(f'Consultando protocolo: {protocolo}')
r = requests.post(url, data=soap.encode('utf-8'), headers=headers, cert=(tc.name, tk.name), verify=False, timeout=60)
print(f'Status: {r.status_code}')
print(f'Response ({len(r.text)} chars):')
print(r.text[:3000])

os.unlink(tc.name)
os.unlink(tk.name)
