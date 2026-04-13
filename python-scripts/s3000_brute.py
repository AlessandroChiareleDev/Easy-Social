"""
Brute-force S-3000 attempt: try all known S-1210 recibos for CPF,
then attempt S-1200 retification.
"""
import sys, os, time, logging, json
from lxml import etree

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from db_config import DB_CONFIG, LOCAL_DB_CONFIG
import psycopg2, psycopg2.extras
from esocial.certificate_manager import CertificateManager
from esocial.esocial_client import ESocialClient
from esocial.soap_builder import SOAPEnvelopeBuilder
from esocial.xml_s3000 import S3000XMLGenerator
from esocial.xml_signer import S1010XMLSigner as XMLSigner

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("s3000_brute")

AMBIENTE = "1"
PER_APUR = "2025-09"
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


def _enviar_e_consultar(xml_bytes, pfx_data, senha, empregador, grupo, max_poll=15, poll_interval=5):
    xml_assinado = XMLSigner.assinar(xml_bytes, pfx_data, senha)
    transmissor = empregador.copy()
    soap = SOAPEnvelopeBuilder.montar_envio(
        [xml_assinado], empregador, transmissor, grupo=grupo
    )
    url_envio = SOAPEnvelopeBuilder.url_envio(producao=True)
    resultado = ESocialClient.enviar_lote(soap, pfx_data, senha, url=url_envio)

    if not resultado.get("sucesso"):
        return {"sucesso": False, "erro": resultado.get("erro") or resultado.get("descricao")}

    protocolo = resultado["protocolo"]
    log.info(f"  Protocolo: {protocolo}")

    url_consulta = SOAPEnvelopeBuilder.url_consulta(producao=True)
    for attempt in range(max_poll):
        time.sleep(poll_interval)
        consulta = ESocialClient.consultar_lote(protocolo, pfx_data, senha, url=url_consulta)

        if consulta.get("eventos"):
            evt = consulta["eventos"][0]
            nr_recibo = evt.get("nr_recibo")
            if nr_recibo:
                return {"sucesso": True, "nr_recibo": nr_recibo, "protocolo": protocolo}
            else:
                ocorr = evt.get("ocorrencias", [])
                ocorr_txt = "; ".join(f"[{o.get('codigo')}] {o.get('descricao','')}" for o in ocorr)
                codigo = evt.get("codigo_resposta", "?")
                descricao = evt.get("descricao", "")
                return {
                    "sucesso": False,
                    "erro": f"Código {codigo}: {descricao}. Ocorrências: {ocorr_txt}",
                    "protocolo": protocolo,
                }
        elif consulta.get("codigo_resposta") == "101":
            log.info(f"  ⏳ Processando... ({attempt+1}/{max_poll})")
        else:
            log.info(f"  Consulta: {consulta.get('codigo_resposta')} - {consulta.get('descricao')}")

    return {"sucesso": False, "erro": f"Timeout após {max_poll} tentativas", "protocolo": protocolo}


# All known S-1210 recibos for this CPF (oldest to newest)
S1210_RECIBOS = [
    "1.1.0000000035006855661",  # Original Oct 6
    "1.1.0000000035299436298",  # Retif Oct 24
    "1.1.0000000039841834445",  # Pipeline retif
]

def main():
    cnpj, pfx_data, senha = _load_cert()
    empregador = {"tpInsc": 1, "nrInsc": cnpj}

    log.info("=== Brute-force S-3000 para todos os recibos S-1210 conhecidos ===")
    log.info(f"CPF: {CPF}")

    for recibo in S1210_RECIBOS:
        log.info(f"\n--- Tentando S-3000 excluir S-1210 recibo: {recibo} ---")
        xml_3000 = S3000XMLGenerator.gerar(
            empregador=empregador,
            tp_evento="S-1210",
            nr_rec_evt=recibo,
            cpf_trab=CPF,
            per_apur=PER_APUR,
            tp_amb=AMBIENTE,
        )
        result = _enviar_e_consultar(xml_3000, pfx_data, senha, empregador, grupo="2")
        if result["sucesso"]:
            log.info(f"  ✅ S-3000 OK — Novo recibo: {result['nr_recibo']}")
        else:
            log.info(f"  ❌ Falhou: {result.get('erro', '?')}")

    log.info("\n=== Todas as tentativas concluídas ===")


if __name__ == "__main__":
    main()
