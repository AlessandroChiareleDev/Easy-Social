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
from app.xml_diff import eventos_iguais  # noqa: E402
from app.xml_s1210 import NS, _gerar_id  # noqa: E402
from app.xml_signer import S1010XMLSigner  # noqa: E402


EMPRESA_ID = 2
PER_APUR = "2025-08"
CONFIRM_TOKEN = "REENVIAR_XML_IDENTICO_277"
OUT_DIR = ROOT / "relatorio_ana" / "REENVIO_AGOSTO_XML_IDENTICO"
XML_DIR = OUT_DIR / "xml_unsigned"
MANIFEST = OUT_DIR / "manifest_reenvio_xml_identico.json"
SETEMBRO = Path(r"C:\Users\xandao\Downloads\solucoes\ARQUIVOS 1210\ARQUIVOS 1210\SETEMBRO")
BASE_XML_DIR = Path(r"C:\Users\xandao\Downloads\solucoes\ARQUIVOS 1210\ARQUIVOS 1210")
SENHA_TXT = Path(r"C:\Users\xandao\Downloads\Senha solucoes.txt")
LOCAL_XML_CACHE: dict[str, list[Path]] | None = None


def qname(tag: str) -> str:
    return f"{{{NS}}}{tag}"


def only_digits(value: Any) -> str:
    return re.sub(r"\D", "", str(value or ""))


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


def read_password() -> str:
    senha = os.getenv("ESOCIAL_CERT_SENHA") or ""
    if senha.strip():
        return senha.strip()
    if SENHA_TXT.exists():
        senha = SENHA_TXT.read_text(encoding="utf-8", errors="ignore").strip()
    if not senha:
        raise RuntimeError("senha do certificado nao encontrada em env nem no TXT esperado")
    return senha


def load_current_targets(conn) -> list[dict[str, Any]]:
    internal_empresa_id = tenant.internal_empresa_id(EMPRESA_ID)
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
        cursor.execute(
            """
            WITH latest AS (
                SELECT DISTINCT ON (it.cpf)
                       it.id AS item_id,
                       it.timeline_envio_id AS envio_id,
                       it.cpf,
                       it.status,
                       it.erro_codigo,
                       it.erro_mensagem,
                       it.nr_recibo_anterior,
                       it.nr_recibo_novo,
                       it.versao_anterior_id,
                       it.xml_enviado_oid,
                       it.criado_em
                  FROM timeline_envio_item it
                  JOIN timeline_envio te ON te.id = it.timeline_envio_id
                  JOIN timeline_mes tm ON tm.id = te.timeline_mes_id
                 WHERE tm.empresa_id = %s
                   AND tm.per_apur = %s
                   AND it.tipo_evento = 'S-1210'
                   AND it.cpf IS NOT NULL
                 ORDER BY it.cpf, it.criado_em DESC NULLS LAST, it.id DESC
            )
            SELECT *
              FROM latest
             WHERE status = 'sem_mudanca'
                OR erro_codigo = 'SEM_MUDANCA'
             ORDER BY cpf
            """,
            (internal_empresa_id, PER_APUR),
        )
        targets = [dict(row) for row in cursor.fetchall()]
    if not targets:
        raise RuntimeError("nenhum CPF atual com status local SEM_MUDANCA")
    missing_receipts = [row["cpf"] for row in targets if not row.get("nr_recibo_anterior")]
    if missing_receipts:
        raise RuntimeError(f"alvos sem nr_recibo_anterior: {missing_receipts[:20]}")
    missing_events = [row["cpf"] for row in targets if not row.get("versao_anterior_id")]
    if missing_events:
        raise RuntimeError(f"alvos sem versao_anterior_id: {missing_events[:20]}")
    return targets


def read_xml_lo(conn, oid: int) -> bytes:
    with conn.cursor() as cursor:
        cursor.execute("SELECT lo_get(%s)", (int(oid),))
        row = cursor.fetchone()
    if not row or row[0] is None:
        raise RuntimeError(f"large object vazio: {oid}")
    return bytes(row[0])


