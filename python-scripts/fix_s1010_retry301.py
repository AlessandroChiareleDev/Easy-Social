"""Identificar qual rubrica do lote 1 falhou com 301.3 e re-enviar."""
import sys, os, time, logging, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from db_config import DB_CONFIG, LOCAL_DB_CONFIG
import psycopg2, psycopg2.extras
from esocial.certificate_manager import CertificateManager
from esocial.esocial_client import ESocialClient
from esocial.soap_builder import SOAPEnvelopeBuilder
from esocial.xml_generator import S1010XMLGenerator
from esocial.xml_signer import S1010XMLSigner as XMLSigner

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("fix_301")

AMBIENTE = "1"
GRUPO = 1
PROTO = "1.1.202604.0000000013007225525"

# Lote 1 = primeiras 50 rubricas da lista
LOTE1_CODES = [
    '509','516','520','521','522','524','526','530','537','544',
    '546','547','550','552','554','555','556','558','566','575',
    '580','582','585','586','587','590','594','595','596','600',
    '605','606','607','610','615','616','619','621','627','631',
    '638','640','641','656','657','658','659','667','677','686',
]

def _extract_code(base_legal_str):
    if not base_legal_str:
        return "0"
    s = str(base_legal_str).strip()
    if " - " in s:
        return s.split(" - ")[0].strip()
    try:
        int(s)
        return s
    except ValueError:
        return "0"

