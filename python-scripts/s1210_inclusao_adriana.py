"""
INCLUSÃO S-1210 Adriana (CPF 31381951805) — Setembro 2025
O S-1210 anterior foi excluído via S-3000. Este é um evento NOVO (indRetif=1).
SEM planSaude (o original não tinha). Apenas infoIRComplem com tpCR.
"""
import sys, os, time, logging
from lxml import etree

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from db_config import LOCAL_DB_CONFIG
from esocial.certificate_manager import CertificateManager
from esocial.esocial_client import ESocialClient
from esocial.soap_builder import SOAPEnvelopeBuilder
from esocial.xml_s1210 import S1210XMLGenerator
from esocial.xml_signer import S1010XMLSigner as XMLSigner
import psycopg2

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("s1210_inclusao_adriana")

AMBIENTE = "1"       # producao
GRUPO = 3            # periodicos
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


def gerar_s1210_inclusao(cnpj_raiz):
    """Gera S-1210 INCLUSÃO (indRetif=1) SEM planSaude."""
    empregador = {"tpInsc": 1, "nrInsc": cnpj_raiz}
    beneficiario = {"cpfBenef": CPF}

    info_pgtos = [
        {
            "dtPgto": "2025-09-05",
            "tpPgto": "1",
            "perRef": "2025-08",
            "ideDmDev": "01511297",
            "vrLiq": "1339.23",
        },
        {
            "dtPgto": "2025-09-19",
            "tpPgto": "1",
            "perRef": "2025-09",
            "ideDmDev": "01511301",
            "vrLiq": "1322.65",
        },
    ]
    info_ir_complem = {"infoIRCR": [{"tpCR": "056107"}]}

    xml_bytes = S1210XMLGenerator.gerar(
        empregador=empregador,
        beneficiario=beneficiario,
        info_pgtos=info_pgtos,
        per_apur=PER_APUR,
        ind_retif="1",             # INCLUSÃO
        nr_recibo=None,            # sem recibo (é inclusão)
        info_ir_complem=info_ir_complem,
        seq=1,
        tp_amb=AMBIENTE,
    )

    return xml_bytes


def main():
    dry_run = "--dry-run" in sys.argv
    cnpj_full, pfx_data, senha = _load_cert()
    cnpj_raiz = cnpj_full[:8]
    empregador_soap = {"tpInsc": 1, "nrInsc": cnpj_full}

    log.info(f"=== S-1210 INCLUSÃO | CPF {CPF} | {PER_APUR} ===")

    # Gerar XML
    xml_bytes = gerar_s1210_inclusao(cnpj_raiz)
    xml_str = xml_bytes.decode() if isinstance(xml_bytes, bytes) else xml_bytes

    # Validações
    assert "<indRetif>1</indRetif>" in xml_str, "Não é inclusão!"
    assert "<nrRecibo>" not in xml_str, "nrRecibo presente numa inclusão!"
    assert "planSaude" not in xml_str, "planSaude NÃO deve estar presente!"
    assert "<tpCR>056107</tpCR>" in xml_str, "tpCR ausente!"
    assert f"<cpfBenef>{CPF}</cpfBenef>" in xml_str, "CPF errado!"
    assert "<ideDmDev>01511297</ideDmDev>" in xml_str, "ideDmDev 01511297 ausente!"
    assert "<ideDmDev>01511301</ideDmDev>" in xml_str, "ideDmDev 01511301 ausente!"
    log.info("Todas validações OK")

    if dry_run:
        log.info("\n=== DRY RUN ===")
        log.info(f"XML tamanho: {len(xml_str)} chars")
        # Mostrar XML limpo
        idx = xml_str.find("<evtPgtos")
        end = xml_str.find("</evtPgtos>") + len("</evtPgtos>")
        if idx > 0 and end > idx:
            log.info(f"\n{xml_str[idx:end]}")
        return

    # Assinar
    log.info("Assinando XML...")
    xml_signed = XMLSigner.assinar(xml_bytes, pfx_data, senha)
    log.info("Assinatura OK")

    # Salvar cópia
    save_path = f"/opt/easy-social/xmls_set2025/s1210_inclusao_adriana_{int(time.time())}.xml"
    with open(save_path, "wb") as f:
        f.write(xml_signed if isinstance(xml_signed, bytes) else xml_signed.encode())
    log.info(f"XML salvo: {save_path}")

    # Montar SOAP
    log.info("Montando lote SOAP...")
    soap = SOAPEnvelopeBuilder.montar_envio(
        [xml_signed], empregador_soap, empregador_soap, grupo=GRUPO
    )

    # Enviar
    url_envio = SOAPEnvelopeBuilder.url_envio(producao=True)
    log.info(f"Enviando... (URL: {url_envio})")
    resultado = ESocialClient.enviar_lote(soap, pfx_data, senha, url=url_envio)

    if not resultado.get("sucesso"):
        log.error(f"FALHA envio: {resultado}")
        sys.exit(1)

    protocolo = resultado["protocolo"]
    log.info(f"Protocolo: {protocolo}")

    # Consultar resultado
    url_consulta = SOAPEnvelopeBuilder.url_consulta(producao=True)
    for attempt in range(25):
        time.sleep(5)
        soap_c = SOAPEnvelopeBuilder.montar_consulta(protocolo)
        retorno = ESocialClient.consultar_lote(soap_c, pfx_data, senha, url=url_consulta)

        if retorno.get("em_processamento") or retorno.get("codigo_resposta") == "101":
            log.info(f"Processando... ({attempt+1}/25)")
            continue

        eventos = retorno.get("eventos", [])
        if not eventos:
            log.warning(f"Sem eventos na resposta: {retorno}")
            continue

        for i, ev in enumerate(eventos):
            nr_recibo = ev.get("nr_recibo")
            ocorr = ev.get("ocorrencias", [])
            if nr_recibo:
                log.info(f"ACEITO! Recibo: {nr_recibo}")
            else:
                desc = "; ".join(
                    f"[{o.get('codigo')}] {o.get('descricao','')[:200]}"
                    for o in ocorr
                )
                log.error(f"REJEITADO: {desc}")
        return

    log.warning("Timeout aguardando resposta do protocolo")


if __name__ == "__main__":
    main()
