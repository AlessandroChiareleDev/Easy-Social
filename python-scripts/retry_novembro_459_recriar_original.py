from __future__ import annotations

import argparse
import json
import re
import sys
import zipfile
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
from app.xml_s1210 import NS as S1210_NS, _gerar_id  # noqa: E402
from app.xml_signer import S1010XMLSigner  # noqa: E402


EMPRESA_ID = 2
CNPJ = "09445502000109"
PER_APUR = "2025-11"
EXPECTED_TOTAL = 6
ZIP_ROOT = Path(r"C:\Users\xandao\Downloads\todos os meses 2025 SOLUCOES")
OUT_DIR = ROOT / "relatorio_ana" / "CORRECAO_JAQUE_PLANO_PENSAO_2025" / PER_APUR / "retry_459_recriar_original"
XML_DIR = OUT_DIR / "xml_unsigned"
MANIFEST = OUT_DIR / "manifest_retry_459_recriar_original.json"
RESULT = OUT_DIR / "resultado_retry_459_recriar_original.json"
TARGET_CPFS: set[str] | None = None


def configure(per_apur: str, expected_total: int, target_cpfs: list[str] | None = None) -> None:
    global PER_APUR, EXPECTED_TOTAL, OUT_DIR, XML_DIR, MANIFEST, RESULT, TARGET_CPFS
    PER_APUR = per_apur
    EXPECTED_TOTAL = expected_total
    TARGET_CPFS = {cpf11(cpf) for cpf in target_cpfs or []} or None
    OUT_DIR = ROOT / "relatorio_ana" / "CORRECAO_JAQUE_PLANO_PENSAO_2025" / PER_APUR / "retry_459_recriar_original"
    XML_DIR = OUT_DIR / "xml_unsigned"
    MANIFEST = OUT_DIR / "manifest_retry_459_recriar_original.json"
    RESULT = OUT_DIR / "resultado_retry_459_recriar_original.json"


def qname(tag: str) -> str:
    return f"{{{S1210_NS}}}{tag}"


def cpf11(value: Any) -> str:
    digits = re.sub(r"\D", "", str(value or ""))
    return digits.zfill(11)[-11:] if digits else ""


def confirm_token() -> str:
    return f"RECRIAR_{PER_APUR.replace('-', '_')}_S1210_ORIGINAL_459"


def direct_child(parent: etree._Element, tag: str) -> etree._Element | None:
    found = parent.xpath(f'./*[local-name()="{tag}"]')
    return found[0] if found else None


def set_child(parent: etree._Element, tag: str, value: str, after_tag: str | None = None) -> etree._Element:
    found = direct_child(parent, tag)
    if found is not None:
        found.text = value
        return found
    node = etree.Element(qname(tag))
    node.text = value
    insert_at = len(parent)
    if after_tag:
        for index, child in enumerate(parent):
            if etree.QName(child).localname == after_tag:
                insert_at = index + 1
                break
    parent.insert(insert_at, node)
    return node


def remove_child(parent: etree._Element, tag: str) -> str | None:
    found = direct_child(parent, tag)
    if found is None:
        return None
    old_text = (found.text or "").strip()
    parent.remove(found)
    return old_text


def read_large_object(conn, oid: int) -> bytes:
    with conn.cursor() as cursor:
        cursor.execute("SELECT lo_get(%s)", (oid,))
        row = cursor.fetchone()
    if not row or row[0] is None:
        raise RuntimeError(f"large object nao encontrado: {oid}")
    return bytes(row[0])


def read_event_xml(row: dict[str, Any]) -> tuple[bytes | None, str]:
    if row.get("xml_bytes") is not None:
        return bytes(row["xml_bytes"]), "db_xml_bytes"
    zip_name = row.get("zip_nome")
    entry = row.get("xml_entry_name")
    if zip_name and entry:
        zip_path = ZIP_ROOT / zip_name
        if zip_path.exists():
            try:
                with zipfile.ZipFile(zip_path) as zip_file:
                    return zip_file.read(entry), f"zip:{zip_name}"
            except Exception as exc:
                return None, f"zip_error:{type(exc).__name__}:{exc}"
    return None, "sem_xml_local"


