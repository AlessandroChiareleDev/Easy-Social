"""Consultar resultado dos 2 lotes de fix S-1010 tpRubr."""
import sys, os, time, logging
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from db_config import LOCAL_DB_CONFIG
import psycopg2
from esocial.certificate_manager import CertificateManager
from esocial.esocial_client import ESocialClient
from esocial.soap_builder import SOAPEnvelopeBuilder

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("consulta")

PROTOCOLOS = [
    "1.1.202604.0000000013007225525",  # lote 1 — 50 rubricas
    "1.1.202604.0000000013007240037",  # lote 2 — 26 rubricas
]

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

    if not row:
        log.error("Nenhum certificado A1 ativo!")
        return

    cnpj, cert_path, senha_enc = row
    senha = CertificateManager.decrypt_password(senha_enc)
    with open(cert_path, "rb") as f:
        pfx_data = f.read()

    url_consulta = SOAPEnvelopeBuilder.url_consulta(producao=True)
    
    for proto in PROTOCOLOS:
        log.info(f"\n{'='*70}")
        log.info(f"Protocolo: {proto}")
        log.info(f"{'='*70}")
        
        consulta = ESocialClient.consultar_lote(proto, pfx_data, senha, url=url_consulta)
        
        cod_resp = consulta.get("codigo_resposta", "?")
        desc_resp = consulta.get("descricao", "?")
        log.info(f"  Código resposta: {cod_resp} — {desc_resp}")
        
        eventos = consulta.get("eventos", [])
        if not eventos:
            log.info(f"  Nenhum evento retornado (ainda processando?)")
            continue
        
        ok = 0
        erros = 0
        for evt in eventos:
            nr_recibo = evt.get("nr_recibo")
            cod = evt.get("codigo_resposta", "")
            desc = evt.get("descricao", "")
            ocorr = evt.get("ocorrencias", [])
            
            if nr_recibo:
                ok += 1
            else:
                erros += 1
                ocorr_txt = "; ".join(
                    f"[{o.get('codigo')}] {o.get('descricao','')[:80]}" for o in ocorr
                ) if ocorr else desc
                log.error(f"    ✗ [{cod}] {ocorr_txt}")
        
        log.info(f"\n  ✅ OK: {ok}  |  ✗ Erros: {erros}  |  Total: {len(eventos)}")

    log.info(f"\n{'='*70}")
    log.info("Consulta concluída")

if __name__ == "__main__":
    main()
