"""
Script de teste: Envio S-1010 para rubricas 566 e 596 em HOMOLOGACAO
Pipeline CPF 08132588983 - Etapa 1: Corrigir rubricas
"""
import sys, os, json, time
sys.path.insert(0, os.path.dirname(__file__))

from db_config import DB_CONFIG, LOCAL_DB_CONFIG
from esocial.certificate_manager import CertificateManager
from esocial.xml_generator import S1010XMLGenerator
from esocial.xml_signer import S1010XMLSigner
from esocial.soap_builder import SOAPEnvelopeBuilder
from esocial.esocial_client import ESocialClient
import psycopg2

TP_AMB = "1"  # PRODUCAO
CNPJ = "05969071000110"
RUBRICA_IDS = ["566", "596"]

def main():
    print("=" * 60)
    print(f"S-1010 ENVIO — tp_amb={TP_AMB} ({'HOMOLOGAÇÃO' if TP_AMB == '2' else 'PRODUÇÃO'})")
    print("=" * 60)

    # 1. Buscar dados das rubricas no Supabase
    print("\n[1] Buscando dados das rubricas no cruzamento_eb...")
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    cur.execute("""
        SELECT cod_rubrica, descricao, cod_natureza,
               incid_inss, incid_irrf, incid_fgts,
               incid_base_legal_inss, incid_base_legal_irrf, incid_base_legal_fgts
        FROM cruzamento_eb
        WHERE cod_rubrica = ANY(%s)
        ORDER BY CAST(cod_rubrica AS int)
    """, (RUBRICA_IDS,))
    rows = cur.fetchall()
    cur.close()
    conn.close()

    if not rows:
        print("ERRO: Rubricas não encontradas!")
        return

    def extrair_codigo(base_legal):
        if not base_legal or base_legal.startswith("Rubrica"):
            return "00"
        return base_legal.split(" - ")[0].strip() or "00"

    # Valores CORRETOS conhecidos — base_legal tem múltiplos códigos concatenados,
    # o split(" - ")[0] pega o primeiro (errado pra 596).
    # Rubrica 566 (INSS mensal): INSS=31, IRRF=41, FGTS=0
    # Rubrica 596 (INSS 13º):   INSS=32, IRRF=42, FGTS=0
    OVERRIDE = {
        "566": {"codIncCP": "31", "codIncIRRF": "41", "codIncFGTS": "00"},
        "596": {"codIncCP": "32", "codIncIRRF": "42", "codIncFGTS": "00"},
    }

    # Montar dados das rubricas
    rubricas = []
    for row in rows:
        cod, desc, nat, inss, irrf, fgts, bl_inss, bl_irrf, bl_fgts = row
        nat_code = (nat or "").split(" - ")[0].strip() if nat else "0"

        override = OVERRIDE.get(cod, {})
        inss_correto = override.get("codIncCP", extrair_codigo(bl_inss))
        irrf_correto = override.get("codIncIRRF", extrair_codigo(bl_irrf))
        fgts_correto = override.get("codIncFGTS", extrair_codigo(bl_fgts))

        rubrica = {
            "codRubr": cod,
            "ideTabRubr": "1",
            "iniValid": "2018-02",  # Data padrão empresa (S-1000)
            "dscRubr": (desc or "RUBRICA")[:100],
            "natRubr": nat_code,
            "tpRubr": 2,  # Desconto (ambas 566 e 596 são descontos)
            "codIncCP": inss_correto,
            "codIncIRRF": irrf_correto,
            "codIncFGTS": fgts_correto,
            "codIncPisPasep": "00",
        }
        rubricas.append(rubrica)

        print(f"\n  Rubrica {cod} - {desc}")
        print(f"    natRubr: {nat_code} (de: {nat})")
        print(f"    INSS atual={inss} → correto={inss_correto} (base: {bl_inss[:60] if bl_inss else 'N/A'}...)")
        print(f"    IRRF atual={irrf} → correto={irrf_correto} (base: {bl_irrf[:60] if bl_irrf else 'N/A'}...)")
        print(f"    FGTS atual={fgts} → correto={fgts_correto} (base: {bl_fgts[:60] if bl_fgts else 'N/A'}...)")

    # 2. Carregar certificado
    print("\n[2] Carregando certificado A1...")
    conn_local = psycopg2.connect(**LOCAL_DB_CONFIG)
    cur_local = conn_local.cursor()
    cur_local.execute("""
        SELECT cnpj, arquivo_path, senha_encrypted
        FROM certificados_a1
        WHERE ativo = TRUE
        LIMIT 1
    """)
    cert_row = cur_local.fetchone()
    cur_local.close()
    conn_local.close()

    if not cert_row:
        print("ERRO: Nenhum certificado ativo encontrado!")
        return

    cert_cnpj, cert_path, senha_enc = cert_row
    senha = CertificateManager.decrypt_password(senha_enc)
    pfx_data = open(cert_path, "rb").read()
    print(f"  Certificado: {cert_path}")
    print(f"  CNPJ cert: {cert_cnpj}")

    empregador = {"tpInsc": 1, "nrInsc": CNPJ}

    # 3. Gerar XMLs
    print("\n[3] Gerando XMLs S-1010 (alteração)...")
    xmls_raw = []
    for i, rubrica in enumerate(rubricas):
        xml_bytes = S1010XMLGenerator.gerar_alteracao(empregador, rubrica, seq=i + 1, tp_amb=TP_AMB)
        xmls_raw.append(xml_bytes)
        print(f"  XML {i+1} gerado: {len(xml_bytes)} bytes")
        # Salvar pra inspeção
        fname = f"_s1010_rubr_{rubrica['codRubr']}_hom.xml"
        with open(fname, "wb") as f:
            f.write(xml_bytes)
        print(f"  Salvo em: {fname}")

    # 4. Assinar XMLs
    print("\n[4] Assinando XMLs...")
    xmls_signed = []
    for i, xml_bytes in enumerate(xmls_raw):
        signed = S1010XMLSigner.assinar(xml_bytes, pfx_data, senha)
        xmls_signed.append(signed)
        print(f"  XML {i+1} assinado: {len(signed)} bytes")

    # 5. Montar SOAP e Enviar
    print("\n[5] Montando envelope SOAP e enviando...")
    soap = SOAPEnvelopeBuilder.montar_envio(
        xmls_signed, empregador, empregador, grupo=1
    )
    url = SOAPEnvelopeBuilder.url_envio(producao=(TP_AMB == "1"))
    print(f"  URL: {url}")
    print(f"  Envelope SOAP: {len(soap)} bytes")

    resultado = ESocialClient.enviar_lote(soap, pfx_data, senha, url=url)
    print(f"\n  Resultado envio:")
    print(json.dumps(resultado, indent=2, ensure_ascii=False))

    if not resultado.get("sucesso"):
        print("\n  *** ERRO NO ENVIO ***")
        return

    protocolo = resultado.get("protocolo")
    print(f"\n  Protocolo: {protocolo}")

    # 6. Consultar resultado
    print("\n[6] Aguardando processamento (10s)...")
    time.sleep(10)

    url_consulta = SOAPEnvelopeBuilder.url_consulta(producao=(TP_AMB == "1"))
    consulta = ESocialClient.consultar_lote(protocolo, pfx_data, senha, url=url_consulta)
    print(f"\n  Resultado consulta:")
    print(json.dumps(consulta, indent=2, ensure_ascii=False))

    # 7. Verificar eventos individuais
    if consulta.get("eventos"):
        for ev in consulta["eventos"]:
            cod = ev.get("codigo", "?")
            desc = ev.get("descricao", "?")
            recibo = ev.get("nrRecibo", "")
            print(f"\n  Evento: cod={cod} desc={desc} recibo={recibo}")
            if cod == "201":
                print("  ✓ SUCESSO")
            else:
                print(f"  ✗ FALHA: {desc}")


if __name__ == "__main__":
    main()
