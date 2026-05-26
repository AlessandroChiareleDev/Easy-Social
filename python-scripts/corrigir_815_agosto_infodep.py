from __future__ import annotations

import argparse
import json
import os
import re
import sys
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
from app import db, esocial_client, tenant  # noqa: E402
from app.xml_s1210 import NS, _gerar_id  # noqa: E402
from app.xml_signer import S1010XMLSigner  # noqa: E402


EMPRESA_ID = 2
PER_APUR = "2025-08"
CPF = "81529368553"
CONFIRM_TOKEN = "INFODEP_815_AGOSTO"
OUT_DIR = ROOT / "relatorio_ana" / "CORRECAO_815_AGOSTO_INFODEP"
XML_DIR = OUT_DIR / "xml_unsigned"
MANIFEST = OUT_DIR / "manifest_815_infodep.json"
SETEMBRO = Path(r"C:\Users\xandao\Downloads\solucoes\ARQUIVOS 1210\ARQUIVOS 1210\SETEMBRO")

DEPENDENTES = [
    {
        "cpfDep": "09274813597",
        "dtNascto": "2003-08-08",
        "nome": "GABRIEL CERQUEIRA E SILVA RODRIGUES",
        "depIRRF": "S",
        "tpDep": "03",
    },
    {
        "cpfDep": "09274837500",
        "dtNascto": "2006-04-28",
        "nome": "CAUA CERQUEIRA E SILVA RODRIGUES",
        "depIRRF": "S",
        "tpDep": "03",
    },
]


def qname(tag: str) -> str:
    return f"{{{NS}}}{tag}"


def child_text(parent: etree._Element, tag: str) -> str:
    found = parent.xpath(f'./*[local-name()="{tag}"]')
    return (found[0].text or "").strip() if found else ""


def direct_child(parent: etree._Element, tag: str) -> etree._Element | None:
    found = parent.xpath(f'./*[local-name()="{tag}"]')
    return found[0] if found else None


def set_child(parent: etree._Element, tag: str, value: str, after_tag: str | None = None) -> None:
    found = direct_child(parent, tag)
    if found is not None:
        found.text = value
        return
    node = etree.Element(qname(tag))
    node.text = value
    insert_at = len(parent)
    if after_tag:
        for index, child in enumerate(parent):
            if etree.QName(child).localname == after_tag:
                insert_at = index + 1
                break
    parent.insert(insert_at, node)


def sub(parent: etree._Element, tag: str, value: str) -> None:
    node = etree.SubElement(parent, qname(tag))
    node.text = value


def latest_row(conn) -> dict[str, Any]:
    internal_empresa_id = tenant.internal_empresa_id(EMPRESA_ID)
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(
            """
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
               AND it.cpf = %s
             ORDER BY it.cpf, it.criado_em DESC NULLS LAST, it.id DESC
            """,
            (internal_empresa_id, PER_APUR, CPF),
        )
        row = cur.fetchone()
    if not row:
        raise RuntimeError(f"sem estado local para CPF {CPF}")
    return dict(row)


def assert_current_error(row: dict[str, Any]) -> None:
    message = str(row.get("erro_mensagem") or "")
    if row.get("status") != "erro_esocial" or str(row.get("erro_codigo")) != "401":
        raise RuntimeError(f"CPF {CPF} nao esta no erro 401 esperado: {row}")
    for dep in DEPENDENTES:
        if dep["cpfDep"] not in message:
            raise RuntimeError(f"erro atual nao cita dependente {dep['cpfDep']}: {message}")
    if not row.get("nr_recibo_anterior"):
        raise RuntimeError("linha atual sem nr_recibo_anterior")


def read_source_xml(conn, row: dict[str, Any]) -> tuple[bytes, str]:
    oid = row.get("xml_enviado_oid")
    if oid:
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT lo_get(%s)", (oid,))
                got = cur.fetchone()
            if got and got[0] is not None:
                return bytes(got[0]), f"oid:{oid}"
        except Exception:
            conn.rollback()
    event_id = row.get("versao_anterior_id")
    if not event_id:
        raise RuntimeError("linha atual sem versao_anterior_id e sem XML OID legivel")
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(
            "SELECT arquivo_origem, xml_entry_name FROM explorador_eventos WHERE id=%s",
            (event_id,),
        )
        event = cur.fetchone()
    if not event:
        raise RuntimeError(f"explorador_eventos nao encontrado: {event_id}")
    name = event.get("arquivo_origem") or event.get("xml_entry_name")
    path = SETEMBRO / str(name or "")
    if not path.exists():
        raise RuntimeError(f"XML origem nao encontrado: {path}")
    return path.read_bytes(), str(path)


