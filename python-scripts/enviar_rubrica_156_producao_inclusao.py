"""
Script de envio S-1010 INCLUSÃO para rubrica 156 (DIF. FERIAS) em PRODUÇÃO
Alteração falhou com erro 105 (rubrica não existe para iniValid=2026-03).
Tentando inclusão para o novo período, com os valores corretos.
tpAmb=1 (Produção), URLs de produção (webservices.envio.esocial.gov.br)
"""

import sys, os, json, time
from datetime import datetime

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

RECIBOS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "recibos_s1010")


def salvar_recibo(nome: str, conteudo: str):
    os.makedirs(RECIBOS_DIR, exist_ok=True)
    filepath = os.path.join(RECIBOS_DIR, nome)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(conteudo)
    print(f"  [RECIBO] Salvo: {filepath}")


def main():
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")

    print("=" * 70)
    print("ENVIO S-1010 INCLUSÃO — RUBRICA 156 (DIF. FERIAS)")
    print("Ambiente: *** PRODUÇÃO *** (tpAmb=1)")
    print("Modo: INCLUSÃO (novo período 2026-03 com valores corrigidos)")
    print("URL: webservices.envio.esocial.gov.br")
    print("=" * 70)

    # 1. Carregar certificado
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    cur.execute("SELECT arquivo_path, senha_encrypted, cnpj FROM certificados_a1 WHERE ativo = TRUE LIMIT 1")
    row = cur.fetchone()
    conn.close()

    if not row:
        print("ERRO: Nenhum certificado ativo encontrado!")
        return

    senha = CertificateManager.decrypt_password(row[1])
    with open(row[0], 'rb') as f:
        pfx_data = f.read()
    cnpj = row[2]
    print(f"[1] Certificado carregado (CNPJ: {cnpj})")

    empregador = {"tpInsc": 1, "nrInsc": cnpj}
    transmissor = {"tpInsc": 1, "nrInsc": cnpj}

    # 2. Gerar XML INCLUSÃO com tpAmb=1 (PRODUÇÃO)
    xml_bytes = S1010XMLGenerator.gerar_inclusao(empregador, RUBRICA_156, tp_amb="1")
    print(f"[2] XML inclusão gerado: {len(xml_bytes)} bytes (tpAmb=1 PRODUÇÃO)")

    from lxml import etree
    root = etree.fromstring(xml_bytes)
    xml_pretty = etree.tostring(root, pretty_print=True, encoding="unicode")
    print(xml_pretty)

    salvar_recibo(f"rubrica_156_producao_inclusao_xml_gerado_{ts}.xml", xml_pretty)

    # 3. Assinar
    xml_assinado = S1010XMLSigner.assinar(xml_bytes, pfx_data, senha)
    print(f"[3] XML assinado: {len(xml_assinado)} bytes")

    xml_assinado_str = xml_assinado.decode("utf-8") if isinstance(xml_assinado, bytes) else xml_assinado
    salvar_recibo(f"rubrica_156_producao_inclusao_xml_assinado_{ts}.xml", xml_assinado_str)

    # 4. Montar SOAP
    soap = SOAPEnvelopeBuilder.montar_envio([xml_assinado], empregador, transmissor, grupo="1")
    print(f"[4] Envelope SOAP: {len(soap)} chars")

    salvar_recibo(f"rubrica_156_producao_inclusao_soap_enviado_{ts}.xml", soap)

    # 5. Enviar a PRODUÇÃO
    url_prod = SOAPEnvelopeBuilder.url_envio(producao=True)
    print(f"[5] Enviando ao eSocial PRODUÇÃO ({url_prod})...")
    resultado = ESocialClient.enviar_lote(soap, pfx_data, senha, url=url_prod)

    print(f"\n  Sucesso:    {resultado.get('sucesso')}")
    print(f"  Codigo:     {resultado.get('codigo_resposta')}")
    print(f"  Descrição:  {resultado.get('descricao')}")
    print(f"  Protocolo:  {resultado.get('protocolo')}")
    if resultado.get("erro"):
        print(f"  ERRO:       {resultado['erro']}")

    salvar_recibo(f"rubrica_156_producao_inclusao_resultado_envio_{ts}.json",
                  json.dumps(resultado, indent=2, ensure_ascii=False))

    # 6. Consultar resultado
    protocolo = resultado.get("protocolo")
    if protocolo:
        print(f"\n[6] Aguardando 10s para consultar resultado...")
        time.sleep(10)

        url_consulta_prod = SOAPEnvelopeBuilder.url_consulta(producao=True)
        consulta = ESocialClient.consultar_lote(protocolo, pfx_data, senha, url=url_consulta_prod)
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

        salvar_recibo(f"rubrica_156_producao_inclusao_resultado_consulta_{ts}.json",
                      json.dumps(consulta, indent=2, ensure_ascii=False))

        # 7. Salvar no banco
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
            print(f"\n[7] Registrado no banco: esocial_envios.id = {envio_id}")
        finally:
            conn.close()

    print("\n" + "=" * 70)
    print("ENVIO PRODUÇÃO (INCLUSÃO) CONCLUÍDO")
    print(f"Recibos salvos em: {RECIBOS_DIR}")
    print("=" * 70)


if __name__ == "__main__":
    main()
