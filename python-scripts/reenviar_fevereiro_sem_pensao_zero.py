from __future__ import annotations

import argparse
import json
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
import psycopg2.extras  # noqa: E402
from app import db, esocial_client, tenant  # noqa: E402
from app.xml_s1210 import NS as S1210_NS, _gerar_id  # noqa: E402
from app.xml_signer import S1010XMLSigner  # noqa: E402


EMPRESA_ID = 2
PER_APUR = "2025-02"
CNPJ = "09445502000109"
CNPJ_RAIZ = CNPJ[:8]
CONFIRM_TOKEN = "REENVIAR_FEVEREIRO_SEM_PENSAO_ZERO"
TARGET_CPFS = ["28710124829", "71985883104"]
OUT_DIR = ROOT / "relatorio_ana" / "CORRECAO_JAQUE_PLANO_PENSAO_2025" / PER_APUR / "retry_sem_pensao_zero"
XML_DIR = OUT_DIR / "xml_unsigned"
ORIGINAL_XML_DIR = ROOT / "relatorio_ana" / "CORRECAO_JAQUE_PLANO_PENSAO_2025" / PER_APUR / "xml_unsigned"
MANIFEST_PATH = OUT_DIR / "manifest_retry_sem_pensao_zero.json"
RESULT_PATH = OUT_DIR / "resultado_retry_sem_pensao_zero.json"


def direct_children(parent: etree._Element, tag: str) -> list[etree._Element]:
    return parent.xpath(f'./*[local-name()="{tag}"]')


def qname(tag: str) -> str:
    return f"{{{S1210_NS}}}{tag}"


def sub(parent: etree._Element, tag: str, value: str | None = None) -> etree._Element:
    child = etree.SubElement(parent, qname(tag))
    if value is not None:
        child.text = value
    return child


