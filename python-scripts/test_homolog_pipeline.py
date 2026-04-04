"""
Script de teste em HOMOLOGAÇÃO — testa cada etapa do pipeline individualmente.
Envia XML real para o eSocial ambiente 2 (homologação) e loga tudo.

SEGURANÇA: tpAmb=2 SEMPRE. Nenhum risco para produção.
"""

import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(__file__))

import psycopg2
from db_config import DB_CONFIG, LOCAL_DB_CONFIG
from esocial.certificate_manager import CertificateManager
from esocial.xml_generator import S1010XMLGenerator
from esocial.xml_s1200 import S1200XMLGenerator
from esocial.xml_s1210 import S1210XMLGenerator
from esocial.xml_s1298 import S1298XMLGenerator
from esocial.xml_s1299 import S1299XMLGenerator
from esocial.xml_signer import S1010XMLSigner
from esocial.soap_builder import SOAPEnvelopeBuilder
from esocial.esocial_client import ESocialClient

# ══════════════════════════════════════════════════════════════════
# CONFIG — HOMOLOGAÇÃO ONLY
# ══════════════════════════════════════════════════════════════════

TP_AMB = "2"  # HOMOLOGAÇÃO — NUNCA MUDAR AQUI
CNPJ_RAIZ = "05969071"
CNPJ_FULL = "05969071000110"
PER_APUR = "2026-02"
CPF_TESTE = "06184644173"

EMPREGADOR = {"tpInsc": 1, "nrInsc": CNPJ_RAIZ}
TRANSMISSOR = {"tpInsc": 1, "nrInsc": CNPJ_FULL}

POLL_RETRIES = 5
POLL_DELAY = 8

# ── Helpers ──────────────────────────────────────────────────────


def load_certificate():
    """Carrega certificado APPA ativo."""
    conn = psycopg2.connect(**LOCAL_DB_CONFIG)
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, cnpj, arquivo_path, senha_encrypted "
                "FROM certificados_a1 WHERE ativo = TRUE LIMIT 1"
            )
            row = cur.fetchone()
            if not row:
                raise RuntimeError("Nenhum certificado ativo!")
            senha = CertificateManager.decrypt_password(row[3])
            with open(row[2], "rb") as f:
                pfx_data = f.read()
            print(f"✓ Certificado carregado: id={row[0]} cnpj={row[1]}")
            return pfx_data, senha
    finally:
        conn.close()


def enviar_e_consultar(xml_bytes, pfx_data, senha, grupo, label):
    """Assina → SOAP → Envia → Polling. Retorna resultado completo."""
    print(f"\n{'='*60}")
    print(f"  TESTE: {label}")
    print(f"{'='*60}")

    # 1. Assinar
    try:
        xml_assinado = S1010XMLSigner.assinar(xml_bytes, pfx_data, senha)
        print(f"  ✓ XML assinado ({len(xml_assinado)} bytes)")
    except Exception as e:
        print(f"  ✗ ERRO ao assinar: {e}")
        return {"sucesso": False, "erro": f"Assinatura: {e}"}

    # 2. SOAP
    try:
        soap = SOAPEnvelopeBuilder.montar_envio(
            [xml_assinado], EMPREGADOR, TRANSMISSOR, grupo=grupo
        )
        print(f"  ✓ SOAP montado ({len(soap)} bytes)")
    except Exception as e:
        print(f"  ✗ ERRO ao montar SOAP: {e}")
        return {"sucesso": False, "erro": f"SOAP: {e}"}

    # 3. Enviar
    url_envio = SOAPEnvelopeBuilder.url_envio(producao=False)
    print(f"  → Enviando para: {url_envio}")
    try:
        resultado = ESocialClient.enviar_lote(soap, pfx_data, senha, url=url_envio)
        print(f"  ← Resposta envio: sucesso={resultado.get('sucesso')}")
        print(f"    protocolo={resultado.get('protocolo')}")
        print(f"    codigo={resultado.get('codigo_resposta')}")
        print(f"    desc={resultado.get('descricao')}")
        if resultado.get("erro"):
            print(f"    erro={resultado.get('erro')}")
    except Exception as e:
        print(f"  ✗ ERRO ao enviar: {e}")
        return {"sucesso": False, "erro": f"Envio: {e}"}

    protocolo = resultado.get("protocolo")
    if not protocolo:
        print(f"  ⚠ Sem protocolo — não será possível consultar")
        return resultado

    # 4. Polling
    url_consulta = SOAPEnvelopeBuilder.url_consulta(producao=False)
    print(f"\n  → Polling de consulta (max {POLL_RETRIES}x, delay {POLL_DELAY}s)")

    for attempt in range(1, POLL_RETRIES + 1):
        time.sleep(POLL_DELAY)
        print(f"    tentativa {attempt}/{POLL_RETRIES}...", end=" ")
        try:
            consulta = ESocialClient.consultar_lote(
                protocolo, pfx_data, senha, url=url_consulta
            )
            cod = consulta.get("codigo_resposta")
            print(f"cod={cod} desc={consulta.get('descricao', '')[:60]}")

            if consulta.get("sucesso") and consulta.get("eventos"):
                for ev in consulta["eventos"]:
                    print(f"    → Evento: cod={ev.get('codigo_resposta')} "
                          f"recibo={ev.get('nr_recibo')} "
                          f"desc={ev.get('descricao', '')[:60]}")
                return {
                    "sucesso": True,
                    "protocolo": protocolo,
                    "eventos": consulta["eventos"],
                }
            elif cod == "101":
                print("    (em processamento, aguardando...)")
                continue
            else:
                # Got response but not success
                print(f"    consulta completa: {json.dumps(consulta, indent=2, ensure_ascii=False)[:500]}")
                return {
                    "sucesso": False,
                    "protocolo": protocolo,
                    "consulta": consulta,
                }
        except Exception as e:
            print(f"ERRO: {e}")

    print(f"  ⚠ Timeout no polling após {POLL_RETRIES} tentativas")
    return {"sucesso": False, "protocolo": protocolo, "erro": "timeout polling"}


