from __future__ import annotations

import argparse
import json
import re
import sys
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
CONFIRM_TOKEN = "REENVIAR_060_MENSAL_1938"
ZIP_PATH = Path(r"C:\Users\xandao\Downloads\todos os meses 2025 SOLUCOES\SOLUCOES_2025-05(01-15).zip")
ENTRY = "ID1094455020000002025050916075329069.S-1210.xml"
OUT_DIR = ROOT / "relatorio_ana" / "CORRECAO_JAQUE_RECIBOS_2025" / "ajuste_060_724"
XML_DIR = OUT_DIR / "xml_unsigned"
MANIFEST = OUT_DIR / "manifest_ajuste_060_724.json"


def only_digits(value: Any) -> str:
    return re.sub(r"\D", "", str(value or ""))


def text(node: etree._Element, tag: str) -> str:
    return str(node.xpath(f'string(.//*[local-name()="{tag}"])') or "").strip()


def set_direct_text(parent: etree._Element, tag: str, value: str) -> None:
    nodes = parent.xpath(f'./*[local-name()="{tag}"]')
    if not nodes:
        raise RuntimeError(f"tag ausente: {tag}")
    nodes[0].text = value


def remove_direct_child(parent: etree._Element, tag: str) -> None:
    for child in list(parent):
        if etree.QName(child).localname == tag:
            parent.remove(child)


def latest_row(conn) -> dict[str, Any]:
    internal_empresa_id = tenant.internal_empresa_id(EMPRESA_ID)
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
        cursor.execute(
            """
            SELECT DISTINCT ON (tm.per_apur, it.cpf)
                   tm.per_apur, it.cpf, it.status, it.erro_codigo, it.erro_mensagem,
                   it.id AS item_id, te.id AS envio_id, it.versao_anterior_id,
                   it.nr_recibo_anterior, it.nr_recibo_novo, it.criado_em
              FROM timeline_envio_item it
              JOIN timeline_envio te ON te.id = it.timeline_envio_id
              JOIN timeline_mes tm ON tm.id = te.timeline_mes_id
             WHERE tm.empresa_id = %s
               AND tm.per_apur = %s
               AND it.tipo_evento = 'S-1210'
               AND it.cpf = %s
             ORDER BY tm.per_apur, it.cpf, it.criado_em DESC NULLS LAST, it.id DESC
            """,
            (internal_empresa_id, PER_APUR, CPF),
        )
        row = cursor.fetchone()
    if not row:
        raise RuntimeError("latest ausente")
    return dict(row)


def source_xml() -> bytes:
    with zipfile.ZipFile(ZIP_PATH) as archive:
        return archive.read(ENTRY)


def prepare_xml(latest: dict[str, Any]) -> tuple[bytes, dict[str, Any]]:
    inner = reenvio_base.inner_s1210(source_xml())
    event_node = inner.xpath('./*[local-name()="evtPgtos"]')[0]
    if only_digits(text(event_node, "cpfBenef")) != CPF or text(event_node, "perApur") != PER_APUR:
        raise RuntimeError("XML fonte divergente")
    tp_insc = int(text(event_node, "tpInsc"))
    nr_insc = text(event_node, "nrInsc")
    event_node.set("Id", _gerar_id(tp_insc, nr_insc))
    ide_evento = event_node.xpath('./*[local-name()="ideEvento"]')[0]
    reenvio_base.set_child(ide_evento, "indRetif", "1")
    remove_direct_child(ide_evento, "nrRecibo")

    kept: list[dict[str, str]] = []
    removed: list[dict[str, str]] = []
    for info_pgto in list(event_node.xpath('.//*[local-name()="infoPgto"]')):
        ide_dmdev = text(info_pgto, "ideDmDev")
        vr_liq = text(info_pgto, "vrLiq") or text(info_pgto, "vlrLiq")
        dt_pgto = text(info_pgto, "dtPgto")
        if ide_dmdev == "1.101.1938MENSA":
            kept.append({"from": ide_dmdev, "to": ide_dmdev, "dtPgto": dt_pgto, "vrLiq": vr_liq})
            continue
        parent = info_pgto.getparent()
        if parent is not None:
            parent.remove(info_pgto)
        removed.append({"ideDmDev": ide_dmdev, "dtPgto": dt_pgto, "vrLiq": vr_liq})

    for signature in inner.xpath('.//*[local-name()="Signature"]'):
        parent = signature.getparent()
        if parent is not None:
            parent.remove(signature)

    if len(kept) != 1:
        raise RuntimeError(f"esperado manter 1 infoPgto mensal; mantidos={kept}")
    remaining = [text(node, "ideDmDev") for node in event_node.xpath('.//*[local-name()="infoPgto"]')]
    xml_new = etree.tostring(inner, xml_declaration=True, encoding="UTF-8", pretty_print=False)
    return xml_new, {
        "cpf": CPF,
        "per_apur": PER_APUR,
        "new_id": event_node.get("Id"),
        "indRetif": text(event_node, "indRetif"),
        "nrRecibo": text(event_node, "nrRecibo"),
        "kept": kept,
        "removed": removed,
        "remaining_ideDmDev": remaining,
        "latest_envio_id": latest.get("envio_id"),
        "latest_item_id": latest.get("item_id"),
        "latest_status": latest.get("status"),
        "latest_codigo": latest.get("erro_codigo"),
    }


