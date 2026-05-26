from __future__ import annotations

import argparse
import json
import os
import re
import sys
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

import pandas as pd
from lxml import etree


ROOT = Path(r"C:\Users\xandao\Documents\GitHub\Easy-Social")
BACKEND_V2 = Path(r"C:\Users\xandao\Documents\GitHub\Easy-eSocial-v2\backend")
if str(ROOT / "python-scripts") not in sys.path:
    sys.path.insert(0, str(ROOT / "python-scripts"))
if str(BACKEND_V2) not in sys.path:
    sys.path.insert(0, str(BACKEND_V2))

import enviar_correcao_agosto_jaque as envio_base  # noqa: E402
from app import db, esocial_client, tenant  # noqa: E402
from app.xml_s1210 import NS, _gerar_id  # noqa: E402
from app.xml_signer import S1010XMLSigner  # noqa: E402


EMPRESA_ID = 2
PER_APUR = "2025-08"
CONFIRM_TOKEN = "JAQUE_2_0_5"
XLSX = Path(r"C:\Users\xandao\Downloads\SOLUCOES_AGOSTO_2025_JAQUE_PLANO_PENSAO_PREENChido 2.0.xlsx")
OUT_DIR = ROOT / "relatorio_ana" / "CORRECAO_AGOSTO_JAQUE_2_0"
XML_DIR = OUT_DIR / "xml_unsigned"
MANIFEST = OUT_DIR / "manifest_jaque_2_0_5.json"

BASE_XMLS = {
    "14193059804": Path(r"C:\Users\xandao\Downloads\solucoes\ARQUIVOS 1210\ARQUIVOS 1210\SETEMBRO\ID1094455020000002025091819045800006.S-1210.xml"),
    "25585996827": Path(r"C:\Users\xandao\Downloads\solucoes\ARQUIVOS 1210\ARQUIVOS 1210\SETEMBRO\ID1094455020000002025091819064600010.S-1210.xml"),
    "30729903877": Path(r"C:\Users\xandao\Downloads\solucoes\ARQUIVOS 1210\ARQUIVOS 1210\SETEMBRO\ID1094455020000002025091819041800014.S-1210.xml"),
    "38870126404": Path(r"C:\Users\xandao\Downloads\solucoes\ARQUIVOS 1210\ARQUIVOS 1210\SETEMBRO\ID1094455020000002025091819152500005.S-1210.xml"),
    "39428963895": Path(r"C:\Users\xandao\Downloads\solucoes\ARQUIVOS 1210\ARQUIVOS 1210\SETEMBRO\ID1094455020000002025091819212400001.S-1210.xml"),
}


def digits(value: Any) -> str:
    return re.sub(r"\D", "", str(value or ""))


def cpf11(value: Any) -> str:
    only_digits = digits(value)
    return only_digits.zfill(11) if only_digits else ""


def money(value: Any) -> Decimal:
    if value is None or str(value).strip() == "" or str(value) == "nan":
        return Decimal("0.00")
    return Decimal(str(value).replace("R$", "").replace(".", "").replace(",", ".") if "," in str(value) else str(value)).quantize(Decimal("0.01"))


def money_str(value: Decimal) -> str:
    return f"{value.quantize(Decimal('0.01')):.2f}"


def qname(tag: str) -> str:
    return f"{{{NS}}}{tag}"


def direct_child(parent: etree._Element, tag: str) -> etree._Element | None:
    found = parent.xpath(f'./*[local-name()="{tag}"]')
    return found[0] if found else None


def set_child(parent: etree._Element, tag: str, value: str, after_tag: str | None = None) -> etree._Element:
    child = direct_child(parent, tag)
    if child is not None:
        child.text = value
        return child
    child = etree.Element(qname(tag))
    child.text = value
    insert_at = len(parent)
    if after_tag:
        for index, existing in enumerate(parent):
            if etree.QName(existing).localname == after_tag:
                insert_at = index + 1
                break
    parent.insert(insert_at, child)
    return child


def sub(parent: etree._Element, tag: str, value: str | None = None) -> etree._Element:
    child = etree.SubElement(parent, qname(tag))
    if value is not None:
        child.text = value
    return child


def inner_event_root(path: Path) -> etree._Element:
    root = etree.parse(str(path)).getroot()
    candidates = root.xpath('//*[local-name()="eSocial" and ./*[local-name()="evtPgtos"]]')
    if not candidates:
        raise RuntimeError(f"XML S-1210 interno nao encontrado: {path}")
    inner = candidates[0]
    for signature in inner.xpath('.//*[local-name()="Signature"]'):
        parent = signature.getparent()
        if parent is not None:
            parent.remove(signature)
    return inner


