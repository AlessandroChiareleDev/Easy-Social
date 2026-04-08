"""
Download S-5002 + S-5001 — LEAN (sem consulta, nrRecibos hardcoded).

Usa apenas 2 requests da cota diária (10/dia):
  1. Batch download 3 S-5002 por nrRecibo
  2. Batch download 4 S-5001 por nrRecibo
  + 1 consulta 2025-01 (se sobrar cota)
  + downloads 2025-01

Total máximo: ~5 requests (em vez de 6+ do download_dia8.py).

nrRecibos extraídos da consulta bem-sucedida (envio #24, 2026-04-08 05:07).
"""
import sys, os, re, json
sys.path.insert(0, os.path.dirname(__file__))

import psycopg2
from db_config import DB_CONFIG, LOCAL_DB_CONFIG
from esocial.certificate_manager import CertificateManager
from esocial.esocial_client import ESocialClient
from esocial.envio_tracker import registrar_consulta

CPF = "08132588983"
PERIODO = "2024-12"

# ── nrRecibos conhecidos (consulta de 2026-04-08 05:07) ──────────
S5002_RECIBOS = [
    "1.1.0000000029478368826",   # S-5002 (evento emp: 2024-12-10)
    "1.1.0000000029734597713",   # S-5002 (evento emp: 2024-12-18 11:06)
    "1.1.0000000029740909596",   # S-5002 (evento emp: 2024-12-18 13:04)
]

S5001_RECIBOS = [
    "1.1.0000000029388417020",   # S-5001 (evento emp: 2024-12-06)
    "1.1.0000000029710914787",   # S-5001 (evento emp: 2024-12-17)
    "1.1.0000000029736720591",   # S-5001 (evento emp: 2024-12-18 11:39)
    "1.1.0000000029815504274",   # S-5001 (evento emp: 2024-12-20)
]

# Mapa de IDs correspondentes (para referência)
S5002_IDS = [
    "ID20000000000000000000029478368345",
    "ID20000000000000000000029734597512",
    "ID20000000000000000000029740909549",
]

# ── Certificado (banco local) ────────────────────────────────────
local_conn = psycopg2.connect(**LOCAL_DB_CONFIG)
cur = local_conn.cursor()
cur.execute("SELECT cnpj, arquivo_path, senha_encrypted FROM certificados_a1 WHERE ativo = TRUE LIMIT 1")
cnpj, arquivo_path, senha_enc = cur.fetchone()
local_conn.close()

senha = CertificateManager.decrypt_password(senha_enc)
with open(arquivo_path, "rb") as f:
    pfx_data = f.read()

empregador = {"tpInsc": 1, "nrInsc": cnpj[:8]}

# ── Tracker (Supabase) ──────────────────────────────────────────
conn = psycopg2.connect(**DB_CONFIG)