def inner_s1210(xml_bytes: bytes) -> etree._Element:
    parser = etree.XMLParser(remove_blank_text=True)
    root = etree.fromstring(xml_bytes, parser=parser)
    candidates = root.xpath('//*[local-name()="eSocial" and ./*[local-name()="evtPgtos"]]')
    if not candidates:
        raise RuntimeError("XML S-1210 interno nao encontrado")
    inner = etree.fromstring(etree.tostring(candidates[0]), parser=parser)
    for signature in inner.xpath('.//*[local-name()="Signature"]'):
        parent = signature.getparent()
        if parent is not None:
            parent.remove(signature)
    return inner


def ensure_info_ir(inner: etree._Element) -> etree._Element:
    ide_benef = inner.xpath('//*[local-name()="evtPgtos"]/*[local-name()="ideBenef"]')
    if not ide_benef:
        raise RuntimeError("ideBenef nao encontrado")
    info_ir = direct_child(ide_benef[0], "infoIRComplem")
    if info_ir is None:
        info_ir = etree.Element(qname("infoIRComplem"))
        ide_benef[0].append(info_ir)
    return info_ir


def upsert_info_deps(info_ir: etree._Element) -> int:
    for existing in list(info_ir.xpath('./*[local-name()="infoDep"]')):
        info_ir.remove(existing)
    first_ircr = direct_child(info_ir, "infoIRCR")
    insert_at = info_ir.index(first_ircr) if first_ircr is not None else len(info_ir)
    for offset, dep in enumerate(DEPENDENTES):
        node = etree.Element(qname("infoDep"))
        for tag in ("cpfDep", "dtNascto", "nome", "depIRRF", "tpDep"):
            sub(node, tag, dep[tag])
        info_ir.insert(insert_at + offset, node)
    return len(DEPENDENTES)


def prepare_xml(xml_bytes: bytes, receipt: str) -> tuple[bytes, dict[str, Any]]:
    inner = inner_s1210(xml_bytes)
    evt = inner.xpath('./*[local-name()="evtPgtos"]')[0]
    old_id = evt.get("Id") or ""
    cpf = inner.xpath('string(//*[local-name()="ideBenef"]/*[local-name()="cpfBenef"])').strip()
    if cpf != CPF:
        raise RuntimeError(f"XML origem e de CPF {cpf}, esperado {CPF}")
    tp_insc = int(inner.xpath('string(//*[local-name()="ideEmpregador"]/*[local-name()="tpInsc"])') or "1")
    nr_insc = inner.xpath('string(//*[local-name()="ideEmpregador"]/*[local-name()="nrInsc"])')
    evt.set("Id", _gerar_id(tp_insc, nr_insc))
    ide_evento = evt.xpath('./*[local-name()="ideEvento"]')[0]
    set_child(ide_evento, "indRetif", "2")
    set_child(ide_evento, "nrRecibo", receipt, after_tag="indRetif")
    info_ir = ensure_info_ir(inner)
    inserted = upsert_info_deps(info_ir)

    ded_rows = []
    for node in inner.xpath('//*[local-name()="dedDepen"]'):
        ded_rows.append({
            "tpRend": child_text(node, "tpRend") or "11",
            "cpfDep": child_text(node, "cpfDep"),
            "vlrDedDep": child_text(node, "vlrDedDep"),
        })
    expected_deds = {dep["cpfDep"] for dep in DEPENDENTES}
    actual_deds = {row["cpfDep"] for row in ded_rows if row["vlrDedDep"] == "189.59"}
    if expected_deds - actual_deds:
        raise RuntimeError(f"dedDepen esperadas ausentes: {sorted(expected_deds - actual_deds)}")
    if inner.xpath('.//*[local-name()="Signature"]'):
        raise RuntimeError("Signature antiga permaneceu no XML")
    if inner.xpath('string(//*[local-name()="perApur"])') != PER_APUR:
        raise RuntimeError("perApur divergente")
    if inner.xpath('string(//*[local-name()="tpAmb"])') != "1":
        raise RuntimeError("tpAmb divergente de producao")

    output = etree.tostring(inner, xml_declaration=True, encoding="UTF-8", pretty_print=False)
    return output, {
        "source_id": old_id,
        "new_id": evt.get("Id"),
        "indRetif": inner.xpath('string(//*[local-name()="indRetif"])'),
        "nrRecibo": inner.xpath('string(//*[local-name()="nrRecibo"])'),
        "infoDep_inserted": inserted,
        "infoDep": [node.xpath('string(./*[local-name()="cpfDep"])') for node in inner.xpath('//*[local-name()="infoDep"]')],
        "dedDepen": ded_rows,
    }