def find_previous_timeline_xml(conn, target: dict[str, Any]) -> tuple[bytes, str] | None:
    internal_empresa_id = tenant.internal_empresa_id(EMPRESA_ID)
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
        cursor.execute(
            """
            SELECT it.id AS item_id, it.xml_enviado_oid, it.status, it.erro_codigo, it.criado_em
              FROM timeline_envio_item it
              JOIN timeline_envio te ON te.id = it.timeline_envio_id
              JOIN timeline_mes tm ON tm.id = te.timeline_mes_id
             WHERE tm.empresa_id = %s
               AND tm.per_apur = %s
               AND it.tipo_evento = 'S-1210'
               AND it.cpf = %s
               AND it.xml_enviado_oid IS NOT NULL
               AND it.id <> %s
             ORDER BY it.criado_em DESC NULLS LAST, it.id DESC
             LIMIT 20
            """,
            (internal_empresa_id, PER_APUR, target["cpf"], target["item_id"]),
        )
        rows = [dict(row) for row in cursor.fetchall()]
    for row in rows:
        try:
            xml_bytes = read_xml_lo(conn, int(row["xml_enviado_oid"]))
            return xml_bytes, f"timeline_envio_item:{row['item_id']}:xml_enviado_oid:{row['xml_enviado_oid']}"
        except Exception:
            conn.rollback()
    return None


def local_xml_cache() -> dict[str, list[Path]]:
    global LOCAL_XML_CACHE
    if LOCAL_XML_CACHE is not None:
        return LOCAL_XML_CACHE
    indexed: dict[str, list[Path]] = {}
    cpf_pattern = re.compile(rb"<cpfBenef>(\d{11})</cpfBenef>")
    per_pattern = f"<perApur>{PER_APUR}</perApur>".encode("utf-8")
    for path in BASE_XML_DIR.rglob("*.xml"):
        try:
            data = path.read_bytes()
        except OSError:
            continue
        if per_pattern not in data:
            continue
        match = cpf_pattern.search(data)
        if not match:
            continue
        cpf = match.group(1).decode("ascii")
        indexed.setdefault(cpf, []).append(path)
    for paths in indexed.values():
        paths.sort(key=lambda item: str(item))
    LOCAL_XML_CACHE = indexed
    return indexed


def find_local_xml_by_cpf(target: dict[str, Any]) -> tuple[bytes, str] | None:
    paths = local_xml_cache().get(only_digits(target["cpf"]), [])
    if not paths:
        return None
    chosen = paths[-1]
    return chosen.read_bytes(), str(chosen)


def read_source_xml(conn, target: dict[str, Any]) -> tuple[bytes, str]:
    previous = find_previous_timeline_xml(conn, target)
    if previous is not None:
        return previous

    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
        cursor.execute(
            """
            SELECT id, cpf, nr_recibo, id_evento, arquivo_origem, xml_entry_name,
                   xml_oid, xml_bytes, xml_size_bytes
              FROM explorador_eventos
             WHERE id = %s
            """,
            (target["versao_anterior_id"],),
        )
        event = cursor.fetchone()
    if not event:
        raise RuntimeError(f"explorador_eventos ausente para CPF {target['cpf']}: {target['versao_anterior_id']}")

    event_cpf = only_digits(event.get("cpf"))
    if event_cpf and event_cpf != only_digits(target["cpf"]):
        raise RuntimeError(f"CPF divergente no evento base: alvo={target['cpf']} evento={event_cpf}")

    xml_bytes = event.get("xml_bytes")
    if xml_bytes is not None:
        return bytes(xml_bytes), f"explorador_eventos.xml_bytes:{event['id']}"
    xml_oid = event.get("xml_oid")
    if xml_oid is not None:
        try:
            return read_xml_lo(conn, int(xml_oid)), f"explorador_eventos.xml_oid:{xml_oid}"
        except Exception:
            conn.rollback()

    name = event.get("arquivo_origem") or event.get("xml_entry_name")
    path = SETEMBRO / str(name or "")
    if path.exists():
        return path.read_bytes(), str(path)
    local = find_local_xml_by_cpf(target)
    if local is not None:
        return local
    raise RuntimeError(f"XML fonte nao encontrado para CPF {target['cpf']}: {path}")


