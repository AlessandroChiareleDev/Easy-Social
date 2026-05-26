from __future__ import annotations

import csv
import json
import re
import sys
import zipfile
from collections import defaultdict
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

from lxml import etree


ROOT = Path(r"C:\Users\xandao\Documents\GitHub\Easy-Social")
BACKEND = Path(r"C:\Users\xandao\Documents\GitHub\Easy-eSocial-v2\backend")
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from app import db, tenant  # noqa: E402


EMPRESA_ID = 2
PER_APUR = "2025-08"
DTPGTO_TARGET = "2025-08"
PROOF_MONTHS = ("2025-07", "2025-09")
ALL_DTPGTO_MONTHS = ("2025-07", "2025-08", "2025-09")
VALOR_PADRAO = Decimal("189.59")
CPF_ZERO = "00000000000"

ZIP_DIR = Path.home() / "Downloads" / "todos os meses 2025 SOLUCOES"
ZIP_NAMES = {
    "2025-07": ["SOLUCOES_2025-08(01-15).zip", "SOLUCOES_2025-08(16-31).zip"],
    "2025-08": ["SOLUCOES_2025-09(01-15).zip", "SOLUCOES_2025-09(16-30).zip"],
    "2025-09": ["SOLUCOES_2025-10(01-15).zip", "SOLUCOES_2025-10(16-31).zip"],
}

OUT_DIR = ROOT / "relatorio_ana" / "CORRECAO_AGOSTO_202_DEDDEPEN"
PREFLIGHT = OUT_DIR / "preflight_agosto_202_deddepen.json"
REPORT_JSON = OUT_DIR / "resolvedor_quinzenais_dtpgto_agosto_202_deddepen.json"
REPORT_CSV = OUT_DIR / "resolvedor_quinzenais_dtpgto_agosto_202_deddepen.csv"
MANIFEST_JSON = OUT_DIR / "manifest_correcao_202_deddepen_quinzenais.json"
MANIFEST_CSV = OUT_DIR / "manifest_correcao_202_deddepen_quinzenais.csv"
XML_DIR = OUT_DIR / "xml_correcao_202_deddepen_quinzenais_unsigned"
ALL_YEAR_PROOF_JSON = OUT_DIR / "provas_ano_todo_deddepen_reais_202.json"


def text(value: Any) -> str:
    if value is None:
        return ""
    return re.sub(r"\s+", " ", str(value).strip())


def digits(value: Any) -> str:
    return re.sub(r"\D", "", text(value))


def cpf11(value: Any) -> str:
    raw = digits(value)
    return raw.zfill(11) if raw else ""


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


def local_name(node: Any) -> str:
    return etree.QName(node).localname


def children(node: Any, tag: str) -> list[Any]:
    return node.xpath(f'./*[local-name()="{tag}"]')


def child_text(node: Any, tag: str) -> str:
    found = children(node, tag)
    return text(found[0].text) if found else ""


def xtexts(node: Any, expr: str) -> list[str]:
    return [text(item) for item in node.xpath(expr) if text(item)]


def first_xtext(node: Any, expr: str) -> str:
    values = xtexts(node, expr)
    return values[0] if values else ""


def namespace(root: Any) -> str:
    evt = root.xpath('//*[local-name()="evtPgtos"]')
    if evt:
        ns = etree.QName(evt[0]).namespace
        if ns:
            return ns
    return root.nsmap.get(None) or "http://www.esocial.gov.br/schema/evt/evtPgtos/v_S_01_03_00"


def qname(root: Any, tag: str) -> str:
    return f"{{{namespace(root)}}}{tag}"


def set_direct_child(root: Any, parent: Any, tag: str, value: str, after_tag: str | None = None) -> Any:
    found = children(parent, tag)
    if found:
        found[0].text = value
        return found[0]
    node = etree.Element(qname(root, tag))
    node.text = value
    insert_at = 0
    if after_tag:
        for index, child in enumerate(parent):
            if local_name(child) == after_tag:
                insert_at = index + 1
                break
    parent.insert(insert_at, node)
    return node


def event_id(root: Any, seq: int) -> str:
    evt = root.xpath('//*[local-name()="evtPgtos"]')[0]
    ide_emp = evt.xpath('./*[local-name()="ideEmpregador"]')[0]
    tp_insc = child_text(ide_emp, "tpInsc") or "1"
    nr_insc = digits(child_text(ide_emp, "nrInsc"))
    nr_insc = nr_insc.ljust(14, "0")[:14]
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    return f"ID{tp_insc}{nr_insc}{stamp}{seq:05d}"


