import sys, os, time, logging
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from db_config import LOCAL_DB_CONFIG
from esocial.certificate_manager import CertificateManager
from esocial.esocial_client import ESocialClient
from esocial.soap_builder import SOAPEnvelopeBuilder
import psycopg2

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("consulta")

PROTOCOLO = sys.argv[1] if len(sys.argv) > 1 else "1.1.202604.0000000013009230046"

conn = psycopg2.connect(**LOCAL_DB_CONFIG)
cur = conn.cursor()
cur.execute("SELECT cnpj, arquivo_path, senha_encrypted FROM certificados_a1 WHERE ativo = TRUE LIMIT 1")
cnpj, cert_path, senha_enc = cur.fetchone()
conn.close()
senha = CertificateManager.decrypt_password(senha_enc)
with open(cert_path, "rb") as f:
    pfx_data = f.read()

url = SOAPEnvelopeBuilder.url_consulta(producao=True)
log.info("Consultando proto: %s", PROTOCOLO)

for attempt in range(10):
    soap_c = SOAPEnvelopeBuilder.montar_consulta(PROTOCOLO)
    retorno = ESocialClient.consultar_lote(soap_c, pfx_data, senha, url=url)
    log.info("Retorno: %s", retorno)

    err = retorno.get("erro", "")
    if err and "500" in str(err):
        log.info("API 500, tentativa %d/10, aguardando 15s...", attempt + 1)
        time.sleep(15)
        continue

    eventos = retorno.get("eventos", [])
    for i, ev in enumerate(eventos):
        nr = ev.get("nr_recibo")
        ocorr = ev.get("ocorrencias", [])
        if nr:
            log.info("Evt %d: ACEITO recibo=%s", i + 1, nr)
        else:
            parts = []
            for o in ocorr:
                cod = o.get("codigo", "?")
                desc = o.get("descricao", "")
                parts.append("[%s] %s" % (cod, desc[:200]))
            log.error("Evt %d: REJEITADO: %s", i + 1, "; ".join(parts))
    break