def inner_s1210(xml_bytes: bytes) -> etree._Element:
    parser = etree.XMLParser(remove_blank_text=True)
    root = etree.fromstring(xml_bytes, parser=parser)
    candidates = root.xpath('//*[local-name()="eSocial" and ./*[local-name()="evtPgtos"]]')
    if not candidates:
        raise RuntimeError("XML interno S-1210 nao encontrado")
    inner = etree.fromstring(etree.tostring(candidates[0]), parser=parser)
    for signature in inner.xpath('.//*[local-name()="Signature"]'):
        parent = signature.getparent()
        if parent is not None:
            parent.remove(signature)
    return inner


def prepare_xml(target: dict[str, Any], xml_source: bytes) -> tuple[bytes, dict[str, Any]]:
    inner = inner_s1210(xml_source)
    event_nodes = inner.xpath('./*[local-name()="evtPgtos"]')
    if not event_nodes:
        raise RuntimeError("evtPgtos ausente")
    event_node = event_nodes[0]
    old_id = event_node.get("Id") or ""
    cpf = only_digits(inner.xpath('string(//*[local-name()="ideBenef"]/*[local-name()="cpfBenef"])'))
    if cpf != only_digits(target["cpf"]):
        raise RuntimeError(f"XML fonte e de CPF {cpf}, alvo {target['cpf']}")

    tp_insc_text = inner.xpath('string(//*[local-name()="ideEmpregador"]/*[local-name()="tpInsc"])')
    nr_insc = inner.xpath('string(//*[local-name()="ideEmpregador"]/*[local-name()="nrInsc"])').strip()
    if not tp_insc_text or not nr_insc:
        raise RuntimeError(f"ideEmpregador incompleto para CPF {target['cpf']}")
    event_node.set("Id", _gerar_id(int(tp_insc_text), nr_insc))

    ide_evento_nodes = event_node.xpath('./*[local-name()="ideEvento"]')
    if not ide_evento_nodes:
        raise RuntimeError(f"ideEvento ausente para CPF {target['cpf']}")
    ide_evento = ide_evento_nodes[0]
    set_child(ide_evento, "indRetif", "2")
    set_child(ide_evento, "nrRecibo", str(target["nr_recibo_anterior"]), after_tag="indRetif")

    tp_amb = inner.xpath('string(//*[local-name()="ideEvento"]/*[local-name()="tpAmb"])').strip()
    per_apur = inner.xpath('string(//*[local-name()="ideEvento"]/*[local-name()="perApur"])').strip()
    if tp_amb != "1":
        raise RuntimeError(f"tpAmb nao e producao para CPF {target['cpf']}: {tp_amb}")
    if per_apur != PER_APUR:
        raise RuntimeError(f"perApur divergente para CPF {target['cpf']}: {per_apur}")
    if inner.xpath('.//*[local-name()="Signature"]'):
        raise RuntimeError(f"assinatura antiga permaneceu para CPF {target['cpf']}")

    xml_new = etree.tostring(inner, xml_declaration=True, encoding="UTF-8", pretty_print=False)
    if not eventos_iguais(xml_source, xml_new):
        raise RuntimeError(f"corpo canonico mudou para CPF {target['cpf']}")
    return xml_new, {
        "cpf": target["cpf"],
        "source_id": old_id,
        "new_id": event_node.get("Id"),
        "nr_recibo_anterior": str(target["nr_recibo_anterior"]),
        "versao_anterior_id": target["versao_anterior_id"],
        "latest_item_id": target["item_id"],
        "latest_envio_id": target["envio_id"],
        "source_status": target["status"],
        "source_error_code": target["erro_codigo"],
    }


