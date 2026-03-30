"""
Script de envio S-1010 INCLUSÃO para rubrica 156 (DIF. FERIAS) em HOMOLOGAÇÃO
A rubrica não existe em homologação, então primeiro precisamos criar via inclusão.
Depois de confirmar que funciona, faremos alteração em produção.
"""

import sys, os, json, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import psycopg2
from esocial.certificate_manager import CertificateManager
from esocial.xml_generator import S1010XMLGenerator
from esocial.xml_signer import S1010XMLSigner
from esocial.soap_builder import SOAPEnvelopeBuilder
from esocial.esocial_client import ESocialClient

DB_CONFIG = {
    "host": "localhost", "port": 5432, "database": "easy_social_db",
    "user": "easy_social_user", "password": "sua_senha_segura",
}

RUBRICA_156 = {
    "codRubr": "156",
    "ideTabRubr": "1",
    "iniValid": "2026-03",
    "dscRubr": "DIF. FERIAS",
    "natRubr": 1016,
    "tpRubr": 1,
    "codIncCP": 11,
    "codIncIRRF": 13,
    "codIncFGTS": 11,
    "codIncPisPasep": 0,
}


def main():
    print("=" * 70)
    print("ENVIO S-1010 INCLUSÃO — RUBRICA 156 (DIF. FERIAS)")
    print("Ambiente: HOMOLOGAÇÃO (tpAmb=2)")
    print("Modo: INCLUSÃO (rubrica não existe em homologação)")
    print("=" * 70)

    # 1. Carregar certificado
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    cur.execute("SELECT arquivo_path, senha_encrypted, cnpj FROM certificados_a1 WHERE ativo = TRUE LIMIT 1")
    row = cur.fetchone()
    conn.close()

    senha = CertificateManager.decrypt_password(row[1])
    with open(row[0], 'rb') as f:
        pfx_data = f.read()
    cnpj = row[2]
    print(f"[1] Certificado carregado (CNPJ: {cnpj})")

    empregador = {"tpInsc": 1, "nrInsc": cnpj}
    transmissor = {"tpInsc": 1, "nrInsc": cnpj}

    # 2. Gerar XML INCLUSÃO
    xml_bytes = S1010XMLGenerator.gerar_inclusao(empregador, RUBRICA_156)
    print(f"[2] XML inclusão gerado: {len(xml_bytes)} bytes")

    from lxml import etree
    root = etree.fromstring(xml_bytes)
    print(etree.tostring(root, pretty_print=True, encoding="unicode"))

    # 3. Assinar
    xml_assinado = S1010XMLSigner.assinar(xml_bytes, pfx_data, senha)
    print(f"[3] XML assinado: {len(xml_assinado)} bytes")

    # 4. Montar SOAP
    soap = SOAPEnvelopeBuilder.montar_envio([xml_assinado], empregador, transmissor, grupo=1)
    print(f"[4] Envelope SOAP: {len(soap)} chars")

    # 5. Enviar
    print("[5] Enviando ao eSocial (homologação)...")
    resultado = ESocialClient.enviar_lote(soap, pfx_data, senha)

    print(f"\n  Sucesso:    {resultado.get('sucesso')}")
    print(f"  Codigo:     {resultado.get('codigo_resposta')}")
    print(f"  Descrição:  {resultado.get('descricao')}")
    print(f"  Protocolo:  {resultado.get('protocolo')}")
    if resultado.get("erro"):
        print(f"  ERRO:       {resultado['erro']}")

    # 6. Consultar resultado
    protocolo = resultado.get("protocolo")
    if protocolo:
        print(f"\n[6] Aguardando 8s para consultar resultado...")
        time.sleep(8)

        consulta = ESocialClient.consultar_lote(protocolo, pfx_data, senha)
        print(f"  Consulta - Sucesso: {consulta.get('sucesso')}")
        print(f"  Consulta - Codigo:  {consulta.get('codigo_resposta')}")
        print(f"  Consulta - Desc:    {consulta.get('descricao')}")

        if consulta.get('eventos'):
            for evt in consulta['eventos']:
                print(f"\n  Evento {evt.get('id', '?')}:")
                print(f"    Codigo: {evt.get('codigo_resposta')}")
                print(f"    Desc:   {evt.get('descricao')}")
                print(f"    Recibo: {evt.get('nr_recibo')}")
                if evt.get('ocorrencias'):
                    for oc in evt['ocorrencias']:
                        print(f"    Ocorr:  [{oc.get('tipo')}] {oc.get('codigo')}: {oc.get('descricao')}")
        else:
            print("  Nenhum evento retornado (pode estar em processamento)")
            print(json.dumps(consulta, indent=2, ensure_ascii=False))

        # Salvar
        conn = psycopg2.connect(**DB_CONFIG)
        try:
            with conn.cursor() as cur2:
                cur2.execute("""
                    INSERT INTO esocial_envios
                    (tipo_evento, modo, status, protocolo_envio,
                     codigo_resposta, descricao_resposta, total_eventos,
                     rubrica_ids, ocorrencias)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                """, (
                    "S-1010", "inclusao",
                    "enviado" if resultado.get("sucesso") else "erro",
                    protocolo,
                    resultado.get("codigo_resposta"),
                    resultado.get("descricao"),
                    1, json.dumps(["156"]),
                    json.dumps(resultado.get("ocorrencias", [])),
                ))
                envio_id = cur2.fetchone()[0]
                conn.commit()
                print(f"\n  Envio salvo no banco com ID: {envio_id}")
        finally:
            conn.close()


if __name__ == "__main__":
    main()
