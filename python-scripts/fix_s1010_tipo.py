"""
Fix S-1010: Reenviar rubricas 571 e 572 com tpRubr=2 (Desconto) correto.

Bug encontrado: _load_rubricas_by_ids() hardcodava tipo="Vencimento" (tpRubr=1).
Rubricas 571 (DESC. I.R.F. S/FERIAS) e 572 (DESC. I.R.F. S/13º SALARIO)
são DESCONTOS (tpRubr=2) mas foram enviadas como VENCIMENTOS (tpRubr=1).

Isso causava [1955] porque eSocial via a rubrica como proventos (tipo 1),
e o somatório de tipo 1,3 > tipo 2,4 para codIncIRRF 33 → negativo.
"""
import sys, os, json, time, logging
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from db_config import DB_CONFIG, LOCAL_DB_CONFIG
import psycopg2
from esocial.certificate_manager import CertificateManager
from esocial.esocial_client import ESocialClient
from esocial.soap_builder import SOAPEnvelopeBuilder
from esocial.xml_generator import S1010XMLGenerator
from esocial.xml_signer import S1010XMLSigner as XMLSigner

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("fix_s1010_tipo")

AMBIENTE = "1"  # PRODUÇÃO
GRUPO = 1       # tabelas

RUBRICAS = [
    {
        "codRubr": "571",
        "ideTabRubr": "1",
        "iniValid": "2018-02",
        "dscRubr": "DESC. I.R.F. S/FERIAS",
        "natRubr": "9203",
        "tpRubr": 2,          # DESCONTO — estava sendo enviado como 1!!
        "codIncCP": "0",
        "codIncIRRF": "33",
        "codIncFGTS": "0",
        "codIncPisPasep": "00",
    },
    {
        "codRubr": "572",
        "ideTabRubr": "1",
        "iniValid": "2018-02",
        "dscRubr": "DESC. I.R.F. S/13 SALARIO",
        "natRubr": "9203",
        "tpRubr": 2,          # DESCONTO — estava sendo enviado como 1!!
        "codIncCP": "0",
        "codIncIRRF": "32",
        "codIncFGTS": "0",
        "codIncPisPasep": "00",
    },
]


def main():
    log.info("=" * 60)
    log.info("FIX S-1010: Rubricas 571/572 → tpRubr=2 (Desconto)")
    log.info("=" * 60)

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
        sys.exit(1)

    cnpj, cert_path, senha_enc = row
    senha = CertificateManager.decrypt_password(senha_enc)
    with open(cert_path, "rb") as f:
        pfx_data = f.read()

    empregador = {"tpInsc": 1, "nrInsc": cnpj}
    is_producao = (AMBIENTE == "1")
    tp_amb = AMBIENTE

    generator = S1010XMLGenerator()

    for rubrica in RUBRICAS:
        log.info(f"\n--- Rubrica {rubrica['codRubr']}: {rubrica['dscRubr']} ---")
        log.info(f"  tpRubr={rubrica['tpRubr']} (Desconto), codIncIRRF={rubrica['codIncIRRF']}")

        # Gerar XML S-1010 alteração
        xml_bytes = generator.gerar_alteracao(empregador, rubrica, tp_amb=tp_amb)
        
        # Log the XML to verify tpRubr
        xml_str = xml_bytes.decode('utf-8') if isinstance(xml_bytes, bytes) else xml_bytes
        import re
        tp_match = re.search(r'<tpRubr>(\d+)</tpRubr>', xml_str)
        log.info(f"  XML tpRubr: {tp_match.group(1) if tp_match else '???'}")

        # Assinar
        xml_assinado = XMLSigner.assinar(xml_bytes, pfx_data, senha)

        # SOAP
        soap = SOAPEnvelopeBuilder.montar_envio(
            [xml_assinado], empregador, empregador, grupo=GRUPO
        )

        # Enviar
        url_envio = SOAPEnvelopeBuilder.url_envio(producao=is_producao)
        log.info(f"  Enviando para {url_envio}...")
        resultado = ESocialClient.enviar_lote(soap, pfx_data, senha, url=url_envio)

        if not resultado.get("sucesso"):
            log.error(f"  ✗ Envio falhou: {resultado.get('erro') or resultado.get('descricao')}")
            continue

        protocolo = resultado.get("protocolo")
        log.info(f"  ✓ Enviado! Protocolo: {protocolo}")

        # Consultar resultado
        url_consulta = SOAPEnvelopeBuilder.url_consulta(producao=is_producao)
        for attempt in range(10):
            time.sleep(5)
            consulta = ESocialClient.consultar_lote(protocolo, pfx_data, senha, url=url_consulta)
            
            if consulta.get("eventos"):
                for evt in consulta["eventos"]:
                    nr_recibo = evt.get("nr_recibo")
                    cod = evt.get("codigo_resposta", "")
                    desc = evt.get("descricao", "")
                    ocorr = evt.get("ocorrencias", [])

                    if nr_recibo:
                        log.info(f"  ✅ SUCESSO — Recibo: {nr_recibo}")
                    else:
                        ocorr_txt = "; ".join(
                            f"[{o.get('codigo')}] {o.get('descricao','')}" for o in ocorr
                        ) if ocorr else desc
                        log.error(f"  ✗ Rejeitado — [{cod}] {ocorr_txt}")
                break
            elif consulta.get("codigo_resposta") == "101":
                log.info(f"  ⏳ Aguardando... (tentativa {attempt+1}/10)")
                continue
            else:
                log.warning(f"  Consulta: {consulta.get('codigo_resposta')} — {consulta.get('descricao')}")
                if consulta.get("codigo_resposta") not in ("101", "201", "202"):
                    break
        
        time.sleep(2)  # pausa entre rubricas

    log.info("\n" + "=" * 60)
    log.info("FIX S-1010 concluído")
    log.info("=" * 60)


if __name__ == "__main__":
    main()
