from __future__ import annotations

import argparse
import json
import re
import sys
import time
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Any

import psycopg2.extras
from lxml import etree


ROOT = Path(r"C:\Users\xandao\Documents\GitHub\Easy-Social")
BACKEND_V2 = Path(r"C:\Users\xandao\Documents\GitHub\Easy-eSocial-v2\backend")
if str(ROOT / "python-scripts") not in sys.path:
    sys.path.insert(0, str(ROOT / "python-scripts"))
if str(BACKEND_V2) not in sys.path:
    sys.path.insert(0, str(BACKEND_V2))

import enviar_correcao_agosto_jaque as envio_base  # noqa: E402
import reenviar_agosto_sem_mudanca_solucoes as reenvio_base  # noqa: E402
from app import db, esocial_client, tenant  # noqa: E402
from app.xml_s1210 import _gerar_id  # noqa: E402
from app.xml_signer import S1010XMLSigner  # noqa: E402


EMPRESA_ID = 2
CNPJ = "09445502000109"
PER_APUR = "2025-04"
CPF = "06042642405"
CONFIRM_TOKEN = "REENVIAR_060_S1200_S1210"
ZIP_PATH = Path(r"C:\Users\xandao\Downloads\todos os meses 2025 SOLUCOES\SOLUCOES_2025-05(01-15).zip")
S1200_ENTRY = "ID1094455020000002025050719102010280.S-1200.xml"
S1210_ENTRY = "ID1094455020000002025050916075329069.S-1210.xml"
OUT_DIR = ROOT / "relatorio_ana" / "CORRECAO_JAQUE_RECIBOS_2025" / "cpf_060_s1200_s1210"
XML_DIR = OUT_DIR / "xml_unsigned"
MANIFEST = OUT_DIR / "manifest_060_s1200_s1210.json"


def only_digits(value: Any) -> str:
    return re.sub(r"\D", "", str(value or ""))


def text(node: etree._Element, tag: str) -> str:
    return str(node.xpath(f'string(.//*[local-name()="{tag}"])') or "").strip()


def texts(node: etree._Element, tag: str) -> list[str]:
    return [str(v).strip() for v in node.xpath(f'.//*[local-name()="{tag}"]/text()') if str(v).strip()]


def direct_text(node: etree._Element, tag: str) -> str:
    return str(node.xpath(f'string(./*[local-name()="{tag}"])') or "").strip()


def set_direct_text(parent: etree._Element, tag: str, value: str) -> None:
    nodes = parent.xpath(f'./*[local-name()="{tag}"]')
    if not nodes:
        raise RuntimeError(f"tag direta ausente: {tag}")
    nodes[0].text = value


def remove_direct_child(parent: etree._Element, tag: str) -> None:
    for child in list(parent):
        if etree.QName(child).localname == tag:
            parent.remove(child)


def read_zip(entry: str) -> bytes:
    with zipfile.ZipFile(ZIP_PATH) as archive:
        return archive.read(entry)


def inner_event(xml_bytes: bytes, event_tag: str) -> etree._Element:
    parser = etree.XMLParser(remove_blank_text=True, recover=True, huge_tree=True)
    root = etree.fromstring(xml_bytes, parser=parser)
    candidates = root.xpath(f'//*[local-name()="eSocial" and ./*[local-name()="{event_tag}"]]')
    if not candidates:
        raise RuntimeError(f"eSocial/{event_tag} nao encontrado")
    inner = etree.fromstring(etree.tostring(candidates[0]), parser=parser)
    for signature in inner.xpath('.//*[local-name()="Signature"]'):
        parent = signature.getparent()
        if parent is not None:
            parent.remove(signature)
    return inner


def prepare_s1200() -> tuple[bytes, dict[str, Any]]:
    inner = inner_event(read_zip(S1200_ENTRY), "evtRemun")
    event_node = inner.xpath('./*[local-name()="evtRemun"]')[0]
    if only_digits(text(event_node, "cpfTrab")) != CPF or text(event_node, "perApur") != PER_APUR:
        raise RuntimeError("S-1200 fonte divergente")
    old_id = event_node.get("Id") or ""
    event_node.set("Id", _gerar_id(int(text(event_node, "tpInsc")), text(event_node, "nrInsc")))
    ide_evento = event_node.xpath('./*[local-name()="ideEvento"]')[0]
    reenvio_base.set_child(ide_evento, "indRetif", "1")
    remove_direct_child(ide_evento, "nrRecibo")
    ide_dmdev = texts(event_node, "ideDmDev")
    xml_new = etree.tostring(inner, xml_declaration=True, encoding="UTF-8", pretty_print=False)
    return xml_new, {"tipo_evento": "S-1200", "cpf": CPF, "per_apur": PER_APUR, "old_id": old_id, "new_id": event_node.get("Id"), "ideDmDev": ide_dmdev, "indRetif": text(event_node, "indRetif"), "nrRecibo": text(event_node, "nrRecibo")}


