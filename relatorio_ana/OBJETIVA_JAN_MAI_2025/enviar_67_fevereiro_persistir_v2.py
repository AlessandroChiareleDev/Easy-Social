from __future__ import annotations

import hashlib
import json
import sys
import time
from datetime import datetime
from pathlib import Path

import psycopg2.extras
from lxml import etree

ROOT = Path(__file__).resolve().parents[2]
V2_BACKEND = Path(r"C:\Users\xandao\Documents\GitHub\Easy-eSocial-v2\backend")
sys.path.insert(0, str(V2_BACKEND))

from app import db, esocial_client, tenant  # noqa: E402
from app.envio_s1298 import _load_certificado  # noqa: E402

EMPRESA_ID = 3
PER_APUR = "2025-02"
BATCH_SIZE = 40
POLL_WAITS = [1.0, 1.5, 2.0, 3.0, 4.0] + [5.0] * 55

OUT_ROOT = ROOT / "relatorio_ana" / "OBJETIVA_JAN_MAI_2025" / "xmls_fevereiro_67_corrigidos"
MANIFEST = OUT_ROOT / "manifest_67_xmls_corrigidos.json"
RUN_DIR = OUT_ROOT / "retorno_envio_67_fevereiro"
RESULT_PATH = RUN_DIR / "resultado_envio_67_fevereiro.json"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def xp_text(root: etree._Element, name: str) -> str:
    return root.xpath(f'string(//*[local-name()="{name}"])')


def xml_info(xml_bytes: bytes) -> dict:
    root = etree.fromstring(xml_bytes)
    return {
        "id_evento": esocial_client._extrair_id(xml_bytes),
        "cpf": xp_text(root, "cpfBenef"),
        "indRetif": xp_text(root, "indRetif"),
        "nrRecibo": xp_text(root, "nrRecibo"),
        "perApur": xp_text(root, "perApur"),
        "dtPgto": [node.text for node in root.xpath('//*[local-name()="dtPgto"]')],
        "planSaude_count": len(root.xpath('//*[local-name()="planSaude"]')),
        "signature_count": len(root.xpath('//*[local-name()="Signature"]')),
    }


def write_lo(conn, data: bytes | str | None) -> int | None:
    if data is None:
        return None
    payload = data.encode("utf-8") if isinstance(data, str) else data
    if not payload:
        return None
    lo = conn.lobject(0, mode="wb")
    oid = lo.oid
    try:
        lo.write(payload)
    finally:
        lo.close()
    return int(oid)


def find_old_event_id(cursor, cpf: str, nr_recibo: str | None) -> int | None:
    if not nr_recibo:
        return None
    cursor.execute(
        """
        SELECT id
          FROM explorador_eventos
         WHERE tipo_evento='S-1210'
           AND per_apur=%s
           AND cpf=%s
           AND nr_recibo=%s
         ORDER BY dt_processamento DESC NULLS LAST, id DESC
         LIMIT 1
        """,
        (PER_APUR, cpf, nr_recibo),
    )
    row = cursor.fetchone()
    return int(row["id"]) if row else None


def create_timeline_envio(conn, total: int) -> int:
    internal_id = tenant.internal_empresa_id(EMPRESA_ID)
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
        cursor.execute(
            "SELECT id FROM timeline_mes WHERE empresa_id=%s AND per_apur=%s",
            (internal_id, PER_APUR),
        )
        mes = cursor.fetchone()
        if not mes:
            raise RuntimeError(f"timeline_mes ausente para empresa_id={EMPRESA_ID} per_apur={PER_APUR}")

        cursor.execute(
            "SELECT COALESCE(MAX(sequencia), 0) + 1 AS seq FROM timeline_envio WHERE timeline_mes_id=%s",
            (mes["id"],),
        )
        sequencia = int(cursor.fetchone()["seq"])
        cursor.execute(
            """
            INSERT INTO timeline_envio
              (timeline_mes_id, sequencia, tipo, status, iniciado_em,
               total_tentados, total_sucesso, total_erro, resumo)
            VALUES (%s, %s, 'envio_massa', 'em_andamento', now(), %s, 0, 0, %s)
            RETURNING id
            """,
            (
                mes["id"],
                sequencia,
                total,
                psycopg2.extras.Json(
                    {
                        "rotulo": "objetiva_fev_67_xml_corrigidos",
                        "origem": "relatorio_ana/OBJETIVA_JAN_MAI_2025",
                        "modo": "producao",
                    }
                ),
            ),
        )
        envio_id = int(cursor.fetchone()["id"])
    conn.commit()
    return envio_id