def current_459_rows(conn) -> list[dict[str, Any]]:
    internal_empresa_id = tenant.internal_empresa_id(EMPRESA_ID)
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
                         WHERE (
                                        status = 'erro_esocial'
                                AND erro_codigo = '401'
                                AND erro_mensagem LIKE '%%459%%'
                         )
                                OR erro_codigo = '459_SEM_RECIBO'
             ORDER BY cpf
            """,
            (internal_empresa_id, PER_APUR),
        )
        return [dict(row) for row in cursor.fetchall()]


def s3000_exclusions(conn, cpf: str, receipt: str) -> list[dict[str, Any]]:
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
        cursor.execute(
            """
            SELECT ev.id, ev.cpf, ev.per_apur, ev.nr_recibo, ev.id_evento,
                   ev.dt_processamento, ev.xml_entry_name, ev.xml_bytes,
                   z.nome_arquivo_original AS zip_nome
              FROM explorador_eventos ev
              LEFT JOIN empresa_zips_brutos z ON z.id = ev.zip_id
             WHERE ev.cpf = %s
               AND ev.tipo_evento = 'S-3000'
             ORDER BY ev.dt_processamento NULLS LAST, ev.id
            """,
            (cpf,),
        )
        rows = [dict(row) for row in cursor.fetchall()]
    matches: list[dict[str, Any]] = []
    for row in rows:
        raw, source = read_event_xml(row)
        if not raw:
            continue
        root = etree.fromstring(raw)
        nr_rec_evt = root.xpath('string(//*[local-name()="nrRecEvt"])').strip()
        per_apur_xml = root.xpath('string(//*[local-name()="perApur"])').strip()
        cpf_xml = cpf11(root.xpath('string(//*[local-name()="cpfBenef"] | //*[local-name()="cpfTrab"])'))
        if nr_rec_evt == receipt and per_apur_xml == PER_APUR and cpf_xml == cpf:
            matches.append(
                {
                    "s3000_id": row["id"],
                    "s3000_recibo": row.get("nr_recibo"),
                    "s3000_id_evento": row.get("id_evento"),
                    "s3000_dt": row.get("dt_processamento"),
                    "s3000_xml": row.get("xml_entry_name"),
                    "s3000_source": source,
                    "nrRecEvt": nr_rec_evt,
                }
            )
    return matches


def later_s1210_count(conn, cpf: str, excluded_at: Any) -> int:
    with conn.cursor() as cursor:
        cursor.execute(
            """
            SELECT COUNT(*)
              FROM explorador_eventos
             WHERE cpf = %s
               AND tipo_evento = 'S-1210'
               AND per_apur = %s
               AND COALESCE(cd_resposta, '201') IN ('201', '202')
               AND dt_processamento > %s
            """,
            (cpf, PER_APUR, excluded_at),
        )
        return int(cursor.fetchone()[0])


def inner_s1210(xml_bytes: bytes) -> etree._Element:
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


def prepare_original_xml(xml_bytes: bytes, target: dict[str, Any]) -> tuple[bytes, dict[str, Any]]:
    inner = inner_s1210(xml_bytes)
    event_nodes = inner.xpath('./*[local-name()="evtPgtos"]')
    if not event_nodes:
        raise RuntimeError("evtPgtos ausente")
    event = event_nodes[0]
    old_id = event.get("Id") or ""
    cpf = cpf11(inner.xpath('string(//*[local-name()="ideBenef"]/*[local-name()="cpfBenef"])'))
    if cpf != target["cpf"]:
        raise RuntimeError(f"XML fonte e de CPF {cpf}, alvo {target['cpf']}")
    tp_insc = int(inner.xpath('string(//*[local-name()="ideEmpregador"]/*[local-name()="tpInsc"])') or "1")
    nr_insc = inner.xpath('string(//*[local-name()="ideEmpregador"]/*[local-name()="nrInsc"])').strip()
    event.set("Id", _gerar_id(tp_insc, nr_insc))

    ide_evento = event.xpath('./*[local-name()="ideEvento"]')[0]
    set_child(ide_evento, "indRetif", "1")
    removed_receipt = remove_child(ide_evento, "nrRecibo")
    if removed_receipt and removed_receipt != target["nr_recibo_anterior"]:
        raise RuntimeError(f"nrRecibo removido diverge do recibo excluido: {removed_receipt} != {target['nr_recibo_anterior']}")

    tp_amb = inner.xpath('string(//*[local-name()="ideEvento"]/*[local-name()="tpAmb"])').strip()
    per_apur = inner.xpath('string(//*[local-name()="ideEvento"]/*[local-name()="perApur"])').strip()
    if tp_amb != "1":
        raise RuntimeError(f"tpAmb nao e producao: {tp_amb}")
    if per_apur != PER_APUR:
        raise RuntimeError(f"perApur divergente: {per_apur}")
    if inner.xpath('.//*[local-name()="Signature"]'):
        raise RuntimeError("Signature antiga permaneceu")
    if inner.xpath('string(//*[local-name()="ideEvento"]/*[local-name()="nrRecibo"])'):
        raise RuntimeError("nrRecibo permaneceu em XML original")

    output = etree.tostring(inner, xml_declaration=True, encoding="UTF-8", pretty_print=False)
    return output, {
        "cpf": target["cpf"],
        "source_id": old_id,
        "new_id": event.get("Id"),
        "indRetif": inner.xpath('string(//*[local-name()="indRetif"])'),
        "nrRecibo": inner.xpath('string(//*[local-name()="nrRecibo"])'),
        "perApur": per_apur,
        "tpAmb": tp_amb,
        "removed_receipt": removed_receipt,
    }


def generate_manifest() -> dict[str, Any]:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    XML_DIR.mkdir(parents=True, exist_ok=True)
    for old_xml in XML_DIR.glob("*.xml"):
        old_xml.unlink()

    conn = db.connect(empresa_id=EMPRESA_ID)
    targets: list[dict[str, Any]] = []
    skipped: list[dict[str, Any]] = []
    try:
        rows = current_459_rows(conn)
        if TARGET_CPFS:
            rows = [row for row in rows if cpf11(row.get("cpf")) in TARGET_CPFS]
        for row in rows:
            cpf = cpf11(row.get("cpf"))
            record = {"cpf": cpf, "latest_item_id": row.get("item_id"), "latest_envio_id": row.get("envio_id"), "generated": False}
            if not row.get("xml_enviado_oid"):
                record["reason"] = "sem xml_enviado_oid no erro atual"
                skipped.append(record)
                continue
            if not row.get("nr_recibo_anterior"):
                record["reason"] = "sem nr_recibo_anterior no erro atual"
                skipped.append(record)
                continue
            exclusions = s3000_exclusions(conn, cpf, str(row["nr_recibo_anterior"]))
            if len(exclusions) != 1:
                record["reason"] = f"S-3000 local que exclui recibo nao encontrado de forma unica: {len(exclusions)}"
                skipped.append(record)
                continue
            later_count = later_s1210_count(conn, cpf, exclusions[0]["s3000_dt"])
            if later_count:
                record["reason"] = f"existe S-1210 local posterior ao S-3000: {later_count}"
                skipped.append(record)
                continue
            try:
                source_xml = read_large_object(conn, int(row["xml_enviado_oid"]))
                xml_new, validation = prepare_original_xml(source_xml, {**row, "cpf": cpf})
            except Exception as exc:
                conn.rollback()
                record["reason"] = f"{type(exc).__name__}: {exc}"
                skipped.append(record)
                continue
            xml_path = XML_DIR / f"S1210_{PER_APUR}_{cpf}_original_pos_s3000_unsigned.xml"
            xml_path.write_bytes(xml_new)
            targets.append(
                {
                    "cpf": cpf,
                    "xml": str(xml_path),
                    "evento_id": None,
                    "nr_recibo": None,
                    "id_evento": validation["new_id"],
                    "latest_item_id": row.get("item_id"),
                    "latest_envio_id": row.get("envio_id"),
                    "receipt_excluded": str(row["nr_recibo_anterior"]),
                    "s3000_proof": exclusions[0],
                    "validation": validation,
                    "generated": True,
                }
            )
    finally:
        conn.close()

    manifest = {
        "empresa_id": EMPRESA_ID,
        "per_apur": PER_APUR,
        "regra": "401/459 com recibo excluido por S-3000: recriar S-1210 como original indRetif=1 sem nrRecibo",
        "target_cpfs_filter": sorted(TARGET_CPFS) if TARGET_CPFS else None,
        "total_current_459": len(targets) + len(skipped),
        "total_retry": len(targets),
        "total_skipped": len(skipped),
        "targets": targets,
        "skipped": skipped,
    }
    MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
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
                "indRetif": root.xpath('string(//*[local-name()="indRetif"])'),
                "nrRecibo": root.xpath('string(//*[local-name()="ideEvento"]/*[local-name()="nrRecibo"])'),
                "perApur": root.xpath('string(//*[local-name()="perApur"])'),
                "tpAmb": root.xpath('string(//*[local-name()="tpAmb"])'),
                "signature": bool(root.xpath('//*[local-name()="Signature"]')),
            }
        )
    wrong = [row for row in rows if row["indRetif"] != "1" or row["nrRecibo"] or row["perApur"] != PER_APUR or row["tpAmb"] != "1" or row["signature"]]
    return {"total": len(rows), "wrong": wrong, "sample": rows[:10]}


def sign_targets(targets: list[dict[str, Any]], senha: str) -> list[dict[str, Any]]:
    pfx_data = correcao_base.DEFAULT_CERT.read_bytes()
    signed: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    for item in targets:
        unsigned_xml = Path(item["xml"]).read_bytes()
        xml_assinado = S1010XMLSigner.assinar(unsigned_xml, pfx_data, senha)
        signed_id = esocial_client._extrair_id(xml_assinado)
        if signed_id != item["id_evento"]:
            raise RuntimeError(f"Id assinado divergente para {item['cpf']}: {signed_id} != {item['id_evento']}")
        if signed_id in seen_ids:
            raise RuntimeError(f"Id duplicado apos assinatura: {signed_id}")
        seen_ids.add(signed_id)
        signed.append({**item, "xml_assinado": xml_assinado, "id_evento_assinado": signed_id})
    return signed


def assert_still_current_459(conn, targets: list[dict[str, Any]]) -> None:
    internal_empresa_id = tenant.internal_empresa_id(EMPRESA_ID)
    cpfs = [item["cpf"] for item in targets]
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
        cursor.execute(
            """
            WITH latest AS (
                SELECT DISTINCT ON (it.cpf)
                       it.cpf, it.status, it.erro_codigo, it.erro_mensagem,
                       it.id AS item_id, te.id AS envio_id, it.criado_em
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
            (internal_empresa_id, PER_APUR, cpfs),
        )
        latest = {cpf11(row["cpf"]): dict(row) for row in cursor.fetchall()}
    invalid = []
    for cpf in cpfs:
        row = latest.get(cpf)
        if not row:
            invalid.append({"cpf": cpf, "reason": "sem latest timeline"})
            continue
        message = str(row.get("erro_mensagem") or "")
        code = str(row.get("erro_codigo") or "")
        if not (
            (row.get("status") == "erro_esocial" and code == "401" and "459" in message)
            or code == "459_SEM_RECIBO"
        ):
            invalid.append({"cpf": cpf, "status": row.get("status"), "erro_codigo": code, "mensagem": message[:160]})
    if invalid:
        raise RuntimeError(f"alvos deixaram de estar em estado 459 atual: {invalid[:20]}")


