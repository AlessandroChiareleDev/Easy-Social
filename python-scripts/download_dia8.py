"""Download S-5002 pós-pipeline — dia 8 de abril 2026."""
import sys, os, json, re
sys.path.insert(0, os.path.dirname(__file__))

import psycopg2
from db_config import DB_CONFIG, LOCAL_DB_CONFIG
from esocial.certificate_manager import CertificateManager
from esocial.esocial_client import ESocialClient
from esocial.envio_tracker import registrar_consulta

CPF = "08132588983"

# Certificado do banco local
local_conn = psycopg2.connect(**LOCAL_DB_CONFIG)
cur = local_conn.cursor()
cur.execute("SELECT cnpj, arquivo_path, senha_encrypted FROM certificados_a1 WHERE ativo = TRUE LIMIT 1")
cnpj, arquivo_path, senha_enc = cur.fetchone()
local_conn.close()

# Tracker no Supabase
conn = psycopg2.connect(**DB_CONFIG)

senha = CertificateManager.decrypt_password(senha_enc)
with open(arquivo_path, "rb") as f:
    pfx_data = f.read()

empregador = {"tpInsc": 1, "nrInsc": cnpj[:8]}

print("=" * 60)
print("  DOWNLOAD S-5002 — DIA 8, PÓS-BLOQUEIO")
print(f"  CPF: {CPF} | CNPJ: {cnpj}")
print("=" * 60)

for per in ["2024-12", "2025-01"]:
    print(f"\n{'='*60}")
    print(f"  PERÍODO: {per}")
    print(f"{'='*60}")

    # 1. Consultar identificadores
    print("\n  [1] Consultando identificadores...")
    result = ESocialClient.consultar_identificadores_trabalhador(
        cpf=CPF,
        dt_ini=f"{per}-01T00:00:00",
        dt_fim=f"{per}-28T23:59:59",
        pfx_data=pfx_data,
        password=senha,
        empregador=empregador,
        producao=True,
    )

    # Registrar consulta
    registrar_consulta(
        conn,
        tipo_consulta="CONSULTA-IDENT",
        ambiente="1",
        resultado=result,
        cpf=CPF,
        per_apur=per,
        xml_resposta=result.get("xml_resposta"),
        origem="download_dia8",
    )

    if not result.get("sucesso"):
        cod = result.get("codigo_resposta", "?")
        desc = result.get("descricao", "?")
        print(f"  FALHA ({cod}): {desc}")
        continue

    eventos = result.get("eventos", [])
    print(f"  OK! {len(eventos)} eventos encontrados")

    # Classificar
    por_tipo = {}
    for ev in eventos:
        tp = ev.get("tipo", "?")
        por_tipo.setdefault(tp, []).append(ev)

    for tp, evs in sorted(por_tipo.items()):
        print(f"    {tp}: {len(evs)}")

    # 2. Baixar S-5002 por nrRecibo
    s5002 = por_tipo.get("S-5002", [])
    if not s5002:
        print("\n  Nenhum S-5002 encontrado!")
        continue

    nr_recibos = [e["nrRec"] for e in s5002 if e.get("nrRec")]
    print(f"\n  [2] Baixando {len(nr_recibos)} S-5002 por nrRecibo...")
    for nr in nr_recibos:
        print(f"      nrRec: {nr}")

    dl = ESocialClient.solicitar_download_por_nrrecibo(
        nr_recibos=nr_recibos,
        pfx_data=pfx_data,
        password=senha,
        empregador=empregador,
        producao=True,
    )

    # Registrar download
    registrar_consulta(
        conn,
        tipo_consulta="DOWNLOAD-S5002",
        ambiente="1",
        resultado=dl,
        cpf=CPF,
        per_apur=per,
        xml_resposta=dl.get("xml_resposta"),
        origem="download_dia8",
    )

    if not dl.get("sucesso"):
        desc = dl.get("descricao") or dl.get("erro", "?")
        print(f"  Download por nrRecibo FALHOU: {desc}")

        # Tentativa alternativa: por ID
        print("\n  [2b] Tentando por ID...")
        ids = [e["id"] for e in s5002 if e.get("id")]
        dl = ESocialClient.solicitar_download_por_id(
            ids=ids,
            pfx_data=pfx_data,
            password=senha,
            empregador=empregador,
            producao=True,
        )
        registrar_consulta(
            conn,
            tipo_consulta="DOWNLOAD-S5002",
            ambiente="1",
            resultado=dl,
            cpf=CPF,
            per_apur=per,
            xml_resposta=dl.get("xml_resposta"),
            origem="download_dia8",
        )

        if not dl.get("sucesso"):
            print(f"  Download por ID também FALHOU: {dl.get('descricao') or dl.get('erro', '?')}")
            continue

    # 3. Parsear XMLs baixados
    for i, arq in enumerate(dl.get("arquivos", [])):
        xml = arq.get("evento_xml") or arq.get("xml_evento") or ""
        nr = arq.get("nr_recibo", "?")
        print(f"\n  {'='*50}")
        print(f"  S-5002 #{i+1} (recibo: {nr})")
        print(f"  {'='*50}")

        if not xml:
            print(f"  Sem XML! Keys: {list(arq.keys())}")
            continue

        # Nome
        nm = re.findall(r'<nmTrab>([^<]+)</nmTrab>', xml)
        if nm:
            print(f"  NOME: {nm[0]}")

        cpf_b = re.findall(r'<cpfBenef>([^<]+)</cpfBenef>', xml)
        print(f"  cpfBenef: {cpf_b[0] if cpf_b else '?'}")

        rec_base = re.findall(r'<nrRecArqBase>([^<]+)</nrRecArqBase>', xml)
        print(f"  nrRecArqBase: {rec_base}")

        # infoIR — IRRF detalhado
        infos = re.findall(r'<infoIR><tpInfoIR>(\d+)</tpInfoIR><valor>([^<]+)</valor></infoIR>', xml)
        if infos:
            desc_map = {
                "11": "Rend. tributável",
                "12": "Rend. 13º sal",
                "31": "IRRF retido mensal",
                "32": "IRRF retido 13º",
                "34": "IRRF retido RRA",
                "41": "Ded. INSS mensal",
                "42": "Ded. INSS 13º",
                "46": "Ded. INSS RRA",
                "51": "Ded. pensão alim.",
                "61": "Ded. dependentes",
                "70": "Isent. 65 anos",
                "71": "Isent. mol. grave",
                "73": "Isent. lucros div.",
                "76": "Isent. diárias",
                "79": "Isent. outros",
                "7900": "Contrib. previd.",
                "9": "Isento",
            }
            print(f"\n  === IRRF DETALHADO (infoIR) ===")
            for tp, val in infos:
                label = desc_map.get(tp, f"tipo {tp}")
                print(f"    tpInfoIR={tp:5s} ({label:25s}) = R$ {val}")

        # totApurMen
        tots = re.findall(r'<CRMen>(\d+)</CRMen><vlrCRMen>([^<]+)</vlrCRMen>', xml)
        if tots:
            print(f"\n  === VALORES APURADOS (totApurMen) ===")
            for cr, vl in tots:
                print(f"    CRMen={cr} vlrCRMen=R$ {vl}")

        # totApurDia (se existir)
        tots_dia = re.findall(r'<CRDia>(\d+)</CRDia><vlrCRDia>([^<]+)</vlrCRDia>', xml)
        if tots_dia:
            print(f"\n  === VALORES DIÁRIOS (totApurDia) ===")
            for cr, vl in tots_dia:
                print(f"    CRDia={cr} vlrCRDia=R$ {vl}")

        # Salvar XML
        fname = f"s5002_dia8_{per}_{i+1}.xml"
        with open(fname, "w", encoding="utf-8") as f:
            f.write(xml)
        print(f"\n  Salvo: {fname}")

