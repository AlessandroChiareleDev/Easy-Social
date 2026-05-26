from __future__ import annotations

import argparse
import json
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
import reenviar_agosto_sem_mudanca_solucoes as reenvio_base  # noqa: E402
from app import db, esocial_client, tenant  # noqa: E402
from app.xml_diff import eventos_iguais  # noqa: E402
from app.xml_s1210 import _gerar_id  # noqa: E402
from app.xml_signer import S1010XMLSigner  # noqa: E402


EMPRESA_ID = 2
PER_APUR = "2025-08"
ENVIO_ERRO_ID = 928
CONFIRM_TOKEN = "CORRIGIR_RECIBO_EXPLORADOR_58"
OUT_DIR = ROOT / "relatorio_ana" / "REENVIO_AGOSTO_XML_IDENTICO"
CANDIDATES = OUT_DIR / "receipts_candidates_58_explorador.json"
XML_DIR = OUT_DIR / "xml_unsigned_recibo_explorador_fix"
MANIFEST = OUT_DIR / "manifest_corrigir_recibo_explorador_58.json"


def load_candidates() -> list[dict[str, Any]]:
    if not CANDIDATES.exists():
        raise RuntimeError(f"candidatos de recibo nao encontrados: {CANDIDATES}")
    data = json.loads(CANDIDATES.read_text(encoding="utf-8"))
    if len(data) != 58:
        raise RuntimeError(f"esperado 58 candidatos; encontrado {len(data)}")
    for item in data:
        if not item.get("cpf") or not item.get("chosen_receipt") or not item.get("error_item_id"):
            raise RuntimeError(f"candidato incompleto: {item}")
        if item["chosen_receipt"] == item.get("receipt_used_wrong"):
            raise RuntimeError(f"recibo candidato igual ao errado para CPF {item['cpf']}")
    return sorted(data, key=lambda item: item["cpf"])


def current_error_rows(conn, cpfs: list[str]) -> dict[str, dict[str, Any]]:
    internal_empresa_id = tenant.internal_empresa_id(EMPRESA_ID)
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
        cursor.execute(
            """
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
               AND it.cpf = ANY(%s)
             ORDER BY it.cpf, it.criado_em DESC NULLS LAST, it.id DESC
            """,
            (internal_empresa_id, PER_APUR, cpfs),
        )
        rows = {row["cpf"]: dict(row) for row in cursor.fetchall()}
    missing = [cpf for cpf in cpfs if cpf not in rows]
    if missing:
        raise RuntimeError(f"CPFs sem linha atual: {missing[:20]}")
    return rows


def assert_current_receipt_error(row: dict[str, Any], candidate: dict[str, Any]) -> None:
    if int(row["item_id"]) != int(candidate["error_item_id"]):
        raise RuntimeError(
            f"CPF {candidate['cpf']} mudou de item atual: {row['item_id']} != {candidate['error_item_id']}"
        )
    if row.get("status") != "erro_esocial" or str(row.get("erro_codigo")) != "401":
        raise RuntimeError(f"CPF {candidate['cpf']} nao esta no erro 401 atual: {row}")
    message = str(row.get("erro_mensagem") or "")
    if "459" not in message and "157" not in message:
        raise RuntimeError(f"CPF {candidate['cpf']} erro atual nao e 459/157: {message}")
    if str(row.get("nr_recibo_anterior") or "") != str(candidate.get("receipt_used_wrong") or ""):
        raise RuntimeError(
            f"CPF {candidate['cpf']} recibo errado mudou: {row.get('nr_recibo_anterior')} != {candidate.get('receipt_used_wrong')}"
        )
    if not row.get("xml_enviado_oid"):
        raise RuntimeError(f"CPF {candidate['cpf']} sem xml_enviado_oid no erro atual")


