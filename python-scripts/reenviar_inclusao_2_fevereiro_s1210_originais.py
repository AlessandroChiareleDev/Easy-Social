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
PER_APUR = "2025-02"
CONFIRM_TOKEN = "REENVIAR_INCLUSAO_2_FEVEREIRO"
ZIP_PATH = Path(r"C:\Users\xandao\Downloads\todos os meses 2025 SOLUCOES\SOLUCOES_2025-03(01-15).zip")
OUT_DIR = ROOT / "relatorio_ana" / "CORRECAO_JAQUE_RECIBOS_2025" / "reinclusao_2_fevereiro"
XML_DIR = OUT_DIR / "xml_unsigned"
MANIFEST = OUT_DIR / "manifest_reinclusao_2_fevereiro.json"

TARGETS: list[dict[str, str]] = [
    {
        "cpf": "36832724810",
        "entry": "ID1094455020000002025030714514935064.S-1210.xml",
        "recibo_exclusao": "1.1.0000000031405347921",
    },
    {
        "cpf": "93564139249",
        "entry": "ID1094455020000002025030714072447183.S-1210.xml",
        "recibo_exclusao": "1.1.0000000031331770805",
    },
]


def only_digits(value: Any) -> str:
    return re.sub(r"\D", "", str(value or ""))


def text(node: etree._Element, tag: str) -> str:
    return str(node.xpath(f'string(.//*[local-name()="{tag}"])') or "").strip()


def direct_text(node: etree._Element, tag: str) -> str:
    return str(node.xpath(f'string(./*[local-name()="{tag}"])') or "").strip()


def remove_direct_child(parent: etree._Element, tag: str) -> None:
    for child in list(parent):
        if etree.QName(child).localname == tag:
            parent.remove(child)


def read_source(entry: str) -> bytes:
    with zipfile.ZipFile(ZIP_PATH) as archive:
        return archive.read(entry)


def latest_rows(conn) -> dict[str, dict[str, Any]]:
    internal_empresa_id = tenant.internal_empresa_id(EMPRESA_ID)
    cpfs = [item["cpf"] for item in TARGETS]
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
        cursor.execute(
            """
            SELECT DISTINCT ON (it.cpf)
                   tm.per_apur, it.cpf, it.status, it.erro_codigo, it.erro_mensagem,
                   it.id AS item_id, te.id AS envio_id, it.versao_anterior_id,
                   it.nr_recibo_anterior, it.nr_recibo_novo, it.criado_em
              FROM timeline_envio_item it
              JOIN timeline_envio te ON te.id = it.timeline_envio_id
              JOIN timeline_mes tm ON tm.id = te.timeline_mes_id
             WHERE tm.empresa_id = %s
               AND tm.per_apur = %s
               AND it.tipo_evento = 'S-1210'
               AND it.cpf = ANY(%s)
             ORDER BY it.cpf, it.criado_em DESC NULLS LAST, it.id DESC
            """,
            (internal_empresa_id, PER_APUR, cpfs),
        )
        rows = {row["cpf"]: dict(row) for row in cursor.fetchall()}
    missing = [cpf for cpf in cpfs if cpf not in rows]
    if missing:
        raise RuntimeError(f"latest ausente para CPFs: {missing}")
    return rows