# Também baixar S-5001 para conferência INSS
print(f"\n\n{'='*60}")
print("  DOWNLOAD S-5001 (INSS) PARA CONFERÊNCIA")
print(f"{'='*60}")

for per in ["2024-12"]:
    print(f"\n  Período: {per}")
    result = ESocialClient.consultar_identificadores_trabalhador(
        cpf=CPF,
        dt_ini=f"{per}-01T00:00:00",
        dt_fim=f"{per}-28T23:59:59",
        pfx_data=pfx_data,
        password=senha,
        empregador=empregador,
        producao=True,
    )
    if not result.get("sucesso"):
        print(f"  Consulta falhou")
        continue

    eventos = result.get("eventos", [])
    s5001 = [e for e in eventos if e.get("tipo") == "S-5001"]
    if not s5001:
        print("  Nenhum S-5001")
        continue

    nr_recibos = [e["nrRec"] for e in s5001 if e.get("nrRec")]
    print(f"  Baixando {len(nr_recibos)} S-5001...")

    dl = ESocialClient.solicitar_download_por_nrrecibo(
        nr_recibos=nr_recibos,
        pfx_data=pfx_data,
        password=senha,
        empregador=empregador,
        producao=True,
    )
    if dl.get("sucesso"):
        for i, arq in enumerate(dl.get("arquivos", [])):
            xml = arq.get("evento_xml") or arq.get("xml_evento") or ""
            if xml:
                fname = f"s5001_dia8_{per}_{i+1}.xml"
                with open(fname, "w", encoding="utf-8") as f:
                    f.write(xml)
                print(f"  Salvo: {fname}")

                # INSS detalhado
                inss_calc = re.findall(r'<vrBcCp00>([^<]+)</vrBcCp00>', xml)
                inss_desc = re.findall(r'<vrDescSest>([^<]+)</vrDescSest>', xml)
                inss_fgts = re.findall(r'<vrBcFGTS>([^<]+)</vrBcFGTS>', xml)

                if inss_calc:
                    print(f"  vrBcCp00 (base INSS): R$ {inss_calc[0]}")
                if inss_fgts:
                    print(f"  vrBcFGTS (base FGTS): R$ {inss_fgts[0]}")
    else:
        print(f"  Download S-5001 falhou: {dl.get('descricao','?')}")

print(f"\n{'='*60}")
print("  FIM")
print(f"{'='*60}")

conn.close()
