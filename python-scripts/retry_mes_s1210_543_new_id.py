from __future__ import annotations

import argparse
import json
import re
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
CNPJ = "09445502000109"


def confirm_token(per_apur: str) -> str:
    return f"RETRY_{per_apur.replace('-', '_')}_S1210_543_NEW_ID"


def month_dir(per_apur: str) -> Path:
    return ROOT / "relatorio_ana" / "CORRECAO_JAQUE_PLANO_PENSAO_2025" / per_apur


def retry_dir(per_apur: str) -> Path:
    return month_dir(per_apur) / "retry_s1210_543_new_id"


def xml_dir(per_apur: str) -> Path:
    return retry_dir(per_apur) / "xml_unsigned"


def manifest_path(per_apur: str) -> Path:
    return retry_dir(per_apur) / "manifest_retry_s1210_543_new_id.json"


def current_543_rows(per_apur: str) -> list[dict[str, Any]]:
    internal_empresa_id = tenant.internal_empresa_id(EMPRESA_ID)
    conn = db.connect(empresa_id=EMPRESA_ID)
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
            cursor.execute(
                """
                WITH latest AS (
                    SELECT DISTINCT ON (it.cpf)
                           it.id AS item_id, te.id AS envio_id, it.cpf, it.status,
                           it.erro_codigo, it.erro_mensagem, it.nr_recibo_anterior,
                           it.nr_recibo_novo, it.versao_anterior_id, it.xml_enviado_oid,
                           it.criado_em
                      FROM timeline_envio_item it
                      JOIN timeline_envio te ON te.id = it.timeline_envio_id
                      JOIN timeline_mes tm ON tm.id = te.timeline_mes_id
                     WHERE tm.empresa_id = %s
                       AND tm.per_apur = %s
                       AND it.tipo_evento = 'S-1210'
                     ORDER BY it.cpf, it.criado_em DESC NULLS LAST, it.id DESC
                )
                SELECT * FROM latest
                 WHERE status = 'erro_esocial'
                   AND erro_codigo = '401'
                   AND erro_mensagem LIKE '%%543%%'
                   AND erro_mensagem LIKE '%%mesmo identificador%%'
                 ORDER BY cpf
                """,
                (internal_empresa_id, per_apur),
            )
            return [dict(row) for row in cursor.fetchall()]
    finally:
        conn.close()


def read_large_object(conn, oid: int) -> bytes:
    with conn.cursor() as cursor:
        cursor.execute("SELECT lo_get(%s)", (oid,))
        row = cursor.fetchone()
    if not row or row[0] is None:
        raise RuntimeError(f"large object nao encontrado: {oid}")
    return bytes(row[0])


def unsigned_inner_s1210(xml_bytes: bytes) -> etree._Element:
    parser = etree.XMLParser(remove_blank_text=True)
    root = etree.fromstring(xml_bytes, parser=parser)
    candidates = root.xpath('//*[local-name()="eSocial" and ./*[local-name()="evtPgtos"]]')
    if candidates:
        root = candidates[0]
    inner = etree.fromstring(etree.tostring(root), parser=parser)
    for signature in inner.xpath('.//*[local-name()="Signature"]'):
        parent = signature.getparent()
        if parent is not None:
            parent.remove(signature)
    return inner


def prepare_xml(xml_bytes: bytes, per_apur: str) -> tuple[bytes, dict[str, str]]:
    inner = unsigned_inner_s1210(xml_bytes)
    event_nodes = inner.xpath('./*[local-name()="evtPgtos"]')
    if not event_nodes:
        raise RuntimeError("evtPgtos ausente")
    event = event_nodes[0]
    old_id = event.get("Id") or ""
    tp_insc = int(inner.xpath('string(//*[local-name()="ideEmpregador"]/*[local-name()="tpInsc"])') or "1")
    nr_insc = inner.xpath('string(//*[local-name()="ideEmpregador"]/*[local-name()="nrInsc"])')
    new_id = _gerar_id(tp_insc, nr_insc)
    event.set("Id", new_id)
    if inner.xpath('string(//*[local-name()="perApur"])') != per_apur:
        raise RuntimeError("perApur divergente")
    if inner.xpath('string(//*[local-name()="indRetif"])') != "2":
        raise RuntimeError("XML nao esta como retificacao")
    receipt = inner.xpath('string(//*[local-name()="nrRecibo"])')
    if not receipt:
        raise RuntimeError("nrRecibo ausente")
    if inner.xpath('.//*[local-name()="Signature"]'):
        raise RuntimeError("Signature antiga permaneceu")
    output = etree.tostring(inner, xml_declaration=True, encoding="UTF-8", pretty_print=False)
    return output, {"source_id": old_id, "new_id": new_id, "nrRecibo": receipt}


