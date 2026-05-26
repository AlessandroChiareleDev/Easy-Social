from __future__ import annotations

import argparse
import csv
import json
import os
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
PER_APUR = "2025-02"
CNPJ = "09445502000109"
CNPJ_RAIZ = CNPJ[:8]
CONFIRM_TOKEN = "RETRY_FEVEREIRO_INFODEP_1861"
OUT_DIR = ROOT / "relatorio_ana" / "CORRECAO_JAQUE_PLANO_PENSAO_2025" / PER_APUR / "retry_infodep_1861"
XML_DIR = OUT_DIR / "xml_unsigned"
MANIFEST_ORIGINAL = ROOT / "relatorio_ana" / "CORRECAO_JAQUE_PLANO_PENSAO_2025" / PER_APUR / "manifest_correcao_jaque_2025-02.json"
ERROS_CSV = ROOT / "relatorio_ana" / "CORRECAO_JAQUE_PLANO_PENSAO_2025" / PER_APUR / "erros_pos_envio_931.csv"
MANIFEST_RETRY = OUT_DIR / "manifest_retry_infodep_1861.json"
PENDENTES_ZERO = OUT_DIR / "pendentes_valor_zero.csv"


def qname(tag: str) -> str:
    return f"{{{S1210_NS}}}{tag}"


def direct_children(parent: etree._Element, tag: str) -> list[etree._Element]:
    return parent.xpath(f'./*[local-name()="{tag}"]')


def sub(parent: etree._Element, tag: str, value: str | None = None) -> etree._Element:
    child = etree.SubElement(parent, qname(tag))
    if value is not None:
        child.text = value
    return child


def add_info_dep(xml_bytes: bytes, cpf_dep: str) -> bytes:
    root = etree.fromstring(xml_bytes)
    for signature in root.xpath('.//*[local-name()="Signature"]'):
        parent = signature.getparent()
        if parent is not None:
            parent.remove(signature)

    evt = root.xpath('//*[local-name()="evtPgtos"]')[0]
    evt.set("Id", _gerar_id(1, CNPJ_RAIZ))
    info_ir_nodes = root.xpath('//*[local-name()="infoIRComplem"]')
    if not info_ir_nodes:
        raise RuntimeError("infoIRComplem ausente")
    info_ir = info_ir_nodes[0]
    existing = {node.xpath('string(./*[local-name()="cpfDep"])').strip() for node in direct_children(info_ir, "infoDep")}
    if cpf_dep not in existing:
        info_dep = etree.Element(qname("infoDep"))
        sub(info_dep, "cpfDep", cpf_dep)
        ircr_nodes = direct_children(info_ir, "infoIRCR")
        insert_at = info_ir.index(ircr_nodes[0]) if ircr_nodes else 0
        info_ir.insert(insert_at, info_dep)
    if root.xpath('string(//*[local-name()="perApur"])') != PER_APUR:
        raise RuntimeError("perApur divergente")
    if not root.xpath('//*[local-name()="penAlim"]'):
        raise RuntimeError("penAlim ausente")
    return etree.tostring(root, xml_declaration=True, encoding="UTF-8")


