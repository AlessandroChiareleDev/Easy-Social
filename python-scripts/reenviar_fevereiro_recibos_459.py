from __future__ import annotations

import argparse
import json
import sys
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

import corrigir_mes_respostas_jaque_plano_pensao as correcao_base  # noqa: E402
import enviar_correcao_agosto_jaque as envio_base  # noqa: E402
from app import db, esocial_client, tenant  # noqa: E402
from app.xml_s1210 import _gerar_id  # noqa: E402
from app.xml_signer import S1010XMLSigner  # noqa: E402


EMPRESA_ID = 2
PER_APUR = "2025-02"
CNPJ = "09445502000109"
CNPJ_RAIZ = CNPJ[:8]
CONFIRM_TOKEN = "REENVIAR_FEVEREIRO_RECIBOS_459"
TARGET_RECEIPTS = {
    "36832724810": "1.1.0000000031405347921",
    "93564139249": "1.1.0000000031331770805",
}
OUT_DIR = ROOT / "relatorio_ana" / "CORRECAO_JAQUE_PLANO_PENSAO_2025" / PER_APUR / "retry_recibos_459"
XML_DIR = OUT_DIR / "xml_unsigned"
MANIFEST_PATH = OUT_DIR / "manifest_retry_recibos_459.json"
RESULT_PATH = OUT_DIR / "resultado_retry_recibos_459.json"


def latest_rows() -> dict[str, dict[str, Any]]:
    internal_empresa_id = tenant.internal_empresa_id(EMPRESA_ID)
    conn = db.connect(empresa_id=EMPRESA_ID)
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
            cursor.execute(
                """
                WITH latest AS (
                    SELECT DISTINCT ON (it.cpf)
                           it.id AS item_id, it.cpf, it.status, it.erro_codigo, it.erro_mensagem,
                           it.versao_anterior_id AS evento_id, it.nr_recibo_anterior,
                           it.xml_enviado_oid, te.id AS envio_id, it.criado_em
                      FROM timeline_envio_item it
                      JOIN timeline_envio te ON te.id = it.timeline_envio_id
                      JOIN timeline_mes tm ON tm.id = te.timeline_mes_id
                     WHERE tm.empresa_id = %s
                       AND tm.per_apur = %s
                       AND it.tipo_evento = 'S-1210'
                       AND it.cpf = ANY(%s)
                     ORDER BY it.cpf, it.criado_em DESC NULLS LAST, it.id DESC
                )
                SELECT * FROM latest ORDER BY cpf
                """,
                (internal_empresa_id, PER_APUR, list(TARGET_RECEIPTS)),
            )
            return {str(row["cpf"]): dict(row) for row in cursor.fetchall()}
    finally:
        conn.close()


def read_large_object(oid: int) -> bytes:
    conn = db.connect(empresa_id=EMPRESA_ID)
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT lo_get(%s)", (oid,))
            row = cursor.fetchone()
            if not row or row[0] is None:
                raise RuntimeError(f"OID sem conteudo: {oid}")
            return bytes(row[0])
    finally:
        conn.close()


def rewrite_receipt(xml_bytes: bytes, cpf: str, new_receipt: str) -> tuple[bytes, dict[str, Any]]:
    root = etree.fromstring(xml_bytes)
    for signature in root.xpath('.//*[local-name()="Signature"]'):
        parent = signature.getparent()
        if parent is not None:
            parent.remove(signature)
    evt_nodes = root.xpath('//*[local-name()="evtPgtos"]')
    if not evt_nodes:
        raise RuntimeError(f"{cpf}: evtPgtos ausente")
    evt_nodes[0].set("Id", _gerar_id(1, CNPJ_RAIZ))
    nr_nodes = root.xpath('//*[local-name()="nrRecibo"]')
    if not nr_nodes:
        raise RuntimeError(f"{cpf}: nrRecibo ausente")
    old_receipt = (nr_nodes[0].text or "").strip()
    nr_nodes[0].text = new_receipt
    counts = {
        "cpfBenef": root.xpath('string(//*[local-name()="cpfBenef"])'),
        "perApur": root.xpath('string(//*[local-name()="perApur"])'),
        "indRetif": root.xpath('string(//*[local-name()="indRetif"])'),
        "old_nrRecibo": old_receipt,
        "new_nrRecibo": new_receipt,
        "id": evt_nodes[0].get("Id"),
        "infoPgto": len(root.xpath('//*[local-name()="infoPgto"]')),
        "infoIRComplem": len(root.xpath('//*[local-name()="infoIRComplem"]')),
        "planSaude": len(root.xpath('//*[local-name()="planSaude"]')),
        "penAlim": len(root.xpath('//*[local-name()="penAlim"]')),
        "dedDepen": len(root.xpath('//*[local-name()="dedDepen"]')),
        "signature": len(root.xpath('//*[local-name()="Signature"]')),
    }
    if counts["cpfBenef"] != cpf:
        raise RuntimeError(f"{cpf}: cpfBenef divergente {counts['cpfBenef']}")
    if counts["perApur"] != PER_APUR or counts["indRetif"] != "2":
        raise RuntimeError(f"{cpf}: XML nao e retificacao de {PER_APUR}")
    return etree.tostring(root, xml_declaration=True, encoding="UTF-8"), counts