def prepare_s1210() -> tuple[bytes, dict[str, Any]]:
    inner = inner_event(read_zip(S1210_ENTRY), "evtPgtos")
    event_node = inner.xpath('./*[local-name()="evtPgtos"]')[0]
    if only_digits(text(event_node, "cpfBenef")) != CPF or text(event_node, "perApur") != PER_APUR:
        raise RuntimeError("S-1210 fonte divergente")
    old_id = event_node.get("Id") or ""
    event_node.set("Id", _gerar_id(int(text(event_node, "tpInsc")), text(event_node, "nrInsc")))
    ide_evento = event_node.xpath('./*[local-name()="ideEvento"]')[0]
    reenvio_base.set_child(ide_evento, "indRetif", "1")
    remove_direct_child(ide_evento, "nrRecibo")
    mapped: list[dict[str, str]] = []
    for info_pgto in event_node.xpath('.//*[local-name()="infoPgto"]'):
        ide_dmdev = direct_text(info_pgto, "ideDmDev")
        if ide_dmdev == "1.101.1938MENSA":
            set_direct_text(info_pgto, "ideDmDev", "1.101.2234MENSA")
            mapped.append({"from": ide_dmdev, "to": "1.101.2234MENSA", "dtPgto": text(info_pgto, "dtPgto"), "vrLiq": text(info_pgto, "vrLiq")})
        else:
            mapped.append({"from": ide_dmdev, "to": ide_dmdev, "dtPgto": text(info_pgto, "dtPgto"), "vrLiq": text(info_pgto, "vrLiq")})
    xml_new = etree.tostring(inner, xml_declaration=True, encoding="UTF-8", pretty_print=False)
    return xml_new, {"tipo_evento": "S-1210", "cpf": CPF, "per_apur": PER_APUR, "old_id": old_id, "new_id": event_node.get("Id"), "mapped": mapped, "ideDmDev": texts(event_node, "ideDmDev"), "vrLiq": texts(event_node, "vrLiq"), "indRetif": text(event_node, "indRetif"), "nrRecibo": text(event_node, "nrRecibo")}


def generate_manifest() -> dict[str, Any]:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    XML_DIR.mkdir(parents=True, exist_ok=True)
    s1200_xml, s1200_meta = prepare_s1200()
    s1210_xml, s1210_meta = prepare_s1210()
    s1200_path = XML_DIR / "S1200_2025-04_06042642405_reinclusao_unsigned.xml"
    s1210_path = XML_DIR / "S1210_2025-04_06042642405_reinclusao_unsigned.xml"
    s1200_path.write_bytes(s1200_xml)
    s1210_path.write_bytes(s1210_xml)
    manifest = {
        "empresa_id": EMPRESA_ID,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "regra": "reenviar S-1200 original e depois S-1210 original alinhado ao S-1200 para CPF 06042642405",
        "targets": [
            {"tipo_evento": "S-1200", "per_apur": PER_APUR, "cpf": CPF, "xml": str(s1200_path), "evento_id": None, "nr_recibo": None, "id_evento": s1200_meta["new_id"], "validation": s1200_meta},
            {"tipo_evento": "S-1210", "per_apur": PER_APUR, "cpf": CPF, "xml": str(s1210_path), "evento_id": None, "nr_recibo": None, "id_evento": s1210_meta["new_id"], "validation": s1210_meta},
        ],
    }
    MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    return manifest


def sign_target(target: dict[str, Any], senha: str) -> dict[str, Any]:
    xml_assinado = S1010XMLSigner.assinar(Path(target["xml"]).read_bytes(), envio_base.DEFAULT_CERT.read_bytes(), senha)
    signed_id = esocial_client._extrair_id(xml_assinado)
    if signed_id != target["id_evento"]:
        raise RuntimeError(f"Id assinado divergente: {signed_id}")
    return {**target, "xml_assinado": xml_assinado, "id_evento_assinado": signed_id}


