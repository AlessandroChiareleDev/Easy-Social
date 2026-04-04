"""
Pipeline Completo: Retificação S-1200/S-1210 para CPF 08132588983
Período: 2024-12, PRODUÇÃO (tpAmb=1)

Passos:
  1. S-1298 — Reabertura do período 2024-12
  2. S-1200 — Retificação (indRetif=2, mesmos dados)
  3. S-1210 — Retificação (indRetif=2, mesmos dados)
  4. S-1299 — Fechamento do período 2024-12

Objetivo: Forçar recálculo do S-5002 usando incidências corrigidas
          das rubricas 566 (codIncIRRF 11→41) e 596 (codIncIRRF 12→42).
"""
import sys, os, json, time
from datetime import datetime
sys.path.insert(0, os.path.dirname(__file__))

from db_config import DB_CONFIG, LOCAL_DB_CONFIG
from esocial.certificate_manager import CertificateManager
from esocial.xml_s1298 import S1298XMLGenerator
from esocial.xml_s1200 import S1200XMLGenerator
from esocial.xml_s1210 import S1210XMLGenerator
from esocial.xml_s1299 import S1299XMLGenerator
from esocial.xml_signer import S1010XMLSigner as XMLSigner  # Genérico
from esocial.soap_builder import SOAPEnvelopeBuilder
from esocial.esocial_client import ESocialClient
import psycopg2

# ============================================================================
# CONFIGURAÇÃO
# ============================================================================
TP_AMB = "1"  # PRODUÇÃO
CNPJ_COMPLETO = "05969071000110"
CNPJ_RAIZ = "05969071"
PER_APUR = "2024-12"
CPF = "08132588983"

# nrRecibos vigentes (do prontuário)
S1200_NR_RECIBO = "1.1.0000000030324738244"
S1210_NR_RECIBO = "1.1.0000000030328525269"

EMPREGADOR = {"tpInsc": 1, "nrInsc": CNPJ_COMPLETO}

# ============================================================================
# PAYLOADS (extraídos do XML S-1200 vigente ID...10150500001)
# ============================================================================
DM_DEVS = [
    {
        "ideDmDev": "20241129.1.01512563",
        "codCateg": "101",
        "infoPerApur": {
            "ideEstabLot": [{
                "tpInsc": "1",
                "nrInsc": CNPJ_COMPLETO,
                "codLotacao": "E00278-001-05A",
                "remunPerApur": [{
                    "matricula": "001-001-056502",
                    "itensRemun": [
                        {"codRubr": "9276", "ideTabRubr": "1", "vrRubr": "231.00", "indApurIR": "0"},
                    ],
                    "infoAgNocivo": {"grauExp": "1"},
                }],
            }],
        },
    },
    {
        "ideDmDev": "20241129.1.01512566",
        "codCateg": "101",
        "infoPerApur": {
            "ideEstabLot": [{
                "tpInsc": "1",
                "nrInsc": CNPJ_COMPLETO,
                "codLotacao": "E00278-001-05A",
                "remunPerApur": [{
                    "matricula": "001-001-056502",
                    "itensRemun": [
                        {"codRubr": "9284", "ideTabRubr": "1", "vrRubr": "667.80", "indApurIR": "0"},
                    ],
                    "infoAgNocivo": {"grauExp": "1"},
                }],
            }],
        },
    },
    {
        "ideDmDev": "10711955",
        "codCateg": "101",
        "infoPerApur": {
            "ideEstabLot": [{
                "tpInsc": "1",
                "nrInsc": CNPJ_COMPLETO,
                "codLotacao": "E00278-001-05A",
                "remunPerApur": [{
                    "matricula": "001-001-056502",
                    "itensRemun": [
                        {"codRubr": "2",   "ideTabRubr": "1",     "qtdRubr": "30.00",  "vrRubr": "2501.20", "indApurIR": "0"},
                        {"codRubr": "10",  "ideTabRubr": "EA001", "vrRubr": "125.06",  "indApurIR": "0"},
                        {"codRubr": "105", "ideTabRubr": "EA001", "qtdRubr": "34.34",  "vrRubr": "585.62",  "indApurIR": "0"},
                        {"codRubr": "160", "ideTabRubr": "EA001", "vrRubr": "140.55",  "indApurIR": "0"},
                        {"codRubr": "273", "ideTabRubr": "1",     "vrRubr": "0.70",    "indApurIR": "0"},
                        {"codRubr": "541", "ideTabRubr": "1",     "vrRubr": "1.20",    "indApurIR": "0"},
                        {"codRubr": "566", "ideTabRubr": "1",     "qtdRubr": "12.00",  "vrRubr": "301.11",  "indApurIR": "0"},
                        {"codRubr": "570", "ideTabRubr": "1",     "qtdRubr": "7.50",   "vrRubr": "39.63",   "indApurIR": "0"},
                        {"codRubr": "672", "ideTabRubr": "1",     "vrRubr": "150.07",  "indApurIR": "0"},
                        {"codRubr": "776", "ideTabRubr": "1",     "vrRubr": "108.12",  "indApurIR": "0"},
                    ],
                    "infoAgNocivo": {"grauExp": "1"},
                }],
            }],
        },
    },
    {
        "ideDmDev": "10711965",
        "codCateg": "101",
        "infoPerApur": {
            "ideEstabLot": [{
                "tpInsc": "1",
                "nrInsc": CNPJ_COMPLETO,
                "codLotacao": "E00278-001-05A",
                "remunPerApur": [{
                    "matricula": "001-001-056502",
                    "itensRemun": [
                        {"codRubr": "273", "ideTabRubr": "1",     "vrRubr": "0.44",   "indApurIR": "0"},
                        {"codRubr": "480", "ideTabRubr": "EA001", "vrRubr": "70.94",  "indApurIR": "0"},
                        {"codRubr": "596", "ideTabRubr": "1",     "qtdRubr": "9.00",  "vrRubr": "6.38",   "indApurIR": "0"},
                    ],
                    "infoAgNocivo": {"grauExp": "1"},
                }],
            }],
        },
    },
]