def main():
    # Load cert
    conn_local = psycopg2.connect(**LOCAL_DB_CONFIG)
    try:
        with conn_local.cursor() as cur:
            cur.execute(
                "SELECT cnpj, arquivo_path, senha_encrypted "
                "FROM certificados_a1 WHERE ativo = TRUE LIMIT 1"
            )
            row = cur.fetchone()
    finally:
        conn_local.close()

    cnpj, cert_path, senha_enc = row
    senha = CertificateManager.decrypt_password(senha_enc)
    with open(cert_path, "rb") as f:
        pfx_data = f.read()

    # First, consult the lote to find which event failed
    url_consulta = SOAPEnvelopeBuilder.url_consulta(producao=True)
    consulta = ESocialClient.consultar_lote(PROTO, pfx_data, senha, url=url_consulta)
    
    eventos = consulta.get("eventos", [])
    failed_ids = []
    ok_ids = []
    
    for evt in eventos:
        nr_recibo = evt.get("nr_recibo")
        evt_id = evt.get("id", "")
        if nr_recibo:
            ok_ids.append(evt_id)
        else:
            failed_ids.append(evt_id)
            log.info(f"FAILED event ID: {evt_id}")
            log.info(f"  Full event: {evt}")
    
    log.info(f"\nOK: {len(ok_ids)}, Failed: {len(failed_ids)}")
    
    if not failed_ids:
        log.info("Nenhum falhou! Todos OK.")
        return
    
    # Try to identify the rubrica from the event ID
    # Event IDs are: ID{tpInsc}{nrInsc}{timestamp}{seq:05d}
    # The seq tells us which position (1-50) in the lote
    for fid in failed_ids:
        # Extract sequence from last 5 chars
        seq_str = fid[-5:] if len(fid) >= 5 else "?"
        try:
            seq = int(seq_str)
            if 1 <= seq <= len(LOTE1_CODES):
                failed_code = LOTE1_CODES[seq - 1]
                log.info(f"  Failed seq={seq} → rubrica {failed_code}")
            else:
                log.info(f"  Failed seq={seq} (out of range)")
                failed_code = None
        except ValueError:
            log.info(f"  Could not parse seq from ID: {fid}")
            failed_code = None
    
    if not failed_code:
        log.info("Não consegui identificar a rubrica. Vou reenviar todas do lote 1 que não receberam recibo.")
        return
    
    log.info(f"\n--- Reenviando rubrica {failed_code} ---")
    
    # Load rubrica data
    conn = psycopg2.connect(**DB_CONFIG, keepalives=1, keepalives_idle=30,
                            keepalives_interval=10, keepalives_count=3)
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    
    cur.execute("""
        SELECT cod_rubrica, descricao, cod_natureza,
               incid_base_legal_inss, incid_base_legal_irrf, incid_base_legal_fgts,
               ini_valid_esocial
        FROM cruzamento_eb
        WHERE cod_rubrica = %s AND envio_status IN ('enviado', 'feito')
    """, (failed_code,))
    c = dict(cur.fetchone())
    
    # tpRubr
    cur.execute("SELECT DISTINCT tp_rubr FROM explorador_rubricas WHERE cod_rubr = %s AND tp_rubr IS NOT NULL", (failed_code,))
    r = cur.fetchone()
    tp = int(r['tp_rubr']) if r else None
    if tp is None:
        cur.execute("SELECT valor_novo FROM esocial_depara WHERE campo = 'tpRubr' AND cod_rubrica = %s", (failed_code,))
        r = cur.fetchone()
        tp = int(r['valor_novo']) if r else 2
    
    # codIncPisPasep
    cur.execute("SELECT valor_novo FROM esocial_depara WHERE campo = 'codIncPisPasep' AND cod_rubrica = %s", (failed_code,))
    r = cur.fetchone()
    pis = r['valor_novo'] if r else "00"
    
    conn.close()
    
    rub = {
        "codRubr": failed_code,
        "ideTabRubr": "1",
        "iniValid": c.get('ini_valid_esocial') or "2018-02",
        "dscRubr": (c.get('descricao') or f"RUBRICA {failed_code}")[:100],
        "natRubr": _extract_code(c.get('cod_natureza')),
        "tpRubr": tp,
        "codIncCP": _extract_code(c.get('incid_base_legal_inss')),
        "codIncIRRF": _extract_code(c.get('incid_base_legal_irrf')),
        "codIncFGTS": _extract_code(c.get('incid_base_legal_fgts')),
        "codIncPisPasep": pis,
    }
    
    log.info(f"  Dados: {rub}")
    
    empregador = {"tpInsc": 1, "nrInsc": cnpj}
    generator = S1010XMLGenerator()
    
    xml_bytes = generator.gerar_alteracao(empregador, rub, tp_amb=AMBIENTE)
    xml_assinado = XMLSigner.assinar(xml_bytes, pfx_data, senha)
    
    soap = SOAPEnvelopeBuilder.montar_envio(
        [xml_assinado], empregador, empregador, grupo=GRUPO
    )
    
    url_envio = SOAPEnvelopeBuilder.url_envio(producao=True)
    log.info(f"  Enviando para {url_envio}...")
    resultado = ESocialClient.enviar_lote(soap, pfx_data, senha, url=url_envio)
    
    if not resultado.get("sucesso"):
        log.error(f"  ✗ Envio falhou: {resultado.get('erro') or resultado.get('descricao')}")
        return
    
    protocolo = resultado.get("protocolo")
    log.info(f"  ✓ Protocolo: {protocolo}")
    
    for attempt in range(15):
        time.sleep(5)
        consulta = ESocialClient.consultar_lote(protocolo, pfx_data, senha, url=url_consulta)
        
        if consulta.get("eventos"):
            for evt in consulta["eventos"]:
                nr_recibo = evt.get("nr_recibo")
                if nr_recibo:
                    log.info(f"  ✅ SUCESSO — Recibo: {nr_recibo}")
                else:
                    ocorr = evt.get("ocorrencias", [])
                    ocorr_txt = "; ".join(f"[{o.get('codigo')}] {o.get('descricao','')}" for o in ocorr)
                    log.error(f"  ✗ Rejeitado: {ocorr_txt}")
            break
        elif consulta.get("codigo_resposta") == "101":
            log.info(f"  ⏳ Aguardando... ({attempt+1}/15)")
        else:
            log.warning(f"  Consulta: {consulta.get('codigo_resposta')} - {consulta.get('descricao')}")
            break

if __name__ == "__main__":
    main()