def generate_manifest() -> dict[str, Any]:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    XML_DIR.mkdir(parents=True, exist_ok=True)
    conn = db.connect(empresa_id=EMPRESA_ID)
    try:
        row = latest_row(conn)
        assert_current_error(row)
        source_xml, source = read_source_xml(conn, row)
        xml_out, meta = prepare_xml(source_xml, str(row["nr_recibo_anterior"]))
    finally:
        conn.close()
    xml_path = XML_DIR / f"S1210_{PER_APUR}_{CPF}_infodep_unsigned.xml"
    xml_path.write_bytes(xml_out)
    target = {
        "cpf": CPF,
        "xml": str(xml_path),
        "evento_id": row["versao_anterior_id"],
        "nr_recibo": str(row["nr_recibo_anterior"]),
        "id_evento": meta["new_id"],
        "source_xml": source,
        "source_id": meta["source_id"],
        "latest_item_id": row["item_id"],
        "latest_envio_id": row["envio_id"],
        "correcao": "inserir infoDep para dependentes usados em dedDepen 401/1861",
        "dependentes": DEPENDENTES,
        "validation": meta,
    }
    manifest = {
        "empresa_id": EMPRESA_ID,
        "per_apur": PER_APUR,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "total": 1,
        "targets": [target],
    }
    MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    return manifest


def dry_run() -> dict[str, Any]:
    manifest = generate_manifest()
    target = manifest["targets"][0]
    return {
        "ok": True,
        "dry_run": True,
        "manifest": str(MANIFEST),
        "cpf": target["cpf"],
        "xml": target["xml"],
        "nr_recibo": target["nr_recibo"],
        "validation": target["validation"],
    }


def _criar_timeline_envio_815(conn, total: int) -> tuple[int, int]:
    internal_empresa_id = tenant.internal_empresa_id(EMPRESA_ID)
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(
            "SELECT id FROM timeline_mes WHERE empresa_id=%s AND per_apur=%s",
            (internal_empresa_id, PER_APUR),
        )
        mes = cur.fetchone()
        if not mes:
            raise RuntimeError(f"timeline_mes nao existe para empresa={EMPRESA_ID} per_apur={PER_APUR}")
        mes_id = int(mes["id"])
        cur.execute(
            "SELECT COALESCE(MAX(sequencia), 0)+1 AS prox FROM timeline_envio WHERE timeline_mes_id=%s",
            (mes_id,),
        )
        sequencia = int(cur.fetchone()["prox"])
        cur.execute(
            """
            INSERT INTO timeline_envio
              (timeline_mes_id, sequencia, tipo, status,
               iniciado_em, total_tentados, total_sucesso, total_erro, resumo)
            VALUES
              (%s, %s, 'envio_massa', 'em_andamento', now(), %s, 0, 0, %s)
            RETURNING id
            """,
            (
                mes_id,
                sequencia,
                total,
                psycopg2.extras.Json({
                    "rotulo": "correcao_815_agosto_infodep",
                    "empresa_id_externo": EMPRESA_ID,
                    "per_apur": PER_APUR,
                    "ambiente": "producao",
                    "origem": str(MANIFEST),
                    "regra": "401/1861: inserir infoDep para CPFs ja usados em dedDepen",
                }),
            ),
        )
        envio_id = int(cur.fetchone()["id"])
    conn.commit()
    return envio_id, mes_id


def execute() -> dict[str, Any]:
    manifest = generate_manifest()
    target = manifest["targets"][0]
    senha = os.getenv("ESOCIAL_CERT_SENHA") or ""
    if not senha:
        raise RuntimeError("ESOCIAL_CERT_SENHA nao definida")
    unsigned = Path(target["xml"]).read_bytes()
    xml_assinado = S1010XMLSigner.assinar(unsigned, envio_base.DEFAULT_CERT.read_bytes(), senha)
    signed_id = esocial_client._extrair_id(xml_assinado)
    if signed_id != target["id_evento"]:
        raise RuntimeError(f"Id assinado divergente: {signed_id} != {target['id_evento']}")
    signed = [{**target, "xml_assinado": xml_assinado, "id_evento_assinado": signed_id}]

    conn_db = db.connect(empresa_id=EMPRESA_ID)
    conn_w = db.connect(empresa_id=EMPRESA_ID)
    try:
        assert_current_error(latest_row(conn_db))
        envio_base._verificar_estado_atual(conn_db, signed)
        envio_id, mes_id = _criar_timeline_envio_815(conn_db, len(signed))
        print(f"=> correcao 815 infoDep: envio_id={envio_id} timeline_mes={mes_id} targets=1")
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
                "rotulo_final": "correcao_815_agosto_infodep",
                "protocolo": resultado.get("protocolo"),
                "histograma_erros": histograma,
                "manifest": str(MANIFEST),
                "cpfs": [CPF],
            },
        )
        print("\n=== RESUMO CORRECAO 815 INFODEP ===")
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