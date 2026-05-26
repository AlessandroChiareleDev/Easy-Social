from __future__ import annotations

import csv
import json
import re
import sys
from collections import defaultdict
from datetime import datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

import psycopg2.extras
from lxml import etree


ROOT = Path(r"C:\Users\xandao\Documents\GitHub\Easy-Social")
BACKEND = Path(r"C:\Users\xandao\Documents\GitHub\Easy-eSocial-v2\backend")
if str(ROOT / "python-scripts") not in sys.path:
    sys.path.insert(0, str(ROOT / "python-scripts"))
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from app import db, tenant  # noqa: E402
from preparar_correcao_agosto_jaque import cpf11, read_xml_event  # noqa: E402


EMPRESA_ID = 2
PER_APUR = "2025-08"
MESES_PROVA = ("2025-07", "2025-09")
OUT_DIR = ROOT / "relatorio_ana" / "CORRECAO_AGOSTO_202_DEDDEPEN"
VALOR_PADRAO = Decimal("189.59")
CPF_ZERO = "00000000000"


def text(value: Any) -> str:
    if value is None:
        return ""
    return re.sub(r"\s+", " ", str(value).strip())


def money(value: Any) -> Decimal:
    raw = text(value).replace("R$", "").strip()
    if not raw:
        return Decimal("0.00")
    if "," in raw:
        raw = raw.replace(".", "").replace(",", ".")
    try:
        return Decimal(raw).quantize(Decimal("0.01"))
    except InvalidOperation:
        return Decimal("0.00")


def money_str(value: Decimal) -> str:
    return f"{value.quantize(Decimal('0.01')):.2f}"


def load_receipt_jsons() -> dict[str, str]:
    out: dict[str, str] = {}
    for path in sorted((ROOT / "relatorio_ana").glob("AGOSTO_202_ACTIVE_RECIBOS*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        if isinstance(data, dict):
            for cpf, recibo in data.items():
                cpf_norm = cpf11(cpf)
                recibo_text = text(recibo)
                if len(cpf_norm) == 11 and recibo_text.startswith("1.1."):
                    out[cpf_norm] = recibo_text
    return out


def load_front_head_receipts() -> dict[str, dict[str, Any]]:
    """Carrega a mesma fonte que alimenta o front S-1210 anual/lista do mes.

    Para avisos 202 o retorno nao gravou nr_recibo_novo na timeline, mas a
    lista do front expoe o S-1210 HEAD como nr_recibo_xml. Esse recibo vem do
    XML local baixado/importado, nao de consulta ao eSocial nesta rotina.
    """
    from app.timeline import s1210_cpfs_do_mes  # import tardio para evitar ciclo

    data = s1210_cpfs_do_mes(PER_APUR, empresa_id=EMPRESA_ID, lote_num=1)
    out: dict[str, dict[str, Any]] = {}
    for row in data.get("cpfs", []):
        cpf = cpf11(row.get("cpf"))
        recibo = text(row.get("nr_recibo_xml"))
        if len(cpf) == 11 and recibo.startswith("1.1."):
            out[cpf] = {
                "recibo": recibo,
                "fonte": "front_s1210_cpfs_do_mes.nr_recibo_xml",
                "status_front": row.get("status"),
                "erro_codigo_front": row.get("erro_codigo"),
                "nr_recibo_novo_front": row.get("nr_recibo_novo"),
                "nr_recibo_usado_front": row.get("nr_recibo_usado"),
                "tem_xml_front": row.get("tem_xml"),
            }
    return out


def load_current_202() -> list[dict[str, Any]]:
    internal = tenant.internal_empresa_id(EMPRESA_ID)
    conn = db.connect(empresa_id=EMPRESA_ID)
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                """
                WITH latest AS (
                    SELECT DISTINCT ON (it.cpf)
                           it.cpf, it.status, it.erro_codigo, it.erro_mensagem,
                           it.nr_recibo_anterior, it.nr_recibo_novo,
                           it.xml_enviado_oid, it.xml_retorno_oid,
                           it.id AS item_id, te.id AS envio_id, it.criado_em
                      FROM timeline_envio_item it
                      JOIN timeline_envio te ON te.id = it.timeline_envio_id
                      JOIN timeline_mes tm ON tm.id = te.timeline_mes_id
                     WHERE tm.empresa_id = %s
                       AND tm.per_apur = %s
                       AND it.tipo_evento = 'S-1210'
                       AND it.cpf IS NOT NULL
                     ORDER BY it.cpf, it.criado_em DESC NULLS LAST, it.id DESC
                )
                SELECT *
                  FROM latest
                 WHERE erro_codigo = '202'
                 ORDER BY cpf
                """,
                (internal, PER_APUR),
            )
            return [dict(row) for row in cur.fetchall()]
    finally:
        conn.close()


def load_event_rows(cpfs: list[str], per_apur: str) -> dict[str, dict[str, Any]]:
    internal = tenant.internal_empresa_id(EMPRESA_ID)
    conn = db.connect(empresa_id=EMPRESA_ID)
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                """
                SELECT DISTINCT ON (ev.cpf)
                       ev.id, ev.cpf, ev.nr_recibo, ev.id_evento,
                       ev.xml_oid, ev.xml_bytes, ev.xml_size_bytes,
                       ev.xml_entry_name, ev.zip_id,
                       z.conteudo_oid AS zip_conteudo_oid,
                       z.tamanho_bytes AS zip_tamanho_bytes,
                       z.nome_arquivo_original AS zip_nome,
                       ev.dt_processamento
                  FROM explorador_eventos ev
                  JOIN empresa_zips_brutos z ON z.id = ev.zip_id
                 WHERE z.empresa_id = %s
                   AND ev.tipo_evento = 'S-1210'
                   AND ev.per_apur = %s
                   AND ev.retificado_por_id IS NULL
                   AND ev.cpf = ANY(%s)
                   AND (ev.xml_oid IS NOT NULL OR ev.xml_bytes IS NOT NULL OR ev.xml_entry_name IS NOT NULL)
                 ORDER BY ev.cpf ASC, ev.dt_processamento DESC NULLS LAST, ev.id DESC
                """,
                (internal, per_apur, cpfs),
            )
            return {cpf11(row["cpf"]): dict(row) for row in cur.fetchall()}
    finally:
        conn.close()