# ============================================================================
# PAYLOAD S-1210 (extraído do XML vigente ID...13304200015)
# ============================================================================
INFO_PGTOS = [
    {
        "dtPgto": "2024-12-06",
        "tpPgto": "1",
        "perRef": "2024-11",
        "ideDmDev": "10711884",
        "vrLiq": "2883",
    },
    {
        "dtPgto": "2024-12-20",
        "tpPgto": "1",
        "perRef": "2024",
        "ideDmDev": "10711933",
        "vrLiq": "1273",
    },
]

INFO_IR_COMPLEM = {
    "infoIRCR": [
        {
            "tpCR": "056107",
            "dedDepen": [
                {"tpRend": "12", "cpfDep": "14020816930", "vlrDedDep": "189.59"},
                {"tpRend": "11", "cpfDep": "14020816930", "vlrDedDep": "189.59"},
            ],
        },
    ],
}


# ============================================================================
# FUNÇÕES AUXILIARES
# ============================================================================
def carregar_certificado():
    """Carrega certificado A1 ativo do banco local."""
    conn = psycopg2.connect(**LOCAL_DB_CONFIG)
    cur = conn.cursor()
    cur.execute("""
        SELECT cnpj, arquivo_path, senha_encrypted
        FROM certificados_a1
        WHERE ativo = TRUE
        LIMIT 1
    """)
    row = cur.fetchone()
    cur.close()
    conn.close()
    if not row:
        raise RuntimeError("Nenhum certificado ativo!")
    _, cert_path, senha_enc = row
    senha = CertificateManager.decrypt_password(senha_enc)
    pfx_data = open(cert_path, "rb").read()
    return pfx_data, senha


def enviar_e_consultar(xml_bytes, pfx_data, senha, grupo, nome_passo):
    """Assina, monta SOAP, envia e consulta resultado."""
    print(f"\n  Assinando XML {nome_passo}...")
    signed = XMLSigner.assinar(xml_bytes, pfx_data, senha)
    print(f"    Assinado: {len(signed)} bytes")

    print(f"  Montando SOAP (grupo={grupo})...")
    soap = SOAPEnvelopeBuilder.montar_envio(
        [signed], EMPREGADOR, EMPREGADOR, grupo=grupo
    )
    url = SOAPEnvelopeBuilder.url_envio(producao=(TP_AMB == "1"))
    print(f"    URL: {url}")

    print(f"  Enviando {nome_passo}...")
    resultado = ESocialClient.enviar_lote(soap, pfx_data, senha, url=url)
    print(f"    Resultado: {json.dumps(resultado, indent=2, ensure_ascii=False)}")

    if not resultado.get("sucesso"):
        print(f"  *** ERRO no envio de {nome_passo} ***")
        return None

    protocolo = resultado.get("protocolo")
    print(f"    Protocolo: {protocolo}")

    # Consultar com retry
    url_consulta = SOAPEnvelopeBuilder.url_consulta(producao=(TP_AMB == "1"))
    for tentativa in range(5):
        wait = 15 if tentativa == 0 else 10
        print(f"  Aguardando {wait}s (tentativa {tentativa + 1}/5)...")
        time.sleep(wait)

        consulta = ESocialClient.consultar_lote(protocolo, pfx_data, senha, url=url_consulta)
        codigo = consulta.get("codigo_resposta", "")
        print(f"    Consulta: codigo={codigo}")

        if codigo in ("201", "202"):
            print(f"    ✓ {nome_passo} PROCESSADO com sucesso!")
            if consulta.get("eventos"):
                for ev in consulta["eventos"]:
                    print(f"      Evento: cod={ev.get('codigo')} recibo={ev.get('nrRecibo', '-')}")
            return consulta
        elif codigo == "101":
            print(f"    Em processamento...")
            continue
        else:
            print(f"    Resposta: {json.dumps(consulta, indent=2, ensure_ascii=False)}")
            if codigo not in ("101", ""):
                print(f"    *** Código inesperado: {codigo} ***")
                return consulta

    print(f"  *** TIMEOUT: {nome_passo} não processado após 5 tentativas ***")
    return {"timeout": True, "protocolo": protocolo}