def prepare_xml(conn, row: dict[str, Any], candidate: dict[str, Any]) -> tuple[bytes, dict[str, Any]]:
    xml_error = reenvio_base.read_xml_lo(conn, int(row["xml_enviado_oid"]))
    inner = reenvio_base.inner_s1210(xml_error)
    event_node = inner.xpath('./*[local-name()="evtPgtos"]')[0]
    old_id = event_node.get("Id") or ""
    cpf = reenvio_base.only_digits(inner.xpath('string(//*[local-name()="ideBenef"]/*[local-name()="cpfBenef"])'))
    if cpf != candidate["cpf"]:
        raise RuntimeError(f"XML do erro e de CPF {cpf}, esperado {candidate['cpf']}")
    tp_insc_text = inner.xpath('string(//*[local-name()="ideEmpregador"]/*[local-name()="tpInsc"])').strip()
    nr_insc = inner.xpath('string(//*[local-name()="ideEmpregador"]/*[local-name()="nrInsc"])').strip()
    event_node.set("Id", _gerar_id(int(tp_insc_text), nr_insc))
    ide_evento = event_node.xpath('./*[local-name()="ideEvento"]')[0]
    old_receipt = ide_evento.xpath('string(./*[local-name()="nrRecibo"])').strip()
    if old_receipt != candidate["receipt_used_wrong"]:
        raise RuntimeError(f"CPF {cpf} XML nao contem recibo errado esperado: {old_receipt}")
    reenvio_base.set_child(ide_evento, "indRetif", "2")
    reenvio_base.set_child(ide_evento, "nrRecibo", candidate["chosen_receipt"], after_tag="indRetif")
    if inner.xpath('string(//*[local-name()="ideEvento"]/*[local-name()="tpAmb"])').strip() != "1":
        raise RuntimeError(f"CPF {cpf} nao esta em tpAmb producao")
    if inner.xpath('string(//*[local-name()="ideEvento"]/*[local-name()="perApur"])').strip() != PER_APUR:
        raise RuntimeError(f"CPF {cpf} perApur divergente")
    xml_new = etree.tostring(inner, xml_declaration=True, encoding="UTF-8", pretty_print=False)
    if not eventos_iguais(xml_error, xml_new):
        raise RuntimeError(f"CPF {cpf} corpo canonico mudou")
    return xml_new, {
        "cpf": cpf,
        "source_error_item_id": row["item_id"],
        "source_error_envio_id": row["envio_id"],
        "source_xml_oid": row["xml_enviado_oid"],
        "old_id": old_id,
        "new_id": event_node.get("Id"),
        "wrong_receipt": candidate["receipt_used_wrong"],
        "chosen_receipt": candidate["chosen_receipt"],
        "chosen_source": candidate["chosen_source"],
    }


def generate_manifest() -> dict[str, Any]:
    XML_DIR.mkdir(parents=True, exist_ok=True)
    candidates = load_candidates()
    conn = db.connect(empresa_id=EMPRESA_ID)
    generated: list[dict[str, Any]] = []
    try:
        rows = current_error_rows(conn, [item["cpf"] for item in candidates])
        seen_ids: set[str] = set()
        for candidate in candidates:
            row = rows[candidate["cpf"]]
            assert_current_receipt_error(row, candidate)
            xml_new, meta = prepare_xml(conn, row, candidate)
            if meta["new_id"] in seen_ids:
                raise RuntimeError(f"Id duplicado: {meta['new_id']}")
            seen_ids.add(str(meta["new_id"]))
            xml_path = XML_DIR / f"S1210_{PER_APUR}_{candidate['cpf']}_fix459_unsigned.xml"
            xml_path.write_bytes(xml_new)
            generated.append({
                "cpf": candidate["cpf"],
                "xml": str(xml_path),
                "evento_id": row["versao_anterior_id"],
                "nr_recibo": candidate["chosen_receipt"],
                "id_evento": meta["new_id"],
                "validation": meta,
            })
    finally:
        conn.close()
    manifest = {
        "empresa_id": EMPRESA_ID,
        "per_apur": PER_APUR,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "total": len(generated),
        "regra": "corrigir erro 157/459 usando recibo da versao_anterior_id ativa do explorador",
        "targets": generated,
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
            raise RuntimeError(f"Id assinado divergente para CPF {target['cpf']}: {signed_id}")
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
                    "rotulo": "corrigir_recibo_explorador_xml_identico_58",
                    "empresa_id_externo": EMPRESA_ID,
                    "per_apur": PER_APUR,
                    "ambiente": "producao",
                    "origem": str(MANIFEST),
                    "envio_origem_erro": ENVIO_ERRO_ID,
                }),
            ),
        )
        envio_id = int(cursor.fetchone()["id"])
    conn.commit()
    return envio_id, month_id


def execute() -> dict[str, Any]:
    manifest = generate_manifest()
    targets = manifest["targets"]
    if len(targets) != 58:
        raise RuntimeError(f"esperado enviar 58 correcoes; encontrados {len(targets)}")
    senha = reenvio_base.read_password()
    signed = sign_targets(targets, senha)
    conn_db = db.connect(empresa_id=EMPRESA_ID)
    conn_w = db.connect(empresa_id=EMPRESA_ID)
    try:
        envio_base._verificar_estado_atual(conn_db, signed)
        envio_id, month_id = create_timeline(conn_db, len(signed))
        print(f"=> correcao recibo explorador: envio_id={envio_id} timeline_mes={month_id} targets={len(signed)}")
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
                "rotulo_final": "corrigir_recibo_explorador_xml_identico_58",
                "protocolos": protocolos,
                "histograma_erros": histograma,
                "manifest": str(MANIFEST),
                "envio_origem_erro": ENVIO_ERRO_ID,
            },
        )
        print("\n=== RESUMO CORRECAO RECIBO EXPLORADOR XML IDENTICO ===")
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