def execute(*, allow_skipped: bool = False) -> dict[str, Any]:
    manifest = generate_manifest()
    validation = validate_manifest(manifest)
    if validation["wrong"]:
        raise RuntimeError(f"validacao falhou: {validation['wrong'][:5]}")
    if manifest["total_retry"] != EXPECTED_TOTAL or (manifest["total_skipped"] and not allow_skipped):
        raise RuntimeError(
            f"esperado {EXPECTED_TOTAL} XMLs"
            f"{'' if allow_skipped else ' e 0 skipped'}: "
            f"retry={manifest['total_retry']} skipped={manifest['total_skipped']}"
        )
    senha = correcao_base.read_password()
    signed = sign_targets(manifest["targets"], senha)

    conn_db = db.connect(empresa_id=EMPRESA_ID)
    conn_w = db.connect(empresa_id=EMPRESA_ID)
    try:
        envio_base.PER_APUR = PER_APUR
        envio_base.PREFLIGHT = MANIFEST
        envio_base.CFG_GRUPO = correcao_base.GRUPO
        envio_base.POLL_TENTATIVAS = correcao_base.POLL_TENTATIVAS
        envio_base.POLL_INTERVALO_S = correcao_base.POLL_INTERVALO_S
        assert_still_current_459(conn_db, signed)
        envio_id, mes_id = correcao_base._create_timeline_envio(conn_db, PER_APUR, len(signed), MANIFEST)
        print(f"=> retry 459 recriar original {PER_APUR}: envio_id={envio_id} timeline_mes={mes_id} targets={len(signed)}")
        item_ids = envio_base._criar_items(conn_db, envio_id, signed)
        envio_base._persistir_xmls_assinados(conn_db, conn_w, signed, item_ids)

        sucesso = 0
        erro = 0
        histograma: dict[str, int] = {}
        protocolos: list[str] = []
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
            sucesso += int(resultado["sucesso"])
            erro += int(resultado["erro"])
            if resultado.get("protocolo"):
                protocolos.append(str(resultado["protocolo"]))
            for codigo, total in (resultado.get("histograma") or {}).items():
                histograma[codigo] = histograma.get(codigo, 0) + int(total)

        envio_base._atualizar_envio(
            conn_db,
            envio_id,
            status="concluido",
            sucesso=sucesso,
            erro=erro,
            resumo_extra={
                "rotulo_final": "retry_459_recriar_s1210_original_pos_s3000",
                "per_apur": PER_APUR,
                "manifest": str(MANIFEST),
                "protocolos": protocolos,
                "histograma_erros": histograma,
            },
        )
        target_cpfs = [item["cpf"] for item in manifest["targets"]]
        latest = correcao_base.latest_status_summary(PER_APUR, target_cpfs)
        result = {
            "per_apur": PER_APUR,
            "envio_id": envio_id,
            "sucesso": sucesso,
            "erro": erro,
            "protocolos": protocolos,
            "histograma": histograma,
            "manifest": str(MANIFEST),
            "latest": latest,
        }
        RESULT.write_text(json.dumps(result, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
        return result
    finally:
        conn_db.close()
        conn_w.close()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--per-apur", default=PER_APUR)
    parser.add_argument("--expected-total", type=int, default=EXPECTED_TOTAL)
    parser.add_argument("--cpf", action="append", default=[])
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--allow-skipped", action="store_true")
    parser.add_argument("--confirmar", default="")
    args = parser.parse_args()
    if not re.fullmatch(r"20\d{2}-\d{2}", args.per_apur):
        raise SystemExit(f"per_apur invalido: {args.per_apur}")
    configure(args.per_apur, args.expected_total, args.cpf)
    if not args.execute:
        manifest = generate_manifest()
        print(json.dumps({"manifest": manifest, "validation": validate_manifest(manifest)}, ensure_ascii=False, indent=2, default=str))
        return 0
    if args.confirmar != confirm_token():
        raise SystemExit(f"Para executar, use --confirmar {confirm_token()}")
    print(json.dumps(execute(allow_skipped=args.allow_skipped), ensure_ascii=False, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())