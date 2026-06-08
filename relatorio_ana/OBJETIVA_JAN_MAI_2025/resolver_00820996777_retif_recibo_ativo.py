from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path

import psycopg2.extras

ROOT = Path(__file__).resolve().parents[2]
SCRIPT_DIR = Path(__file__).resolve().parent
V2_BACKEND = Path(r"C:\Users\xandao\Documents\GitHub\Easy-eSocial-v2\backend")
sys.path.insert(0, str(SCRIPT_DIR))
sys.path.insert(0, str(V2_BACKEND))

from app import db, esocial_client, tenant  # noqa: E402
from app.envio_s1298 import _load_certificado  # noqa: E402
from app.envio_teste_100 import _ler_xml_evento  # noqa: E402
from app.xml_extractor import extrair_s1210  # noqa: E402
from app.xml_s1210 import S1210XMLGenerator  # noqa: E402
from app.xml_signer import S1010XMLSigner  # noqa: E402
from enviar_69_restantes_persistir_v2 import (  # noqa: E402
    EMPRESA_ID,
    PER_APUR,
    build_error_message,
    find_old_event_id,
    insert_item,
    insert_success_event,
    poll_batch,
    update_item_result,
    write_lo,
    xml_info,
)

CPF = "00820996777"
RECIBO_ATIVO_LOCAL = "1.1.0000000030733257763"
OUT_ROOT = ROOT / "relatorio_ana" / "OBJETIVA_JAN_MAI_2025" / "xmls_janeiro_70_corrigidos"
XML_DIR = OUT_ROOT / "03_recibo_459_retificacao_recibo_ativo"
RESULT_PATH = OUT_ROOT / "retorno_envio_008_retif_recibo_ativo.json"


def create_envio_individual(conn) -> int:
    internal_id = tenant.internal_empresa_id(EMPRESA_ID)
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
        cursor.execute(
            "SELECT id FROM timeline_mes WHERE empresa_id=%s AND per_apur=%s",
            (internal_id, PER_APUR),
        )
        mes = cursor.fetchone()
        if not mes:
            raise RuntimeError("timeline_mes ausente")
        cursor.execute(
            "SELECT COALESCE(MAX(sequencia), 0) + 1 AS seq FROM timeline_envio WHERE timeline_mes_id=%s",
            (mes["id"],),
        )
        seq = int(cursor.fetchone()["seq"])
        cursor.execute(
            """
            INSERT INTO timeline_envio
              (timeline_mes_id, sequencia, tipo, status, iniciado_em,
               total_tentados, total_sucesso, total_erro, resumo)
            VALUES (%s, %s, 'envio_individual', 'em_andamento', now(), 1, 0, 0, %s)
            RETURNING id
            """,
            (
                mes["id"],
                seq,
                psycopg2.extras.Json(
                    {
                        "rotulo": "objetiva_jan_resolve_008_apos_106",
                        "cpf": CPF,
                        "recibo_ativo_local": RECIBO_ATIVO_LOCAL,
                        "motivo": "inclusao retornou 106 duplicidade; retificar recibo ativo local",
                    }
                ),
            ),
        )
        envio_id = int(cursor.fetchone()["id"])
    conn.commit()
    return envio_id


def load_base_event(conn):
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
        cursor.execute(
            """
            SELECT ev.*, z.conteudo_oid, z.tamanho_bytes
              FROM explorador_eventos ev
              JOIN empresa_zips_brutos z ON z.id=ev.zip_id
             WHERE ev.tipo_evento='S-1210'
               AND ev.per_apur=%s
               AND ev.cpf=%s
               AND ev.nr_recibo=%s
             ORDER BY ev.dt_processamento DESC NULLS LAST, ev.id DESC
             LIMIT 1
            """,
            (PER_APUR, CPF, RECIBO_ATIVO_LOCAL),
        )
        row = cursor.fetchone()
        if not row:
            raise RuntimeError("evento base ativo local nao encontrado")
        return row


