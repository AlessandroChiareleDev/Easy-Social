from __future__ import annotations

import hashlib
import json
import re
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any

import psycopg2.extras
from lxml import etree

ROOT = Path(__file__).resolve().parents[1]
V2_BACKEND = Path(r"C:\Users\xandao\Documents\GitHub\Easy-eSocial-v2\backend")
HELPERS_DIR = ROOT / "relatorio_ana" / "OBJETIVA_JAN_MAI_2025"
sys.path.insert(0, str(V2_BACKEND))
sys.path.insert(0, str(HELPERS_DIR))

from app import db, esocial_client, tenant  # noqa: E402
from app.envio_s1298 import _load_certificado  # noqa: E402
from app.envio_teste_100 import _ler_xml_evento  # noqa: E402
from app.xml_extractor import extrair_s1210  # noqa: E402
from app.xml_s1210 import S1210XMLGenerator  # noqa: E402
from app.xml_signer import S1010XMLSigner  # noqa: E402

import gerar_xmls_fevereiro_67_corrigidos as plan_helpers  # noqa: E402

EMPRESA_ID = 3
AMBIENTE = "producao"
GRUPO = 3
OUT_ROOT = ROOT / "relatorio_ana" / "OBJETIVA_RECIBOS_459_SET_DEZ_2025"
XML_DIR = OUT_ROOT / "xmls"
RESULT_PATH = OUT_ROOT / "resultado_resolucao_recibos_459.json"
POLL_WAITS = [1.0, 1.5, 2.0, 3.0, 4.0] + [5.0] * 45

FIXES = [
    {
        "per_apur": "2025-09",
        "cpf": "06701349960",
        "base_recibo_local": "1.1.0000000035182530057",
        "recibo_ativo": "1.1.0000000035183951429",
        "s1200_periodos": ["2025-08", "2025-09"],
        "seq": 9091,
    },
    {
        "per_apur": "2025-12",
        "cpf": "00831605588",
        "base_recibo_local": "1.1.0000000037295806756",
        "recibo_ativo": "1.1.0000000037296094083",
        "s1200_periodos": ["2025-11", "2025-12"],
        "seq": 1212,
    },
]


def norm_cpf(value: str) -> str:
    return re.sub(r"\D", "", str(value or "")).zfill(11)[-11:]


def xp_text(root: etree._Element, name: str) -> str:
    return root.xpath(f'string(//*[local-name()="{name}"])')


def event_xml(lo_conn, row: dict[str, Any]) -> bytes:
    if row.get("xml_bytes"):
        return bytes(row["xml_bytes"])
    return _ler_xml_evento(lo_conn, row)


def xml_info(xml_bytes: bytes) -> dict[str, Any]:
    root = etree.fromstring(xml_bytes)
    return {
        "id_evento": root.xpath('string(//*[local-name()="evtPgtos"]/@Id)'),
        "cpf": norm_cpf(xp_text(root, "cpfBenef")),
        "indRetif": xp_text(root, "indRetif"),
        "nrRecibo": xp_text(root, "nrRecibo"),
        "perApur": xp_text(root, "perApur"),
        "dtPgto": [node.text for node in root.xpath('//*[local-name()="dtPgto"]')],
        "ideDmDev": [node.text for node in root.xpath('//*[local-name()="ideDmDev"]')],
        "planSaude_count": len(root.xpath('//*[local-name()="planSaude"]')),
        "signature_count": len(root.xpath('//*[local-name()="Signature"]')),
    }


def write_lo(conn, data: bytes | str | None) -> int | None:
    if data is None:
        return None
    payload = data.encode("utf-8") if isinstance(data, str) else data
    if not payload:
        return None
    large_object = conn.lobject(0, mode="wb")
    try:
        large_object.write(payload)
        return int(large_object.oid)
    finally:
        large_object.close()