def generate_manifest() -> dict[str, Any]:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    XML_DIR.mkdir(parents=True, exist_ok=True)
    for old_xml in XML_DIR.glob("*.xml"):
        old_xml.unlink()
    latest = latest_rows()
    targets: list[dict[str, Any]] = []
    blocked: list[dict[str, Any]] = []
    for cpf, new_receipt in TARGET_RECEIPTS.items():
        row = latest.get(cpf)
        if not row:
            blocked.append({"cpf": cpf, "reason": "sem latest local"})
            continue
        message = str(row.get("erro_mensagem") or "")
        if row.get("status") != "erro_esocial" or "459" not in message:
            blocked.append({"cpf": cpf, "reason": "latest nao e erro 459", "latest": row})
            continue
        if not row.get("xml_enviado_oid") or not row.get("evento_id"):
            blocked.append({"cpf": cpf, "reason": "latest sem xml_enviado_oid/evento_id", "latest": row})
            continue
        xml_new, counts = rewrite_receipt(read_large_object(int(row["xml_enviado_oid"])), cpf, new_receipt)
        out_xml = XML_DIR / f"S1210_{PER_APUR}_{cpf}_recibo_459_unsigned.xml"
        out_xml.write_bytes(xml_new)
        targets.append(
            {
                "cpf": cpf,
                "evento_id": row["evento_id"],
                "nr_recibo": new_receipt,
                "xml": str(out_xml),
                "source_item_id": row["item_id"],
                "source_envio_id": row["envio_id"],
                "source_xml_enviado_oid": row["xml_enviado_oid"],
                "source_erro": message,
                **counts,
            }
        )
    manifest = {
        "empresa_id": EMPRESA_ID,
        "per_apur": PER_APUR,
        "regra": "retry 459: substituir somente nrRecibo pelo recibo ativo informado pelo usuario",
        "total_targets": len(targets),
        "blocked_count": len(blocked),
        "targets": targets,
        "blocked": blocked,
    }
    MANIFEST_PATH.write_text(json.dumps(manifest, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    return manifest


def validate_manifest(manifest: dict[str, Any]) -> dict[str, Any]:
    rows = []
    for item in manifest["targets"]:
        xml_bytes = Path(item["xml"]).read_bytes()
        root = etree.fromstring(xml_bytes)
        rows.append(
            {
                "cpf": item["cpf"],
                "cpfBenef": root.xpath('string(//*[local-name()="cpfBenef"])'),
                "perApur": root.xpath('string(//*[local-name()="perApur"])'),
                "indRetif": root.xpath('string(//*[local-name()="indRetif"])'),
                "nrRecibo": root.xpath('string(//*[local-name()="nrRecibo"])'),
                "expected_nrRecibo": TARGET_RECEIPTS[item["cpf"]],
                "id": esocial_client._extrair_id(xml_bytes),
                "signature": bool(root.xpath('//*[local-name()="Signature"]')),
            }
        )
    wrong = [
        row
        for row in rows
        if row["cpf"] != row["cpfBenef"]
        or row["perApur"] != PER_APUR
        or row["indRetif"] != "2"
        or row["nrRecibo"] != row["expected_nrRecibo"]
        or not str(row["id"] or "").startswith("ID1")
        or row["signature"]
    ]
    return {"total": len(rows), "wrong": wrong, "sample": rows}


def sign_targets(targets: list[dict[str, Any]], senha: str) -> list[dict[str, Any]]:
    pfx_data = correcao_base.DEFAULT_CERT.read_bytes()
    signed: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    for item in targets:
        unsigned = Path(item["xml"]).read_bytes()
        xml_assinado = S1010XMLSigner.assinar(unsigned, pfx_data, senha)
        signed_id = esocial_client._extrair_id(xml_assinado)
        if not signed_id:
            raise RuntimeError(f"Id assinado ausente para {item['cpf']}")
        if signed_id in seen_ids:
            raise RuntimeError(f"Id duplicado {signed_id}")
        seen_ids.add(signed_id)
        signed.append({**item, "xml_assinado": xml_assinado, "id_evento_assinado": signed_id})
    return signed


def execute() -> dict[str, Any]:
    manifest = generate_manifest()
    validation = validate_manifest(manifest)
    if manifest["blocked_count"]:
        raise RuntimeError(f"ha CPFs bloqueados: {manifest['blocked']}")
    if validation["wrong"]:
        raise RuntimeError(f"validacao falhou: {validation['wrong']}")
    if manifest["total_targets"] != 2:
        raise RuntimeError(f"esperava 2 alvos, recebi {manifest['total_targets']}")
    senha = correcao_base.read_password()
    signed = sign_targets(manifest["targets"], senha)
    conn_db = db.connect(empresa_id=EMPRESA_ID)
    conn_w = db.connect(empresa_id=EMPRESA_ID)
    try:
        envio_base.PER_APUR = PER_APUR
        envio_base.PREFLIGHT = MANIFEST_PATH
        envio_base.CFG_GRUPO = correcao_base.GRUPO
        envio_base.POLL_TENTATIVAS = correcao_base.POLL_TENTATIVAS
        envio_base.POLL_INTERVALO_S = correcao_base.POLL_INTERVALO_S
        envio_base._verificar_estado_atual(conn_db, signed)
        envio_id, mes_id = correcao_base._create_timeline_envio(conn_db, PER_APUR, len(signed), MANIFEST_PATH)
        print(f"=> retry recibos 459: envio_id={envio_id} timeline_mes={mes_id} targets={len(signed)}")
        item_ids = envio_base._criar_items(conn_db, envio_id, signed)
        envio_base._persistir_xmls_assinados(conn_db, conn_w, signed, item_ids)
        resultado = envio_base._processar_lote(
            signed,
            item_ids,
            cert_path=correcao_base.DEFAULT_CERT,
            senha=senha,
            cnpj=CNPJ,
            conn_db=conn_db,
            conn_w=conn_w,
        )
        envio_base._atualizar_envio(
            conn_db,
            envio_id,
            status="concluido",
            sucesso=int(resultado["sucesso"]),
            erro=int(resultado["erro"]),
            resumo_extra={
                "rotulo_final": "retry_fevereiro_recibos_459",
                "manifest": str(MANIFEST_PATH),
                "protocolo": resultado.get("protocolo"),
                "histograma_erros": resultado.get("histograma") or {},
            },
        )
        result = {
            "envio_id": envio_id,
            "sucesso": int(resultado["sucesso"]),
            "erro": int(resultado["erro"]),
            "protocolo": resultado.get("protocolo"),
            "histograma": resultado.get("histograma") or {},
            "manifest": str(MANIFEST_PATH),
        }
        RESULT_PATH.write_text(json.dumps(result, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
        return result
    finally:
        conn_db.close()
        conn_w.close()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--confirmar", default="")
    args = parser.parse_args()
    if not args.execute:
        manifest = generate_manifest()
        print(json.dumps({"manifest": manifest, "validation": validate_manifest(manifest)}, ensure_ascii=False, indent=2, default=str))
        return 0
    if args.confirmar != CONFIRM_TOKEN:
        raise SystemExit(f"Para executar, use --confirmar {CONFIRM_TOKEN}")
    print(json.dumps(execute(), ensure_ascii=False, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())