def main() -> None:
    XML_DIR.mkdir(parents=True, exist_ok=True)
    cert = _load_certificado(EMPRESA_ID, None)
    pfx_data = Path(cert["cert_path"]).read_bytes()

    conn = db.connect(empresa_id=EMPRESA_ID)
    lo_conn = db.connect(empresa_id=EMPRESA_ID)
    result = {}
    try:
        envio_id = create_envio_individual(conn)
        base_event = load_base_event(conn)
        campos = extrair_s1210(_ler_xml_evento(lo_conn, base_event))
        xml_unsigned = S1210XMLGenerator.gerar(
            empregador=campos["empregador"],
            beneficiario=campos["beneficiario"],
            info_pgtos=campos["info_pgtos"],
            per_apur=campos["per_apur"],
            ind_retif="2",
            nr_recibo=RECIBO_ATIVO_LOCAL,
            info_ir_complem=campos["info_ir_complem"],
            plan_saude=campos["plan_saude"],
            seq=801,
            tp_amb="1",
        )
        xml_signed = S1010XMLSigner.assinar(xml_unsigned, pfx_data, cert["senha"])
        xml_path = XML_DIR / f"S1210_2025-01_{CPF}_retificacao_recibo_ativo_assinado.xml"
        xml_path.write_bytes(xml_signed)
        info = xml_info(xml_signed)
        old_event_id = int(base_event["id"])
        xml_oid = write_lo(conn, xml_signed)
        item_id = insert_item(
            conn,
            envio_id=envio_id,
            cpf=CPF,
            status="pendente",
            old_event_id=old_event_id,
            old_recibo=RECIBO_ATIVO_LOCAL,
            xml_enviado_oid=xml_oid,
        )

        evento = esocial_client.EventoLote(xml_bytes=xml_signed, id_evento=info["id_evento"])
        envio = esocial_client.enviar_lote(
            [evento],
            cert_path=cert["cert_path"],
            cert_password=cert["senha"],
            cnpj_empregador=cert["cnpj"],
            ambiente="producao",
            grupo=3,
        )
        protocolo = envio.get("protocolo")
        if not envio.get("sucesso") or not protocolo:
            msg = envio.get("descricao") or envio.get("erro") or "lote rejeitado"
            update_item_result(
                conn,
                item_id=item_id,
                status="erro_esocial" if envio.get("http_status") == 200 else "falha_rede",
                nr_recibo_novo=None,
                erro_codigo=str(envio.get("codigo_resposta") or "ERRO_LOTE")[:32],
                erro_mensagem=str(msg)[:1000],
                xml_retorno_oid=write_lo(conn, envio.get("response_xml")),
                duracao_ms=None,
            )
            raise RuntimeError(f"envio nao aceito: {msg}")

        returned, _attempts = poll_batch(protocolo, {info["id_evento"]}, cert)
        match = returned.get(info["id_evento"])
        if not match:
            update_item_result(
                conn,
                item_id=item_id,
                status="pendente_consulta",
                nr_recibo_novo=None,
                erro_codigo="SEM_RETORNO",
                erro_mensagem="sem retorno na consulta",
                xml_retorno_oid=None,
                duracao_ms=None,
            )
            raise RuntimeError("sem retorno para o evento")

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
                duracao_ms=None,
            )
            item = {
                "cpf": CPF,
                "acao": "retificacao_indRetif_2_recibo_ativo_apos_106",
                "xml_path": str(xml_path.relative_to(ROOT)).replace("\\", "/"),
                "planSaude": campos.get("plan_saude") or [],
                "rubricas_usadas": [],
            }
            new_event_id = insert_success_event(
                conn,
                envio_id=envio_id,
                item_id=item_id,
                item=item,
                xml_bytes=xml_signed,
                info=info,
                old_event_id=old_event_id,
                old_recibo=RECIBO_ATIVO_LOCAL,
                nr_recibo_novo=match["nr_recibo"],
                codigo=codigo,
                descricao=match.get("descricao") or "",
                protocolo=protocolo,
                ocorrencias=ocorrencias,
            )
            status = "sucesso"
            erro = 0
        else:
            msg = build_error_message(codigo, match.get("descricao"), ocorrencias)
            update_item_result(
                conn,
                item_id=item_id,
                status="erro_esocial",
                nr_recibo_novo=None,
                erro_codigo=codigo[:32],
                erro_mensagem=msg,
                xml_retorno_oid=xml_retorno_oid,
                duracao_ms=None,
            )
            new_event_id = None
            status = "erro_esocial"
            erro = 1

        with conn.cursor() as cursor:
            cursor.execute(
                """
                UPDATE timeline_envio
                   SET status='concluido', finalizado_em=now(),
                       total_sucesso=%s, total_erro=%s,
                       resumo = resumo || %s::jsonb
                 WHERE id=%s
                """,
                (
                    1 if status == "sucesso" else 0,
                    erro,
                    json.dumps(
                        {
                            "protocolo": protocolo,
                            "codigo": codigo,
                            "descricao": match.get("descricao"),
                            "nr_recibo_novo": match.get("nr_recibo"),
                            "finalizado_em": datetime.now().isoformat(timespec="seconds"),
                        },
                        ensure_ascii=False,
                    ),
                    envio_id,
                ),
            )
        conn.commit()
        result = {
            "ok": status == "sucesso",
            "cpf": CPF,
            "timeline_envio_id": envio_id,
            "timeline_item_id": item_id,
            "versao_nova_id": new_event_id,
            "status": status,
            "protocolo": protocolo,
            "codigo": codigo,
            "descricao": match.get("descricao"),
            "nr_recibo_novo": match.get("nr_recibo"),
            "ocorrencias": ocorrencias,
            "xml_path": str(xml_path.relative_to(ROOT)).replace("\\", "/"),
        }
    finally:
        conn.close()
        lo_conn.close()

    RESULT_PATH.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()