# ============================================================================
# MAIN
# ============================================================================
def main():
    print("=" * 70)
    print(f"PIPELINE RETIFICAÇÃO — CPF {CPF} — perApur={PER_APUR}")
    print(f"Ambiente: {'PRODUÇÃO' if TP_AMB == '1' else 'HOMOLOGAÇÃO'}")
    print("=" * 70)

    pfx_data, senha = carregar_certificado()
    print("Certificado carregado OK")

    resultados = {}

    # ===== PASSO 1: S-1298 (Reabertura) =====
    print("\n" + "=" * 70)
    print("PASSO 1: S-1298 — Reabertura do período")
    print("=" * 70)
    xml_1298 = S1298XMLGenerator.gerar(
        empregador=EMPREGADOR,
        per_apur=PER_APUR,
        ind_apuracao="1",
        seq=1,
        tp_amb=TP_AMB,
    )
    print(f"  XML S-1298 gerado: {len(xml_1298)} bytes")
    with open("_pipeline_s1298.xml", "wb") as f:
        f.write(xml_1298)

    r = enviar_e_consultar(xml_1298, pfx_data, senha, grupo="3", nome_passo="S-1298")
    resultados["S-1298"] = r
    if not r or r.get("timeout"):
        print("\n*** S-1298 falhou ou timeout. Abortando pipeline. ***")
        print("*** Se código 101 (processando), tente consulta manual com o protocolo. ***")
        return

    # ===== PASSO 2: S-1200 (Retificação) =====
    print("\n" + "=" * 70)
    print("PASSO 2: S-1200 — Retificação da remuneração")
    print("=" * 70)
    xml_1200 = S1200XMLGenerator.gerar(
        empregador=EMPREGADOR,
        trabalhador={"cpfTrab": CPF},
        dm_devs=DM_DEVS,
        per_apur=PER_APUR,
        ind_retif="2",
        nr_recibo=S1200_NR_RECIBO,
        ind_apuracao="1",
        seq=2,
        tp_amb=TP_AMB,
    )
    print(f"  XML S-1200 gerado: {len(xml_1200)} bytes")
    with open("_pipeline_s1200.xml", "wb") as f:
        f.write(xml_1200)

    r = enviar_e_consultar(xml_1200, pfx_data, senha, grupo="3", nome_passo="S-1200")
    resultados["S-1200"] = r
    if not r or r.get("timeout"):
        print("\n*** S-1200 falhou ou timeout. Abortando pipeline. ***")
        return

    # ===== PASSO 3: S-1210 (Retificação) =====
    print("\n" + "=" * 70)
    print("PASSO 3: S-1210 — Retificação do pagamento")
    print("=" * 70)
    xml_1210 = S1210XMLGenerator.gerar(
        empregador=EMPREGADOR,
        beneficiario={"cpfBenef": CPF},
        info_pgtos=INFO_PGTOS,
        per_apur=PER_APUR,
        ind_retif="2",
        nr_recibo=S1210_NR_RECIBO,
        info_ir_complem=INFO_IR_COMPLEM,
        seq=3,
        tp_amb=TP_AMB,
    )
    print(f"  XML S-1210 gerado: {len(xml_1210)} bytes")
    with open("_pipeline_s1210.xml", "wb") as f:
        f.write(xml_1210)

    r = enviar_e_consultar(xml_1210, pfx_data, senha, grupo="3", nome_passo="S-1210")
    resultados["S-1210"] = r
    if not r or r.get("timeout"):
        print("\n*** S-1210 falhou ou timeout. Abortando pipeline. ***")
        return

    # ===== PASSO 4: S-1299 (Fechamento) =====
    print("\n" + "=" * 70)
    print("PASSO 4: S-1299 — Fechamento do período")
    print("=" * 70)
    xml_1299 = S1299XMLGenerator.gerar(
        empregador=EMPREGADOR,
        per_apur=PER_APUR,
        ind_apuracao="1",
        evt_remun="S",
        evt_pgtos="S",
        seq=4,
        tp_amb=TP_AMB,
    )
    print(f"  XML S-1299 gerado: {len(xml_1299)} bytes")
    with open("_pipeline_s1299.xml", "wb") as f:
        f.write(xml_1299)

    r = enviar_e_consultar(xml_1299, pfx_data, senha, grupo="3", nome_passo="S-1299")
    resultados["S-1299"] = r

    # ===== RESUMO =====
    print("\n" + "=" * 70)
    print("RESUMO DO PIPELINE")
    print("=" * 70)
    for passo, res in resultados.items():
        if res is None:
            status = "FALHA"
        elif res.get("timeout"):
            status = f"TIMEOUT (protocolo={res.get('protocolo')})"
        elif res.get("codigo_resposta") in ("201", "202"):
            recibos = [ev.get("nrRecibo", "") for ev in res.get("eventos", [])]
            status = f"OK — recibos: {', '.join(recibos)}"
        else:
            status = f"cod={res.get('codigo_resposta')} — {res.get('descricao', '?')}"
        print(f"  {passo}: {status}")

    # ===== SALVAR SNAPSHOT PÓS-PIPELINE =====
    print("\n" + "=" * 70)
    print("SALVANDO SNAPSHOT PÓS-PIPELINE")
    print("=" * 70)
    try:
        snapshot_pos = {
            "cpf": CPF,
            "per_apur": PER_APUR,
            "capturado_em": datetime.now().isoformat(),
            "tipo": "pos_pipeline",
            "descricao": "Estado após execução do pipeline S-1298→S-1200→S-1210→S-1299",
            "resultados_pipeline": {},
        }
        for passo, res in resultados.items():
            snapshot_pos["resultados_pipeline"][passo] = {
                "codigo_resposta": res.get("codigo_resposta") if res else None,
                "eventos": res.get("eventos", []) if res else [],
                "protocolo": res.get("protocolo") if res else None,
            }

        # Capturar estado atualizado do cruzamento_eb
        import psycopg2 as pg2
        from psycopg2.extras import RealDictCursor as RDC
        conn_snap = pg2.connect(**DB_CONFIG)
        cur_snap = conn_snap.cursor(cursor_factory=RDC)
        cur_snap.execute("""
            SELECT id, cod_rubrica, descricao, incid_inss, incid_irrf, incid_fgts,
                   corrigido, envio_status
            FROM cruzamento_eb WHERE cod_rubrica = ANY(%s)
        """, (["566", "596"],))
        snapshot_pos["cruzamento_eb"] = [dict(r) for r in cur_snap.fetchall()]
        for r in snapshot_pos["cruzamento_eb"]:
            if r.get("corrigido_em"):
                r["corrigido_em"] = r["corrigido_em"].isoformat()

        # Recibos novos do pipeline
        snapshot_pos["recibos_novos"] = {}
        for passo, res in resultados.items():
            if res and res.get("eventos"):
                for ev in res["eventos"]:
                    if ev.get("nrRecibo"):
                        snapshot_pos["recibos_novos"][passo] = ev["nrRecibo"]

        # Salvar JSON
        json_path = os.path.join(os.path.dirname(__file__), f"_snapshot_pos_pipeline_{CPF}.json")
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(snapshot_pos, f, indent=2, ensure_ascii=False, default=str)
        print(f"  JSON: {json_path}")

        # Salvar no banco
        cur_snap2 = conn_snap.cursor()
        cur_snap2.execute("""
            CREATE TABLE IF NOT EXISTS pipeline_audit (
                id serial PRIMARY KEY,
                cpf varchar(11) NOT NULL,
                per_apur varchar(7) NOT NULL,
                tipo varchar(20) NOT NULL,
                dados jsonb NOT NULL,
                created_at timestamptz DEFAULT now()
            )
        """)
        cur_snap2.execute("""
            INSERT INTO pipeline_audit (cpf, per_apur, tipo, dados)
            VALUES (%s, %s, %s, %s)
            RETURNING id
        """, (CPF, PER_APUR, "pos_pipeline", json.dumps(snapshot_pos, ensure_ascii=False, default=str)))
        audit_id = cur_snap2.fetchone()[0]
        conn_snap.commit()
        cur_snap.close()
        cur_snap2.close()
        conn_snap.close()
        print(f"  DB: pipeline_audit id={audit_id}")
    except Exception as e:
        print(f"  ERRO ao salvar snapshot pós: {e}")


if __name__ == "__main__":
    main()
