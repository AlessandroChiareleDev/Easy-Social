"""
FECHAR FOLHA SETEMBRO 2025 — Envia S-1299.
SEM CONSULTA (cota esgotada). Apenas envia e retorna o protocolo.
"""
import sys, os, time, logging
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import psycopg2
from db_config import LOCAL_DB_CONFIG
from esocial.certificate_manager import CertificateManager
from esocial.esocial_client import ESocialClient
from esocial.soap_builder import SOAPEnvelopeBuilder
from esocial.xml_s1299 import S1299XMLGenerator
from esocial.xml_signer import S1010XMLSigner as XMLSigner

PER_APUR = "2025-09"
AMBIENTE = "1"          # PRODUCAO
IND_APURACAO = "1"      # mensal
GRUPO = 3               # periodicos

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("/tmp/fechar_set2025.log"),
    ],
)
log = logging.getLogger("fechar")


def main():
    log.info("=" * 60)
    log.info(f"  FECHAR FOLHA {PER_APUR} — PRODUCAO")
    log.info("=" * 60)

    # Certificado
    conn = psycopg2.connect(**LOCAL_DB_CONFIG)
    cur = conn.cursor()
    cur.execute("SELECT cnpj, arquivo_path, senha_encrypted FROM certificados_a1 WHERE ativo=TRUE LIMIT 1")
    row = cur.fetchone()
    conn.close()
    cnpj = row[0]
    with open(row[1], "rb") as f:
        pfx_data = f.read()
    senha = CertificateManager.decrypt_password(row[2])
    empregador = {"tpInsc": 1, "nrInsc": cnpj}

    # Gerar S-1299
    log.info("Gerando S-1299...")
    xml_bytes = S1299XMLGenerator.gerar(empregador, PER_APUR, IND_APURACAO, tp_amb=AMBIENTE)
    log.info(f"  XML gerado ({len(xml_bytes)} bytes)")

    # Salvar copia
    save_path = f"/opt/easy-social/xmls_set2025/s1299_fechar_{int(time.time())}.xml"
    with open(save_path, "wb") as f:
        f.write(xml_bytes)
    log.info(f"  XML salvo: {save_path}")

    # Assinar
    log.info("Assinando...")
    signed = XMLSigner.assinar(xml_bytes, pfx_data, senha)
    log.info("  Assinado OK")

    # Montar SOAP
    soap = SOAPEnvelopeBuilder.montar_envio([signed], empregador, empregador, grupo=GRUPO)
    log.info(f"  SOAP montado ({len(soap)} chars)")

    # Enviar
    log.info("Enviando S-1299 ao eSocial...")
    url_envio = SOAPEnvelopeBuilder.url_envio(producao=True)
    resultado = ESocialClient.enviar_lote(soap, pfx_data, senha, url=url_envio)

    if not resultado.get("sucesso"):
        log.error(f"  FALHA no envio: {resultado}")
        return False

    protocolo = resultado.get("protocolo")
    log.info(f"  PROTOCOLO: {protocolo}")
    log.info("  Consulta desabilitada (cota esgotada)")
    log.info(f"  Verifique no portal: Gestao de Eventos > protocolo {protocolo}")
    return protocolo


if __name__ == "__main__":
    result = main()
    if result:
        print(f"\n>>> S-1299 ENVIADO! Protocolo: {result} <<<")
        print(">>> Verifique no portal do eSocial se foi aceito <<<")
    else:
        print("\n>>> FALHA AO ENVIAR S-1299 <<<")