def generate_manifest(per_apur: str) -> dict[str, Any]:
    retry_dir(per_apur).mkdir(parents=True, exist_ok=True)
    xml_dir(per_apur).mkdir(parents=True, exist_ok=True)
    for old_xml in xml_dir(per_apur).glob("*.xml"):
        old_xml.unlink()

    rows = current_543_rows(per_apur)
    targets: list[dict[str, Any]] = []
    skipped: list[dict[str, Any]] = []
    conn = db.connect(empresa_id=EMPRESA_ID)
    try:
        for row in rows:
            cpf = re.sub(r"\D", "", str(row.get("cpf") or "")).zfill(11)[-11:]
            if not row.get("xml_enviado_oid"):
                skipped.append({**row, "reason": "sem xml_enviado_oid no ultimo erro"})
                continue
            if not row.get("nr_recibo_anterior"):
                skipped.append({**row, "reason": "sem nr_recibo_anterior"})
                continue
            try:
                source_xml = read_large_object(conn, int(row["xml_enviado_oid"]))
                xml_out, meta = prepare_xml(source_xml, per_apur)
            except Exception as exc:
                conn.rollback()
                skipped.append({**row, "reason": f"{type(exc).__name__}: {exc}"})
                continue
            out_xml = xml_dir(per_apur) / f"S1210_{per_apur}_{cpf}_new_id_unsigned.xml"
            out_xml.write_bytes(xml_out)
            targets.append(
                {
                    "cpf": cpf,
                    "xml": str(out_xml),
                    "evento_id": row.get("versao_anterior_id"),
                    "nr_recibo": str(row["nr_recibo_anterior"]),
                    "latest_item_id": row.get("item_id"),
                    "latest_envio_id": row.get("envio_id"),
                    "validation": meta,
                }
            )
    finally:
        conn.close()

    manifest = {
        "empresa_id": EMPRESA_ID,
        "per_apur": per_apur,
        "regra": "retry 401/543 de S-1210: trocar somente o Id do evento e reenviar",
        "total_current_543": len(rows),
        "total_retry": len(targets),
        "total_skipped": len(skipped),
        "targets": targets,
        "skipped": skipped,
    }
    manifest_path(per_apur).write_text(json.dumps(manifest, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    return manifest


def validate_manifest(manifest: dict[str, Any]) -> dict[str, Any]:
    rows = []
    for item in manifest.get("targets") or []:
        xml_bytes = Path(item["xml"]).read_bytes()
        root = etree.fromstring(xml_bytes)
        rows.append(
            {
                "cpf": item["cpf"],
                "id": esocial_client._extrair_id(xml_bytes),
                "perApur": root.xpath('string(//*[local-name()="perApur"])'),
                "indRetif": root.xpath('string(//*[local-name()="indRetif"])'),
                "nrRecibo": root.xpath('string(//*[local-name()="nrRecibo"])'),
                "signature": bool(root.xpath('//*[local-name()="Signature"]')),
            }
        )
    wrong = [row for row in rows if row["perApur"] != manifest["per_apur"] or row["indRetif"] != "2" or row["signature"]]
    return {"total": len(rows), "wrong": wrong, "sample": rows[:10]}


def sign_targets(targets: list[dict[str, Any]], senha: str) -> list[dict[str, Any]]:
    pfx_data = correcao_base.DEFAULT_CERT.read_bytes()
    signed: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    for item in targets:
        unsigned_xml = Path(item["xml"]).read_bytes()
        xml_assinado = S1010XMLSigner.assinar(unsigned_xml, pfx_data, senha)
        signed_id = esocial_client._extrair_id(xml_assinado)
        if not signed_id:
            raise RuntimeError(f"Id assinado ausente para {item['cpf']}")
        if signed_id in seen_ids:
            raise RuntimeError(f"Id duplicado {signed_id}")
        seen_ids.add(signed_id)
        signed.append({**item, "xml_assinado": xml_assinado, "id_evento_assinado": signed_id})
    return signed


def execute(per_apur: str) -> dict[str, Any]:
    manifest = generate_manifest(per_apur)
    validation = validate_manifest(manifest)
    if validation["wrong"]:
        raise RuntimeError(f"validacao falhou: {validation['wrong'][:5]}")
    if not manifest["targets"]:
        raise RuntimeError("nenhum alvo para retry")
    senha = correcao_base.read_password()
    signed = sign_targets(manifest["targets"], senha)

    conn_db = db.connect(empresa_id=EMPRESA_ID)
    conn_w = db.connect(empresa_id=EMPRESA_ID)
    try:
        envio_base.PER_APUR = per_apur
        envio_base.PREFLIGHT = manifest_path(per_apur)
        envio_base.CFG_GRUPO = correcao_base.GRUPO
        envio_base.POLL_TENTATIVAS = correcao_base.POLL_TENTATIVAS
        envio_base.POLL_INTERVALO_S = correcao_base.POLL_INTERVALO_S
        envio_base._verificar_estado_atual(conn_db, signed)
        envio_id, mes_id = correcao_base._create_timeline_envio(conn_db, per_apur, len(signed), manifest_path(per_apur))
        print(f"=> retry S-1210 543 new Id {per_apur}: envio_id={envio_id} timeline_mes={mes_id} targets={len(signed)}")
        item_ids = envio_base._criar_items(conn_db, envio_id, signed)
        envio_base._persistir_xmls_assinados(conn_db, conn_w, signed, item_ids)

        sucesso_total = 0
        erro_total = 0
        protocolos: list[str] = []
        histograma: dict[str, int] = {}
        for index in range(0, len(signed), correcao_base.CFG_LOTE_MAX):
            lote = signed[index:index + correcao_base.CFG_LOTE_MAX]
            resultado = envio_base._processar_lote(
                lote,
                item_ids,
                cert_path=correcao_base.DEFAULT_CERT,
                senha=senha,
                cnpj=CNPJ,
                conn_db=conn_db,
                conn_w=conn_w,
            )
            sucesso_total += int(resultado["sucesso"])
            erro_total += int(resultado["erro"])
            if resultado.get("protocolo"):
                protocolos.append(str(resultado["protocolo"]))
            for codigo, total in (resultado.get("histograma") or {}).items():
                histograma[codigo] = histograma.get(codigo, 0) + int(total)

        envio_base._atualizar_envio(
            conn_db,
            envio_id,
            status="concluido",
            sucesso=sucesso_total,
            erro=erro_total,
            resumo_extra={
                "rotulo_final": "retry_mes_s1210_543_new_id",
                "per_apur": per_apur,
                "manifest": str(manifest_path(per_apur)),
                "protocolos": protocolos,
                "histograma_erros": histograma,
            },
        )
        target_cpfs = [item["cpf"] for item in manifest["targets"]]
        latest = correcao_base.latest_status_summary(per_apur, target_cpfs)
        result = {
            "per_apur": per_apur,
            "envio_id": envio_id,
            "sucesso": sucesso_total,
            "erro": erro_total,
            "protocolos": protocolos,
            "histograma": histograma,
            "manifest": str(manifest_path(per_apur)),
            "latest": latest,
        }
        (retry_dir(per_apur) / "resultado_retry_s1210_543_new_id.json").write_text(
            json.dumps(result, ensure_ascii=False, indent=2, default=str),
            encoding="utf-8",
        )
        return result
    finally:
        conn_db.close()
        conn_w.close()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--per-apur", required=True)
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--confirmar", default="")
    args = parser.parse_args()

    if not re.fullmatch(r"20\d{2}-\d{2}", args.per_apur):
        raise SystemExit(f"per_apur invalido: {args.per_apur}")
    if not args.execute:
        manifest = generate_manifest(args.per_apur)
        print(json.dumps({"manifest": manifest, "validation": validate_manifest(manifest)}, ensure_ascii=False, indent=2, default=str))
        return 0
    expected_token = confirm_token(args.per_apur)
    if args.confirmar != expected_token:
        raise SystemExit(f"Para executar, use --confirmar {expected_token}")
    print(json.dumps(execute(args.per_apur), ensure_ascii=False, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())