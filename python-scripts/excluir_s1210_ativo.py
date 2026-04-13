"""Excluir S-1210 ativo para CPF 31381951805 antes de retificar S-1200."""
import sys, os, time, logging
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from db_config import LOCAL_DB_CONFIG
from esocial.certificate_manager import CertificateManager
from esocial.esocial_client import ESocialClient
from esocial.soap_builder import SOAPEnvelopeBuilder
from esocial.xml_s3000 import S3000XMLGenerator
from esocial.xml_signer import S1010XMLSigner as XMLSigner
import psycopg2

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("s3000")

AMBIENTE = "1"
GRUPO = 4  # S-3000 goes in grupo 4 (exclusao)

# Recibos S-1210 candidatos (do mais recente pro mais antigo)
RECIBOS = [
    "1.1.0000000035299436298",  # Oct 24 pipeline
    "1.1.0000000035006855661",  # Oct 6 original
]


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
    cnpj_raiz = cnpj_full[:8]
    empregador_soap = {"tpInsc": 1, "nrInsc": cnpj_full}

    dry_run = "--dry-run" in sys.argv

    for recibo in RECIBOS:
        log.info(f"=== Tentando S-3000 para S-1210 recibo: {recibo} ===")

        xml_bytes = S3000XMLGenerator.gerar(
            empregador={"tpInsc": 1, "nrInsc": cnpj_raiz},
            tp_evento="S-1210",
            nr_rec_evt=recibo,
            cpf_trab="31381951805",
            per_apur="2025-09",
            ind_apuracao="1",
            tp_amb=AMBIENTE,
        )

        if dry_run:
            xml_str = xml_bytes.decode("utf-8") if isinstance(xml_bytes, bytes) else xml_bytes
            log.info(f"DRY RUN - XML size: {len(xml_str)} bytes")
            if recibo in xml_str:
                log.info(f"OK - recibo {recibo} presente no XML")
            continue

        xml_assinado = XMLSigner.assinar(xml_bytes, pfx_data, senha)
        soap = SOAPEnvelopeBuilder.montar_envio(
            [xml_assinado], empregador_soap, empregador_soap, grupo=GRUPO
        )

        url_envio = SOAPEnvelopeBuilder.url_envio(producao=True)
        log.info("Enviando...")
        resultado = ESocialClient.enviar_lote(soap, pfx_data, senha, url=url_envio)

        if not resultado.get("sucesso"):
            log.error(f"FALHA envio: {resultado.get('erro') or resultado.get('descricao')}")
            continue

        protocolo = resultado.get("protocolo")
        log.info(f"Protocolo: {protocolo}")

        url_consulta = SOAPEnvelopeBuilder.url_consulta(producao=True)
        for attempt in range(20):
            time.sleep(5)
            consulta = ESocialClient.consultar_lote(protocolo, pfx_data, senha, url=url_consulta)
            if consulta.get("eventos"):
                for evt in consulta["eventos"]:
                    nr_rec = evt.get("nr_recibo")
                    if nr_rec:
                        log.info(f"ACEITO! Recibo exclusao: {nr_rec}")
                        log.info("S-1210 excluido com sucesso. Agora rode fix_774_to_607.py --step1")
                        return
                    else:
                        ocorr = evt.get("ocorrencias", [])
                        desc_resp = evt.get("descricao", "")
                        ocorr_txt = "; ".join(
                            f"[{o.get('codigo')}] {o.get('descricao','')[:120]}" for o in ocorr
                        )
                        log.warning(f"Rejeitado: {desc_resp} {ocorr_txt}")
                        if any(o.get("codigo") == "536" for o in ocorr):
                            log.info("Erro [536] = ja excluido. Tentando proximo recibo...")
                        break
                break
            elif consulta.get("codigo_resposta") == "101":
                log.info(f"Processando... ({attempt+1}/20)")
            else:
                log.warning(f"Resp: {consulta.get('codigo_resposta')} - {consulta.get('descricao')}")
                if attempt > 10:
                    break

    log.info("Todos os recibos tentados.")


if __name__ == "__main__":
    main()
