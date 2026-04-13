"""Re-incluir S-1210 do CPF 31381951805 em setembro/2025 - EXATAMENTE como estava."""
import sys, os, time, logging
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from db_config import LOCAL_DB_CONFIG
from esocial.certificate_manager import CertificateManager
from esocial.esocial_client import ESocialClient
from esocial.soap_builder import SOAPEnvelopeBuilder
from esocial.xml_s1210 import S1210XMLGenerator
from esocial.xml_signer import S1010XMLSigner as XMLSigner
import psycopg2

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("reincluir")

AMBIENTE = "1"  # producao
GRUPO = "3"     # periodicos

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

def _enviar_e_consultar(soap_xml, pfx_data, senha, descricao):
    """Envia lote e consulta resultado."""
    url_envio = SOAPEnvelopeBuilder.url_envio(producao=True)
    log.info(f"[{descricao}] Enviando...")
    resultado = ESocialClient.enviar_lote(soap_xml, pfx_data, senha, url=url_envio)
    
    if not resultado.get("sucesso"):
        log.error(f"[{descricao}] FALHA envio: {resultado.get('erro') or resultado.get('descricao')}")
        return False, resultado
    
    protocolo = resultado.get("protocolo")
    log.info(f"[{descricao}] Protocolo: {protocolo}")
    
    url_consulta = SOAPEnvelopeBuilder.url_consulta(producao=True)
    for attempt in range(20):
        time.sleep(5)
        consulta = ESocialClient.consultar_lote(protocolo, pfx_data, senha, url=url_consulta)
        
        if consulta.get("eventos"):
            for evt in consulta["eventos"]:
                nr_recibo = evt.get("nr_recibo")
                if nr_recibo:
                    log.info(f"[{descricao}] ✅ Recibo: {nr_recibo}")
                else:
                    ocorr = evt.get("ocorrencias", [])
                    desc_resp = evt.get("descricao", "")
                    ocorr_txt = "; ".join(f"[{o.get('codigo')}] {o.get('descricao','')}" for o in ocorr)
                    log.error(f"[{descricao}] ✗ Rejeitado: {desc_resp} {ocorr_txt}")
            return True, consulta
        elif consulta.get("codigo_resposta") == "101":
            log.info(f"[{descricao}] ⏳ Processando... ({attempt+1}/20)")
        else:
            log.warning(f"[{descricao}] Resposta: {consulta.get('codigo_resposta')} - {consulta.get('descricao')}")
            if attempt > 10:
                return False, consulta
    
    log.warning(f"[{descricao}] Timeout consultando protocolo {protocolo}")
    return False, {"protocolo": protocolo, "status": "timeout"}

def main():
    cnpj, pfx_data, senha = _load_cert()
    
    empregador = {"tpInsc": 1, "nrInsc": cnpj}
    empregador_soap = {"tpInsc": 1, "nrInsc": cnpj}
    
    # Dados EXATOS do S-1210 original (copiados do XML)
    beneficiario = {"cpfBenef": "31381951805"}
    
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
    
    info_ir_complem = {
        "infoIRCR": [{"tpCR": "056107"}]
    }
    
    log.info("=== Re-incluindo S-1210 CPF 31381951805 set/2025 ===")
    log.info(f"Pagamentos: {len(info_pgtos)}")
    for p in info_pgtos:
        log.info(f"  dtPgto={p['dtPgto']} dmDev={p['ideDmDev']} vrLiq={p['vrLiq']}")
    
    # Gerar XML como INCLUSÃO (indRetif=1, sem nrRecibo)
    xml_bytes = S1210XMLGenerator.gerar(
        empregador=empregador,
        beneficiario=beneficiario,
        info_pgtos=info_pgtos,
        per_apur="2025-09",
        ind_retif="1",
        info_ir_complem=info_ir_complem,
        seq=1,
        tp_amb=AMBIENTE,
    )
    
    xml_assinado = XMLSigner.assinar(xml_bytes, pfx_data, senha)
    
    soap = SOAPEnvelopeBuilder.montar_envio(
        [xml_assinado], empregador_soap, empregador_soap, grupo=int(GRUPO)
    )
    
    ok, result = _enviar_e_consultar(soap, pfx_data, senha, "S-1210 inclusão")
    
    if ok:
        log.info("=== S-1210 RE-INCLUÍDO COM SUCESSO ===")
    else:
        log.error(f"=== FALHA: {result} ===")

if __name__ == "__main__":
    main()