def insert_item(
    conn,
    *,
    envio_id: int,
    cpf: str,
    status: str,
    old_event_id: int | None,
    old_recibo: str | None,
    xml_enviado_oid: int | None,
) -> int:
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
        cursor.execute(
            """
            INSERT INTO timeline_envio_item
              (timeline_envio_id, cpf, tipo_evento, status,
               versao_anterior_id, nr_recibo_anterior, xml_enviado_oid)
            VALUES (%s, %s, 'S-1210', %s, %s, %s, %s)
            RETURNING id
            """,
            (envio_id, cpf, status, old_event_id, old_recibo, xml_enviado_oid),
        )
        item_id = int(cursor.fetchone()["id"])
    conn.commit()
    return item_id


def update_item_result(
    conn,
    *,
    item_id: int,
    status: str,
    nr_recibo_novo: str | None,
    erro_codigo: str | None,
    erro_mensagem: str | None,
    xml_retorno_oid: int | None,
    duracao_ms: int | None,
) -> None:
    with conn.cursor() as cursor:
        cursor.execute(
            """
            UPDATE timeline_envio_item
               SET status=%s,
                   nr_recibo_novo=%s,
                   erro_codigo=%s,
                   erro_mensagem=%s,
                   xml_retorno_oid=COALESCE(%s, xml_retorno_oid),
                   duracao_ms=%s
             WHERE id=%s
            """,
            (status, nr_recibo_novo, erro_codigo, erro_mensagem, xml_retorno_oid, duracao_ms, item_id),
        )
    conn.commit()


def build_error_message(codigo: str | None, descricao: str | None, ocorrencias: list[dict]) -> str:
    parts = [f"{codigo}: {descricao}"]
    for oc in ocorrencias[:8]:
        parts.append(f"  - {oc.get('codigo')}: {oc.get('descricao')}")
    return " | ".join(parts)[:1000]


def insert_success_event(
    conn,
    *,
    envio_id: int,
    item_id: int,
    item: dict,
    xml_bytes: bytes,
    info: dict,
    old_event_id: int | None,
    old_recibo: str | None,
    nr_recibo_novo: str,
    codigo: str,
    descricao: str,
    protocolo: str,
    ocorrencias: list[dict],
) -> int:
    sha = hashlib.sha256(xml_bytes).hexdigest()
    dados = {
        "origem": "objetiva_fev_67_xml_corrigidos",
        "acao": item.get("acao"),
        "protocolo": protocolo,
        "codigo": codigo,
        "descricao": descricao,
        "ocorrencias": ocorrencias,
        "dtPgto": info.get("dtPgto"),
        "planSaude": item.get("planSaude"),
        "rubricas_usadas": item.get("rubricas_usadas"),
    }
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
        cursor.execute(
            """
            INSERT INTO explorador_eventos
              (tipo_evento, cpf, per_apur, nr_recibo, id_evento,
               dt_processamento, cd_resposta, arquivo_origem, dados_json,
               xml_entry_name, referenciado_recibo, origem_envio_id,
               xml_size_bytes, xml_sha256, xml_bytes)
            VALUES
              ('S-1210', %s, %s, %s, %s, now(), %s, %s, %s::jsonb,
               %s, %s, %s, %s, %s, %s)
            RETURNING id
            """,
            (
                info["cpf"],
                PER_APUR,
                nr_recibo_novo,
                info["id_evento"],
                codigo,
                Path(item["xml_path"]).name,
                json.dumps(dados, ensure_ascii=False),
                Path(item["xml_path"]).name,
                old_recibo if info.get("indRetif") == "2" else None,
                envio_id,
                len(xml_bytes),
                sha,
                psycopg2.Binary(xml_bytes),
            ),
        )
        new_event_id = int(cursor.fetchone()["id"])
        if old_event_id is not None and info.get("indRetif") == "2":
            cursor.execute(
                "UPDATE explorador_eventos SET retificado_por_id=%s WHERE id=%s",
                (new_event_id, old_event_id),
            )
        cursor.execute(
            "UPDATE timeline_envio_item SET versao_nova_id=%s WHERE id=%s",
            (new_event_id, item_id),
        )
    conn.commit()
    return new_event_id


