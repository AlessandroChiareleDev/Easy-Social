from __future__ import annotations

import csv
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from lxml import etree


ROOT = Path(r"C:\Users\xandao\Documents\GitHub\Easy-Social")
BACKEND = Path(r"C:\Users\xandao\Documents\GitHub\Easy-eSocial-v2\backend")
if str(ROOT / "python-scripts") not in sys.path:
    sys.path.insert(0, str(ROOT / "python-scripts"))
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from app import db  # noqa: E402
from preparar_correcao_agosto_202_deddepen import (  # noqa: E402
    CPF_ZERO,
    EMPRESA_ID,
    OUT_DIR,
    PER_APUR,
    cpf11,
    child_text,
    children,
    load_event_rows,
    read_xml_event,
    text,
)


SUMMARY_PATH = OUT_DIR / "preflight_agosto_202_deddepen.json"
XML_DIR = OUT_DIR / "xml_correcao_202_deddepen_unsigned"
MANIFEST_JSON = OUT_DIR / "manifest_correcao_202_deddepen.json"
MANIFEST_CSV = OUT_DIR / "manifest_correcao_202_deddepen.csv"


def local_name(node: Any) -> str:
    return etree.QName(node).localname


def namespace(root: Any) -> str:
    evt = root.xpath('//*[local-name()="evtPgtos"]')
    if evt:
        ns = etree.QName(evt[0]).namespace
        if ns:
            return ns
    return root.nsmap.get(None) or "http://www.esocial.gov.br/schema/evt/evtPgtos/v_S_01_03_00"


def qname(root: Any, tag: str) -> str:
    return f"{{{namespace(root)}}}{tag}"


def sub(root: Any, parent: Any, tag: str, value: Any = None) -> Any:
    node = etree.Element(qname(root, tag))
    if value is not None:
        node.text = str(value)
    parent.append(node)
    return node


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
    nr_insc = re.sub(r"\D", "", child_text(ide_emp, "nrInsc") or "")
    nr_insc = nr_insc.ljust(14, "0")[:14]
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    return f"ID{tp_insc}{nr_insc}{stamp}{seq:05d}"


def wanted_info_deps(item: dict[str, Any], dependent_cpfs: set[str]) -> list[dict[str, str]]:
    out: dict[str, dict[str, str]] = {}
    for month in ("2025-09", "2025-07"):
        prova = (item.get("provas") or {}).get(month) or {}
        for info_dep in prova.get("infoDep") or []:
            cpf_dep = cpf11(info_dep.get("cpfDep"))
            if cpf_dep in dependent_cpfs and cpf_dep not in out:
                cleaned = {"cpfDep": cpf_dep}
                for tag in ("dtNascto", "nome", "depIRRF", "tpDep", "descrDep"):
                    value = text(info_dep.get(tag))
                    if value:
                        cleaned[tag] = value
                out[cpf_dep] = cleaned
    return list(out.values())


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
                child.text = str(value)
                node.append(child)
        info_ir.insert(insert_at + offset, node)
    return len(to_insert)


def replace_ded_depen(root: Any, item: dict[str, Any]) -> tuple[int, list[str]]:
    evt = root.xpath('//*[local-name()="evtPgtos"]')
    if not evt:
        raise ValueError("evtPgtos nao encontrado")
    ide_benef = evt[0].xpath('./*[local-name()="ideBenef"]')
    if not ide_benef:
        raise ValueError("ideBenef nao encontrado")
    info_nodes = ide_benef[0].xpath('./*[local-name()="infoIRComplem"]')
    if not info_nodes:
        raise ValueError("infoIRComplem nao encontrado no XML atual")
    info_ir = info_nodes[0]

    corrections = item.get("dedDepen_corrigir") or []
    by_tpcr: dict[str, list[dict[str, str]]] = {}
    for correction in corrections:
        by_tpcr.setdefault(correction["tpCR"], []).append(correction)
    dependent_cpfs = {correction["cpfDep"] for correction in corrections}
    info_dep_inserted = insert_missing_info_deps(root, info_ir, wanted_info_deps(item, dependent_cpfs))

    inserted = 0
    touched_tpcr: set[str] = set()
    for info_ircr in children(info_ir, "infoIRCR"):
        tp_cr = child_text(info_ircr, "tpCR")
        wanted = by_tpcr.get(tp_cr) or []
        if not wanted:
            continue
        touched_tpcr.add(tp_cr)
        for old_ded in list(children(info_ircr, "dedDepen")):
            info_ircr.remove(old_ded)

        insert_at = len(info_ircr)
        for index, child in enumerate(info_ircr):
            if local_name(child) == "penAlim":
                insert_at = index
                break
        for offset, correction in enumerate(wanted):
            ded = etree.Element(qname(root, "dedDepen"))
            for tag in ("tpRend", "cpfDep", "vlrDedDep"):
                child = etree.Element(qname(root, tag))
                child.text = str(correction[tag])
                ded.append(child)
            info_ircr.insert(insert_at + offset, ded)
            inserted += 1

    missing_tpcr = sorted(set(by_tpcr) - touched_tpcr)
    notes = [f"infoDep_inseridos={info_dep_inserted}"]
    if missing_tpcr:
        notes.append(f"tpCR_sem_infoIRCR={','.join(missing_tpcr)}")
    return inserted, notes


