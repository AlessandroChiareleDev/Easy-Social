from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

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
CNPJ_RAIZ = CNPJ[:8]


def qname(tag: str) -> str:
    return f"{{{S1210_NS}}}{tag}"


def cpf11(value: Any) -> str:
    digits = re.sub(r"\D", "", str(value or ""))
    return digits.zfill(11)[-11:] if digits else ""


def confirm_token(per_apur: str) -> str:
    return f"RETRY_{per_apur.replace('-', '_')}_INFODEP_1861"


def month_dir(per_apur: str) -> Path:
    return ROOT / "relatorio_ana" / "CORRECAO_JAQUE_PLANO_PENSAO_2025" / per_apur


def retry_dir(per_apur: str) -> Path:
    return month_dir(per_apur) / "retry_infodep_1861"


def xml_dir(per_apur: str) -> Path:
    return retry_dir(per_apur) / "xml_unsigned"


def original_manifest_path(per_apur: str) -> Path:
    return month_dir(per_apur) / f"manifest_correcao_jaque_{per_apur}.json"


def original_result_path(per_apur: str) -> Path:
    return month_dir(per_apur) / f"resultado_execucao_{per_apur}.json"


def retry_manifest_path(per_apur: str) -> Path:
    return retry_dir(per_apur) / "manifest_retry_infodep_1861.json"


def extract_cpf_dependente(message: str) -> str:
    patterns = [
        r"CPF do dependente\s+(\d{11})",
        r"dependente\s+(\d{11})\s+inv",
        r"cpfDep[^0-9]*(\d{11})",
    ]
    for pattern in patterns:
        match = re.search(pattern, message, flags=re.IGNORECASE)
        if match:
            return cpf11(match.group(1))
    return ""


def direct_children(parent: etree._Element, tag: str) -> list[etree._Element]:
    return parent.xpath(f'./*[local-name()="{tag}"]')


def sub(parent: etree._Element, tag: str, value: str | None = None) -> etree._Element:
    child = etree.SubElement(parent, qname(tag))
    if value is not None:
        child.text = value
    return child


def add_info_dep(xml_bytes: bytes, per_apur: str, cpf_dependente: str) -> bytes:
    root = etree.fromstring(xml_bytes)
    for signature in root.xpath('.//*[local-name()="Signature"]'):
        parent = signature.getparent()
        if parent is not None:
            parent.remove(signature)

    event_nodes = root.xpath('//*[local-name()="evtPgtos"]')
    if not event_nodes:
        raise RuntimeError("evtPgtos ausente")
    event_nodes[0].set("Id", _gerar_id(1, CNPJ_RAIZ))

    info_ir_nodes = root.xpath('//*[local-name()="infoIRComplem"]')
    if not info_ir_nodes:
        raise RuntimeError("infoIRComplem ausente")
    info_ir = info_ir_nodes[0]

    existing = {node.xpath('string(./*[local-name()="cpfDep"])').strip() for node in direct_children(info_ir, "infoDep")}
    if cpf_dependente not in existing:
        info_dep = etree.Element(qname("infoDep"))
        sub(info_dep, "cpfDep", cpf_dependente)
        ircr_nodes = direct_children(info_ir, "infoIRCR")
        insert_at = info_ir.index(ircr_nodes[0]) if ircr_nodes else 0
        info_ir.insert(insert_at, info_dep)

    if root.xpath('string(//*[local-name()="perApur"])') != per_apur:
        raise RuntimeError("perApur divergente")
    if not root.xpath('//*[local-name()="penAlim"]'):
        raise RuntimeError("penAlim ausente")
    return etree.tostring(root, xml_declaration=True, encoding="UTF-8")


def load_result_error_rows(per_apur: str) -> list[dict[str, Any]]:
    path = original_result_path(per_apur)
    if not path.exists():
        raise RuntimeError(f"resultado original nao encontrado: {path}")
    result = json.loads(path.read_text(encoding="utf-8"))
    rows: list[dict[str, Any]] = []
    for row in (result.get("latest") or {}).get("rows") or []:
        message = str(row.get("erro_mensagem") or "")
        cpf_dependente = extract_cpf_dependente(message)
        if row.get("status") == "erro_esocial" and str(row.get("erro_codigo") or "") == "401" and "1861" in message and cpf_dependente:
            rows.append({**row, "cpf": cpf11(row.get("cpf")), "cpf_dependente": cpf_dependente})
    return rows


