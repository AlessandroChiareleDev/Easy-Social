from __future__ import annotations

import json
import re
import sys
from datetime import datetime, timezone
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
BASE_DIR = ROOT / "relatorio_ana" / "CORRECAO_AGOSTO_202_DEDDEPEN"
ORIGINAL_MANIFEST = BASE_DIR / "manifest_reenvio_original_agosto_202.json"
OUT_DIR = BASE_DIR / "xml_retificacao_espelho_agosto_202_unsigned"
MANIFEST = BASE_DIR / "manifest_retificacao_espelho_agosto_202.json"
RECIBOS_CORRETOS_XLSX = ROOT / "relatorio_ana" / "RECIBOS_CORRETOS_35_SOLUCOES_AGOSTO_459.xlsx"


def digits(value: Any) -> str:
    return re.sub(r"\D", "", str(value or ""))


def text(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "").strip())


def cpf11(value: Any) -> str:
    raw = text(value)
    if re.fullmatch(r"\d+\.0", raw):
        raw = raw[:-2]
    only_digits = digits(raw)
    return only_digits.zfill(11) if only_digits else ""


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


def children(node: Any, tag: str) -> list[Any]:
    return node.xpath(f'./*[local-name()="{tag}"]')


def child_text(node: Any, tag: str) -> str:
    found = children(node, tag)
    return text(found[0].text) if found else ""


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


def make_event_id(root: Any, seq: int) -> str:
    evt = root.xpath('//*[local-name()="evtPgtos"]')[0]
    ide_emp = evt.xpath('./*[local-name()="ideEmpregador"]')[0]
    tp_insc = child_text(ide_emp, "tpInsc") or "1"
    nr_insc = digits(child_text(ide_emp, "nrInsc")).ljust(14, "0")[:14]
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    return f"ID{tp_insc}{nr_insc}{stamp}{seq:05d}"


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
            for cpf, receipt, status, code, envio_id, item_id in cur.fetchall():
                receipt = text(receipt)
                if receipt.startswith("1.1."):
                    out[str(cpf)] = {
                        "recibo": receipt,
                        "fonte": f"timeline_envio_item:{envio_id}/{item_id}:{status}:{code}",
                    }
            return out
    finally:
        conn.close()


def load_xlsx_receipt_overrides() -> dict[str, dict[str, str]]:
    if not RECIBOS_CORRETOS_XLSX.exists():
        return {}
    import pandas as pd

    df = pd.read_excel(RECIBOS_CORRETOS_XLSX)
    if "Recibo correto" not in df.columns:
        raise RuntimeError(f"planilha sem coluna 'Recibo correto': {RECIBOS_CORRETOS_XLSX}")
    cpf_column = "CPF normalizado" if "CPF normalizado" in df.columns else "CPF"
    if cpf_column not in df.columns:
        raise RuntimeError(f"planilha sem coluna CPF: {RECIBOS_CORRETOS_XLSX}")
    out: dict[str, dict[str, str]] = {}
    for _, row in df.iterrows():
        cpf = cpf11(row.get(cpf_column))
        receipt = text(row.get("Recibo correto"))
        if len(cpf) == 11 and receipt.startswith("1.1."):
            out[cpf] = {"recibo": receipt, "fonte": RECIBOS_CORRETOS_XLSX.name}
    return out


def prepare_retification_bytes(xml_bytes_in: bytes, receipt: str, seq: int) -> tuple[bytes, dict[str, Any]]:
    parser = etree.XMLParser(remove_blank_text=True, recover=False, huge_tree=True)
    root = etree.fromstring(xml_bytes_in, parser=parser)

    for signature in root.xpath('//*[local-name()="Signature"]'):
        parent = signature.getparent()
        if parent is not None:
            parent.remove(signature)

    evt = root.xpath('//*[local-name()="evtPgtos"]')[0]
    old_id = evt.get("Id") or ""
    new_id = make_event_id(root, seq)
    evt.set("Id", new_id)

    ide_evento = evt.xpath('./*[local-name()="ideEvento"]')[0]
    old_ind_retif = child_text(ide_evento, "indRetif")
    set_direct_child(root, ide_evento, "indRetif", "2")
    set_direct_child(root, ide_evento, "nrRecibo", receipt, after_tag="indRetif")

    return etree.tostring(root, xml_declaration=True, encoding="UTF-8", pretty_print=False), {
        "source_event_id": old_id,
        "id_evento": new_id,
        "source_indRetif": old_ind_retif,
        "indRetif": "2",
        "nrRecibo": receipt,
    }


