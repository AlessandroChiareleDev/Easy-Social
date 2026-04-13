"""
FECHAR FOLHA SETEMBRO 2025 — Envia S-1299.
NÃO RODA AUTOMATICAMENTE — aguardar OK do operador.

Uso: python3 fechar_set2025.py
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
MAX_POLL = 8
POLL_DELAY = 15

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(f"/tmp/fechar_set2025.log"),
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
    is_producao = (AMBIENTE == "1")

    # Gerar S-1299
    log.info("Gerando S-1299...")
    xml_bytes = S1299XMLGenerator.gerar(empregador, PER_APUR, IND_APURACAO, tp_amb=AMBIENTE)
    log.info(f"  XML gerado ({len(xml_bytes)} bytes)")

    # Assinar
    log.info("Assinando...")
    signed = XMLSigner.assinar(xml_bytes, pfx_data, senha)
    log.info("  Assinado OK")

    # Montar SOAP
    soap = SOAPEnvelopeBuilder.montar_envio([signed], empregador, empregador, grupo=GRUPO)
    log.info(f"  SOAP montado ({len(soap)} chars)")

    # Enviar
    log.info("Enviando ao eSocial...")
    url_envio = SOAPEnvelopeBuilder.url_envio(producao=is_producao)
    resultado = ESocialClient.enviar_lote(soap, pfx_data, senha, url=url_envio)

    if not resultado.get("sucesso"):
        log.error(f"  FALHA no envio: {resultado.get('descricao') or resultado.get('erro')}")
        return False

    protocolo = resultado.get("protocolo")
    log.info(f"  Protocolo: {protocolo}")

    if not protocolo:
        log.error("  Sem protocolo!")
        return False

    # Consultar resultado
    url_consulta = SOAPEnvelopeBuilder.url_consulta(producao=is_producao)
    for attempt in range(1, MAX_POLL + 1):
        log.info(f"  Consultando... (tentativa {attempt}/{MAX_POLL})")
        time.sleep(POLL_DELAY)
        consulta = ESocialClient.consultar_lote(protocolo, pfx_data, senha, url=url_consulta)

        if consulta.get("codigo_resposta") == "101":
            log.info("  Em processamento, aguardando...")
            continue

        if consulta.get("sucesso") and consulta.get("eventos"):
            for evt in consulta["eventos"]:
                recibo = evt.get("nr_recibo")
                cod = evt.get("codigo_resposta")
                desc = evt.get("descricao", "")
                if recibo:
                    log.info(f"  ✓ S-1299 ACEITO! Recibo: {recibo}")
                    log.info(f"    Codigo: {cod} — {desc}")
                    return True
                else:
                    log.error(f"  ✗ S-1299 REJEITADO: [{cod}] {desc}")
                    return False

        if consulta.get("sucesso") is False and consulta.get("codigo_resposta") != "101":
            log.error(f"  Consulta falhou: {consulta.get('descricao') or consulta.get('erro')}")
            break

    log.warning(f"  Timeout — protocolo {protocolo} não resolvido após {MAX_POLL} tentativas")
    log.info(f"  Consulte depois: python3 consultar_proto.py {protocolo}")
    return None


if __name__ == "__main__":
    result = main()
    if result is True:
        print("\n>>> FOLHA SETEMBRO 2025 FECHADA COM SUCESSO <<<")
    elif result is False:
        print("\n>>> FALHA AO FECHAR — VERIFIQUE O LOG <<<")
    else:
        print("\n>>> INCONCLUSIVO — VERIFIQUE O PROTOCOLO <<<")