def poll_batch(protocolo: str, expected_ids: set[str], cert: dict) -> tuple[dict[str, dict], int]:
    accumulated: dict[str, dict] = {}
    attempts = 0
    for attempt, wait_seconds in enumerate(POLL_WAITS, start=1):
        time.sleep(wait_seconds)
        attempts = attempt
        consulta = esocial_client.consultar_lote(
            protocolo,
            cert_path=cert["cert_path"],
            cert_password=cert["senha"],
            ambiente="producao",
        )
        raw_path = RUN_DIR / "xml_bruto" / "consultas" / f"consulta_{protocolo.replace('.', '_')}_att{attempt:03d}.xml"
        raw_path.parent.mkdir(parents=True, exist_ok=True)
        if consulta.get("response_xml"):
            raw_path.write_text(consulta["response_xml"], encoding="utf-8")
        for event in consulta.get("eventos") or []:
            event_id = event.get("id_evento")
            if event_id:
                accumulated[event_id] = event
        print(f"poll {protocolo} att={attempt} retornos={len(accumulated)}/{len(expected_ids)}", flush=True)
        if expected_ids.issubset(set(accumulated)):
            break
    return accumulated, attempts


def send_all(conn, envio_id: int, manifest: dict, cert: dict) -> list[dict]:
    results = []
    items = list(manifest["items"])
    for batch_index, start in enumerate(range(0, len(items), BATCH_SIZE), start=1):
        batch_items = items[start : start + BATCH_SIZE]
        eventos = []
        by_id = {}
        print(f"\nLOTE {batch_index}: preparando {len(batch_items)} XMLs", flush=True)
        for item in batch_items:
            xml_path = ROOT / item["xml_path"]
            xml_bytes = xml_path.read_bytes()
            info = xml_info(xml_bytes)
            if info["cpf"] != item["cpf"] or info["perApur"] != PER_APUR or info["indRetif"] != "2":
                raise RuntimeError(f"XML divergente para {item['cpf']}: {info}")
            if not info["id_evento"] or info["signature_count"] != 1 or info["planSaude_count"] < 1:
                raise RuntimeError(f"XML invalido para {item['cpf']}: {info}")
            old_recibo = item.get("nr_recibo_anterior")
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                old_event_id = find_old_event_id(cursor, item["cpf"], old_recibo)
            xml_oid = write_lo(conn, xml_bytes)
            item_id = insert_item(
                conn,
                envio_id=envio_id,
                cpf=item["cpf"],
                status="pendente",
                old_event_id=old_event_id,
                old_recibo=old_recibo,
                xml_enviado_oid=xml_oid,
            )
            evento = esocial_client.EventoLote(xml_bytes=xml_bytes, id_evento=info["id_evento"])
            eventos.append(evento)
            by_id[info["id_evento"]] = {
                "item": item,
                "item_id": item_id,
                "old_event_id": old_event_id,
                "old_recibo": old_recibo,
                "xml_bytes": xml_bytes,
                "info": info,
            }
        conn.commit()

        t0 = time.time()
        envio = esocial_client.enviar_lote(
            eventos,
            cert_path=cert["cert_path"],
            cert_password=cert["senha"],
            cnpj_empregador=cert["cnpj"],
            ambiente="producao",
            grupo=3,
        )
        raw_envio_path = RUN_DIR / "xml_bruto" / "envios" / f"envio_lote_{batch_index:02d}.xml"
        raw_envio_path.parent.mkdir(parents=True, exist_ok=True)
        if envio.get("response_xml"):
            raw_envio_path.write_text(envio["response_xml"], encoding="utf-8")
        print(
            f"LOTE {batch_index}: envio cd={envio.get('codigo_resposta')} proto={envio.get('protocolo')} sucesso={envio.get('sucesso')}",
            flush=True,
        )

        if not envio.get("sucesso") or not envio.get("protocolo"):
            xml_ret_oid = write_lo(conn, envio.get("response_xml"))
            status = "erro_esocial" if envio.get("http_status") == 200 else "falha_rede"
            msg = envio.get("descricao") or envio.get("erro") or "lote rejeitado"
            for data in by_id.values():
                update_item_result(
                    conn,
                    item_id=data["item_id"],
                    status=status,
                    nr_recibo_novo=None,
                    erro_codigo=str(envio.get("codigo_resposta") or "ERRO_LOTE")[:32],
                    erro_mensagem=str(msg)[:1000],
                    xml_retorno_oid=xml_ret_oid,
                    duracao_ms=int((time.time() - t0) * 1000) // max(len(by_id), 1),
                )
                results.append({"cpf": data["item"]["cpf"], "status": status, "erro": msg})
            continue

        protocolo = envio["protocolo"]
        returned, attempts = poll_batch(protocolo, set(by_id), cert)
        duracao_ms = int((time.time() - t0) * 1000) // max(len(by_id), 1)

        for event_id, data in by_id.items():
            item = data["item"]
            match = returned.get(event_id)
            if not match:
                update_item_result(
                    conn,
                    item_id=data["item_id"],
                    status="pendente_consulta",
                    nr_recibo_novo=None,
                    erro_codigo="SEM_RETORNO",
                    erro_mensagem=f"sem retorno apos {attempts} consultas",
                    xml_retorno_oid=None,
                    duracao_ms=duracao_ms,
                )
                results.append({"cpf": item["cpf"], "status": "pendente_consulta", "protocolo": protocolo})
                continue

            xml_retorno_oid = write_lo(conn, match.get("xml_retorno"))
            codigo = str(match.get("codigo") or "")
            ocorrencias = match.get("ocorrencias") or []
            if codigo in {"201", "202"} and match.get("nr_recibo"):
                erro_codigo = codigo if codigo == "202" else None
                erro_mensagem = build_error_message(codigo, match.get("descricao"), ocorrencias) if codigo == "202" else None
                update_item_result(
                    conn,
                    item_id=data["item_id"],
                    status="sucesso",
                    nr_recibo_novo=match.get("nr_recibo"),
                    erro_codigo=erro_codigo,
                    erro_mensagem=erro_mensagem,
                    xml_retorno_oid=xml_retorno_oid,
                    duracao_ms=duracao_ms,
                )
                new_event_id = insert_success_event(
                    conn,
                    envio_id=envio_id,
                    item_id=data["item_id"],
                    item=item,
                    xml_bytes=data["xml_bytes"],
                    info=data["info"],
                    old_event_id=data["old_event_id"],
                    old_recibo=data["old_recibo"],
                    nr_recibo_novo=match["nr_recibo"],
                    codigo=codigo,
                    descricao=match.get("descricao") or "",
                    protocolo=protocolo,
                    ocorrencias=ocorrencias,
                )
                results.append(
                    {
                        "cpf": item["cpf"],
                        "status": "sucesso",
                        "codigo": codigo,
                        "protocolo": protocolo,
                        "nr_recibo_novo": match.get("nr_recibo"),
                        "versao_nova_id": new_event_id,
                    }
                )
            else:
                msg = build_error_message(codigo, match.get("descricao"), ocorrencias)
                update_item_result(
                    conn,
                    item_id=data["item_id"],
                    status="erro_esocial",
                    nr_recibo_novo=None,
                    erro_codigo=codigo[:32],
                    erro_mensagem=msg,
                    xml_retorno_oid=xml_retorno_oid,
                    duracao_ms=duracao_ms,
                )
                results.append(
                    {
                        "cpf": item["cpf"],
                        "status": "erro_esocial",
                        "codigo": codigo,
                        "descricao": match.get("descricao"),
                        "ocorrencias": ocorrencias,
                        "protocolo": protocolo,
                    }
                )
        ok_count = sum(1 for result in results if result["status"] == "sucesso")
        err_count = sum(1 for result in results if result["status"] != "sucesso")
        print(f"LOTE {batch_index}: acumulado ok={ok_count} pend/erro={err_count}", flush=True)
    return results


