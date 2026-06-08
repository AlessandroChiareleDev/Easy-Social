from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import psycopg2.extras

ROOT = Path(__file__).resolve().parents[1]
SCRIPT_DIR = ROOT / "relatorio_ana"
V2_BACKEND = Path(r"C:\Users\xandao\Documents\GitHub\Easy-eSocial-v2\backend")
sys.path.insert(0, str(SCRIPT_DIR))
sys.path.insert(0, str(V2_BACKEND))

from app import db, esocial_client  # noqa: E402
from app.envio_s1298 import _load_certificado  # noqa: E402
from app.xml_extractor import extrair_s1210  # noqa: E402
from app.xml_s1210 import S1210XMLGenerator  # noqa: E402
from app.xml_signer import S1010XMLSigner  # noqa: E402

import resolver_recibos_459_setembro_dezembro_objetiva as base  # noqa: E402

EMPRESA_ID = 3
FIX = {
    "per_apur": "2025-09",
    "cpf": "06701349960",
    "base_recibo_local": "1.1.0000000035182530057",
    "recibo_s3000_exclusao": "1.1.0000000035183951429",
    "recibo_ativo": "",
    "s1200_periodos": ["2025-08", "2025-09"],
    "seq": 9092,
}
OUT_ROOT = ROOT / "relatorio_ana" / "OBJETIVA_RECIBOS_459_SET_DEZ_2025"
XML_DIR = OUT_ROOT / "xmls"
RESULT_PATH = OUT_ROOT / "resultado_inclusao_setembro_06701349960.json"