def load_planilha() -> tuple[dict[str, dict[str, Any]], dict[str, dict[str, Any]]]:
    plano_df = pd.read_excel(XLSX, sheet_name="Plano de saude")
    pensao_df = pd.read_excel(XLSX, sheet_name="Pensao alimenticia")
    plano: dict[str, dict[str, Any]] = {}
    for _, row in plano_df.iterrows():
        cpf = cpf11(row.get("CPF Normalizado") or row.get("CPF"))
        if not cpf:
            continue
        titular = money(row.get("Valor Titular Descontado em Folha "))
        dependente = money(row.get("Valor dependente Descontado em Folha "))
        plano[cpf] = {
            "cnpjOper": digits(row.get("CNPJ Operadora")).zfill(14),
            "regANS": digits(row.get("Registro ANS")),
            "vlrSaudeTit": money_str(titular),
            "vlrSaudeDepSemCpf": money_str(dependente) if dependente > 0 else None,
        }
    pensao: dict[str, dict[str, Any]] = {}
    for _, row in pensao_df.iterrows():
        cpf = cpf11(row.get("CPF Normalizado") or row.get("CPF"))
        if not cpf:
            continue
        valor = money(row.get("Valor Deduzido 1"))
        if valor <= 0:
            valor = money(row.get("Tipo Rendimento 1"))
        pensao[cpf] = {
            "cpfDep": cpf11(row.get("CPF Beneficiario 1")),
            "tpRend": "11",
            "vlrDedPenAlim": money_str(valor),
        }
    return plano, pensao