def update_envio_totals(conn, envio_id: int, results: list[dict]) -> None:
    sucesso = sum(1 for result in results if result["status"] == "sucesso")
    erro = sum(1 for result in results if result["status"] != "sucesso")
    protocolos = sorted({result.get("protocolo") for result in results if result.get("protocolo")})
    resumo = {
        "finalizado_por": "enviar_67_fevereiro_persistir_v2.py",
        "finalizado_em": datetime.now().isoformat(timespec="seconds"),
        "protocolos": protocolos,
        "sucesso": sucesso,
        "erro": erro,
    }
    with conn.cursor() as cursor:
        cursor.execute(
            """
            UPDATE timeline_envio
               SET status='concluido',
                   finalizado_em=now(),
                   total_sucesso=%s,
                   total_erro=%s,
                   resumo = resumo || %s::jsonb
             WHERE id=%s
            """,
            (sucesso, erro, json.dumps(resumo, ensure_ascii=False), envio_id),
        )
    conn.commit()


def main() -> None:
    RUN_DIR.mkdir(parents=True, exist_ok=True)
    manifest = load_json(MANIFEST)
    cert = _load_certificado(EMPRESA_ID, None)

    if manifest.get("per_apur_s1210") != PER_APUR:
        raise RuntimeError(f"manifest per_apur divergente: {manifest.get('per_apur_s1210')}")
    expected_total = int(manifest.get("total_xmls_gerados") or len(manifest["items"]))
    if len(manifest["items"]) != expected_total:
        raise RuntimeError(f"manifest deveria ter {expected_total} items, tem {len(manifest['items'])}")

    conn = db.connect(empresa_id=EMPRESA_ID)
    all_results: dict = {}
    try:
        envio_id = create_timeline_envio(conn, total=len(manifest["items"]))
        print(f"timeline_envio_id={envio_id}", flush=True)
        results = send_all(conn, envio_id, manifest, cert)
        update_envio_totals(conn, envio_id, results)
        all_results = {
            "ok": True,
            "empresa": "OBJETIVA",
            "empresa_id": EMPRESA_ID,
            "per_apur": PER_APUR,
            "timeline_envio_id": envio_id,
            "total_enviados_agora": len(results),
            "total_sucesso": sum(1 for result in results if result["status"] == "sucesso"),
            "total_erro_ou_pendente": sum(1 for result in results if result["status"] != "sucesso"),
            "results": results,
        }
    finally:
        conn.close()

    RESULT_PATH.write_text(json.dumps(all_results, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({k: v for k, v in all_results.items() if k != "results"}, ensure_ascii=False, indent=2), flush=True)
    if all_results.get("total_erro_ou_pendente"):
        print("ERROS/PENDENTES:", flush=True)
        for result in all_results["results"]:
            if result["status"] != "sucesso":
                print(json.dumps(result, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()