# ══════════════════════════════════════════════════════════════════
# TESTES INDIVIDUAIS
# ══════════════════════════════════════════════════════════════════


def test_s1010(pfx_data, senha):
    """Testa S-1010 alteração de rubrica."""
    # Buscar uma rubrica com divergência no cruzamento_eb
    conn = psycopg2.connect(**DB_CONFIG)
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT cod_rubrica, tab_rubr, descricao_eb, natureza_esocial,
                       inss_correto, irrf_correto, fgts_correto, ini_valid_esocial
                FROM cruzamento_eb
                WHERE divergencia = TRUE AND envio_status != 'feito'
                LIMIT 1
            """)
            row = cur.fetchone()
            if not row:
                print("  ⚠ Nenhuma rubrica com divergência encontrada")
                return None
    finally:
        conn.close()

    nat_rubr = (row[3] or "").split(" - ")[0].strip() if row[3] else ""
    rubrica = {
        "codRubr": row[0],
        "ideTabRubr": row[1] or "1",
        "iniValid": row[7] or "2025-01",
        "dscRubr": (row[2] or "RUBRICA")[:100],
        "natRubr": nat_rubr,
        "tpRubr": "1",
        "codIncCP": row[4] or "00",
        "codIncIRRF": row[5] or "00",
        "codIncFGTS": row[6] or "00",
    }
    print(f"  Rubrica: {rubrica['codRubr']} — {rubrica['dscRubr'][:50]}")
    print(f"  codIncIRRF={rubrica['codIncIRRF']} natRubr={rubrica['natRubr']}")

    xml_bytes = S1010XMLGenerator.gerar_alteracao(
        EMPREGADOR, rubrica, seq=1, tp_amb=TP_AMB
    )
    return enviar_e_consultar(xml_bytes, pfx_data, senha, grupo="1", label="S-1010 Alteração")


def test_s1298(pfx_data, senha):
    """Testa S-1298 reabertura de período."""
    xml_bytes = S1298XMLGenerator.gerar(
        EMPREGADOR, PER_APUR, ind_apuracao="1", tp_amb=TP_AMB
    )
    return enviar_e_consultar(xml_bytes, pfx_data, senha, grupo="3", label="S-1298 Reabertura")


def test_s1200(pfx_data, senha):
    """Testa S-1200 inclusão com dm_devs mínimo."""
    trabalhador = {"cpfTrab": CPF_TESTE}

    # Estrutura mínima válida de dm_devs para teste
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
                                    {
                                        "codRubr": "1000",
                                        "ideTabRubr": "1",
                                        "vrRubr": "2000.00",
                                    },
                                    {
                                        "codRubr": "566",
                                        "ideTabRubr": "1",
                                        "vrRubr": "160.00",
                                    },
                                ],
                            }
                        ],
                    }
                ]
            },
        }
    ]

    xml_bytes = S1200XMLGenerator.gerar(
        empregador=EMPREGADOR,
        trabalhador=trabalhador,
        dm_devs=dm_devs,
        per_apur=PER_APUR,
        ind_retif="1",  # Inclusão original em homologação
        ind_apuracao="1",
        tp_amb=TP_AMB,
    )
    return enviar_e_consultar(xml_bytes, pfx_data, senha, grupo="1", label="S-1200 Inclusão")


def test_s1210(pfx_data, senha, ide_dm_dev="TESTE001"):
    """Testa S-1210 inclusão com info_pgtos mínimo."""
    beneficiario = {"cpfBenef": CPF_TESTE}

    info_pgtos = [
        {
            "dtPgto": "2026-02-06",
            "tpPgto": "1",
            "perRef": PER_APUR,
            "ideDmDev": ide_dm_dev,
            "vrLiq": "1840.00",
        }
    ]

    xml_bytes = S1210XMLGenerator.gerar(
        empregador=EMPREGADOR,
        beneficiario=beneficiario,
        info_pgtos=info_pgtos,
        per_apur=PER_APUR,
        ind_retif="1",
        tp_amb=TP_AMB,
    )
    return enviar_e_consultar(xml_bytes, pfx_data, senha, grupo="1", label="S-1210 Inclusão")


def test_s1299(pfx_data, senha):
    """Testa S-1299 fechamento."""
    responsavel = {
        "nmResp": "ALEXANDRE TESTE",
        "cpfResp": "00000000000",
        "telefone": "4199999999",
        "email": "teste@teste.com",
    }

    xml_bytes = S1299XMLGenerator.gerar(
        empregador=EMPREGADOR,
        per_apur=PER_APUR,
        responsavel=responsavel,
        ind_apuracao="1",
        tp_amb=TP_AMB,
    )
    return enviar_e_consultar(xml_bytes, pfx_data, senha, grupo="3", label="S-1299 Fechamento")


# ══════════════════════════════════════════════════════════════════
# MAIN — Executa testes em sequência
# ══════════════════════════════════════════════════════════════════


def main():
    print("╔══════════════════════════════════════════════════════════╗")
    print("║  TESTE PIPELINE HOMOLOGAÇÃO — tpAmb=2                  ║")
    print("║  CNPJ: 05969071 (APPA)                                 ║")
    print("║  CPF:  06184644173                                     ║")
    print("║  Período: 2026-02                                      ║")
    print("╚══════════════════════════════════════════════════════════╝")

    pfx_data, senha = load_certificate()

    results = {}

    # 1. S-1010 — Corrigir rubrica
    print("\n\n▸ STEP 1: S-1010 (Alteração de rubrica)")
    results["s1010"] = test_s1010(pfx_data, senha)

    # 2. S-1298 — Reabrir período
    print("\n\n▸ STEP 2: S-1298 (Reabertura)")
    results["s1298"] = test_s1298(pfx_data, senha)

    # 3. S-1200 — Enviar remuneração (inclusão em homologação)
    print("\n\n▸ STEP 3: S-1200 (Inclusão remuneração)")
    results["s1200"] = test_s1200(pfx_data, senha)

    # 4. S-1210 — Enviar pagamento (inclusão em homologação)
    print("\n\n▸ STEP 4: S-1210 (Inclusão pagamento)")
    results["s1210"] = test_s1210(pfx_data, senha)

    # 5. S-1299 — Fechar período
    print("\n\n▸ STEP 5: S-1299 (Fechamento)")
    results["s1299"] = test_s1299(pfx_data, senha)

    # ── Resumo ──
    print("\n\n" + "=" * 60)
    print("  RESUMO FINAL")
    print("=" * 60)
    for step, result in results.items():
        if result is None:
            status = "⚠ SKIP"
        elif result.get("sucesso"):
            status = "✓ OK"
        else:
            status = f"✗ FALHA: {result.get('erro', '')[:60]}"
        print(f"  {step}: {status}")


if __name__ == "__main__":
    main()