def latest_errors(cpfs: list[str]) -> dict[str, dict[str, Any]]:
    internal_id = tenant.internal_empresa_id(EMPRESA_ID)
    conn = db.connect(empresa_id=EMPRESA_ID)
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT DISTINCT ON (it.cpf)
                       it.cpf, it.status, it.erro_codigo, it.erro_mensagem,
                       it.nr_recibo_anterior, it.nr_recibo_novo, te.id AS envio_id, it.id AS item_id
                  FROM timeline_envio_item it
                  JOIN timeline_envio te ON te.id=it.timeline_envio_id
                  JOIN timeline_mes tm ON tm.id=te.timeline_mes_id
                 WHERE tm.empresa_id=%s
                   AND tm.per_apur=%s
                   AND it.tipo_evento='S-1210'
                   AND it.cpf=ANY(%s)
                 ORDER BY it.cpf, it.criado_em DESC NULLS LAST, it.id DESC
                """,
                (internal_id, PER_APUR, cpfs),
            )
            columns = [desc[0] for desc in cursor.description]
            return {row[0]: dict(zip(columns, row)) for row in cursor.fetchall()}
    finally:
        conn.close()


def prepare_base(cpf: str, receipt: str) -> tuple[etree._Element, dict[str, Any]]:
    path = BASE_XMLS[cpf]
    inner = inner_event_root(path)
    evt = inner.xpath('./*[local-name()="evtPgtos"]')[0]
    old_id = evt.get("Id") or ""
    tp_insc = int(inner.xpath('string(//*[local-name()="ideEmpregador"]/*[local-name()="tpInsc"])') or "1")
    nr_insc = inner.xpath('string(//*[local-name()="ideEmpregador"]/*[local-name()="nrInsc"])')
    evt.set("Id", _gerar_id(tp_insc, nr_insc))
    ide_evento = evt.xpath('./*[local-name()="ideEvento"]')[0]
    set_child(ide_evento, "indRetif", "2")
    set_child(ide_evento, "nrRecibo", receipt, after_tag="indRetif")
    return inner, {
        "source_xml": str(path),
        "source_id": old_id,
        "new_id": evt.get("Id"),
        "receipt": receipt,
        "per_apur": inner.xpath('string(//*[local-name()="perApur"])'),
    }


def ensure_info_ir_complem(inner: etree._Element) -> etree._Element:
    ide_benef = inner.xpath('//*[local-name()="ideBenef"]')[0]
    found = direct_child(ide_benef, "infoIRComplem")
    if found is not None:
        return found
    info_ir = etree.Element(qname("infoIRComplem"))
    ide_benef.append(info_ir)
    return info_ir


def add_plan_saude(inner: etree._Element, plan: dict[str, Any]) -> None:
    info_ir = ensure_info_ir_complem(inner)
    for existing in info_ir.xpath('./*[local-name()="planSaude"]'):
        info_ir.remove(existing)
    plan_node = etree.Element(qname("planSaude"))
    sub(plan_node, "cnpjOper", plan["cnpjOper"])
    sub(plan_node, "regANS", plan["regANS"])
    sub(plan_node, "vlrSaudeTit", plan["vlrSaudeTit"])
    info_ir.append(plan_node)


def add_info_dep_if_missing(info_ir: etree._Element, cpf_dep: str) -> None:
    existing_cpfs = {node.xpath('string(./*[local-name()="cpfDep"])') for node in info_ir.xpath('./*[local-name()="infoDep"]')}
    if cpf_dep in existing_cpfs:
        return
    info_dep = etree.Element(qname("infoDep"))
    sub(info_dep, "cpfDep", cpf_dep)
    first_ircr = direct_child(info_ir, "infoIRCR")
    insert_at = info_ir.index(first_ircr) if first_ircr is not None else 0
    info_ir.insert(insert_at, info_dep)


def add_pensao(inner: etree._Element, pensao: dict[str, Any]) -> None:
    info_ir = ensure_info_ir_complem(inner)
    add_info_dep_if_missing(info_ir, pensao["cpfDep"])
    ircr_list = info_ir.xpath('./*[local-name()="infoIRCR"]')
    if len(ircr_list) != 1:
        raise RuntimeError(f"esperado 1 infoIRCR para pensao; encontrado {len(ircr_list)}")
    ircr = ircr_list[0]
    for existing in ircr.xpath('./*[local-name()="penAlim"]'):
        ircr.remove(existing)
    pen = etree.Element(qname("penAlim"))
    sub(pen, "tpRend", pensao["tpRend"])
    sub(pen, "cpfDep", pensao["cpfDep"])
    sub(pen, "vlrDedPenAlim", pensao["vlrDedPenAlim"])
    ircr.append(pen)


def generate_manifest() -> dict[str, Any]:
    if not XLSX.exists():
        raise RuntimeError(f"planilha nao encontrada: {XLSX}")
    for cpf, path in BASE_XMLS.items():
        if not path.exists():
            raise RuntimeError(f"XML base nao encontrado para {cpf}: {path}")
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    XML_DIR.mkdir(parents=True, exist_ok=True)
    for old_xml in XML_DIR.glob("*.xml"):
        old_xml.unlink()

    plano, pensao = load_planilha()
    target_cpfs = sorted(set(plano) | set(pensao))
    if target_cpfs != sorted(BASE_XMLS):
        raise RuntimeError(f"CPFs da planilha/base divergentes: planilha={target_cpfs} base={sorted(BASE_XMLS)}")
    latest = latest_errors(target_cpfs)
    targets: list[dict[str, Any]] = []
    for cpf in target_cpfs:
        current = latest.get(cpf)
        if not current:
            raise RuntimeError(f"sem estado local para CPF {cpf}")
        if current.get("status") != "erro_esocial" or str(current.get("erro_codigo")) == "202":
            raise RuntimeError(f"CPF {cpf} nao esta mais em erro real: {current}")
        receipt = str(current.get("nr_recibo_anterior") or "")
        inner, meta = prepare_base(cpf, receipt)
        if cpf in plano:
            add_plan_saude(inner, plano[cpf])
        if cpf in pensao:
            add_pensao(inner, pensao[cpf])
        if inner.xpath('.//*[local-name()="Signature"]'):
            raise RuntimeError(f"Signature antiga ainda presente para CPF {cpf}")
        if inner.xpath('string(//*[local-name()="perApur"])') != PER_APUR:
            raise RuntimeError(f"perApur divergente para CPF {cpf}")
        out_path = XML_DIR / f"S1210_{PER_APUR}_{cpf}_jaque_2_0_unsigned.xml"
        out_path.write_bytes(etree.tostring(inner, xml_declaration=True, encoding="UTF-8"))
        targets.append({
            "cpf": cpf,
            "xml": str(out_path),
            "evento_id": None,
            "nr_recibo": receipt,
            "source_xml": meta["source_xml"],
            "source_id": meta["source_id"],
            "id_evento": meta["new_id"],
            "has_plano": cpf in plano,
            "has_pensao": cpf in pensao,
            "plano": plano.get(cpf),
            "pensao": pensao.get(cpf),
            "latest_item_id": current.get("item_id"),
            "latest_envio_id": current.get("envio_id"),
        })
    manifest = {
        "empresa_id": EMPRESA_ID,
        "per_apur": PER_APUR,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "planilha": str(XLSX),
        "regra": "XML base das quinzenas de setembro; retificacao indRetif=2; corrigir planSaude/pensao; sem consulta/download eSocial",
        "targets": targets,
        "total": len(targets),
    }
    MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    return manifest


def validate_manifest(manifest: dict[str, Any]) -> dict[str, Any]:
    out = []
    for item in manifest["targets"]:
        root = etree.fromstring(Path(item["xml"]).read_bytes())
        out.append({
            "cpf": item["cpf"],
            "indRetif": root.xpath('string(//*[local-name()="indRetif"])'),
            "nrRecibo": root.xpath('string(//*[local-name()="nrRecibo"])'),
            "perApur": root.xpath('string(//*[local-name()="perApur"])'),
            "planSaude": len(root.xpath('//*[local-name()="planSaude"]')),
            "infoDep": [node.xpath('string(./*[local-name()="cpfDep"])') for node in root.xpath('//*[local-name()="infoDep"]')],
            "penAlim": [node.xpath('string(./*[local-name()="cpfDep"])') for node in root.xpath('//*[local-name()="penAlim"]')],
            "signature": bool(root.xpath('//*[local-name()="Signature"]')),
        })
    return {"total": len(out), "items": out}


def dry_run() -> dict[str, Any]:
    manifest = generate_manifest()
    validation = validate_manifest(manifest)
    return {"ok": True, "dry_run": True, "manifest": str(MANIFEST), "validation": validation}


def execute() -> dict[str, Any]:
    manifest = generate_manifest()
    targets = manifest["targets"]
    if len(targets) != 5:
        raise RuntimeError(f"esperado 5 targets; encontrado {len(targets)}")
    senha = os.getenv("ESOCIAL_CERT_SENHA") or ""
    if not senha:
        raise RuntimeError("ESOCIAL_CERT_SENHA nao definida")
    pfx_data = envio_base.DEFAULT_CERT.read_bytes()
    signed: list[dict[str, Any]] = []
    for item in targets:
        unsigned_xml = Path(item["xml"]).read_bytes()
        xml_assinado = S1010XMLSigner.assinar(unsigned_xml, pfx_data, senha)
        signed_id = esocial_client._extrair_id(xml_assinado)
        if signed_id != item["id_evento"]:
            raise RuntimeError(f"Id assinado divergente para CPF {item['cpf']}")
        signed.append({**item, "xml_assinado": xml_assinado, "id_evento_assinado": signed_id})

    conn_db = db.connect(empresa_id=EMPRESA_ID)
    conn_w = db.connect(empresa_id=EMPRESA_ID)
    try:
        envio_base._verificar_estado_atual(conn_db, signed)
        envio_id, mes_id = envio_base._criar_timeline_envio(conn_db, len(signed))
        print(f"=> jaque 2.0: envio_id={envio_id} timeline_mes={mes_id} targets={len(signed)}")
        item_ids = envio_base._criar_items(conn_db, envio_id, signed)
        envio_base._persistir_xmls_assinados(conn_db, conn_w, signed, item_ids)
        resultado = envio_base._processar_lote(
            signed,
            item_ids,
            cert_path=envio_base.DEFAULT_CERT,
            senha=senha,
            cnpj="09445502000109",
            conn_db=conn_db,
            conn_w=conn_w,
        )
        sucesso = int(resultado["sucesso"])
        erro = int(resultado["erro"])
        histograma = dict(resultado.get("histograma") or {})
        envio_base._atualizar_envio(
            conn_db,
            envio_id,
            status="concluido",
            sucesso=sucesso,
            erro=erro,
            resumo_extra={
                "rotulo_final": "jaque_2_0_plano_pensao_5",
                "protocolo": resultado.get("protocolo"),
                "histograma_erros": histograma,
                "manifest": str(MANIFEST),
                "cpfs": [item["cpf"] for item in signed],
            },
        )
        print("\n=== RESUMO JAQUE 2.0 ===")
        print(f"envio_id  : {envio_id}")
        print(f"protocolo : {resultado.get('protocolo')}")
        print(f"sucesso   : {sucesso}")
        print(f"erro      : {erro}")
        print(f"histograma: {histograma}")
        return {"envio_id": envio_id, "sucesso": sucesso, "erro": erro, "histograma": histograma}
    finally:
        conn_db.close()
        conn_w.close()


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