def load_targets() -> dict[str, dict[str, Any]]:
    data = json.loads(PREFLIGHT.read_text(encoding="utf-8"))
    out: dict[str, dict[str, Any]] = {}
    for item in data.get("evidence") or []:
        cpf = cpf11(item.get("cpf"))
        if len(cpf) == 11 and item.get("erro_codigo") == "202":
            out[cpf] = item
    if not out:
        raise RuntimeError(f"nenhum alvo 202 encontrado em {PREFLIGHT}")
    return dict(sorted(out.items()))


def load_receipt_overrides() -> dict[str, dict[str, str]]:
    out: dict[str, dict[str, str]] = {}
    for path in sorted((ROOT / "relatorio_ana").glob("AGOSTO_202_ACTIVE_RECIBOS*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        if not isinstance(data, dict):
            continue
        for cpf_raw, receipt_raw in data.items():
            cpf = cpf11(cpf_raw)
            receipt = text(receipt_raw)
            if len(cpf) == 11 and receipt.startswith("1.1."):
                out[cpf] = {"recibo": receipt, "fonte": path.name}

    test_path = OUT_DIR / "teste_recibo_override" / "resultado_teste_recibo_02254091786.json"
    if test_path.exists():
        data = json.loads(test_path.read_text(encoding="utf-8"))
        for item in data.get("items") or []:
            cpf = cpf11(item.get("cpf"))
            receipt = text(item.get("nr_recibo_novo"))
            if len(cpf) == 11 and receipt.startswith("1.1."):
                out[cpf] = {"recibo": receipt, "fonte": test_path.name}
    return out


def load_latest_timeline_receipts(cpfs: list[str]) -> dict[str, dict[str, str]]:
    internal = tenant.internal_empresa_id(EMPRESA_ID)
    conn = db.connect(empresa_id=EMPRESA_ID)
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT DISTINCT ON (it.cpf)
                       it.cpf, it.nr_recibo_novo, it.status, it.erro_codigo, te.id AS envio_id, it.id AS item_id
                  FROM timeline_envio_item it
                  JOIN timeline_envio te ON te.id = it.timeline_envio_id
                  JOIN timeline_mes tm ON tm.id = te.timeline_mes_id
                 WHERE tm.empresa_id = %s
                   AND tm.per_apur = %s
                   AND it.tipo_evento = 'S-1210'
                   AND it.cpf = ANY(%s)
                   AND it.nr_recibo_novo IS NOT NULL
                   AND it.nr_recibo_novo <> ''
                 ORDER BY it.cpf, it.criado_em DESC NULLS LAST, it.id DESC
                """,
                (internal, PER_APUR, cpfs),
            )
            out: dict[str, dict[str, str]] = {}
            for cpf_raw, receipt, status, code, envio_id, item_id in cur.fetchall():
                cpf = cpf11(cpf_raw)
                if receipt and text(receipt).startswith("1.1."):
                    out[cpf] = {
                        "recibo": text(receipt),
                        "fonte": f"timeline_envio_item:{envio_id}/{item_id}:{status}:{code}",
                    }
            return out
    finally:
        conn.close()


def cpf_regex(target_cpfs: set[str]) -> re.Pattern[bytes]:
    return re.compile(b"(?:" + b"|".join(re.escape(cpf.encode()) for cpf in sorted(target_cpfs)) + b")")


def receipt_from_download(root: Any) -> str:
    candidates = xtexts(root, './/*[local-name()="retornoEvento"]//*[local-name()="recibo"]/*[local-name()="nrRecibo"]/text()')
    if candidates:
        return candidates[-1]
    candidates = xtexts(root, './/*[local-name()="recibo"]//*[local-name()="nrRecibo"]/text()')
    if candidates:
        return candidates[-1]
    return ""


def extract_ir(evt: Any) -> dict[str, Any]:
    info_nodes = evt.xpath('.//*[local-name()="ideBenef"]/*[local-name()="infoIRComplem"]')
    if not info_nodes:
        return {"infoDep": [], "dedDepen": [], "ded_zero": []}
    info = info_nodes[0]
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
    zeros: list[dict[str, str]] = []
    for ircr in children(info, "infoIRCR"):
        tp_cr = child_text(ircr, "tpCR")
        for node in children(ircr, "dedDepen"):
            item = {
                "tpCR": tp_cr,
                "tpRend": child_text(node, "tpRend") or "11",
                "cpfDep": cpf11(child_text(node, "cpfDep")),
                "vlrDedDep": money_str(money(child_text(node, "vlrDedDep"))),
            }
            if item["cpfDep"] == CPF_ZERO:
                zeros.append(item)
            elif len(item["cpfDep"]) == 11 and money(item["vlrDedDep"]) > 0:
                deds.append(item)
    return {"infoDep": info_deps, "dedDepen": deds, "ded_zero": zeros}


def parse_s1210(xml_bytes: bytes, zip_name: str, entry: str) -> list[dict[str, Any]]:
    root = etree.fromstring(xml_bytes, parser=etree.XMLParser(recover=True, huge_tree=True))
    rows: list[dict[str, Any]] = []
    for evt in root.xpath('//*[local-name()="evtPgtos"]'):
        cpf = cpf11(first_xtext(evt, './*[local-name()="ideBenef"]/*[local-name()="cpfBenef"]/text()'))
        if len(cpf) != 11:
            continue
        ir = extract_ir(evt)
        rows.append({
            "cpf": cpf,
            "zip": zip_name,
            "entry": entry,
            "id_evento": evt.get("Id") or "",
            "indRetif": first_xtext(evt, './*[local-name()="ideEvento"]/*[local-name()="indRetif"]/text()'),
            "nrReciboRetificado": first_xtext(evt, './*[local-name()="ideEvento"]/*[local-name()="nrRecibo"]/text()'),
            "perApur": first_xtext(evt, './*[local-name()="ideEvento"]/*[local-name()="perApur"]/text()'),
            "dtPgtos": sorted(set(xtexts(evt, './/*[local-name()="infoPgto"]/*[local-name()="dtPgto"]/text()'))),
            "perRefs": sorted(set(xtexts(evt, './/*[local-name()="infoPgto"]/*[local-name()="perRef"]/text()'))),
            "nrRecibo": receipt_from_download(root),
            "cdResposta": first_xtext(root, './/*[local-name()="retornoEvento"]//*[local-name()="cdResposta"]/text()') or first_xtext(root, './/*[local-name()="cdResposta"]/text()'),
            "dhProcessamento": first_xtext(root, './/*[local-name()="processamento"]/*[local-name()="dhProcessamento"]/text()'),
            "protocolo": first_xtext(root, './/*[local-name()="protocoloEnvioLote"]/text()'),
            "infoDep": ir["infoDep"],
            "dedDepen": ir["dedDepen"],
            "ded_zero": ir["ded_zero"],
            "xml_bytes": xml_bytes,
        })
    return rows


def parse_s3000(xml_bytes: bytes, zip_name: str, entry: str) -> list[dict[str, str]]:
    root = etree.fromstring(xml_bytes, parser=etree.XMLParser(recover=True, huge_tree=True))
    if not root.xpath('//*[local-name()="evtExclusao"]'):
        return []
    return [{
        "zip": zip_name,
        "entry": entry,
        "cpf": cpf11(first_xtext(root, './/*[local-name()="cpfTrab"]/text()')),
        "nrRecEvt": first_xtext(root, './/*[local-name()="nrRecEvt"]/text()'),
        "nrReciboS3000": receipt_from_download(root),
        "cdResposta": first_xtext(root, './/*[local-name()="retornoEvento"]//*[local-name()="cdResposta"]/text()') or first_xtext(root, './/*[local-name()="cdResposta"]/text()'),
        "dhProcessamento": first_xtext(root, './/*[local-name()="processamento"]/*[local-name()="dhProcessamento"]/text()'),
    }]


def scan_zips(target_cpfs: set[str]) -> tuple[dict[str, dict[str, list[dict[str, Any]]]], dict[str, list[dict[str, str]]], list[dict[str, Any]]]:
    target_re = cpf_regex(target_cpfs)
    events: dict[str, dict[str, list[dict[str, Any]]]] = {month: defaultdict(list) for month in ALL_DTPGTO_MONTHS}
    deletions_by_receipt: dict[str, list[dict[str, str]]] = defaultdict(list)
    stats: list[dict[str, Any]] = []

    for dt_month, names in ZIP_NAMES.items():
        for zip_name in names:
            path = ZIP_DIR / zip_name
            if not path.exists():
                raise FileNotFoundError(path)
            stat = {"zip": zip_name, "s1210_entries": 0, "s3000_entries": 0, "target_s1210_raw_hits": 0, "target_events": 0, "s3000_deletions": 0}
            with zipfile.ZipFile(path) as zf:
                for info in zf.infolist():
                    if not info.filename.endswith(".xml"):
                        continue
                    is_s1210 = "S-1210" in info.filename
                    is_s3000 = "S-3000" in info.filename
                    if not is_s1210 and not is_s3000:
                        continue
                    data = zf.read(info)
                    if is_s1210:
                        stat["s1210_entries"] += 1
                        if not target_re.search(data):
                            continue
                        stat["target_s1210_raw_hits"] += 1
                        for row in parse_s1210(data, zip_name, info.filename):
                            if row["cpf"] not in target_cpfs:
                                continue
                            for month in ALL_DTPGTO_MONTHS:
                                if any(dt.startswith(month) for dt in row["dtPgtos"]):
                                    events[month][row["cpf"]].append(row)
                                    stat["target_events"] += 1
                    elif is_s3000:
                        stat["s3000_entries"] += 1
                        if not target_re.search(data):
                            continue
                        for row in parse_s3000(data, zip_name, info.filename):
                            if row["cpf"] in target_cpfs and row["nrRecEvt"]:
                                deletions_by_receipt[row["nrRecEvt"]].append(row)
                                stat["s3000_deletions"] += 1
            stats.append(stat)
    return events, deletions_by_receipt, stats


def scan_all_year_real_deds(target_cpfs: set[str]) -> dict[str, dict[str, list[dict[str, Any]]]]:
    target_re = cpf_regex(target_cpfs)
    proofs: dict[str, dict[str, list[dict[str, Any]]]] = defaultdict(lambda: defaultdict(list))
    for path in sorted(ZIP_DIR.glob("SOLUCOES_*.zip")):
        with zipfile.ZipFile(path) as zf:
            for info in zf.infolist():
                if not info.filename.endswith(".xml") or "S-1210" not in info.filename:
                    continue
                data = zf.read(info)
                if not target_re.search(data):
                    continue
                for row in parse_s1210(data, path.name, info.filename):
                    if row["cpf"] not in target_cpfs or not row.get("dedDepen"):
                        continue
                    grouped: dict[tuple[str, str], set[str]] = defaultdict(set)
                    for item in row["dedDepen"]:
                        dep = cpf11(item.get("cpfDep"))
                        if len(dep) == 11 and dep != CPF_ZERO:
                            grouped[(item["tpCR"], item["tpRend"])].add(dep)
                    for (tp_cr, tp_rend), cpfs in grouped.items():
                        if not cpfs:
                            continue
                        proofs[row["cpf"]][f"{tp_cr}|{tp_rend}"].append({
                            "zip": row["zip"],
                            "entry": row["entry"],
                            "dtPgtos": row["dtPgtos"],
                            "perApur": row["perApur"],
                            "nrRecibo": row["nrRecibo"],
                            "cdResposta": row["cdResposta"],
                            "dhProcessamento": row["dhProcessamento"],
                            "cpfs": sorted(cpfs),
                        })
    return {cpf: dict(groups) for cpf, groups in proofs.items()}


def active_event(rows: list[dict[str, Any]], deletions_by_receipt: dict[str, list[dict[str, str]]]) -> tuple[dict[str, Any] | None, list[dict[str, Any]], list[dict[str, Any]]]:
    active: list[dict[str, Any]] = []
    deleted: list[dict[str, Any]] = []
    for row in rows:
        if row.get("nrRecibo") and row["nrRecibo"] in deletions_by_receipt:
            deleted.append(row)
        else:
            active.append(row)
    if not active:
        return None, active, deleted
    return sorted(active, key=lambda item: (item.get("dhProcessamento") or "", item.get("entry") or ""))[-1], active, deleted


def group_values(active: dict[str, Any]) -> dict[tuple[str, str], dict[str, Any]]:
    groups: dict[tuple[str, str], dict[str, Any]] = defaultdict(lambda: {
        "zero_amount": Decimal("0.00"),
        "real_amount": Decimal("0.00"),
        "real_cpfs": set(),
    })
    for item in active.get("ded_zero") or []:
        groups[(item["tpCR"], item["tpRend"])]["zero_amount"] += money(item["vlrDedDep"])
    for item in active.get("dedDepen") or []:
        key = (item["tpCR"], item["tpRend"])
        groups[key]["real_amount"] += money(item["vlrDedDep"])
        groups[key]["real_cpfs"].add(cpf11(item["cpfDep"]))
    return {
        key: {
            "zero_amount": value["zero_amount"].quantize(Decimal("0.01")),
            "real_amount": value["real_amount"].quantize(Decimal("0.01")),
            "real_cpfs": sorted(cpf for cpf in value["real_cpfs"] if cpf and cpf != CPF_ZERO),
        }
        for key, value in groups.items()
        if value["zero_amount"] > 0 or value["real_amount"] > 0
    }


def real_cpfs_by_group(active: dict[str, Any] | None) -> dict[tuple[str, str], list[str]]:
    out: dict[tuple[str, str], set[str]] = defaultdict(set)
    if not active:
        return {}
    for item in active.get("dedDepen") or []:
        cpf = cpf11(item.get("cpfDep"))
        if len(cpf) == 11 and cpf != CPF_ZERO:
            out[(item["tpCR"], item["tpRend"])].add(cpf)
    return {key: sorted(value) for key, value in out.items()}


def info_deps_for_cpfs(*events: dict[str, Any] | None, wanted: set[str]) -> list[dict[str, str]]:
    out: dict[str, dict[str, str]] = {}
    for event in events:
        if not event:
            continue
        for item in event.get("infoDep") or []:
            cpf = cpf11(item.get("cpfDep"))
            if cpf in wanted and cpf not in out:
                cleaned = {"cpfDep": cpf}
                for tag in ("dtNascto", "nome", "depIRRF", "tpDep", "descrDep"):
                    value = text(item.get(tag))
                    if value:
                        cleaned[tag] = value
                out[cpf] = cleaned
    return list(out.values())


def expected_count(amount: Decimal) -> tuple[int | None, str]:
    if amount <= 0:
        return None, "valor_zero"
    quotient = (amount / VALOR_PADRAO).quantize(Decimal("0.0001"))
    as_int = int(quotient)
    if quotient != Decimal(as_int):
        return None, f"valor_nao_multiplo:{money_str(amount)}"
    return as_int, "ok"


def expected_count_for_group(group: dict[str, Any]) -> tuple[int | None, str, str]:
    real_cpfs = group.get("real_cpfs") or []
    zero_amount = group.get("zero_amount") or Decimal("0.00")
    real_amount = group.get("real_amount") or Decimal("0.00")
    if real_cpfs:
        basis = "cpfs_reais_no_alvo" if zero_amount == 0 else "cpfs_reais_no_alvo_remover_zero"
        return len(real_cpfs), "ok", basis
    if zero_amount > 0 and not real_cpfs:
        count, status = expected_count(zero_amount)
        return count, status, "valor_zero_totalizador"
    return expected_count(real_amount) + ("valor_real_sem_cpfs",)


def choose_cpfs_for_group(
    key: tuple[str, str],
    count: int,
    target_reals: dict[tuple[str, str], list[str]],
    july_reals: dict[tuple[str, str], list[str]],
    sep_reals: dict[tuple[str, str], list[str]],
    year_records: list[dict[str, Any]],
) -> tuple[str, list[str], str]:
    target = target_reals.get(key) or []
    july = july_reals.get(key) or []
    sep = sep_reals.get(key) or []

    if len(july) == count and len(sep) == count and july == sep:
        return "alta", sep, "julho_setembro_iguais"
    if len(target) == count:
        return "target_real", target, "cpf_real_no_proprio_evento"
    if len(sep) == count and not july:
        return "media", sep, "somente_setembro"
    if len(july) == count and not sep:
        return "media", july, "somente_julho"
    if len(july) == count and len(sep) == count and july != sep:
        return "manual", [], "julho_setembro_divergentes"

    year_sets: dict[tuple[str, ...], list[dict[str, Any]]] = defaultdict(list)
    for record in year_records:
        cpfs = tuple(record.get("cpfs") or [])
        if len(cpfs) == count:
            year_sets[cpfs].append(record)
    if year_sets:
        best_cpfs, records = sorted(
            year_sets.items(),
            key=lambda item: (len(item[1]), max((r.get("dhProcessamento") or "") for r in item[1])),
            reverse=True,
        )[0]
        if len(records) >= 2:
            return "ano_multiplo", list(best_cpfs), f"ano_todo_{len(records)}_ocorrencias"
        return "ano_unico", list(best_cpfs), "ano_todo_1_ocorrencia"

    union = sorted(set(target) | set(july) | set(sep))
    if len(union) == count and union:
        return "manual", union, "uniao_bate_mas_fontes_nao_confirmam"
    return "pendente", [], f"esperado_{count}_cpfs_encontrado_{len(union)}"


def insert_missing_info_deps(root: Any, info_ir: Any, info_deps: list[dict[str, str]]) -> int:
    existing = {cpf11(child_text(node, "cpfDep")) for node in children(info_ir, "infoDep")}
    to_insert = [item for item in info_deps if item["cpfDep"] not in existing]
    if not to_insert:
        return 0
    insert_at = len(info_ir)
    for index, child in enumerate(info_ir):
        if local_name(child) in {"infoIRCR", "planSaude"}:
            insert_at = index
            break
    for offset, item in enumerate(to_insert):
        node = etree.Element(qname(root, "infoDep"))
        for tag in ("cpfDep", "dtNascto", "nome", "depIRRF", "tpDep", "descrDep"):
            value = item.get(tag)
            if value:
                child = etree.Element(qname(root, tag))
                child.text = value
                node.append(child)
        info_ir.insert(insert_at + offset, node)
    return len(to_insert)


def replace_ded_depen(root: Any, corrections: list[dict[str, str]], info_deps: list[dict[str, str]]) -> tuple[int, list[str]]:
    evt = root.xpath('//*[local-name()="evtPgtos"]')
    if not evt:
        raise ValueError("evtPgtos nao encontrado")
    ide_benef = evt[0].xpath('./*[local-name()="ideBenef"]')
    if not ide_benef:
        raise ValueError("ideBenef nao encontrado")
    info_nodes = ide_benef[0].xpath('./*[local-name()="infoIRComplem"]')
    if not info_nodes:
        raise ValueError("infoIRComplem nao encontrado")
    info_ir = info_nodes[0]
    info_dep_inserted = insert_missing_info_deps(root, info_ir, info_deps)

    by_group: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for item in corrections:
        by_group[(item["tpCR"], item["tpRend"])].append(item)

    inserted = 0
    touched: set[tuple[str, str]] = set()
    for info_ircr in children(info_ir, "infoIRCR"):
        tp_cr = child_text(info_ircr, "tpCR")
        group_corrections = [item for key, values in by_group.items() if key[0] == tp_cr for item in values]
        if not group_corrections:
            continue
        touched.update((item["tpCR"], item["tpRend"]) for item in group_corrections)
        for old_ded in list(children(info_ircr, "dedDepen")):
            info_ircr.remove(old_ded)
        insert_at = len(info_ircr)
        for index, child in enumerate(info_ircr):
            if local_name(child) == "penAlim":
                insert_at = index
                break
        for offset, item in enumerate(group_corrections):
            ded = etree.Element(qname(root, "dedDepen"))
            for tag in ("tpRend", "cpfDep", "vlrDedDep"):
                child = etree.Element(qname(root, tag))
                child.text = item[tag]
                ded.append(child)
            info_ircr.insert(insert_at + offset, ded)
            inserted += 1

    missing = sorted(set(by_group) - touched)
    notes = [f"infoDep_inseridos={info_dep_inserted}"]
    if missing:
        notes.append("grupos_sem_infoIRCR=" + ",".join(f"{tpcr}/{tpr}" for tpcr, tpr in missing))
    return inserted, notes


def prepare_xml(source_xml: bytes, receipt: str, corrections: list[dict[str, str]], info_deps: list[dict[str, str]], seq: int) -> tuple[bytes, dict[str, Any]]:
    parser = etree.XMLParser(remove_blank_text=True, recover=True, huge_tree=True)
    parsed = etree.fromstring(source_xml, parser=parser)
    evt_src = parsed.xpath('//*[local-name()="evtPgtos"]')
    if not evt_src:
        raise ValueError("evtPgtos nao encontrado")
    event_container = evt_src[0].getparent()
    if event_container is None or local_name(event_container) != "eSocial":
        raise ValueError("container eSocial do evtPgtos nao encontrado")
    root = etree.fromstring(etree.tostring(event_container), parser=parser)
    for signature in root.xpath('//*[local-name()="Signature"]'):
        parent = signature.getparent()
        if parent is not None:
            parent.remove(signature)
    evt = root.xpath('//*[local-name()="evtPgtos"]')[0]
    new_id = event_id(root, seq)
    evt.set("Id", new_id)
    ide_evento = evt.xpath('./*[local-name()="ideEvento"]')[0]
    set_direct_child(root, ide_evento, "indRetif", "2")
    set_direct_child(root, ide_evento, "nrRecibo", receipt, after_tag="indRetif")
    inserted, notes = replace_ded_depen(root, corrections, info_deps)
    zeros = root.xpath('//*[local-name()="dedDepen"]/*[local-name()="cpfDep" and text()=$cpf]', cpf=CPF_ZERO)
    if zeros:
        raise ValueError("cpfDep zero permaneceu em dedDepen")
    if inserted != len(corrections):
        raise ValueError(f"dedDepen inseridos {inserted}, esperado {len(corrections)}")
    return etree.tostring(root, xml_declaration=True, encoding="UTF-8", pretty_print=False), {
        "id_evento": new_id,
        "ded_count": inserted,
        "notes": notes,
    }


def build_report() -> tuple[dict[str, Any], list[dict[str, Any]]]:
    target_meta = load_targets()
    cpfs = list(target_meta)
    receipt_overrides = load_receipt_overrides()
    timeline_receipts = load_latest_timeline_receipts(cpfs)
    events_by_month, deletions_by_receipt, zip_stats = scan_zips(set(cpfs))
    year_proofs = scan_all_year_real_deds(set(cpfs))

    rows: list[dict[str, Any]] = []
    ready: list[dict[str, Any]] = []
    for cpf in cpfs:
        target, target_active_list, target_deleted = active_event(events_by_month[DTPGTO_TARGET].get(cpf, []), deletions_by_receipt)
        july, _, _ = active_event(events_by_month["2025-07"].get(cpf, []), deletions_by_receipt)
        sep, _, _ = active_event(events_by_month["2025-09"].get(cpf, []), deletions_by_receipt)

        problems: list[str] = []
        corrections: list[dict[str, str]] = []
        group_details: list[dict[str, Any]] = []

        if not target:
            problems.append("sem_s1210_ativo_dtpgto_2025_08")
        else:
            group_data = group_values(target)
            if not group_data:
                problems.append("sem_deddepen_no_alvo")
            target_reals = real_cpfs_by_group(target)
            july_reals = real_cpfs_by_group(july)
            sep_reals = real_cpfs_by_group(sep)

            for key, values in sorted(group_data.items()):
                count, count_status, count_basis = expected_count_for_group(values)
                detail: dict[str, Any] = {
                    "tpCR": key[0],
                    "tpRend": key[1],
                    "valor_zero": money_str(values["zero_amount"]),
                    "valor_real": money_str(values["real_amount"]),
                    "qtd_esperada": count,
                    "criterio_qtd": count_basis,
                    "target_cpfs": target_reals.get(key) or [],
                    "julho_cpfs": july_reals.get(key) or [],
                    "setembro_cpfs": sep_reals.get(key) or [],
                }
                if count is None:
                    problems.append(count_status)
                    detail["status"] = count_status
                    group_details.append(detail)
                    continue
                year_key = f"{key[0]}|{key[1]}"
                year_records = year_proofs.get(cpf, {}).get(year_key) or []
                confidence, chosen_cpfs, reason = choose_cpfs_for_group(key, count, target_reals, july_reals, sep_reals, year_records)
                detail.update({
                    "status": confidence,
                    "motivo": reason,
                    "cpfs_escolhidos": chosen_cpfs,
                    "provas_ano_todo_count": len(year_records),
                    "provas_ano_todo_amostra": year_records[:5],
                })
                group_details.append(detail)
                if confidence in {"alta", "target_real", "media", "ano_multiplo", "ano_unico"} and len(chosen_cpfs) == count:
                    for dep_cpf in chosen_cpfs:
                        corrections.append({
                            "tpCR": key[0],
                            "tpRend": key[1],
                            "cpfDep": dep_cpf,
                            "vlrDedDep": money_str(VALOR_PADRAO),
                        })
                else:
                    problems.append(f"grupo_{key[0]}_{key[1]}_{reason}")

        receipt_choice = None
        if cpf in receipt_overrides:
            receipt_choice = receipt_overrides[cpf]
        elif cpf in timeline_receipts:
            receipt_choice = timeline_receipts[cpf]
        elif target and target.get("nrRecibo"):
            receipt_choice = {"recibo": target["nrRecibo"], "fonte": "zip_quinzenal_cadeia_ativa"}
        else:
            problems.append("sem_recibo_ativo")

        info_deps = info_deps_for_cpfs(july, sep, target, wanted={item["cpfDep"] for item in corrections})
        row = {
            "cpf": cpf,
            "status": "pronto" if target and corrections and receipt_choice and not problems else "pendente",
            "problemas": problems,
            "recibo_ativo": (receipt_choice or {}).get("recibo", ""),
            "recibo_fonte": (receipt_choice or {}).get("fonte", ""),
            "target": {key: target.get(key) for key in ("zip", "entry", "id_evento", "indRetif", "perApur", "dtPgtos", "perRefs", "nrRecibo", "cdResposta", "dhProcessamento", "protocolo") if target} if target else {},
            "target_deleted_count": len(target_deleted),
            "target_active_candidates": len(target_active_list),
            "julho": {key: july.get(key) for key in ("zip", "entry", "id_evento", "dtPgtos", "nrRecibo", "cdResposta", "dhProcessamento") if july} if july else {},
            "setembro": {key: sep.get(key) for key in ("zip", "entry", "id_evento", "dtPgtos", "nrRecibo", "cdResposta", "dhProcessamento") if sep} if sep else {},
            "grupos": group_details,
            "dedDepen_corrigir": corrections,
            "infoDep_inserir": info_deps,
            "timeline_item": {"envio_id": target_meta[cpf].get("envio_id"), "item_id": target_meta[cpf].get("item_id")},
        }
        rows.append(row)
        if row["status"] == "pronto":
            ready.append({**row, "_source_xml": target["xml_bytes"]})

    counts = defaultdict(int)
    for row in rows:
        counts[f"status_{row['status']}"] += 1
        for problem in row["problemas"]:
            counts[f"problema_{problem}"] += 1
        for group in row["grupos"]:
            counts[f"grupo_{group.get('status')}"] += 1

    report = {
        "empresa_id": EMPRESA_ID,
        "per_apur": PER_APUR,
        "dtPgto_target": DTPGTO_TARGET,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "regra": {
            "valor_por_dependente": money_str(VALOR_PADRAO),
            "cpf_zero": CPF_ZERO,
            "fonte": str(ZIP_DIR),
            "zip_months": ZIP_NAMES,
            "criterio_evento_ativo": "S-1210 por dtPgto menos recibos excluidos por S-3000; escolher ultimo dhProcessamento ativo",
        },
        "zip_stats": zip_stats,
        "all_year_proof_file": str(ALL_YEAR_PROOF_JSON),
        "counts": {"total_alvos": len(rows), **dict(sorted(counts.items()))},
        "records": rows,
    }
    ALL_YEAR_PROOF_JSON.write_text(json.dumps(year_proofs, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    return report, ready


def write_outputs(report: dict[str, Any], ready: list[dict[str, Any]]) -> None:
    REPORT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    with REPORT_CSV.open("w", encoding="utf-8", newline="") as handle:
        fieldnames = ["cpf", "status", "problemas", "recibo_ativo", "recibo_fonte", "qtd_ded", "dependentes", "target_recibo", "target_zip", "target_entry"]
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in report["records"]:
            writer.writerow({
                "cpf": row["cpf"],
                "status": row["status"],
                "problemas": ";".join(row["problemas"]),
                "recibo_ativo": row["recibo_ativo"],
                "recibo_fonte": row["recibo_fonte"],
                "qtd_ded": len(row["dedDepen_corrigir"]),
                "dependentes": "; ".join(f"{d['tpCR']}/{d['tpRend']}/{d['cpfDep']}/{d['vlrDedDep']}" for d in row["dedDepen_corrigir"]),
                "target_recibo": row.get("target", {}).get("nrRecibo", ""),
                "target_zip": row.get("target", {}).get("zip", ""),
                "target_entry": row.get("target", {}).get("entry", ""),
            })

    XML_DIR.mkdir(parents=True, exist_ok=True)
    for old in XML_DIR.glob("*.xml"):
        old.unlink()

    manifest_targets: list[dict[str, Any]] = []
    for seq, row in enumerate(ready, start=1):
        xml_out, meta = prepare_xml(row["_source_xml"], row["recibo_ativo"], row["dedDepen_corrigir"], row["infoDep_inserir"], seq)
        out_path = XML_DIR / f"S1210_{PER_APUR}_{row['cpf']}_dedDepen202_quinzenais_unsigned.xml"
        out_path.write_bytes(xml_out)
        recibo_confiavel = row["recibo_fonte"] != "zip_quinzenal_cadeia_ativa"
        manifest_targets.append({
            "cpf": row["cpf"],
            "xml": str(out_path),
            "id_evento": meta["id_evento"],
            "recibo_ativo": row["recibo_ativo"],
            "recibo_fonte": row["recibo_fonte"],
            "envio_liberado_local": recibo_confiavel,
            "bloqueio_envio": "" if recibo_confiavel else "recibo_historico_zip_requer_reconsulta_ou_override",
            "ded_count": meta["ded_count"],
            "dependentes": row["dedDepen_corrigir"],
            "source_event_id": row["target"].get("id_evento"),
            "source_recibo": row["target"].get("nrRecibo"),
            "source_zip": row["target"].get("zip"),
            "source_entry": row["target"].get("entry"),
            "notes": meta["notes"],
        })

    MANIFEST_JSON.write_text(json.dumps({
        "empresa_id": EMPRESA_ID,
        "per_apur": PER_APUR,
        "dtPgto_target": DTPGTO_TARGET,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "total_xmls": len(manifest_targets),
        "total_envio_liberado_local": sum(1 for item in manifest_targets if item["envio_liberado_local"]),
        "total_bloqueado_recibo": sum(1 for item in manifest_targets if item["bloqueio_envio"]),
        "xml_dir": str(XML_DIR),
        "fonte_relatorio": str(REPORT_JSON),
        "targets": manifest_targets,
    }, ensure_ascii=False, indent=2, default=str), encoding="utf-8")

    with MANIFEST_CSV.open("w", encoding="utf-8", newline="") as handle:
        fieldnames = ["cpf", "recibo_ativo", "recibo_fonte", "envio_liberado_local", "bloqueio_envio", "ded_count", "dependentes", "xml", "id_evento", "source_recibo", "source_zip", "notes"]
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for item in manifest_targets:
            writer.writerow({
                "cpf": item["cpf"],
                "recibo_ativo": item["recibo_ativo"],
                "recibo_fonte": item["recibo_fonte"],
                "envio_liberado_local": item["envio_liberado_local"],
                "bloqueio_envio": item["bloqueio_envio"],
                "ded_count": item["ded_count"],
                "dependentes": "; ".join(f"{d['tpCR']}/{d['tpRend']}/{d['cpfDep']}/{d['vlrDedDep']}" for d in item["dependentes"]),
                "xml": item["xml"],
                "id_evento": item["id_evento"],
                "source_recibo": item["source_recibo"],
                "source_zip": item["source_zip"],
                "notes": "; ".join(item["notes"]),
            })


def main() -> int:
    report, ready = build_report()
    write_outputs(report, ready)
    print("RESOLVEDOR_CORRECAO_AGOSTO_202_DEDDEPEN_QUINZENAIS_OK")
    print(json.dumps(report["counts"], ensure_ascii=False, sort_keys=True))
    print(f"report_json={REPORT_JSON}")
    print(f"report_csv={REPORT_CSV}")
    print(f"manifest_json={MANIFEST_JSON}")
    print(f"manifest_csv={MANIFEST_CSV}")
    print(f"xml_dir={XML_DIR}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())