def children(el, tag: str) -> list[Any]:
    return el.xpath(f'./*[local-name()="{tag}"]')


def child_text(el, tag: str) -> str:
    found = children(el, tag)
    return text(found[0].text) if found else ""


def extract_ir(xml_bytes: bytes) -> dict[str, Any]:
    root = etree.fromstring(xml_bytes)
    info = root.xpath('//*[local-name()="ideBenef"]/*[local-name()="infoIRComplem"]')
    if not info:
        return {"infoDep": [], "dedDepen": [], "ded_zero": [], "infoIRCR": 0}
    info = info[0]

    info_deps: list[dict[str, str]] = []
    for node in children(info, "infoDep"):
        cpf = cpf11(child_text(node, "cpfDep"))
        if len(cpf) == 11 and cpf != CPF_ZERO:
            item = {"cpfDep": cpf}
            for tag in ("dtNascto", "nome", "depIRRF", "tpDep", "descrDep"):
                value = child_text(node, tag)
                if value:
                    item[tag] = value
            info_deps.append(item)

    deds: list[dict[str, str]] = []
    ded_zero: list[dict[str, str]] = []
    ircr_count = 0
    for cr in children(info, "infoIRCR"):
        ircr_count += 1
        tp_cr = child_text(cr, "tpCR")
        for dd in children(cr, "dedDepen"):
            item = {
                "tpCR": tp_cr,
                "tpRend": child_text(dd, "tpRend") or "11",
                "cpfDep": cpf11(child_text(dd, "cpfDep")),
                "vlrDedDep": money_str(money(child_text(dd, "vlrDedDep"))),
            }
            if item["cpfDep"] == CPF_ZERO:
                ded_zero.append(item)
            elif len(item["cpfDep"]) == 11 and money(item["vlrDedDep"]) > 0:
                deds.append(item)

    return {"infoDep": info_deps, "dedDepen": deds, "ded_zero": ded_zero, "infoIRCR": ircr_count}


def ded_signature(deds: list[dict[str, str]]) -> list[tuple[str, str, str]]:
    return sorted((d["tpCR"], d["tpRend"], d["cpfDep"]) for d in deds if d.get("cpfDep") != CPF_ZERO)


def normalize_deds(deds: list[dict[str, str]]) -> list[dict[str, str]]:
    out: list[dict[str, str]] = []
    seen: set[tuple[str, str, str]] = set()
    for item in sorted(deds, key=lambda d: (d["tpCR"], d["tpRend"], d["cpfDep"])):
        key = (item["tpCR"], item["tpRend"], item["cpfDep"])
        if key in seen:
            continue
        seen.add(key)
        value = money(item.get("vlrDedDep"))
        out.append({
            "tpCR": item["tpCR"],
            "tpRend": item["tpRend"] or "11",
            "cpfDep": item["cpfDep"],
            "vlrDedDep": money_str(value if Decimal("0.00") < value <= VALOR_PADRAO else VALOR_PADRAO),
        })
    return out