def latest_1861_errors(per_apur: str, cpfs: list[str]) -> dict[str, dict[str, Any]]:
    if not cpfs:
        return {}
    internal_empresa_id = tenant.internal_empresa_id(EMPRESA_ID)
    conn = db.connect(empresa_id=EMPRESA_ID)
    try:
        with conn.cursor() as cursor:
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
                SELECT cpf, status, erro_codigo, erro_mensagem, item_id, envio_id, criado_em
                  FROM latest
                 WHERE status = 'erro_esocial'
                   AND erro_codigo = '401'
                   AND erro_mensagem LIKE '%%1861%%'
                """,
                (internal_empresa_id, per_apur, cpfs),
            )
            output: dict[str, dict[str, Any]] = {}
            for cpf, status, erro_codigo, erro_mensagem, item_id, envio_id, criado_em in cursor.fetchall():
                cpf_key = cpf11(cpf)
                output[cpf_key] = {
                    "cpf": cpf_key,
                    "status": status,
                    "erro_codigo": erro_codigo,
                    "erro_mensagem": erro_mensagem,
                    "cpf_dependente": extract_cpf_dependente(str(erro_mensagem or "")),
                    "item_id": item_id,
                    "envio_id": envio_id,
                    "criado_em": criado_em,
                }
            return output
    finally:
        conn.close()


def generate_manifest(per_apur: str) -> dict[str, Any]:
    if not original_manifest_path(per_apur).exists():
        raise RuntimeError(f"manifest original nao encontrado: {original_manifest_path(per_apur)}")

    retry_dir(per_apur).mkdir(parents=True, exist_ok=True)
    xml_dir(per_apur).mkdir(parents=True, exist_ok=True)
    for old_xml in xml_dir(per_apur).glob("*.xml"):
        old_xml.unlink()

    original = json.loads(original_manifest_path(per_apur).read_text(encoding="utf-8"))
    original_targets = {item["cpf"]: item for item in original.get("targets") or [] if item.get("generated")}
    result_rows = load_result_error_rows(per_apur)
    latest_errors = latest_1861_errors(per_apur, [row["cpf"] for row in result_rows])

    targets: list[dict[str, Any]] = []
    skipped: list[dict[str, Any]] = []
    for row in result_rows:
        cpf = row["cpf"]
        latest = latest_errors.get(cpf)
        if not latest:
            skipped.append({**row, "reason": "ultimo status nao e mais 401/1861"})
            continue
        cpf_dependente = latest.get("cpf_dependente") or row.get("cpf_dependente") or ""
        original_target = original_targets.get(cpf)
        if not original_target:
            skipped.append({**row, "reason": "cpf ausente do manifest original"})
            continue
        xml_new = add_info_dep(Path(original_target["xml"]).read_bytes(), per_apur, cpf_dependente)
        out_xml = xml_dir(per_apur) / f"S1210_{per_apur}_{cpf}_infodep_1861_unsigned.xml"
        out_xml.write_bytes(xml_new)
        targets.append(
            {
                "cpf": cpf,
                "cpf_dependente": cpf_dependente,
                "xml": str(out_xml),
                "evento_id": original_target.get("evento_id"),
                "nr_recibo": original_target.get("nr_recibo"),
                "has_plano": bool(original_target.get("has_plano")),
                "has_pensao": bool(original_target.get("has_pensao")),
                "source_item_id": latest.get("item_id"),
                "source_envio_id": latest.get("envio_id"),
            }
        )

    manifest = {
        "empresa_id": EMPRESA_ID,
        "per_apur": per_apur,
        "origem_resultado": str(original_result_path(per_apur)),
        "origem_manifest": str(original_manifest_path(per_apur)),
        "regra": "retry 401/1861 de pensao: inserir infoDep/cpfDep no proprio S-1210",
        "total_result_errors_1861": len(result_rows),
        "total_retry": len(targets),
        "total_skipped": len(skipped),
        "targets": targets,
        "skipped": skipped,
    }
    retry_manifest_path(per_apur).write_text(json.dumps(manifest, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    return manifest


def validate_manifest(manifest: dict[str, Any]) -> dict[str, Any]:
    rows = []
    for item in manifest.get("targets") or []:
        xml_bytes = Path(item["xml"]).read_bytes()
        root = etree.fromstring(xml_bytes)
        info_dep_cpfs = [node.xpath('string(./*[local-name()="cpfDep"])') for node in root.xpath('//*[local-name()="infoDep"]')]
        pen_alim_cpfs = [node.xpath('string(./*[local-name()="cpfDep"])') for node in root.xpath('//*[local-name()="penAlim"]')]
        rows.append(
            {
                "cpf": item["cpf"],
                "cpf_dependente": item["cpf_dependente"],
                "id": esocial_client._extrair_id(xml_bytes),
                "perApur": root.xpath('string(//*[local-name()="perApur"])'),
                "infoDep": info_dep_cpfs,
                "penAlim": pen_alim_cpfs,
                "signature": bool(root.xpath('//*[local-name()="Signature"]')),
            }
        )
    wrong = [
        row for row in rows
        if row["perApur"] != manifest["per_apur"] or row["cpf_dependente"] not in row["infoDep"] or row["signature"]
    ]
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
        envio_base.PREFLIGHT = retry_manifest_path(per_apur)
        envio_base.CFG_GRUPO = correcao_base.GRUPO
        envio_base.POLL_TENTATIVAS = correcao_base.POLL_TENTATIVAS
        envio_base.POLL_INTERVALO_S = correcao_base.POLL_INTERVALO_S
        envio_base._verificar_estado_atual(conn_db, signed)
        envio_id, mes_id = correcao_base._create_timeline_envio(conn_db, per_apur, len(signed), retry_manifest_path(per_apur))
        print(f"=> retry infodep {per_apur}: envio_id={envio_id} timeline_mes={mes_id} targets={len(signed)}")
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
                "rotulo_final": "retry_mes_pensao_infodep_1861",
                "per_apur": per_apur,
                "manifest": str(retry_manifest_path(per_apur)),
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
            "manifest": str(retry_manifest_path(per_apur)),
            "latest": latest,
        }
        (retry_dir(per_apur) / "resultado_retry_infodep_1861.json").write_text(
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