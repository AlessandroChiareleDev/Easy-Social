"""
Test Steps 2-5: S-1298 → S-1200 → S-1210 → S-1299 em HOMOLOGAÇÃO
Rubrica 566 já existe em homologação (inclusão feita em test_quick_s1010.py)

FLUXO:
  1. [DONE] S-1010 inclusão rubrica 566 → recibo 1.2.0000000000306683496
  2. S-1298 reabertura → pode falhar se período não está fechado (OK, pulamos)
  3. S-1200 inclusão com rubrica 566 → precisa do recibo para retificação depois
  4. S-1210 inclusão referenciando ideDmDev do S-1200
  5. S-1299 fechamento
"""
import sys, os, time, json
sys.path.insert(0, os.path.dirname(__file__))

import psycopg2
from db_config import LOCAL_DB_CONFIG
from esocial.certificate_manager import CertificateManager
from esocial.xml_s1200 import S1200XMLGenerator
from esocial.xml_s1210 import S1210XMLGenerator
from esocial.xml_s1298 import S1298XMLGenerator
from esocial.xml_s1299 import S1299XMLGenerator
from esocial.xml_signer import S1010XMLSigner
from esocial.soap_builder import SOAPEnvelopeBuilder
from esocial.esocial_client import ESocialClient

TP_AMB = "2"  # HOMOLOGAÇÃO
CNPJ_RAIZ = "05969071"
CNPJ_FULL = "05969071000110"
PER_APUR = "2026-02"
CPF_TESTE = "06184644173"

EMPREGADOR = {"tpInsc": 1, "nrInsc": CNPJ_RAIZ}
TRANSMISSOR = {"tpInsc": 1, "nrInsc": CNPJ_FULL}


def load_cert():
    conn = psycopg2.connect(**LOCAL_DB_CONFIG)
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT arquivo_path, senha_encrypted FROM certificados_a1 WHERE ativo = TRUE LIMIT 1")
            row = cur.fetchone()
            senha = CertificateManager.decrypt_password(row[1])
            with open(row[0], "rb") as f:
                pfx_data = f.read()
            return pfx_data, senha
    finally:
        conn.close()


def enviar(xml_bytes, pfx_data, senha, grupo, label):
    print(f"\n{'='*60}")
    print(f"  {label}")
    print(f"{'='*60}")

    # Show XML
    print(f"  XML ({len(xml_bytes)} bytes):")
    print(f"  {xml_bytes.decode()[:300]}...")

    # Sign
    xml_assinado = S1010XMLSigner.assinar(xml_bytes, pfx_data, senha)
    print(f"  Assinado: {len(xml_assinado)} bytes")

    # SOAP
    soap = SOAPEnvelopeBuilder.montar_envio([xml_assinado], EMPREGADOR, TRANSMISSOR, grupo=grupo)

    # Send
    url_envio = SOAPEnvelopeBuilder.url_envio(producao=False)
    print(f"  Enviando para {url_envio}...")
    resultado = ESocialClient.enviar_lote(soap, pfx_data, senha, url=url_envio)
    print(f"  Envio: sucesso={resultado.get('sucesso')} cod={resultado.get('codigo_resposta')} prot={resultado.get('protocolo')}")

    protocolo = resultado.get("protocolo")
    if not protocolo:
        print(f"  ERRO: sem protocolo. desc={resultado.get('descricao')}")
        return resultado

    # Poll
    url_consulta = SOAPEnvelopeBuilder.url_consulta(producao=False)
    for i in range(5):
        time.sleep(8)
        print(f"  Consulta {i+1}/5...", end=" ")
        consulta = ESocialClient.consultar_lote(protocolo, pfx_data, senha, url=url_consulta)
        cod = consulta.get("codigo_resposta")
        print(f"cod={cod}")

        if consulta.get("eventos"):
            for ev in consulta["eventos"]:
                status = "OK" if ev.get("nr_recibo") else "FALHA"
                print(f"    [{status}] cod={ev.get('codigo_resposta')} recibo={ev.get('nr_recibo')} desc={ev.get('descricao', '')[:100]}")
                for oc in ev.get("ocorrencias", []):
                    print(f"      OC: cod={oc.get('codigo')} desc={oc.get('descricao', '')[:200]}")
            return {"sucesso": any(e.get("nr_recibo") for e in consulta["eventos"]),
                    "eventos": consulta["eventos"],
                    "protocolo": protocolo}

        if cod == "101":
            continue
        else:
            print(f"    desc={consulta.get('descricao')}")
            return {"sucesso": False, "consulta": consulta}

    return {"sucesso": False, "erro": "timeout"}