def latest_rows(cpfs: list[str]) -> dict[str, dict[str, Any]]:
    internal_empresa_id = tenant.internal_empresa_id(EMPRESA_ID)
    conn = db.connect(empresa_id=EMPRESA_ID)
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
            cursor.execute(
                """
                WITH latest AS (
                    SELECT DISTINCT ON (it.cpf)
                           it.cpf, it.status, it.erro_codigo, it.erro_mensagem,
                           it.versao_anterior_id AS evento_id,
                           it.nr_recibo_anterior, it.nr_recibo_novo,
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
            return {str(row["cpf"]): dict(row) for row in cursor.fetchall()}
    finally:
        conn.close()


def remove_penalim(xml_bytes: bytes) -> tuple[bytes, dict[str, Any]]:
    root = etree.fromstring(xml_bytes)
    for signature in root.xpath('.//*[local-name()="Signature"]'):
        parent = signature.getparent()
        if parent is not None:
            parent.remove(signature)
    evt = root.xpath('//*[local-name()="evtPgtos"]')[0]
    evt.set("Id", _gerar_id(1, CNPJ_RAIZ))
    per_apur = root.xpath('string(//*[local-name()="perApur"])')
    cpf_benef = root.xpath('string(//*[local-name()="cpfBenef"])')
    if per_apur != PER_APUR:
        raise RuntimeError(f"perApur divergente: {per_apur}")
    removed = []
    ircr_nodes = root.xpath('//*[local-name()="infoIRCR"]')
    for ircr in ircr_nodes:
        for pen_alim in direct_children(ircr, "penAlim"):
            removed.append(
                {
                    "tpRend": pen_alim.xpath('string(./*[local-name()="tpRend"])'),
                    "cpfDep": pen_alim.xpath('string(./*[local-name()="cpfDep"])'),
                    "vlrDedPenAlim": pen_alim.xpath('string(./*[local-name()="vlrDedPenAlim"])'),
                }
            )
            ircr.remove(pen_alim)
    info_ir_nodes = root.xpath('//*[local-name()="infoIRComplem"]')
    if not info_ir_nodes:
        raise RuntimeError(f"XML {cpf_benef} sem infoIRComplem")
    info_ir = info_ir_nodes[0]
    ded_dep_cpfs = []
    for node in root.xpath('//*[local-name()="dedDepen"]/*[local-name()="cpfDep"]'):
        cpf_dep = (node.text or "").strip()
        if cpf_dep and cpf_dep not in ded_dep_cpfs:
            ded_dep_cpfs.append(cpf_dep)
    existing_info_dep = {
        node.xpath('string(./*[local-name()="cpfDep"])').strip()
        for node in direct_children(info_ir, "infoDep")
    }
    added_info_dep = []
    if ded_dep_cpfs:
        ircr_children = direct_children(info_ir, "infoIRCR")
        insert_at = info_ir.index(ircr_children[0]) if ircr_children else 0
        for cpf_dep in ded_dep_cpfs:
            if cpf_dep in existing_info_dep:
                continue
            info_dep = etree.Element(qname("infoDep"))
            sub(info_dep, "cpfDep", cpf_dep)
            info_ir.insert(insert_at, info_dep)
            insert_at += 1
            existing_info_dep.add(cpf_dep)
            added_info_dep.append(cpf_dep)
    counts = {
        "cpfBenef": cpf_benef,
        "infoPgto": len(root.xpath('//*[local-name()="infoPgto"]')),
        "infoIRCR": len(root.xpath('//*[local-name()="infoIRCR"]')),
        "dedDepen": len(root.xpath('//*[local-name()="dedDepen"]')),
        "infoDep": len(root.xpath('//*[local-name()="infoDep"]')),
        "added_infoDep": added_info_dep,
        "penAlim": len(root.xpath('//*[local-name()="penAlim"]')),
        "removed_penAlim": removed,
        "nrRecibo": root.xpath('string(//*[local-name()="nrRecibo"])'),
        "indRetif": root.xpath('string(//*[local-name()="indRetif"])'),
        "id": evt.get("Id"),
    }
    if not removed:
        raise RuntimeError(f"XML {cpf_benef} nao tinha penAlim para remover")
    if counts["penAlim"] != 0:
        raise RuntimeError(f"XML {cpf_benef} ainda ficou com penAlim")
    if counts["indRetif"] != "2" or not counts["nrRecibo"]:
        raise RuntimeError(f"XML {cpf_benef} nao esta retificativo com nrRecibo")
    return etree.tostring(root, xml_declaration=True, encoding="UTF-8"), counts


def generate_manifest() -> dict[str, Any]:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    XML_DIR.mkdir(parents=True, exist_ok=True)
    for old_xml in XML_DIR.glob("*.xml"):
        old_xml.unlink()
    latest = latest_rows(TARGET_CPFS)
    targets: list[dict[str, Any]] = []
    blocked: list[dict[str, Any]] = []
    for cpf in TARGET_CPFS:
        row = latest.get(cpf)
        if not row or row.get("status") != "erro_esocial":
            blocked.append({"cpf": cpf, "reason": "latest nao e erro_esocial", "latest": row})
            continue
        source_xml = ORIGINAL_XML_DIR / f"S1210_{PER_APUR}_{cpf}_jaque_unsigned.xml"
        if not source_xml.exists():
            blocked.append({"cpf": cpf, "reason": f"XML falhado nao encontrado: {source_xml}", "latest": row})
            continue
        xml_new, counts = remove_penalim(source_xml.read_bytes())
        out_xml = XML_DIR / f"S1210_{PER_APUR}_{cpf}_sem_pensao_unsigned.xml"
        out_xml.write_bytes(xml_new)
        evento_id = row.get("evento_id")
        nr_recibo = row.get("nr_recibo_anterior") or counts["nrRecibo"]
        if not evento_id or not nr_recibo:
            blocked.append({"cpf": cpf, "reason": "latest sem evento_id/nr_recibo", "latest": row})
            continue
        targets.append(
            {
                "cpf": cpf,
                "evento_id": evento_id,
                "nr_recibo": nr_recibo,
                "xml": str(out_xml),
                "source_xml": str(source_xml),
                "latest_item_id": row.get("item_id"),
                "latest_envio_id": row.get("envio_id"),
                "latest_erro_codigo": row.get("erro_codigo"),
                "latest_erro_mensagem": row.get("erro_mensagem"),
                "has_plano": False,
                "has_pensao": False,
                **counts,
            }
        )
    manifest = {
        "empresa_id": EMPRESA_ID,
        "per_apur": PER_APUR,
        "regra": "reenviar CPFs que nao possuem pensao; remover completamente penAlim zerado, preservar dedDepen e declarar estes dependentes em infoDep",
        "quinzenas_referencia": [
            r"C:\Users\xandao\Downloads\todos os meses 2025 SOLUCOES\SOLUCOES_2025-03(01-15).zip",
            r"C:\Users\xandao\Downloads\todos os meses 2025 SOLUCOES\SOLUCOES_2025-03(15-31).zip",
        ],
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
        root = etree.fromstring(Path(item["xml"]).read_bytes())
        rows.append(
            {
                "cpf": item["cpf"],
                "cpfBenef": root.xpath('string(//*[local-name()="cpfBenef"])'),
                "perApur": root.xpath('string(//*[local-name()="perApur"])'),
                "indRetif": root.xpath('string(//*[local-name()="indRetif"])'),
                "nrRecibo": root.xpath('string(//*[local-name()="nrRecibo"])'),
                "infoPgto": len(root.xpath('//*[local-name()="infoPgto"]')),
                "infoIRCR": len(root.xpath('//*[local-name()="infoIRCR"]')),
                "dedDepen": len(root.xpath('//*[local-name()="dedDepen"]')),
                "infoDep": len(root.xpath('//*[local-name()="infoDep"]')),
                "penAlim": len(root.xpath('//*[local-name()="penAlim"]')),
                "signature": bool(root.xpath('//*[local-name()="Signature"]')),
                "id": esocial_client._extrair_id(Path(item["xml"]).read_bytes()),
            }
        )
    wrong = [
        row
        for row in rows
        if row["cpf"] != row["cpfBenef"]
        or row["perApur"] != PER_APUR
        or row["indRetif"] != "2"
        or not row["nrRecibo"]
        or row["penAlim"] != 0
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
        print(f"=> retry sem pensao: envio_id={envio_id} timeline_mes={mes_id} targets={len(signed)}")
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
                "rotulo_final": "retry_fevereiro_sem_pensao_zero",
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