def prepare_xml(xml_bytes: bytes, item: dict[str, Any], seq: int) -> tuple[bytes, dict[str, Any]]:
    parser = etree.XMLParser(remove_blank_text=True)
    parsed_root = etree.fromstring(xml_bytes, parser=parser)
    evt_src = parsed_root.xpath('//*[local-name()="evtPgtos"]')
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
    set_direct_child(root, ide_evento, "nrRecibo", item["recibo_ativo_local"], after_tag="indRetif")
    inserted, notes = replace_ded_depen(root, item)

    zeros = root.xpath('//*[local-name()="dedDepen"]/*[local-name()="cpfDep" and text()=$cpf]', cpf=CPF_ZERO)
    if zeros:
        raise ValueError("cpfDep zero permaneceu em dedDepen")
    if inserted != len(item.get("dedDepen_corrigir") or []):
        raise ValueError(f"dedDepen inseridos {inserted}, esperado {len(item.get('dedDepen_corrigir') or [])}")

    xml_out = etree.tostring(root, xml_declaration=True, encoding="UTF-8", pretty_print=False)
    return xml_out, {"id_evento": new_id, "ded_count": inserted, "notes": notes}


def load_targets() -> list[dict[str, Any]]:
    summary = json.loads(SUMMARY_PATH.read_text(encoding="utf-8"))
    targets = []
    for item in summary.get("evidence") or []:
        if item.get("confianca") != "alta":
            continue
        if not item.get("dedDepen_corrigir"):
            continue
        if not item.get("tem_recibo_ativo_local"):
            continue
        targets.append(item)
    return sorted(targets, key=lambda row: row["cpf"])


def main() -> int:
    targets = load_targets()
    XML_DIR.mkdir(parents=True, exist_ok=True)
    for old_file in XML_DIR.glob("*.xml"):
        old_file.unlink()

    event_rows = load_event_rows([item["cpf"] for item in targets], PER_APUR)
    manifest: list[dict[str, Any]] = []
    conn = db.connect(empresa_id=EMPRESA_ID)
    try:
        for seq, item in enumerate(targets, start=1):
            cpf = cpf11(item["cpf"])
            event = event_rows.get(cpf)
            if not event:
                raise RuntimeError(f"S-1210 HEAD nao encontrado para {cpf}")
            xml_bytes = read_xml_event(conn, event)
            xml_out, meta = prepare_xml(xml_bytes, item, seq)
            out_path = XML_DIR / f"S1210_{PER_APUR}_{cpf}_dedDepen202_unsigned.xml"
            out_path.write_bytes(xml_out)
            manifest.append({
                "cpf": cpf,
                "xml": str(out_path),
                "id_evento": meta["id_evento"],
                "recibo_ativo": item["recibo_ativo_local"],
                "recibo_fonte": item.get("recibo_fonte_local"),
                "ded_count": meta["ded_count"],
                "dependentes": item["dedDepen_corrigir"],
                "source_event_id": event.get("id_evento"),
                "source_recibo": event.get("nr_recibo"),
                "source_zip": event.get("zip_nome"),
                "notes": meta["notes"],
            })
    finally:
        conn.close()

    MANIFEST_JSON.write_text(json.dumps({
        "empresa_id": EMPRESA_ID,
        "per_apur": PER_APUR,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "total_xmls": len(manifest),
        "xml_dir": str(XML_DIR),
        "targets": manifest,
    }, ensure_ascii=False, indent=2), encoding="utf-8")

    with MANIFEST_CSV.open("w", encoding="utf-8", newline="") as handle:
        fieldnames = ["cpf", "recibo_ativo", "ded_count", "dependentes", "xml", "id_evento", "source_recibo", "notes"]
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for item in manifest:
            writer.writerow({
                "cpf": item["cpf"],
                "recibo_ativo": item["recibo_ativo"],
                "ded_count": item["ded_count"],
                "dependentes": "; ".join(
                    f"{dep['tpCR']}/{dep['tpRend']}/{dep['cpfDep']}/{dep['vlrDedDep']}"
                    for dep in item["dependentes"]
                ),
                "xml": item["xml"],
                "id_evento": item["id_evento"],
                "source_recibo": item["source_recibo"],
                "notes": "; ".join(item["notes"]),
            })

    print("GERAR_CORRECAO_AGOSTO_202_DEDDEPEN_OK")
    print(json.dumps({"total_xmls": len(manifest), "xml_dir": str(XML_DIR)}, ensure_ascii=False, sort_keys=True))
    print(f"manifest_json={MANIFEST_JSON}")
    print(f"manifest_csv={MANIFEST_CSV}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())