DESC_IRRF = {
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

erros = []


def print_header(title):
    w = 60
    print(f"\n{'=' * w}")
    print(f"  {title}")
    print(f"{'=' * w}")


def download_batch(label, nr_recibos, tipo):
    """Baixa batch de eventos por nrRecibo. Retorna lista de dicts com XML."""
    print(f"\n  [{tipo}] Baixando {len(nr_recibos)} {label} por nrRecibo...")
    for nr in nr_recibos:
        print(f"      nrRec: {nr}")

    dl = ESocialClient.solicitar_download_por_nrrecibo(
        nr_recibos=nr_recibos,
        pfx_data=pfx_data,
        password=senha,
        empregador=empregador,
        producao=True,
    )

    registrar_consulta(
        conn,
        tipo_consulta=f"DOWNLOAD-{label}",
        ambiente="1",
        resultado=dl,
        cpf=CPF,
        per_apur=PERIODO,
        xml_resposta=dl.get("xml_resposta"),
        origem="download_s5002_lean",
    )

    if not dl.get("sucesso"):
        desc = dl.get("descricao") or dl.get("erro", "?")
        msg = f"Download {label} FALHOU: {desc}"
        print(f"  ❌ {msg}")
        erros.append(msg)

        # Tentativa por ID (só S-5002)
        if label == "S-5002":
            print(f"\n  [FALLBACK] Tentando S-5002 por ID...")
            dl = ESocialClient.solicitar_download_por_id(
                ids=S5002_IDS,
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
                per_apur=PERIODO,
                xml_resposta=dl.get("xml_resposta"),
                origem="download_s5002_lean",
            )
            if not dl.get("sucesso"):
                msg = f"Download S-5002 por ID também FALHOU: {dl.get('descricao') or dl.get('erro', '?')}"
                print(f"  ❌ {msg}")
                erros.append(msg)
                return []

    return dl.get("arquivos", [])


def parsear_s5002(arqs):
    """Parseia e exibe detalhes dos XMLs S-5002."""
    for i, arq in enumerate(arqs):
        xml = arq.get("evento_xml") or arq.get("xml_evento") or ""
        nr = arq.get("nr_recibo", "?")
        print(f"\n  {'─' * 50}")
        print(f"  S-5002 #{i+1} (recibo: {nr})")
        print(f"  {'─' * 50}")

        if not xml:
            print(f"  ⚠ Sem XML! Keys: {list(arq.keys())}")
            continue

        # Nome e CPF
        nm = re.findall(r'<nmTrab>([^<]+)</nmTrab>', xml)
        cpf_b = re.findall(r'<cpfBenef>([^<]+)</cpfBenef>', xml)
        per = re.findall(r'<perApur>([^<]+)</perApur>', xml)
        rec_base = re.findall(r'<nrRecArqBase>([^<]+)</nrRecArqBase>', xml)

        if nm:
            print(f"  NOME: {nm[0]}")
        print(f"  cpfBenef: {cpf_b[0] if cpf_b else '?'}")
        if per:
            print(f"  perApur: {per[0]}")
        if rec_base:
            print(f"  nrRecArqBase: {rec_base}")

        # === infoIR ===
        infos = re.findall(r'<infoIR><tpInfoIR>(\d+)</tpInfoIR><valor>([^<]+)</valor></infoIR>', xml)
        if infos:
            print(f"\n  ╔═══ IRRF DETALHADO (infoIR) ═══")
            for tp, val in infos:
                label = DESC_IRRF.get(tp, f"tipo {tp}")
                star = " ← CORREÇÃO" if tp in ("41", "42") else ""
                print(f"  ║ tpInfoIR={tp:5s} ({label:25s}) = R$ {val}{star}")
            print(f"  ╚{'═' * 35}")

        # === totApurMen ===
        tots = re.findall(r'<CRMen>(\d+)</CRMen><vlrCRMen>([^<]+)</vlrCRMen>', xml)
        if tots:
            print(f"\n  ╔═══ VALORES APURADOS (totApurMen) ═══")
            for cr, vl in tots:
                print(f"  ║ CRMen={cr} → R$ {vl}")
            print(f"  ╚{'═' * 35}")

        # === totApurDia ===
        tots_dia = re.findall(r'<CRDia>(\d+)</CRDia><vlrCRDia>([^<]+)</vlrCRDia>', xml)
        if tots_dia:
            print(f"\n  === VALORES DIÁRIOS (totApurDia) ===")
            for cr, vl in tots_dia:
                print(f"    CRDia={cr} → R$ {vl}")

        # Salvar XML
        fname = f"s5002_{PERIODO}_{i+1}.xml"
        with open(fname, "w", encoding="utf-8") as f:
            f.write(xml)
        print(f"\n  ✓ Salvo: {fname}")


def parsear_s5001(arqs):
    """Parseia e exibe detalhes dos XMLs S-5001 (INSS)."""
    for i, arq in enumerate(arqs):
        xml = arq.get("evento_xml") or arq.get("xml_evento") or ""
        nr = arq.get("nr_recibo", "?")
        print(f"\n  {'─' * 50}")
        print(f"  S-5001 #{i+1} (recibo: {nr})")
        print(f"  {'─' * 50}")

        if not xml:
            print(f"  ⚠ Sem XML! Keys: {list(arq.keys())}")
            continue

        nm = re.findall(r'<nmTrab>([^<]+)</nmTrab>', xml)
        if nm:
            print(f"  NOME: {nm[0]}")

        for tag, label in [
            ("vrBcCp00", "Base INSS (CP00)"),
            ("vrBcCp15", "Base INSS 15 dias"),
            ("vrBcCp20", "Base INSS apos. especial 20"),
            ("vrBcCp25", "Base INSS apos. especial 25"),
            ("vrBcFGTS", "Base FGTS"),
            ("vrDescSest", "Desconto SEST"),
            ("vrDescSenat", "Desconto SENAT"),
            ("vrCpSeg", "CP Segurados"),
        ]:
            vals = re.findall(f'<{tag}>([^<]+)</{tag}>', xml)
            if vals:
                print(f"  {label}: R$ {vals[0]}")

        fname = f"s5001_{PERIODO}_{i+1}.xml"
        with open(fname, "w", encoding="utf-8") as f:
            f.write(xml)
        print(f"\n  ✓ Salvo: {fname}")


# ══════════════════════════════════════════════════════════════════
#  MAIN
# ══════════════════════════════════════════════════════════════════
print_header(f"DOWNLOAD LEAN — CPF {CPF} | PERÍODO {PERIODO}")
print(f"  CNPJ: {cnpj}")
print(f"  Requests planejados: 2 (S-5002 + S-5001)")
print(f"  Cota diária: 10 requests")

# ── 1. Download S-5002 (IRRF) ───────────────────────────────────
print_header("1. S-5002 (IRRF)")
arqs_5002 = download_batch("S-5002", S5002_RECIBOS, "1")
if arqs_5002:
    parsear_s5002(arqs_5002)
else:
    print("  Nenhum arquivo obtido")

# ── 2. Download S-5001 (INSS) ───────────────────────────────────
print_header("2. S-5001 (INSS)")
arqs_5001 = download_batch("S-5001", S5001_RECIBOS, "2")
if arqs_5001:
    parsear_s5001(arqs_5001)
else:
    print("  Nenhum arquivo obtido")

# ── 3. Consulta 2025-01 ─────────────────────────────────────────
print_header("3. CONSULTA 2025-01")
result_2501 = ESocialClient.consultar_identificadores_trabalhador(
    cpf=CPF,
    dt_ini="2025-01-01T00:00:00",
    dt_fim="2025-01-31T23:59:59",
    pfx_data=pfx_data,
    password=senha,
    empregador=empregador,
    producao=True,
)
registrar_consulta(
    conn,
    tipo_consulta="CONSULTA-IDENT",
    ambiente="1",
    resultado=result_2501,
    cpf=CPF,
    per_apur="2025-01",
    xml_resposta=result_2501.get("xml_resposta"),
    origem="download_s5002_lean",
)

if result_2501.get("sucesso"):
    eventos_2501 = result_2501.get("eventos", [])
    print(f"  {len(eventos_2501)} eventos encontrados para 2025-01")

    por_tipo = {}
    for ev in eventos_2501:
        tp = ev.get("tipo", "?")
        por_tipo.setdefault(tp, []).append(ev)
    for tp, evs in sorted(por_tipo.items()):
        print(f"    {tp}: {len(evs)}")

    # Download S-5002 de 2025-01
    s5002_2501 = por_tipo.get("S-5002", [])
    if s5002_2501:
        nr_recs = [e["nrRec"] for e in s5002_2501 if e.get("nrRec")]
        print(f"\n  Baixando {len(nr_recs)} S-5002 de 2025-01...")
        dl = ESocialClient.solicitar_download_por_nrrecibo(
            nr_recibos=nr_recs,
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
            per_apur="2025-01",
            xml_resposta=dl.get("xml_resposta"),
            origem="download_s5002_lean",
        )
        if dl.get("sucesso"):
            parsear_s5002(dl.get("arquivos", []))
        else:
            msg = f"Download S-5002 2025-01 falhou: {dl.get('descricao') or dl.get('erro', '?')}"
            print(f"  ❌ {msg}")
            erros.append(msg)
    else:
        print("  Nenhum S-5002 em 2025-01")
else:
    cod = result_2501.get("codigo_resposta", "?")
    desc = result_2501.get("descricao", "?")
    msg = f"Consulta 2025-01 falhou ({cod}): {desc}"
    print(f"  ❌ {msg}")
    erros.append(msg)

# ── Resumo ───────────────────────────────────────────────────────
print_header("RESUMO")
print(f"  S-5002 baixados (2024-12): {len(arqs_5002)}")
print(f"  S-5001 baixados (2024-12): {len(arqs_5001)}")
if erros:
    print(f"\n  ⚠ {len(erros)} erro(s):")
    for e in erros:
        print(f"    - {e}")
else:
    print("  ✅ Tudo OK!")

print_header("FIM")
conn.close()