def load_error_rows() -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    retry_rows: list[dict[str, str]] = []
    zero_rows: list[dict[str, str]] = []
    with ERROS_CSV.open("r", encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            codigo = str(row.get("erro_codigo") or "")
            message = str(row.get("erro_mensagem") or "")
            if codigo == "401" and "1861" in message and row.get("cpf_dependente"):
                retry_rows.append(row)
            elif codigo == "402" and "vlrDedPenAlim" in message:
                zero_rows.append(row)
    return retry_rows, zero_rows


def latest_error_cpfs(cpfs: list[str]) -> set[str]:
    if not cpfs:
        return set()
    internal_empresa_id = tenant.internal_empresa_id(EMPRESA_ID)
    conn = db.connect(empresa_id=EMPRESA_ID)
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                WITH latest AS (
                    SELECT DISTINCT ON (it.cpf)
                           it.cpf, it.status, it.erro_codigo, it.erro_mensagem
                      FROM timeline_envio_item it
                      JOIN timeline_envio te ON te.id = it.timeline_envio_id
                      JOIN timeline_mes tm ON tm.id = te.timeline_mes_id
                     WHERE tm.empresa_id = %s
                       AND tm.per_apur = %s
                       AND it.tipo_evento = 'S-1210'
                       AND it.cpf = ANY(%s)
                     ORDER BY it.cpf, it.criado_em DESC NULLS LAST, it.id DESC
                )
                SELECT cpf FROM latest
                 WHERE status = 'erro_esocial'
                   AND erro_codigo = '401'
                   AND erro_mensagem LIKE '%%1861%%'
                """,
                (internal_empresa_id, PER_APUR, cpfs),
            )
            return {row[0] for row in cursor.fetchall()}
    finally:
        conn.close()


def generate_manifest() -> dict[str, Any]:
    if not MANIFEST_ORIGINAL.exists():
        raise RuntimeError(f"manifest original nao encontrado: {MANIFEST_ORIGINAL}")
    if not ERROS_CSV.exists():
        raise RuntimeError(f"CSV de erros nao encontrado: {ERROS_CSV}")
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    XML_DIR.mkdir(parents=True, exist_ok=True)
    for old_xml in XML_DIR.glob("*.xml"):
        old_xml.unlink()

    original = json.loads(MANIFEST_ORIGINAL.read_text(encoding="utf-8"))
    targets_by_cpf = {item["cpf"]: item for item in original.get("targets") or [] if item.get("generated")}
    retry_rows, zero_rows = load_error_rows()
    still_error = latest_error_cpfs([row["cpf"] for row in retry_rows])
    targets: list[dict[str, Any]] = []
    skipped: list[dict[str, Any]] = []
    for row in retry_rows:
        cpf = row["cpf"]
        if cpf not in still_error:
            skipped.append({**row, "reason": "ultimo status nao e mais 401/1861"})
            continue
        original_target = targets_by_cpf.get(cpf)
        if not original_target:
            skipped.append({**row, "reason": "cpf ausente do manifest original"})
            continue
        xml_new = add_info_dep(Path(original_target["xml"]).read_bytes(), row["cpf_dependente"])
        out_xml = XML_DIR / f"S1210_{PER_APUR}_{cpf}_infodep_1861_unsigned.xml"
        out_xml.write_bytes(xml_new)
        targets.append(
            {
                "cpf": cpf,
                "cpf_dependente": row["cpf_dependente"],
                "xml": str(out_xml),
                "evento_id": original_target["evento_id"],
                "nr_recibo": original_target["nr_recibo"],
                "has_plano": False,
                "has_pensao": True,
                "source_item_id": original_target.get("item_id"),
                "source_envio_id": original_target.get("envio_id"),
            }
        )

    with PENDENTES_ZERO.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["cpf", "erro_codigo", "erro_mensagem", "cpf_dependente", "no_manifest_pensao_plano"], extrasaction="ignore")
        writer.writeheader()
        writer.writerows(zero_rows)

    manifest = {
        "empresa_id": EMPRESA_ID,
        "per_apur": PER_APUR,
        "origem": str(ERROS_CSV),
        "regra": "retry somente 401/1861 de pensao; inserir infoDep/cpfDep no proprio S-1210; excluir 402 valor zero",
        "total_retry": len(targets),
        "total_skipped": len(skipped),
        "pendentes_zero": len(zero_rows),
        "targets": targets,
        "skipped": skipped,
        "zero_rows": zero_rows,
    }
    MANIFEST_RETRY.write_text(json.dumps(manifest, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    return manifest


def validate_manifest(manifest: dict[str, Any]) -> dict[str, Any]:
    rows = []
    for item in manifest["targets"]:
        root = etree.fromstring(Path(item["xml"]).read_bytes())
        rows.append(
            {
                "cpf": item["cpf"],
                "cpf_dependente": item["cpf_dependente"],
                "id": esocial_client._extrair_id(Path(item["xml"]).read_bytes()),
                "perApur": root.xpath('string(//*[local-name()="perApur"])'),
                "infoDep": root.xpath('string(//*[local-name()="infoDep"]/*[local-name()="cpfDep"])'),
                "penAlim": root.xpath('string(//*[local-name()="penAlim"]/*[local-name()="cpfDep"])'),
                "signature": bool(root.xpath('//*[local-name()="Signature"]')),
            }
        )
    wrong = [row for row in rows if row["perApur"] != PER_APUR or row["infoDep"] != row["cpf_dependente"] or row["signature"]]
    return {"total": len(rows), "wrong": wrong, "sample": rows[:10]}


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
    if validation["wrong"]:
        raise RuntimeError(f"validacao falhou: {validation['wrong'][:5]}")
    if not manifest["targets"]:
        raise RuntimeError("nenhum alvo para retry")
    senha = correcao_base.read_password()
    signed = sign_targets(manifest["targets"], senha)
    conn_db = db.connect(empresa_id=EMPRESA_ID)
    conn_w = db.connect(empresa_id=EMPRESA_ID)
    try:
        envio_base.PER_APUR = PER_APUR
        envio_base.PREFLIGHT = MANIFEST_RETRY
        envio_base.CFG_GRUPO = correcao_base.GRUPO
        envio_base.POLL_TENTATIVAS = correcao_base.POLL_TENTATIVAS
        envio_base.POLL_INTERVALO_S = correcao_base.POLL_INTERVALO_S
        envio_base._verificar_estado_atual(conn_db, signed)
        envio_id, mes_id = correcao_base._create_timeline_envio(conn_db, PER_APUR, len(signed), MANIFEST_RETRY)
        print(f"=> retry infodep: envio_id={envio_id} timeline_mes={mes_id} targets={len(signed)}")
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
                "rotulo_final": "retry_fevereiro_pensao_infodep_1861",
                "manifest": str(MANIFEST_RETRY),
                "protocolos": protocolos,
                "histograma_erros": histograma,
                "pendentes_zero": str(PENDENTES_ZERO),
            },
        )
        result = {
            "envio_id": envio_id,
            "sucesso": sucesso_total,
            "erro": erro_total,
            "protocolos": protocolos,
            "histograma": histograma,
            "manifest": str(MANIFEST_RETRY),
            "pendentes_zero": str(PENDENTES_ZERO),
        }
        (OUT_DIR / "resultado_retry_infodep_1861.json").write_text(json.dumps(result, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
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