def create_envio_individual(conn, fix: dict[str, Any]) -> int:
    internal_empresa_id = tenant.internal_empresa_id(EMPRESA_ID)
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
        cursor.execute(
            "SELECT id FROM timeline_mes WHERE empresa_id=%s AND per_apur=%s",
            (internal_empresa_id, fix["per_apur"]),
        )
        timeline_mes = cursor.fetchone()
        if not timeline_mes:
            raise RuntimeError(f"timeline_mes ausente para {fix['per_apur']}")
        cursor.execute(
            "SELECT COALESCE(MAX(sequencia), 0) + 1 AS seq FROM timeline_envio WHERE timeline_mes_id=%s",
            (timeline_mes["id"],),
        )
        sequencia = int(cursor.fetchone()["seq"])
        cursor.execute(
            """
            INSERT INTO timeline_envio
              (timeline_mes_id, sequencia, tipo, status, iniciado_em,
               total_tentados, total_sucesso, total_erro, resumo)
            VALUES (%s, %s, 'envio_individual', 'em_andamento', now(), 1, 0, 0, %s)
            RETURNING id
            """,
            (
                timeline_mes["id"],
                sequencia,
                psycopg2.extras.Json(
                    {
                        "rotulo": "objetiva_resolve_recibo_459_set_dez_2025",
                        "cpf": fix["cpf"],
                        "per_apur": fix["per_apur"],
                        "base_recibo_local": fix["base_recibo_local"],
                        "recibo_ativo_informado": fix["recibo_ativo"],
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
    base_event_id: int | None,
    active_recibo: str,
    xml_enviado_oid: int | None,
) -> int:
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
        cursor.execute(
            """
            INSERT INTO timeline_envio_item
              (timeline_envio_id, cpf, tipo_evento, status,
               versao_anterior_id, nr_recibo_anterior, xml_enviado_oid)
            VALUES (%s, %s, 'S-1210', 'pendente', %s, %s, %s)
            RETURNING id
            """,
            (envio_id, cpf, base_event_id, active_recibo, xml_enviado_oid),
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
) -> None:
    with conn.cursor() as cursor:
        cursor.execute(
            """
            UPDATE timeline_envio_item
               SET status=%s,
                   nr_recibo_novo=%s,
                   erro_codigo=%s,
                   erro_mensagem=%s,
                   xml_retorno_oid=COALESCE(%s, xml_retorno_oid)
             WHERE id=%s
            """,
            (status, nr_recibo_novo, erro_codigo, erro_mensagem, xml_retorno_oid, item_id),
        )
    conn.commit()


def finish_envio(conn, envio_id: int, success: bool, resumo: dict[str, Any]) -> None:
    with conn.cursor() as cursor:
        cursor.execute(
            """
            UPDATE timeline_envio
               SET status='concluido', finalizado_em=now(),
                   total_sucesso=%s, total_erro=%s,
                   resumo = resumo || %s::jsonb
             WHERE id=%s
            """,
            (1 if success else 0, 0 if success else 1, json.dumps(resumo, ensure_ascii=False, default=str), envio_id),
        )
    conn.commit()


def build_error_message(codigo: str | None, descricao: str | None, ocorrencias: list[dict[str, Any]]) -> str:
    parts = [f"{codigo}: {descricao}"]
    for ocorrencia in ocorrencias[:8]:
        parts.append(f"  - {ocorrencia.get('codigo')}: {ocorrencia.get('descricao')}")
    return " | ".join(parts)[:1000]


def load_base_event(cursor, fix: dict[str, Any]) -> dict[str, Any]:
    cursor.execute(
        """
        SELECT ev.*, z.conteudo_oid, z.tamanho_bytes
          FROM explorador_eventos ev
          LEFT JOIN empresa_zips_brutos z ON z.id = ev.zip_id
         WHERE ev.tipo_evento = 'S-1210'
           AND ev.per_apur = %s
           AND ev.cpf = %s
           AND ev.nr_recibo = %s
         ORDER BY ev.dt_processamento DESC NULLS LAST, ev.id DESC
         LIMIT 1
        """,
        (fix["per_apur"], fix["cpf"], fix["base_recibo_local"]),
    )
    row = cursor.fetchone()
    if not row:
        raise RuntimeError(f"S-1210 base local ausente para {fix['per_apur']} {fix['cpf']}")
    return dict(row)


def collect_plan_saude(cursor, lo_conn, fix: dict[str, Any], campos: dict[str, Any]) -> tuple[list[dict], list[dict], list[dict], dict | None]:
    existing_plan = campos.get("plan_saude") or []
    if existing_plan:
        return existing_plan, [], [], {"fallback": "planSaude_do_xml_base_local"}

    needed_dm = {info.get("ideDmDev") for info in campos["info_pgtos"] if info.get("ideDmDev")}
    rubricas_by_dm: dict[str, list[dict]] = {}
    source_events: list[dict] = []

    cursor.execute(
        """
        SELECT ev.*, z.conteudo_oid, z.tamanho_bytes
          FROM explorador_eventos ev
          LEFT JOIN empresa_zips_brutos z ON z.id = ev.zip_id
         WHERE ev.tipo_evento = 'S-1200'
           AND ev.cpf = %s
           AND ev.per_apur = ANY(%s)
         ORDER BY ev.dt_processamento DESC NULLS LAST, ev.id DESC
        """,
        (fix["cpf"], fix["s1200_periodos"]),
    )
    for row in cursor.fetchall():
        remaining = needed_dm - set(rubricas_by_dm)
        if not remaining:
            break
        parsed = plan_helpers.parse_s1200_rubricas(event_xml(lo_conn, row), remaining)
        for ide_dm_dev, rubricas in parsed.items():
            if ide_dm_dev in rubricas_by_dm or not rubricas:
                continue
            rubricas_by_dm[ide_dm_dev] = rubricas
            source_events.append(
                {
                    "ideDmDev": ide_dm_dev,
                    "tipo_evento": "S-1200",
                    "source_recibo": row["nr_recibo"],
                    "source_per_apur": row["per_apur"],
                    "source_evento_id": row["id_evento"],
                    "source_db_id": row["id"],
                }
            )

    cursor.execute(
        """
        SELECT ev.*, z.conteudo_oid, z.tamanho_bytes
          FROM explorador_eventos ev
          LEFT JOIN empresa_zips_brutos z ON z.id = ev.zip_id
         WHERE ev.tipo_evento IN ('S-2299', 'S-2399')
           AND ev.cpf = %s
           AND ev.cd_resposta IN ('201', '202')
         ORDER BY ev.dt_processamento DESC NULLS LAST, ev.id DESC
        """,
        (fix["cpf"],),
    )
    for row in cursor.fetchall():
        remaining = needed_dm - set(rubricas_by_dm)
        if not remaining:
            break
        parsed = plan_helpers.parse_rescisao_rubricas(event_xml(lo_conn, row), remaining)
        for ide_dm_dev, rubricas in parsed.items():
            if ide_dm_dev in rubricas_by_dm or not rubricas:
                continue
            rubricas_by_dm[ide_dm_dev] = rubricas
            source_events.append(
                {
                    "ideDmDev": ide_dm_dev,
                    "tipo_evento": row["tipo_evento"],
                    "source_recibo": row["nr_recibo"],
                    "source_per_apur": row["per_apur"],
                    "source_evento_id": row["id_evento"],
                    "source_db_id": row["id"],
                }
            )

    rubricas_usadas: list[dict] = []
    for ide_dm_dev in sorted(needed_dm):
        rubricas_usadas.extend(rubricas_by_dm.get(ide_dm_dev, []))
    plan_saude = plan_helpers.build_plan_saude(rubricas_usadas)
    fallback_source = None
    if not plan_saude:
        original_per_apur = plan_helpers.PER_APUR
        plan_helpers.PER_APUR = fix["per_apur"]
        try:
            plan_saude, fallback_source = plan_helpers.fallback_plan_saude(cursor, lo_conn, fix["cpf"])
        finally:
            plan_helpers.PER_APUR = original_per_apur
    return plan_saude, rubricas_usadas, source_events, fallback_source


def generate_xml(conn, lo_conn, fix: dict[str, Any], cert: dict[str, Any]) -> dict[str, Any]:
    XML_DIR.mkdir(parents=True, exist_ok=True)
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
        base_event = load_base_event(cursor, fix)
        campos = extrair_s1210(event_xml(lo_conn, base_event))
        plan_saude, rubricas_usadas, source_events, fallback_source = collect_plan_saude(cursor, lo_conn, fix, campos)

    unsigned = S1210XMLGenerator.gerar(
        empregador=campos["empregador"],
        beneficiario=campos["beneficiario"],
        info_pgtos=campos["info_pgtos"],
        per_apur=fix["per_apur"],
        ind_retif="2",
        nr_recibo=fix["recibo_ativo"],
        info_ir_complem=campos["info_ir_complem"],
        plan_saude=plan_saude,
        seq=fix["seq"],
        tp_amb="1",
    )
    signed = S1010XMLSigner.assinar(unsigned, Path(cert["cert_path"]).read_bytes(), cert["senha"])
    xml_path = XML_DIR / f"S1210_{fix['per_apur']}_{fix['cpf']}_retifica_recibo_ativo_assinado.xml"
    xml_path.write_bytes(signed)
    info = xml_info(signed)
    if info["cpf"] != fix["cpf"] or info["perApur"] != fix["per_apur"]:
        raise RuntimeError(f"XML divergente para {fix['cpf']}: {info}")
    if info["indRetif"] != "2" or info["nrRecibo"] != fix["recibo_ativo"]:
        raise RuntimeError(f"Recibo/retificacao divergente para {fix['cpf']}: {info}")
    if not info["id_evento"] or info["signature_count"] != 1:
        raise RuntimeError(f"XML invalido para {fix['cpf']}: {info}")
    return {
        "xml_path": str(xml_path.relative_to(ROOT)).replace("\\", "/"),
        "xml_bytes": signed,
        "info": info,
        "base_event_id": int(base_event["id"]),
        "base_evento_id": base_event.get("id_evento"),
        "base_recibo_local": fix["base_recibo_local"],
        "recibo_ativo": fix["recibo_ativo"],
        "planSaude": plan_saude,
        "rubricas_usadas": rubricas_usadas,
        "source_events": source_events,
        "fallback_source": fallback_source,
        "sha256": hashlib.sha256(signed).hexdigest(),
    }


def poll_event(protocolo: str, id_evento: str, cert: dict[str, Any]) -> tuple[dict[str, Any] | None, int]:
    for attempt, wait_seconds in enumerate(POLL_WAITS, start=1):
        time.sleep(wait_seconds)
        consulta = esocial_client.consultar_lote(
            protocolo,
            cert_path=cert["cert_path"],
            cert_password=cert["senha"],
            ambiente=AMBIENTE,
        )
        raw_path = OUT_ROOT / "xml_bruto" / "consultas" / f"consulta_{protocolo.replace('.', '_')}_att{attempt:03d}.xml"
        raw_path.parent.mkdir(parents=True, exist_ok=True)
        if consulta.get("response_xml"):
            raw_path.write_text(consulta["response_xml"], encoding="utf-8")
        for event in consulta.get("eventos") or []:
            if event.get("id_evento") == id_evento:
                print(f"poll {protocolo} att={attempt} retorno=1/1", flush=True)
                return event, attempt
        print(f"poll {protocolo} att={attempt} retorno=0/1", flush=True)
    return None, len(POLL_WAITS)


def insert_success_event(
    conn,
    *,
    envio_id: int,
    item_id: int,
    fix: dict[str, Any],
    generated: dict[str, Any],
    codigo: str,
    descricao: str,
    protocolo: str,
    nr_recibo_novo: str,
    ocorrencias: list[dict[str, Any]],
) -> int:
    info = generated["info"]
    xml_bytes = generated["xml_bytes"]
    dados = {
        "origem": "objetiva_resolve_recibo_459_set_dez_2025",
        "acao": "retificacao_indRetif_2_recibo_ativo_informado",
        "protocolo": protocolo,
        "codigo": codigo,
        "descricao": descricao,
        "ocorrencias": ocorrencias,
        "base_event_id": generated["base_event_id"],
        "base_evento_id": generated["base_evento_id"],
        "base_recibo_local": fix["base_recibo_local"],
        "recibo_ativo_informado": fix["recibo_ativo"],
        "dtPgto": info.get("dtPgto"),
        "ideDmDev": info.get("ideDmDev"),
        "planSaude": generated.get("planSaude") or [],
        "rubricas_usadas": generated.get("rubricas_usadas") or [],
        "source_events": generated.get("source_events") or [],
        "fallback_source": generated.get("fallback_source"),
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
                fix["cpf"],
                fix["per_apur"],
                nr_recibo_novo,
                info["id_evento"],
                codigo,
                Path(generated["xml_path"]).name,
                json.dumps(dados, ensure_ascii=False, default=str),
                Path(generated["xml_path"]).name,
                fix["recibo_ativo"],
                envio_id,
                len(xml_bytes),
                generated["sha256"],
                psycopg2.Binary(xml_bytes),
            ),
        )
        new_event_id = int(cursor.fetchone()["id"])
        cursor.execute("UPDATE timeline_envio_item SET versao_nova_id=%s WHERE id=%s", (new_event_id, item_id))
    conn.commit()
    return new_event_id


def send_fix(conn, fix: dict[str, Any], generated: dict[str, Any], cert: dict[str, Any]) -> dict[str, Any]:
    envio_id = create_envio_individual(conn, fix)
    xml_retorno_oid = None
    xml_oid = write_lo(conn, generated["xml_bytes"])
    item_id = insert_item(
        conn,
        envio_id=envio_id,
        cpf=fix["cpf"],
        base_event_id=generated["base_event_id"],
        active_recibo=fix["recibo_ativo"],
        xml_enviado_oid=xml_oid,
    )
    evento = esocial_client.EventoLote(xml_bytes=generated["xml_bytes"], id_evento=generated["info"]["id_evento"])
    envio = esocial_client.enviar_lote(
        [evento],
        cert_path=cert["cert_path"],
        cert_password=cert["senha"],
        cnpj_empregador=cert["cnpj"],
        ambiente=AMBIENTE,
        grupo=GRUPO,
    )
    raw_envio_path = OUT_ROOT / "xml_bruto" / "envios" / f"envio_{fix['per_apur']}_{fix['cpf']}.xml"
    raw_envio_path.parent.mkdir(parents=True, exist_ok=True)
    if envio.get("response_xml"):
        raw_envio_path.write_text(envio["response_xml"], encoding="utf-8")
    protocolo = envio.get("protocolo")
    print(
        f"{fix['per_apur']} {fix['cpf']}: envio cd={envio.get('codigo_resposta')} proto={protocolo} sucesso={envio.get('sucesso')}",
        flush=True,
    )
    if not envio.get("sucesso") or not protocolo:
        erro_mensagem = envio.get("descricao") or envio.get("erro") or "lote rejeitado"
        update_item_result(
            conn,
            item_id=item_id,
            status="erro_esocial" if envio.get("http_status") == 200 else "falha_rede",
            nr_recibo_novo=None,
            erro_codigo=str(envio.get("codigo_resposta") or "ERRO_LOTE")[:32],
            erro_mensagem=str(erro_mensagem)[:1000],
            xml_retorno_oid=write_lo(conn, envio.get("response_xml")),
        )
        finish_envio(conn, envio_id, False, {"erro": erro_mensagem, "envio": envio})
        return {"ok": False, "stage": "envio", "cpf": fix["cpf"], "per_apur": fix["per_apur"], "envio_id": envio_id, "erro": erro_mensagem}

    match, attempts = poll_event(protocolo, generated["info"]["id_evento"], cert)
    if not match:
        update_item_result(
            conn,
            item_id=item_id,
            status="pendente_consulta",
            nr_recibo_novo=None,
            erro_codigo="SEM_RETORNO",
            erro_mensagem=f"sem retorno apos {attempts} consultas",
            xml_retorno_oid=None,
        )
        finish_envio(conn, envio_id, False, {"protocolo": protocolo, "erro": "sem retorno"})
        return {"ok": False, "stage": "consulta", "cpf": fix["cpf"], "per_apur": fix["per_apur"], "envio_id": envio_id, "protocolo": protocolo}

    codigo = str(match.get("codigo") or "")
    ocorrencias = match.get("ocorrencias") or []
    xml_retorno_oid = write_lo(conn, match.get("xml_retorno"))
    if codigo in {"201", "202"} and match.get("nr_recibo"):
        update_item_result(
            conn,
            item_id=item_id,
            status="sucesso",
            nr_recibo_novo=match.get("nr_recibo"),
            erro_codigo=None if codigo == "201" else codigo,
            erro_mensagem=None if codigo == "201" else build_error_message(codigo, match.get("descricao"), ocorrencias),
            xml_retorno_oid=xml_retorno_oid,
        )
        new_event_id = insert_success_event(
            conn,
            envio_id=envio_id,
            item_id=item_id,
            fix=fix,
            generated=generated,
            codigo=codigo,
            descricao=match.get("descricao") or "",
            protocolo=protocolo,
            nr_recibo_novo=match["nr_recibo"],
            ocorrencias=ocorrencias,
        )
        finish_envio(
            conn,
            envio_id,
            True,
            {
                "protocolo": protocolo,
                "codigo": codigo,
                "descricao": match.get("descricao"),
                "nr_recibo_novo": match.get("nr_recibo"),
                "attempts": attempts,
            },
        )
        return {
            "ok": True,
            "cpf": fix["cpf"],
            "per_apur": fix["per_apur"],
            "timeline_envio_id": envio_id,
            "timeline_item_id": item_id,
            "versao_nova_id": new_event_id,
            "protocolo": protocolo,
            "codigo": codigo,
            "descricao": match.get("descricao"),
            "nr_recibo_novo": match.get("nr_recibo"),
            "xml_path": generated["xml_path"],
            "recibo_ativo_informado": fix["recibo_ativo"],
            "base_recibo_local": fix["base_recibo_local"],
            "planSaude_count": generated["info"]["planSaude_count"],
        }

    erro_mensagem = build_error_message(codigo, match.get("descricao"), ocorrencias)
    update_item_result(
        conn,
        item_id=item_id,
        status="erro_esocial",
        nr_recibo_novo=None,
        erro_codigo=codigo[:32],
        erro_mensagem=erro_mensagem,
        xml_retorno_oid=xml_retorno_oid,
    )
    finish_envio(conn, envio_id, False, {"protocolo": protocolo, "codigo": codigo, "erro": erro_mensagem})
    return {
        "ok": False,
        "cpf": fix["cpf"],
        "per_apur": fix["per_apur"],
        "timeline_envio_id": envio_id,
        "timeline_item_id": item_id,
        "protocolo": protocolo,
        "codigo": codigo,
        "descricao": match.get("descricao"),
        "ocorrencias": ocorrencias,
        "erro_mensagem": erro_mensagem,
        "xml_path": generated["xml_path"],
    }


def main() -> int:
    OUT_ROOT.mkdir(parents=True, exist_ok=True)
    cert = _load_certificado(EMPRESA_ID, None)
    conn = db.connect(empresa_id=EMPRESA_ID)
    lo_conn = db.connect(empresa_id=EMPRESA_ID)
    generated_items = []
    results = []
    try:
        for fix in FIXES:
            generated = generate_xml(conn, lo_conn, fix, cert)
            generated_items.append({key: value for key, value in generated.items() if key != "xml_bytes"})
            results.append(send_fix(conn, fix, generated, cert))
    finally:
        conn.close()
        lo_conn.close()

    payload = {
        "ok": all(result.get("ok") for result in results),
        "empresa": "OBJETIVA",
        "empresa_id": EMPRESA_ID,
        "ambiente": AMBIENTE,
        "gerado_em": datetime.now().isoformat(timespec="seconds"),
        "sem_chamada_download_ou_identificadores": True,
        "fixes": FIXES,
        "generated": generated_items,
        "results": results,
    }
    RESULT_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False, indent=2, default=str), flush=True)
    return 0 if payload["ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main())