def generate_manifest() -> dict[str, Any]:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    XML_DIR.mkdir(parents=True, exist_ok=True)
    conn = db.connect(empresa_id=EMPRESA_ID)
    try:
        latest = latest_row(conn)
    finally:
        conn.close()
    xml_new, meta = prepare_xml(latest)
    xml_path = XML_DIR / "S1210_2025-04_06042642405_ajuste_724_unsigned.xml"
    xml_path.write_bytes(xml_new)
    manifest = {
        "empresa_id": EMPRESA_ID,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "total": 1,
        "regra": "reenviar inclusao S-1210 CPF 06042642405 ajustando ideDmDev mensal para S-1200 ativo e removendo feria sem S-1200 ativo",
        "targets": [
            {
                "per_apur": PER_APUR,
                "cpf": CPF,
                "xml": str(xml_path),
                "evento_id": latest.get("versao_anterior_id"),
                "nr_recibo": None,
                "id_evento": meta["new_id"],
                "validation": meta,
            }
        ],
    }
    MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    return manifest


def sign_target(target: dict[str, Any]) -> dict[str, Any]:
    xml_assinado = S1010XMLSigner.assinar(Path(target["xml"]).read_bytes(), envio_base.DEFAULT_CERT.read_bytes(), reenvio_base.read_password())
    signed_id = esocial_client._extrair_id(xml_assinado)
    if signed_id != target["id_evento"]:
        raise RuntimeError(f"Id assinado divergente: {signed_id}")
    return {**target, "xml_assinado": xml_assinado, "id_evento_assinado": signed_id}


def create_timeline(conn) -> tuple[int, int]:
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
            (month_id, sequence, psycopg2.extras.Json({"rotulo": "reenviar_06042642405_s1210_ajustado", "manifest": str(MANIFEST)})),
        )
        envio_id = int(cursor.fetchone()["id"])
    conn.commit()
    return envio_id, month_id


def execute() -> dict[str, Any]:
    manifest = generate_manifest()
    signed = [sign_target(manifest["targets"][0])]
    senha = reenvio_base.read_password()
    conn_db = db.connect(empresa_id=EMPRESA_ID)
    conn_w = db.connect(empresa_id=EMPRESA_ID)
    try:
        envio_id, month_id = create_timeline(conn_db)
        print(f"=> ajuste 724 CPF 060: envio_id={envio_id} timeline_mes={month_id}")
        item_ids = envio_base._criar_items(conn_db, envio_id, signed)
        envio_base._persistir_xmls_assinados(conn_db, conn_w, signed, item_ids)
        result = envio_base._processar_lote(signed, item_ids, cert_path=envio_base.DEFAULT_CERT, senha=senha, cnpj=CNPJ, conn_db=conn_db, conn_w=conn_w)
        envio_base._atualizar_envio(
            conn_db,
            envio_id,
            status="concluido",
            sucesso=int(result["sucesso"]),
            erro=int(result["erro"]),
            resumo_extra={"protocolos": [result.get("protocolo")], "histograma_erros": result.get("histograma") or {}, "manifest": str(MANIFEST)},
        )
        return {"envio_id": envio_id, **result, "manifest": str(MANIFEST)}
    finally:
        conn_db.close()
        conn_w.close()


def dry_run() -> dict[str, Any]:
    manifest = generate_manifest()
    target = manifest["targets"][0]
    return {"ok": True, "target": target["validation"], "manifest": str(MANIFEST)}


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