def create_timeline(conn, tipo_evento: str) -> tuple[int, int]:
    internal_empresa_id = tenant.internal_empresa_id(EMPRESA_ID)
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
        cursor.execute("SELECT id FROM timeline_mes WHERE empresa_id=%s AND per_apur=%s", (internal_empresa_id, PER_APUR))
        month_id = int(cursor.fetchone()["id"])
        cursor.execute("SELECT COALESCE(MAX(sequencia), 0)+1 AS prox FROM timeline_envio WHERE timeline_mes_id=%s", (month_id,))
        sequence = int(cursor.fetchone()["prox"])
        cursor.execute(
            """
            INSERT INTO timeline_envio
              (timeline_mes_id, sequencia, tipo, status, iniciado_em, total_tentados, total_sucesso, total_erro, resumo)
            VALUES (%s, %s, 'envio_massa', 'em_andamento', now(), 1, 0, 0, %s)
            RETURNING id
            """,
            (month_id, sequence, psycopg2.extras.Json({"rotulo": "reenviar_060_s1200_e_s1210", "tipo_evento": tipo_evento, "manifest": str(MANIFEST)})),
        )
        envio_id = int(cursor.fetchone()["id"])
    conn.commit()
    return envio_id, month_id


def create_item(conn, envio_id: int, target: dict[str, Any]) -> dict[str, int]:
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
        cursor.execute(
            """
            INSERT INTO timeline_envio_item
              (timeline_envio_id, cpf, tipo_evento, status, versao_anterior_id, nr_recibo_anterior, xml_enviado_oid)
            VALUES (%s, %s, %s, 'pendente', %s, %s, NULL)
            RETURNING id
            """,
            (envio_id, target["cpf"], target["tipo_evento"], target.get("evento_id"), target.get("nr_recibo")),
        )
        item_id = int(cursor.fetchone()["id"])
    conn.commit()
    return {target["cpf"]: item_id}


def process_one(conn_db, conn_w, target: dict[str, Any], senha: str) -> dict[str, Any]:
    envio_id, month_id = create_timeline(conn_db, target["tipo_evento"])
    print(f"=> {target['tipo_evento']} CPF 060 envio_id={envio_id} timeline_mes={month_id}")
    item_ids = create_item(conn_db, envio_id, target)
    envio_base._persistir_xmls_assinados(conn_db, conn_w, [target], item_ids)
    result = envio_base._processar_lote([target], item_ids, cert_path=envio_base.DEFAULT_CERT, senha=senha, cnpj=CNPJ, conn_db=conn_db, conn_w=conn_w)
    envio_base._atualizar_envio(conn_db, envio_id, status="concluido", sucesso=int(result["sucesso"]), erro=int(result["erro"]), resumo_extra={"protocolos": [result.get("protocolo")], "histograma_erros": result.get("histograma") or {}, "manifest": str(MANIFEST)})
    return {"tipo_evento": target["tipo_evento"], "envio_id": envio_id, **result}


def execute() -> dict[str, Any]:
    manifest = generate_manifest()
    senha = reenvio_base.read_password()
    signed = [sign_target(target, senha) for target in manifest["targets"]]
    conn_db = db.connect(empresa_id=EMPRESA_ID)
    conn_w = db.connect(empresa_id=EMPRESA_ID)
    results: list[dict[str, Any]] = []
    try:
        first = process_one(conn_db, conn_w, signed[0], senha)
        results.append(first)
        if int(first["sucesso"]) != 1:
            return {"manifest": str(MANIFEST), "results": results, "stopped": "S-1200 nao aceito"}
        time.sleep(2)
        results.append(process_one(conn_db, conn_w, signed[1], senha))
    finally:
        conn_db.close()
        conn_w.close()
    return {"manifest": str(MANIFEST), "results": results}


def dry_run() -> dict[str, Any]:
    manifest = generate_manifest()
    return {"ok": True, "targets": [{"tipo_evento": item["tipo_evento"], **item["validation"]} for item in manifest["targets"]], "manifest": str(MANIFEST)}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--confirmar", default="")
    args = parser.parse_args()
    if not args.execute:
        print(json.dumps(dry_run(), ensure_ascii=False, indent=2, default=str))
        return 0
    if args.confirmar != CONFIRM_TOKEN:
        raise SystemExit(f"Para executar, use --confirmar {CONFIRM_TOKEN}")
    print(json.dumps(execute(), ensure_ascii=False, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())