def insert_success_event_inclusion(
    conn,
    *,
    envio_id: int,
    item_id: int,
    generated: dict[str, Any],
    codigo: str,
    descricao: str,
    protocolo: str,
    nr_recibo_novo: str,
    ocorrencias: list[dict[str, Any]],
) -> int:
    info = generated["info"]
    xml_bytes = generated["xml_bytes"]
    sha = hashlib.sha256(xml_bytes).hexdigest()
    dados = {
        "origem": "objetiva_inclusao_06701349960_setembro_apos_s3000",
        "acao": "inclusao_indRetif_1_apos_s3000_excluir_s1210",
        "protocolo": protocolo,
        "codigo": codigo,
        "descricao": descricao,
        "ocorrencias": ocorrencias,
        "base_event_id": generated["base_event_id"],
        "base_evento_id": generated["base_evento_id"],
        "base_recibo_local_excluido": FIX["base_recibo_local"],
        "recibo_s3000_exclusao_informado": FIX["recibo_s3000_exclusao"],
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
               %s, NULL, %s, %s, %s, %s)
            RETURNING id
            """,
            (
                FIX["cpf"],
                FIX["per_apur"],
                nr_recibo_novo,
                info["id_evento"],
                codigo,
                Path(generated["xml_path"]).name,
                json.dumps(dados, ensure_ascii=False, default=str),
                Path(generated["xml_path"]).name,
                envio_id,
                len(xml_bytes),
                sha,
                psycopg2.Binary(xml_bytes),
            ),
        )
        new_event_id = int(cursor.fetchone()["id"])
        cursor.execute("UPDATE timeline_envio_item SET versao_nova_id=%s WHERE id=%s", (new_event_id, item_id))
    conn.commit()
    return new_event_id


def generate_inclusion(conn, lo_conn, cert: dict[str, Any]) -> dict[str, Any]:
    XML_DIR.mkdir(parents=True, exist_ok=True)
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
        base_event = base.load_base_event(cursor, FIX)
        campos = extrair_s1210(base.event_xml(lo_conn, base_event))
        plan_saude, rubricas_usadas, source_events, fallback_source = base.collect_plan_saude(cursor, lo_conn, FIX, campos)

    unsigned = S1210XMLGenerator.gerar(
        empregador=campos["empregador"],
        beneficiario=campos["beneficiario"],
        info_pgtos=campos["info_pgtos"],
        per_apur=FIX["per_apur"],
        ind_retif="1",
        nr_recibo=None,
        info_ir_complem=campos["info_ir_complem"],
        plan_saude=plan_saude,
        seq=FIX["seq"],
        tp_amb="1",
    )
    signed = S1010XMLSigner.assinar(unsigned, Path(cert["cert_path"]).read_bytes(), cert["senha"])
    xml_path = XML_DIR / "S1210_2025-09_06701349960_inclusao_apos_s3000_assinado.xml"
    xml_path.write_bytes(signed)
    info = base.xml_info(signed)
    if info["cpf"] != FIX["cpf"] or info["perApur"] != FIX["per_apur"]:
        raise RuntimeError(f"XML divergente: {info}")
    if info["indRetif"] != "1" or info["nrRecibo"]:
        raise RuntimeError(f"Inclusao invalida: {info}")
    if not info["id_evento"] or info["signature_count"] != 1:
        raise RuntimeError(f"XML invalido: {info}")
    return {
        "xml_path": str(xml_path.relative_to(ROOT)).replace("\\", "/"),
        "xml_bytes": signed,
        "info": info,
        "base_event_id": int(base_event["id"]),
        "base_evento_id": base_event.get("id_evento"),
        "planSaude": plan_saude,
        "rubricas_usadas": rubricas_usadas,
        "source_events": source_events,
        "fallback_source": fallback_source,
    }


def send_inclusion(conn, generated: dict[str, Any], cert: dict[str, Any]) -> dict[str, Any]:
    envio_id = base.create_envio_individual(conn, FIX)
    xml_oid = base.write_lo(conn, generated["xml_bytes"])
    item_id = base.insert_item(
        conn,
        envio_id=envio_id,
        cpf=FIX["cpf"],
        base_event_id=generated["base_event_id"],
        active_recibo=FIX["base_recibo_local"],
        xml_enviado_oid=xml_oid,
    )
    evento = esocial_client.EventoLote(xml_bytes=generated["xml_bytes"], id_evento=generated["info"]["id_evento"])
    envio = esocial_client.enviar_lote(
        [evento],
        cert_path=cert["cert_path"],
        cert_password=cert["senha"],
        cnpj_empregador=cert["cnpj"],
        ambiente=base.AMBIENTE,
        grupo=base.GRUPO,
    )
    protocolo = envio.get("protocolo")
    raw_envio_path = OUT_ROOT / "xml_bruto" / "envios" / "envio_inclusao_setembro_06701349960.xml"
    raw_envio_path.parent.mkdir(parents=True, exist_ok=True)
    if envio.get("response_xml"):
        raw_envio_path.write_text(envio["response_xml"], encoding="utf-8")
    print(f"inclusao setembro 06701349960: envio cd={envio.get('codigo_resposta')} proto={protocolo} sucesso={envio.get('sucesso')}", flush=True)
    if not envio.get("sucesso") or not protocolo:
        erro_mensagem = envio.get("descricao") or envio.get("erro") or "lote rejeitado"
        base.update_item_result(
            conn,
            item_id=item_id,
            status="erro_esocial" if envio.get("http_status") == 200 else "falha_rede",
            nr_recibo_novo=None,
            erro_codigo=str(envio.get("codigo_resposta") or "ERRO_LOTE")[:32],
            erro_mensagem=str(erro_mensagem)[:1000],
            xml_retorno_oid=base.write_lo(conn, envio.get("response_xml")),
        )
        base.finish_envio(conn, envio_id, False, {"erro": erro_mensagem, "envio": envio})
        return {"ok": False, "stage": "envio", "timeline_envio_id": envio_id, "erro": erro_mensagem}

    match, attempts = base.poll_event(protocolo, generated["info"]["id_evento"], cert)
    if not match:
        base.update_item_result(
            conn,
            item_id=item_id,
            status="pendente_consulta",
            nr_recibo_novo=None,
            erro_codigo="SEM_RETORNO",
            erro_mensagem=f"sem retorno apos {attempts} consultas",
            xml_retorno_oid=None,
        )
        base.finish_envio(conn, envio_id, False, {"protocolo": protocolo, "erro": "sem retorno"})
        return {"ok": False, "stage": "consulta", "timeline_envio_id": envio_id, "protocolo": protocolo}

    codigo = str(match.get("codigo") or "")
    ocorrencias = match.get("ocorrencias") or []
    xml_retorno_oid = base.write_lo(conn, match.get("xml_retorno"))
    if codigo in {"201", "202"} and match.get("nr_recibo"):
        base.update_item_result(
            conn,
            item_id=item_id,
            status="sucesso",
            nr_recibo_novo=match.get("nr_recibo"),
            erro_codigo=None if codigo == "201" else codigo,
            erro_mensagem=None if codigo == "201" else base.build_error_message(codigo, match.get("descricao"), ocorrencias),
            xml_retorno_oid=xml_retorno_oid,
        )
        new_event_id = insert_success_event_inclusion(
            conn,
            envio_id=envio_id,
            item_id=item_id,
            generated=generated,
            codigo=codigo,
            descricao=match.get("descricao") or "",
            protocolo=protocolo,
            nr_recibo_novo=match["nr_recibo"],
            ocorrencias=ocorrencias,
        )
        base.finish_envio(
            conn,
            envio_id,
            True,
            {"protocolo": protocolo, "codigo": codigo, "descricao": match.get("descricao"), "nr_recibo_novo": match.get("nr_recibo"), "attempts": attempts},
        )
        return {
            "ok": True,
            "cpf": FIX["cpf"],
            "per_apur": FIX["per_apur"],
            "timeline_envio_id": envio_id,
            "timeline_item_id": item_id,
            "versao_nova_id": new_event_id,
            "protocolo": protocolo,
            "codigo": codigo,
            "descricao": match.get("descricao"),
            "nr_recibo_novo": match.get("nr_recibo"),
            "xml_path": generated["xml_path"],
        }

    erro_mensagem = base.build_error_message(codigo, match.get("descricao"), ocorrencias)
    base.update_item_result(
        conn,
        item_id=item_id,
        status="erro_esocial",
        nr_recibo_novo=None,
        erro_codigo=codigo[:32],
        erro_mensagem=erro_mensagem,
        xml_retorno_oid=xml_retorno_oid,
    )
    base.finish_envio(conn, envio_id, False, {"protocolo": protocolo, "codigo": codigo, "erro": erro_mensagem})
    return {"ok": False, "timeline_envio_id": envio_id, "timeline_item_id": item_id, "protocolo": protocolo, "codigo": codigo, "erro_mensagem": erro_mensagem, "ocorrencias": ocorrencias}


def main() -> int:
    OUT_ROOT.mkdir(parents=True, exist_ok=True)
    cert = _load_certificado(EMPRESA_ID, None)
    conn = db.connect(empresa_id=EMPRESA_ID)
    lo_conn = db.connect(empresa_id=EMPRESA_ID)
    try:
        generated = generate_inclusion(conn, lo_conn, cert)
        result = send_inclusion(conn, generated, cert)
    finally:
        conn.close()
        lo_conn.close()

    payload = {
        "ok": result.get("ok") is True,
        "empresa": "OBJETIVA",
        "empresa_id": EMPRESA_ID,
        "ambiente": base.AMBIENTE,
        "gerado_em": datetime.now().isoformat(timespec="seconds"),
        "sem_chamada_download_ou_identificadores": True,
        "fix": FIX,
        "generated": {key: value for key, value in generated.items() if key != "xml_bytes"},
        "result": result,
    }
    RESULT_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False, indent=2, default=str), flush=True)
    return 0 if payload["ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main())