def generate_manifest() -> dict[str, Any]:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    XML_DIR.mkdir(parents=True, exist_ok=True)
    conn = db.connect(empresa_id=EMPRESA_ID)
    generated: list[dict[str, Any]] = []
    try:
        targets = load_current_targets(conn)
        seen_ids: set[str] = set()
        for target in targets:
            xml_source, source = read_source_xml(conn, target)
            xml_new, metadata = prepare_xml(target, xml_source)
            new_id = str(metadata["new_id"])
            if new_id in seen_ids:
                raise RuntimeError(f"Id duplicado gerado: {new_id}")
            seen_ids.add(new_id)
            xml_path = XML_DIR / f"S1210_{PER_APUR}_{target['cpf']}_xml_identico_unsigned.xml"
            xml_path.write_bytes(xml_new)
            generated.append({
                "cpf": target["cpf"],
                "xml": str(xml_path),
                "evento_id": target["versao_anterior_id"],
                "nr_recibo": str(target["nr_recibo_anterior"]),
                "id_evento": new_id,
                "source_xml": source,
                "validation": metadata,
            })
    finally:
        conn.close()

    manifest = {
        "empresa_id": EMPRESA_ID,
        "per_apur": PER_APUR,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "total": len(generated),
        "regra": "reenviar retificacao com corpo canonico identico; muda apenas ideEvento/Id/assinatura",
        "targets": generated,
    }
    MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    return manifest


def sign_targets(targets: list[dict[str, Any]], senha: str) -> list[dict[str, Any]]:
    pfx_data = envio_base.DEFAULT_CERT.read_bytes()
    signed: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    for target in targets:
        unsigned_xml = Path(target["xml"]).read_bytes()
        xml_assinado = S1010XMLSigner.assinar(unsigned_xml, pfx_data, senha)
        signed_id = esocial_client._extrair_id(xml_assinado)
        if signed_id != target["id_evento"]:
            raise RuntimeError(f"Id assinado divergente para CPF {target['cpf']}: {signed_id} != {target['id_evento']}")
        if signed_id in seen_ids:
            raise RuntimeError(f"Id duplicado apos assinar: {signed_id}")
        seen_ids.add(str(signed_id))
        signed.append({**target, "xml_assinado": xml_assinado, "id_evento_assinado": signed_id})
    return signed


def create_timeline(conn, total: int) -> tuple[int, int]:
    internal_empresa_id = tenant.internal_empresa_id(EMPRESA_ID)
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
        cursor.execute(
            "SELECT id FROM timeline_mes WHERE empresa_id=%s AND per_apur=%s",
            (internal_empresa_id, PER_APUR),
        )
        month = cursor.fetchone()
        if not month:
            raise RuntimeError(f"timeline_mes nao existe para empresa={EMPRESA_ID} per_apur={PER_APUR}")
        month_id = int(month["id"])
        cursor.execute(
            "SELECT COALESCE(MAX(sequencia), 0)+1 AS prox FROM timeline_envio WHERE timeline_mes_id=%s",
            (month_id,),
        )
        sequence = int(cursor.fetchone()["prox"])
        cursor.execute(
            """
            INSERT INTO timeline_envio
              (timeline_mes_id, sequencia, tipo, status,
               iniciado_em, total_tentados, total_sucesso, total_erro, resumo)
            VALUES
              (%s, %s, 'envio_massa', 'em_andamento', now(), %s, 0, 0, %s)
            RETURNING id
            """,
            (
                month_id,
                sequence,
                total,
                psycopg2.extras.Json({
                    "rotulo": "reenvio_agosto_xml_identico_sem_guard_543",
                    "empresa_id_externo": EMPRESA_ID,
                    "per_apur": PER_APUR,
                    "ambiente": "producao",
                    "origem": str(MANIFEST),
                    "motivo": "resolver CPFs pulados localmente por comparacao de XML identico",
                }),
            ),
        )
        envio_id = int(cursor.fetchone()["id"])
    conn.commit()
    return envio_id, month_id