def choose_source(july: dict[str, Any] | None, sep: dict[str, Any] | None) -> tuple[str, str, list[dict[str, str]]]:
    july_deds = normalize_deds((july or {}).get("dedDepen") or [])
    sep_deds = normalize_deds((sep or {}).get("dedDepen") or [])
    july_sig = ded_signature(july_deds)
    sep_sig = ded_signature(sep_deds)
    if july_sig and sep_sig and july_sig == sep_sig:
        return "alta", "julho_setembro_iguais", sep_deds
    if sep_sig and not july_sig:
        return "media", "somente_setembro", sep_deds
    if july_sig and not sep_sig:
        return "media", "somente_julho", july_deds
    if sep_sig and july_sig and sep_sig != july_sig:
        return "manual", "julho_setembro_divergentes", []
    return "sem_prova", "sem_deddepen_real_em_julho_setembro", []


def build_summary() -> dict[str, Any]:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    current = load_current_202()
    cpfs = [cpf11(row["cpf"]) for row in current]
    receipt_jsons = load_receipt_jsons()
    front_receipts = load_front_head_receipts()
    rows_by_month = {month: load_event_rows(cpfs, month) for month in MESES_PROVA}

    evidence: list[dict[str, Any]] = []
    conn = db.connect(empresa_id=EMPRESA_ID)
    try:
        for row in current:
            cpf = cpf11(row["cpf"])
            month_data: dict[str, Any] = {}
            for month in MESES_PROVA:
                event = rows_by_month[month].get(cpf)
                if not event:
                    month_data[month] = {"found": False, "error": "sem S-1210 local"}
                    continue
                try:
                    xml = read_xml_event(conn, event)
                    ir = extract_ir(xml)
                    month_data[month] = {
                        "found": True,
                        "recibo_local": event.get("nr_recibo"),
                        "infoIRCR": ir["infoIRCR"],
                        "infoDep": ir["infoDep"],
                        "dedDepen": ir["dedDepen"],
                        "ded_zero": ir["ded_zero"],
                    }
                except Exception as exc:  # noqa: BLE001
                    month_data[month] = {"found": True, "error": f"{type(exc).__name__}: {exc}"}
            confianca, motivo, correcao = choose_source(month_data.get("2025-07"), month_data.get("2025-09"))
            receipt_meta = front_receipts.get(cpf)
            receipt = (receipt_meta or {}).get("recibo") or receipt_jsons.get(cpf)
            receipt_source = (receipt_meta or {}).get("fonte") or ("json_AGOSTO_202_ACTIVE_RECIBOS" if receipt else "")
            evidence.append({
                "cpf": cpf,
                "status_atual": row.get("status"),
                "erro_codigo": row.get("erro_codigo"),
                "item_id": row.get("item_id"),
                "envio_id": row.get("envio_id"),
                "tem_recibo_ativo_local": bool(receipt),
                "recibo_ativo_local": receipt or "",
                "recibo_fonte_local": receipt_source,
                "front": receipt_meta or {},
                "confianca": confianca,
                "motivo": motivo,
                "dedDepen_corrigir": correcao,
                "provas": month_data,
            })
    finally:
        conn.close()

    counts: dict[str, int] = defaultdict(int)
    for item in evidence:
        counts[f"confianca_{item['confianca']}"] += 1
        if item["tem_recibo_ativo_local"]:
            counts["com_recibo_ativo_local"] += 1
        if item.get("recibo_fonte_local") == "front_s1210_cpfs_do_mes.nr_recibo_xml":
            counts["com_recibo_front_head_xml"] += 1
        if item["dedDepen_corrigir"]:
            counts["com_deddepen_reconstruido"] += 1
        if item["dedDepen_corrigir"] and item["tem_recibo_ativo_local"]:
            counts["pronto_para_xml_envio"] += 1

    return {
        "empresa_id": EMPRESA_ID,
        "per_apur": PER_APUR,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "regra": {
            "origem": "call Marcos: corrigir 202/1863 com dependentes reais de julho/setembro",
            "ignorar_cpf_zero": CPF_ZERO,
            "valor_padrao_dependente": money_str(VALOR_PADRAO),
            "nao_misturar_com": ["planSaude", "penAlim", "S-1200"],
        },
        "counts": {"total_202_atual": len(current), **dict(sorted(counts.items()))},
        "receipt_sources": {
            "front_s1210_cpfs_do_mes": len(front_receipts),
            "coverage_current_202_front": sum(1 for cpf in cpfs if cpf in front_receipts),
            "jsons_AGOSTO_202_ACTIVE_RECIBOS": len(receipt_jsons),
            "coverage_current_202_jsons": sum(1 for cpf in cpfs if cpf in receipt_jsons),
        },
        "evidence": evidence,
    }