def prepare_retification(item: dict[str, Any], receipt: str, seq: int) -> tuple[bytes, dict[str, Any]]:
    return prepare_retification_bytes(Path(item["evento_assinado_xml"]).read_bytes(), receipt, seq)


def load_latest_sent_xmls(cpfs: list[str]) -> dict[str, dict[str, Any]]:
    internal = tenant.internal_empresa_id(EMPRESA_ID)
    conn = db.connect(empresa_id=EMPRESA_ID)
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT DISTINCT ON (it.cpf)
                       it.cpf, it.xml_enviado_oid, it.nr_recibo_anterior, it.status, it.erro_codigo, te.id AS envio_id, it.id AS item_id
                  FROM timeline_envio_item it
                  JOIN timeline_envio te ON te.id = it.timeline_envio_id
                  JOIN timeline_mes tm ON tm.id = te.timeline_mes_id
                 WHERE tm.empresa_id = %s
                   AND tm.per_apur = %s
                   AND it.tipo_evento = 'S-1210'
                   AND it.cpf = ANY(%s)
                   AND it.xml_enviado_oid IS NOT NULL
                 ORDER BY it.cpf, it.criado_em DESC NULLS LAST, it.id DESC
                """,
                (internal, PER_APUR, cpfs),
            )
            rows = cur.fetchall()
        out: dict[str, dict[str, Any]] = {}
        for cpf, oid, nr_recibo_anterior, status, code, envio_id, item_id in rows:
            lo = conn.lobject(int(oid), mode="rb")
            try:
                xml_bytes = lo.read()
            finally:
                lo.close()
            out[str(cpf)] = {
                "xml_bytes": bytes(xml_bytes),
                "nr_recibo_anterior": text(nr_recibo_anterior),
                "fonte": f"timeline_envio_item_xml:{envio_id}/{item_id}:{status}:{code}",
            }
        return out
    finally:
        conn.close()


def main() -> None:
    original = json.loads(ORIGINAL_MANIFEST.read_text(encoding="utf-8"))
    targets = original.get("targets") or []
    if len(targets) != 105:
        raise RuntimeError(f"esperado 105 alvos no manifesto original; encontrado {len(targets)}")
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for path in OUT_DIR.glob("*_S1210_2025-08_*_retificacao_espelho_unsigned.xml"):
        path.unlink()

    cpfs = [item["cpf"] for item in targets]
    xlsx_receipts = load_xlsx_receipt_overrides()
    timeline_receipts = load_latest_timeline_receipts(cpfs)
    manifest_targets: list[dict[str, Any]] = []
    failures: list[dict[str, str]] = []
    for seq, item in enumerate(sorted(targets, key=lambda row: row["cpf"]), start=1):
        cpf = item["cpf"]
        override = xlsx_receipts.get(cpf) or timeline_receipts.get(cpf)
        receipt = override["recibo"] if override else item.get("source_nrRecibo")
        receipt_source = override["fonte"] if override else "source_nrRecibo_original_zip_ativo_local"
        if not receipt or not str(receipt).startswith("1.1."):
            failures.append({"cpf": cpf, "erro": "sem_nrRecibo_para_retificacao"})
            continue
        xml_out, meta = prepare_retification(item, receipt, seq)
        out_path = OUT_DIR / f"{seq:03d}_S1210_2025-08_{cpf}_retificacao_espelho_unsigned.xml"
        out_path.write_bytes(xml_out)
        manifest_targets.append({
            "cpf": cpf,
            "xml": str(out_path),
            "id_evento": meta["id_evento"],
            "source_event_id": meta["source_event_id"],
            "source_indRetif": meta["source_indRetif"],
            "indRetif": meta["indRetif"],
            "nrRecibo": meta["nrRecibo"],
            "nrRecibo_fonte": receipt_source,
            "source_zip": item.get("source_zip"),
            "source_entry": item.get("source_entry"),
            "source_cdResposta": item.get("source_cdResposta"),
            "source_protocolo": item.get("source_protocolo"),
            "conteudo": "espelho_do_original; apenas Id, indRetif e nrRecibo alterados; Signature removida para reassinar",
        })

    manifest_cpfs = {item["cpf"] for item in manifest_targets}
    missing_xlsx_cpfs = sorted(set(xlsx_receipts) - manifest_cpfs)
    latest_sent_xmls = load_latest_sent_xmls(missing_xlsx_cpfs) if missing_xlsx_cpfs else {}
    for cpf in missing_xlsx_cpfs:
        sent = latest_sent_xmls.get(cpf)
        if not sent:
            failures.append({"cpf": cpf, "erro": "cpf_da_planilha_sem_xml_no_manifesto_e_sem_xml_enviado_no_banco"})
            continue
        receipt = xlsx_receipts[cpf]["recibo"]
        seq = len(manifest_targets) + 1
        xml_out, meta = prepare_retification_bytes(sent["xml_bytes"], receipt, seq)
        out_path = OUT_DIR / f"{seq:03d}_S1210_2025-08_{cpf}_retificacao_espelho_unsigned.xml"
        out_path.write_bytes(xml_out)
        manifest_targets.append({
            "cpf": cpf,
            "xml": str(out_path),
            "id_evento": meta["id_evento"],
            "source_event_id": meta["source_event_id"],
            "source_indRetif": meta["source_indRetif"],
            "indRetif": meta["indRetif"],
            "nrRecibo": meta["nrRecibo"],
            "nrRecibo_fonte": RECIBOS_CORRETOS_XLSX.name,
            "source_zip": None,
            "source_entry": sent["fonte"],
            "source_cdResposta": None,
            "source_protocolo": None,
            "source_nrRecibo_anterior": sent["nr_recibo_anterior"],
            "conteudo": "espelho_do_xml_enviado_anterior; apenas Id, indRetif e nrRecibo alterados; Signature removida para reassinar",
        })

    manifest = {
        "empresa_id": EMPRESA_ID,
        "per_apur": PER_APUR,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "tipo": "retificacao_espelho_dos_originais_202",
        "sem_consulta_esocial": True,
        "regra": "Basear no XML original aceito com 202; manter conteudo; trocar Id, indRetif=2 e nrRecibo; remover Signature para assinatura nova no envio.",
        "fonte_manifesto_original": str(ORIGINAL_MANIFEST),
        "xml_dir": str(OUT_DIR),
        "total_alvos_originais": len(targets),
        "total_alvos": len(manifest_targets),
        "total_xmls": len(manifest_targets),
        "total_falhas": len(failures),
        "recibos_xlsx_override": sum(1 for item in manifest_targets if item["nrRecibo_fonte"] == RECIBOS_CORRETOS_XLSX.name),
        "recibos_timeline_override": sum(1 for item in manifest_targets if str(item["nrRecibo_fonte"]).startswith("timeline_envio_item:")),
        "failures": failures,
        "targets": manifest_targets,
    }
    MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print("PREPARAR_RETIFICACAO_ESPELHO_AGOSTO_202_SOLUCOES_OK")
    print(json.dumps({
        "total_alvos": manifest["total_alvos"],
        "total_xmls": manifest["total_xmls"],
        "total_falhas": manifest["total_falhas"],
        "recibos_xlsx_override": manifest["recibos_xlsx_override"],
        "recibos_timeline_override": manifest["recibos_timeline_override"],
        "manifest": str(MANIFEST),
        "xml_dir": str(OUT_DIR),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()