def assert_still_current_sem_mudanca(conn, signed: list[dict[str, Any]]) -> None:
    current_targets = load_current_targets(conn)
    current_by_cpf = {row["cpf"]: row for row in current_targets}
    missing = [target["cpf"] for target in signed if target["cpf"] not in current_by_cpf]
    if missing:
        raise RuntimeError(f"CPFs deixaram de estar no status local antes do envio: {missing[:20]}")


def execute() -> dict[str, Any]:
    manifest = generate_manifest()
    targets = manifest["targets"]
    if len(targets) != 277:
        raise RuntimeError(f"esperado reenviar 277 CPFs; encontrados {len(targets)}")
    senha = read_password()
    signed = sign_targets(targets, senha)
    conn_db = db.connect(empresa_id=EMPRESA_ID)
    conn_w = db.connect(empresa_id=EMPRESA_ID)
    try:
        assert_still_current_sem_mudanca(conn_db, signed)
        envio_id, month_id = create_timeline(conn_db, len(signed))
        print(f"=> reenvio XML identico: envio_id={envio_id} timeline_mes={month_id} targets={len(signed)}")
        item_ids = envio_base._criar_items(conn_db, envio_id, signed)
        envio_base._persistir_xmls_assinados(conn_db, conn_w, signed, item_ids)
        print(f"=> XMLs assinados gravados e vinculados: {len(item_ids)}")

        sucesso_total = 0
        erro_total = 0
        protocolos: list[str] = []
        histograma: dict[str, int] = {}
        for index in range(0, len(signed), envio_base.CFG_LOTE_MAX):
            batch = signed[index:index + envio_base.CFG_LOTE_MAX]
            print(f"\n>> lote {index // envio_base.CFG_LOTE_MAX + 1} ({len(batch)} eventos)")
            result = envio_base._processar_lote(
                batch,
                item_ids,
                cert_path=envio_base.DEFAULT_CERT,
                senha=senha,
                cnpj="09445502000109",
                conn_db=conn_db,
                conn_w=conn_w,
            )
            sucesso_total += int(result["sucesso"])
            erro_total += int(result["erro"])
            if result.get("protocolo"):
                protocolos.append(str(result["protocolo"]))
            for code, count in dict(result.get("histograma") or {}).items():
                histograma[str(code)] = histograma.get(str(code), 0) + int(count)

        envio_base._atualizar_envio(
            conn_db,
            envio_id,
            status="concluido",
            sucesso=sucesso_total,
            erro=erro_total,
            resumo_extra={
                "rotulo_final": "reenvio_agosto_xml_identico_sem_guard_543",
                "protocolos": protocolos,
                "histograma_erros": histograma,
                "manifest": str(MANIFEST),
                "total_xml_identico": len(signed),
            },
        )
        print("\n=== RESUMO REENVIO XML IDENTICO AGOSTO ===")
        print(f"envio_id  : {envio_id}")
        print(f"protocolos: {protocolos}")
        print(f"sucesso   : {sucesso_total}")
        print(f"erro      : {erro_total}")
        print(f"histograma: {histograma}")
        return {
            "envio_id": envio_id,
            "sucesso": sucesso_total,
            "erro": erro_total,
            "protocolos": protocolos,
            "histograma": histograma,
            "manifest": str(MANIFEST),
        }
    finally:
        conn_db.close()
        conn_w.close()


def dry_run() -> dict[str, Any]:
    manifest = generate_manifest()
    return {
        "ok": True,
        "dry_run": True,
        "manifest": str(MANIFEST),
        "total": manifest["total"],
        "primeiros_cpfs": [target["cpf"] for target in manifest["targets"][:10]],
        "ultimos_cpfs": [target["cpf"] for target in manifest["targets"][-10:]],
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