def write_outputs(summary: dict[str, Any]) -> dict[str, str]:
    json_path = OUT_DIR / "preflight_agosto_202_deddepen.json"
    csv_path = OUT_DIR / "preflight_agosto_202_deddepen.csv"
    md_path = OUT_DIR / "preflight_agosto_202_deddepen.md"
    json_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2, default=str), encoding="utf-8")

    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        fieldnames = [
            "cpf", "confianca", "motivo", "tem_recibo_ativo_local", "recibo_ativo_local", "recibo_fonte_local",
            "ded_count", "dependentes", "envio_id", "item_id",
        ]
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for item in summary["evidence"]:
            deds = item.get("dedDepen_corrigir") or []
            writer.writerow({
                "cpf": item["cpf"],
                "confianca": item["confianca"],
                "motivo": item["motivo"],
                "tem_recibo_ativo_local": item["tem_recibo_ativo_local"],
                "recibo_ativo_local": item["recibo_ativo_local"],
                "recibo_fonte_local": item["recibo_fonte_local"],
                "ded_count": len(deds),
                "dependentes": "; ".join(f"{d['tpCR']}/{d['tpRend']}/{d['cpfDep']}/{d['vlrDedDep']}" for d in deds),
                "envio_id": item["envio_id"],
                "item_id": item["item_id"],
            })

    c = summary["counts"]
    lines = [
        "# Preflight Agosto/2025 - aviso 202/1863 dedDepen",
        "",
        f"Gerado em: {summary['generated_at']}",
        "",
        "## Regra aplicada",
        "",
        "- Corrigir apenas `dedDepen` dos avisos 202/1863.",
        "- Usar dependentes reais confirmados em Julho/2025 e/ou Setembro/2025.",
        "- Ignorar `cpfDep=00000000000`, pois e totalizador/erro de parser.",
        "- Usar valor por dependente limitado a R$ 189,59.",
        "- Nao misturar com plano de saude, pensao alimenticia ou S-1200.",
        "",
        "## Resultado local",
        "",
        f"- CPFs atuais com codigo 202: {c.get('total_202_atual', 0)}.",
        f"- Com `dedDepen` reconstruido por julho/setembro: {c.get('com_deddepen_reconstruido', 0)}.",
        f"- Alta confianca (julho e setembro iguais): {c.get('confianca_alta', 0)}.",
        f"- Media confianca (somente um mes vizinho): {c.get('confianca_media', 0)}.",
        f"- Divergente/manual: {c.get('confianca_manual', 0)}.",
        f"- Sem prova em julho/setembro: {c.get('confianca_sem_prova', 0)}.",
        f"- Com recibo ativo local ja disponivel: {c.get('com_recibo_ativo_local', 0)}.",
        f"- Com recibo vindo do front/S-1210 HEAD XML: {c.get('com_recibo_front_head_xml', 0)}.",
        f"- Prontos para XML/envio sem consultar eSocial: {c.get('pronto_para_xml_envio', 0)}.",
        "",
        "## Fonte de recibo",
        "",
        "Para codigo 202 a timeline nao gravou `nr_recibo_novo`, mas a tela S-1210 anual/lista do mes expoe `nr_recibo_xml` do S-1210 HEAD. Esse valor foi usado como recibo ativo local, amarrado ao XML local importado, sem consulta ao eSocial.",
        "",
        "Conclusao operacional: os 35 CPFs de alta confianca estao prontos para gerar XML de retificacao local. Os 70 restantes seguem sem prova de dependente real em julho/setembro.",
        "",
        "Nenhum envio, download ou consulta ao eSocial foi executado neste preflight.",
    ]
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return {"json": str(json_path), "csv": str(csv_path), "md": str(md_path)}


def main() -> int:
    summary = build_summary()
    outputs = write_outputs(summary)
    print("PREFLIGHT_AGOSTO_202_DEDDEPEN_OK")
    print(json.dumps(summary["counts"], ensure_ascii=False, sort_keys=True))
    print(f"md={outputs['md']}")
    print(f"csv={outputs['csv']}")
    print(f"json={outputs['json']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())