def main():
    pfx_data, senha = load_cert()
    print(f"Cert OK. tpAmb={TP_AMB} per_apur={PER_APUR} cpf={CPF_TESTE}")

    results = {}

    # ── STEP 2: S-1298 Reabertura ──
    print("\n\n▸ STEP 2: S-1298 Reabertura")
    xml_1298 = S1298XMLGenerator.gerar(EMPREGADOR, PER_APUR, ind_apuracao="1", tp_amb=TP_AMB)
    results["s1298"] = enviar(xml_1298, pfx_data, senha, grupo="3", label="S-1298 Reabertura")

    # Continua mesmo se S-1298 falhar (período pode não estar fechado em homologação)

    # ── STEP 3: S-1200 Inclusão ──
    print("\n\n▸ STEP 3: S-1200 Inclusão de Remuneração")
    dm_devs = [
        {
            "ideDmDev": "TESTE001",
            "codCateg": "101",
            "infoPerApur": {
                "ideEstabLot": [
                    {
                        "tpInsc": 1,
                        "nrInsc": CNPJ_FULL,
                        "codLotacao": "01",
                        "remunPerApur": [
                            {
                                "matricula": "009-001-051736",
                                "itensRemun": [
                                    {"codRubr": "566", "ideTabRubr": "1", "vrRubr": "160.00"},
                                ],
                            }
                        ],
                    }
                ]
            },
        }
    ]
    xml_1200 = S1200XMLGenerator.gerar(
        empregador=EMPREGADOR,
        trabalhador={"cpfTrab": CPF_TESTE},
        dm_devs=dm_devs,
        per_apur=PER_APUR,
        ind_retif="1",  # Inclusão (primeira vez em homologação)
        ind_apuracao="1",
        tp_amb=TP_AMB,
    )
    results["s1200"] = enviar(xml_1200, pfx_data, senha, grupo="3", label="S-1200 Inclusão")

    # ── STEP 4: S-1210 Inclusão ──
    print("\n\n▸ STEP 4: S-1210 Inclusão de Pagamento")
    info_pgtos = [
        {
            "dtPgto": "2026-02-06",
            "tpPgto": "1",
            "perRef": PER_APUR,
            "ideDmDev": "TESTE001",
            "vrLiq": "1840.00",
        }
    ]
    xml_1210 = S1210XMLGenerator.gerar(
        empregador=EMPREGADOR,
        beneficiario={"cpfBenef": CPF_TESTE},
        info_pgtos=info_pgtos,
        per_apur=PER_APUR,
        ind_retif="1",
        tp_amb=TP_AMB,
    )
    results["s1210"] = enviar(xml_1210, pfx_data, senha, grupo="3", label="S-1210 Inclusão")

    # ── STEP 5: S-1299 Fechamento ──
    print("\n\n▸ STEP 5: S-1299 Fechamento")
    responsavel = {
        "nmResp": "ALEXANDRE TESTE",
        "cpfResp": "00000000000",
        "telefone": "4199999999",
        "email": "teste@teste.com",
    }
    xml_1299 = S1299XMLGenerator.gerar(
        empregador=EMPREGADOR,
        per_apur=PER_APUR,
        responsavel=responsavel,
        ind_apuracao="1",
        tp_amb=TP_AMB,
    )
    results["s1299"] = enviar(xml_1299, pfx_data, senha, grupo="3", label="S-1299 Fechamento")

    # ── RESUMO ──
    print("\n\n" + "=" * 60)
    print("  RESUMO")
    print("=" * 60)
    for step, result in results.items():
        if result is None:
            st = "SKIP"
        elif result.get("sucesso"):
            recibos = [e.get("nr_recibo") for e in result.get("eventos", []) if e.get("nr_recibo")]
            st = f"OK recibo={recibos[0] if recibos else 'N/A'}"
        else:
            st = f"FALHA"
        print(f"  {step}: {st}")


if __name__ == "__main__":
    main()