def prepare_xml(target: dict[str, str], latest: dict[str, Any]) -> tuple[bytes, dict[str, Any]]:
    inner = reenvio_base.inner_s1210(read_source(target["entry"]))
    event_node = inner.xpath('./*[local-name()="evtPgtos"]')[0]
    cpf = only_digits(text(event_node, "cpfBenef"))
    per_apur = text(event_node, "perApur")
    if cpf != target["cpf"] or per_apur != PER_APUR:
        raise RuntimeError(f"XML fonte divergente: {per_apur}/{cpf}")
    if text(event_node, "tpAmb") != "1":
        raise RuntimeError(f"tpAmb divergente para {cpf}")

    old_id = event_node.get("Id") or ""
    event_node.set("Id", _gerar_id(int(text(event_node, "tpInsc")), text(event_node, "nrInsc")))
    ide_evento = event_node.xpath('./*[local-name()="ideEvento"]')[0]
    reenvio_base.set_child(ide_evento, "indRetif", "1")
    remove_direct_child(ide_evento, "nrRecibo")
    for signature in inner.xpath('.//*[local-name()="Signature"]'):
        parent = signature.getparent()
        if parent is not None:
            parent.remove(signature)
    info_pgto = []
    for info in event_node.xpath('.//*[local-name()="infoPgto"]'):
        info_pgto.append(
            {
                "perRef": direct_text(info, "perRef"),
                "ideDmDev": direct_text(info, "ideDmDev"),
                "dtPgto": direct_text(info, "dtPgto"),
                "vrLiq": direct_text(info, "vrLiq") or direct_text(info, "vlrLiq"),
            }
        )
    if not info_pgto:
        raise RuntimeError(f"S-1210 fonte sem infoPgto para {cpf}")
    xml_new = etree.tostring(inner, xml_declaration=True, encoding="UTF-8", pretty_print=False)
    return xml_new, {
        "cpf": cpf,
        "per_apur": per_apur,
        "source_zip": ZIP_PATH.name,
        "source_entry": target["entry"],
        "recibo_exclusao_informado": target["recibo_exclusao"],
        "old_id": old_id,
        "new_id": event_node.get("Id"),
        "indRetif": text(event_node, "indRetif"),
        "nrRecibo": text(event_node, "nrRecibo"),
        "infoPgto": info_pgto,
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
        latest = latest_rows(conn)
    finally:
        conn.close()
    targets: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    for index, target in enumerate(TARGETS, start=1):
        row = latest[target["cpf"]]
        if row.get("status") == "sucesso" and str(row.get("erro_codigo") or "") != "202":
            raise RuntimeError(f"CPF {target['cpf']} ja esta sucesso")
        xml_new, meta = prepare_xml(target, row)
        new_id = str(meta["new_id"])
        if new_id in seen_ids:
            raise RuntimeError(f"Id duplicado: {new_id}")
        seen_ids.add(new_id)
        xml_path = XML_DIR / f"S1210_{PER_APUR}_{target['cpf']}_reinclusao_unsigned.xml"
        xml_path.write_bytes(xml_new)
        targets.append(
            {
                "ordem": index,
                "per_apur": PER_APUR,
                "cpf": target["cpf"],
                "xml": str(xml_path),
                "evento_id": row.get("versao_anterior_id"),
                "nr_recibo": None,
                "id_evento": new_id,
                "validation": meta,
            }
        )
    manifest = {
        "empresa_id": EMPRESA_ID,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "total": len(targets),
        "regra": "reenviar os 2 S-1210 originais de fevereiro como inclusao sem nrRecibo",
        "targets": targets,
    }
    MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    return manifest


def sign_targets(targets: list[dict[str, Any]], senha: str) -> list[dict[str, Any]]:
    pfx_data = envio_base.DEFAULT_CERT.read_bytes()
    signed: list[dict[str, Any]] = []
    for target in targets:
        xml_assinado = S1010XMLSigner.assinar(Path(target["xml"]).read_bytes(), pfx_data, senha)
        signed_id = esocial_client._extrair_id(xml_assinado)
        if signed_id != target["id_evento"]:
            raise RuntimeError(f"Id assinado divergente para {target['cpf']}: {signed_id}")
        signed.append({**target, "xml_assinado": xml_assinado, "id_evento_assinado": signed_id})
    return signed


def create_timeline(conn, total: int) -> tuple[int, int]:
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
            VALUES (%s, %s, 'envio_massa', 'em_andamento', now(), %s, 0, 0, %s)
            RETURNING id
            """,
            (month_id, sequence, total, psycopg2.extras.Json({"rotulo": "reenviar_inclusao_2_fevereiro_s1210_originais", "manifest": str(MANIFEST)})),
        )
        envio_id = int(cursor.fetchone()["id"])
    conn.commit()
    return envio_id, month_id


def execute() -> dict[str, Any]:
    manifest = generate_manifest()
    signed = sign_targets(manifest["targets"], reenvio_base.read_password())
    conn_db = db.connect(empresa_id=EMPRESA_ID)
    conn_w = db.connect(empresa_id=EMPRESA_ID)
    try:
        envio_id, month_id = create_timeline(conn_db, len(signed))
        print(f"=> reinclusao fevereiro S-1210: envio_id={envio_id} timeline_mes={month_id} targets={len(signed)}")
        item_ids = envio_base._criar_items(conn_db, envio_id, signed)
        envio_base._persistir_xmls_assinados(conn_db, conn_w, signed, item_ids)
        result = envio_base._processar_lote(signed, item_ids, cert_path=envio_base.DEFAULT_CERT, senha=reenvio_base.read_password(), cnpj=CNPJ, conn_db=conn_db, conn_w=conn_w)
        envio_base._atualizar_envio(conn_db, envio_id, status="concluido", sucesso=int(result["sucesso"]), erro=int(result["erro"]), resumo_extra={"protocolos": [result.get("protocolo")], "histograma_erros": result.get("histograma") or {}, "manifest": str(MANIFEST)})
        return {"envio_id": envio_id, **result, "manifest": str(MANIFEST)}
    finally:
        conn_db.close()
        conn_w.close()


def dry_run() -> dict[str, Any]:
    manifest = generate_manifest()
    return {
        "ok": True,
        "total": manifest["total"],
        "targets": [
            {
                "cpf": target["cpf"],
                "indRetif": target["validation"]["indRetif"],
                "nrRecibo": target["validation"]["nrRecibo"],
                "infoPgto": target["validation"]["infoPgto"],
                "source_entry": target["validation"]["source_entry"],
            }
            for target in manifest["targets"]
        ],
        "manifest": str(MANIFEST),
    }


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