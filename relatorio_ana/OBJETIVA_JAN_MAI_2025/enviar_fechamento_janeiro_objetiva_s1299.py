from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any

import psycopg2.extras
from lxml import etree

ROOT = Path(__file__).resolve().parents[2]
V2_BACKEND = Path(r"C:\Users\xandao\Documents\GitHub\Easy-eSocial-v2\backend")
PYTHON_SCRIPTS = ROOT / "python-scripts"
sys.path.insert(0, str(V2_BACKEND))
sys.path.insert(0, str(PYTHON_SCRIPTS))

from app import db, esocial_client, tenant  # noqa: E402
from app.envio_s1298 import _load_certificado  # noqa: E402
from app.xml_signer import S1010XMLSigner  # noqa: E402
from esocial.xml_s1299 import S1299XMLGenerator  # noqa: E402

EMPRESA_ID = 3
PER_APUR = "2025-01"
AMBIENTE = "producao"
TP_AMB = "1"
GRUPO = 3
CONFIRM_TOKEN = "FECHAR_JANEIRO_OBJETIVA_S1299"
OUT_DIR = ROOT / "relatorio_ana" / "OBJETIVA_JAN_MAI_2025" / "fechamento_janeiro_s1299"
XML_UNSIGNED = OUT_DIR / "S1299_2025-01_OBJETIVA_unsigned.xml"
XML_SIGNED = OUT_DIR / "S1299_2025-01_OBJETIVA_signed.xml"
MANIFEST = OUT_DIR / "manifest_fechamento_s1299_janeiro_objetiva.json"
POLL_WAITS = [1.0, 2.0, 3.0, 5.0] + [8.0] * 16


def xp_text(root: etree._Element, name: str) -> str:
    return root.xpath(f'string(//*[local-name()="{name}"])')


def event_id(xml_bytes: bytes) -> str:
    root = etree.fromstring(xml_bytes)
    value = root.xpath('string(//*[local-name()="evtFechaEvPer"]/@Id)')
    if not value:
        raise RuntimeError("Id do evtFechaEvPer nao encontrado")
    return value


def xml_info(xml_bytes: bytes, *, signed: bool = False) -> dict[str, Any]:
    root = etree.fromstring(xml_bytes)
    info = {
        "id_evento": event_id(xml_bytes),
        "per_apur": xp_text(root, "perApur"),
        "tp_amb": xp_text(root, "tpAmb"),
        "nr_insc": root.xpath('string(//*[local-name()="ideEmpregador"]/*[local-name()="nrInsc"])'),
        "signed": bool(root.xpath('//*[local-name()="Signature"]')),
        "size_bytes": len(xml_bytes),
    }
    if info["per_apur"] != PER_APUR:
        raise RuntimeError(f"perApur divergente: {info}")
    if info["tp_amb"] != TP_AMB:
        raise RuntimeError(f"tpAmb divergente: {info}")
    if signed and not info["signed"]:
        raise RuntimeError("XML assinado sem Signature")
    return info


def preflight_local() -> dict[str, Any]:
    internal_empresa_id = tenant.internal_empresa_id(EMPRESA_ID)
    conn = db.connect(empresa_id=EMPRESA_ID)
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
            cursor.execute(
                """
                WITH latest AS (
                    SELECT DISTINCT ON (it.cpf)
                           it.cpf, it.status, it.erro_codigo, it.erro_mensagem,
                           it.nr_recibo_novo, it.id AS item_id, it.timeline_envio_id AS envio_id
                      FROM timeline_envio_item it
                      JOIN timeline_envio te ON te.id = it.timeline_envio_id
                      JOIN timeline_mes tm ON tm.id = te.timeline_mes_id
                     WHERE tm.empresa_id = %s
                       AND tm.per_apur = %s
                       AND it.tipo_evento = 'S-1210'
                       AND it.cpf IS NOT NULL
                     ORDER BY it.cpf, it.criado_em DESC NULLS LAST, it.id DESC
                )
                SELECT status, COALESCE(erro_codigo, '') AS erro_codigo, COUNT(*) AS total
                  FROM latest
                 GROUP BY status, COALESCE(erro_codigo, '')
                 ORDER BY status, erro_codigo
                """,
                (internal_empresa_id, PER_APUR),
            )
            s1210_stats = [dict(row) for row in cursor.fetchall()]
            cursor.execute(
                """
                WITH latest AS (
                    SELECT DISTINCT ON (it.cpf)
                           it.cpf, it.status, it.erro_codigo, it.erro_mensagem,
                           it.nr_recibo_novo, it.id AS item_id, it.timeline_envio_id AS envio_id
                      FROM timeline_envio_item it
                      JOIN timeline_envio te ON te.id = it.timeline_envio_id
                      JOIN timeline_mes tm ON tm.id = te.timeline_mes_id
                     WHERE tm.empresa_id = %s
                       AND tm.per_apur = %s
                       AND it.tipo_evento = 'S-1210'
                       AND it.cpf IS NOT NULL
                     ORDER BY it.cpf, it.criado_em DESC NULLS LAST, it.id DESC
                )
                SELECT cpf, status, erro_codigo, erro_mensagem, nr_recibo_novo, item_id, envio_id
                  FROM latest
                 WHERE status <> 'sucesso'
                    OR COALESCE(erro_codigo, '') NOT IN ('', '202')
                 ORDER BY cpf
                 LIMIT 20
                """,
                (internal_empresa_id, PER_APUR),
            )
            pendencias = [dict(row) for row in cursor.fetchall()]
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS s1299_fechamento_status (
                  empresa_id    INT          NOT NULL,
                  per_apur      VARCHAR(7)   NOT NULL,
                  fechado       BOOLEAN      NOT NULL DEFAULT FALSE,
                  protocolo     VARCHAR(100),
                  nr_recibo     VARCHAR(100),
                  confirmado_em TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
                  origem        VARCHAR(40)  DEFAULT 'sync',
                  PRIMARY KEY (empresa_id, per_apur)
                )
                """
            )
            cursor.execute(
                """
                SELECT empresa_id, per_apur, fechado, protocolo, nr_recibo, origem, confirmado_em
                  FROM s1299_fechamento_status
                 WHERE empresa_id = %s AND per_apur = %s
                """,
                (internal_empresa_id, PER_APUR),
            )
            fechamento_status = dict(cursor.fetchone() or {})
            cursor.execute(
                """
                SELECT tipo_evento, cd_resposta, COUNT(*) AS total, MAX(dt_processamento) AS ultimo
                  FROM explorador_eventos
                 WHERE per_apur = %s
                   AND tipo_evento IN ('S-1298', 'S-1299')
                 GROUP BY tipo_evento, cd_resposta
                 ORDER BY tipo_evento, cd_resposta
                """,
                (PER_APUR,),
            )
            eventos_periodo = [dict(row) for row in cursor.fetchall()]
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

    if pendencias:
        raise RuntimeError(f"existem pendencias S-1210 antes do fechamento: {pendencias[:5]}")
    if fechamento_status.get("fechado") is True:
        raise RuntimeError(
            f"periodo {PER_APUR} ja consta fechado: "
            f"protocolo={fechamento_status.get('protocolo')} "
            f"recibo={fechamento_status.get('nr_recibo')}"
        )
    return {
        "empresa_id_externo": EMPRESA_ID,
        "empresa_id_interno": internal_empresa_id,
        "per_apur": PER_APUR,
        "s1210_stats": s1210_stats,
        "pendencias_s1210": len(pendencias),
        "fechamento_status_atual": fechamento_status,
        "eventos_s1298_s1299_periodo": eventos_periodo,
    }


def montar_xmls(cert: dict[str, Any]) -> dict[str, Any]:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    cnpj_raiz = str(cert["cnpj"])[:8]
    unsigned = S1299XMLGenerator.gerar(
        {"tpInsc": 1, "nrInsc": cnpj_raiz},
        PER_APUR,
        ind_apuracao="1",
        tp_amb=TP_AMB,
        seq=1,
    )
    unsigned_info = xml_info(unsigned)
    XML_UNSIGNED.write_bytes(unsigned)
    signed = S1010XMLSigner.assinar(unsigned, Path(cert["cert_path"]).read_bytes(), cert["senha"])
    signed_info = xml_info(signed, signed=True)
    if signed_info["id_evento"] != unsigned_info["id_evento"]:
        raise RuntimeError(f"Id mudou apos assinatura: {unsigned_info['id_evento']} != {signed_info['id_evento']}")
    XML_SIGNED.write_bytes(signed)
    return {
        "unsigned_xml": str(XML_UNSIGNED),
        "signed_xml": str(XML_SIGNED),
        "unsigned": unsigned_info,
        "signed": signed_info,
    }


def event_from_consulta(consulta: dict[str, Any] | None, id_evento: str) -> dict[str, Any] | None:
    for item in (consulta or {}).get("eventos") or []:
        if item.get("id_evento") == id_evento:
            return item
    eventos = (consulta or {}).get("eventos") or []
    return eventos[0] if eventos else None


def salvar_fechamento(
    *,
    id_evento: str,
    xml_assinado: bytes,
    protocolo: str | None,
    envio: dict[str, Any],
    consulta: dict[str, Any] | None,
) -> dict[str, Any]:
    evento = event_from_consulta(consulta, id_evento)
    codigo = (evento or {}).get("codigo") or envio.get("codigo_resposta")
    descricao = (evento or {}).get("descricao") or envio.get("descricao") or envio.get("erro")
    recibo = (evento or {}).get("nr_recibo")
    ocorrencias = (evento or {}).get("ocorrencias") or envio.get("ocorrencias") or []
    xml_retorno = (evento or {}).get("xml_retorno")
    aceito = str(codigo) in {"201", "202"} and bool(recibo)
    internal_empresa_id = tenant.internal_empresa_id(EMPRESA_ID)
    sha = hashlib.sha256(xml_assinado).hexdigest()
    dados = {
        "origem": f"envio_s1299_{PER_APUR.replace('-', '_')}_objetiva",
        "protocolo": protocolo,
        "codigo": codigo,
        "descricao": descricao,
        "ocorrencias": ocorrencias,
        "consulta": consulta,
        "envio": {
            "codigo_resposta": envio.get("codigo_resposta"),
            "descricao": envio.get("descricao"),
            "dh_recepcao": envio.get("dh_recepcao"),
            "http_status": envio.get("http_status"),
        },
        "xml_retorno": xml_retorno,
    }
    conn = db.connect(empresa_id=EMPRESA_ID)
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO explorador_eventos
                  (tipo_evento, cpf, per_apur, nr_recibo, id_evento,
                   dt_processamento, cd_resposta, arquivo_origem, dados_json,
                   xml_entry_name, xml_bytes, xml_size_bytes, xml_sha256)
                VALUES
                  ('S-1299', NULL, %s, %s, %s, NOW(), %s, %s, %s::jsonb,
                   %s, %s, %s, %s)
                ON CONFLICT (id_evento) WHERE id_evento IS NOT NULL DO UPDATE
                   SET nr_recibo = COALESCE(EXCLUDED.nr_recibo, explorador_eventos.nr_recibo),
                       dt_processamento = EXCLUDED.dt_processamento,
                       cd_resposta = EXCLUDED.cd_resposta,
                       arquivo_origem = EXCLUDED.arquivo_origem,
                       dados_json = EXCLUDED.dados_json,
                       xml_entry_name = EXCLUDED.xml_entry_name,
                       xml_bytes = EXCLUDED.xml_bytes,
                       xml_size_bytes = EXCLUDED.xml_size_bytes,
                       xml_sha256 = EXCLUDED.xml_sha256
                RETURNING id
                """,
                (
                    PER_APUR,
                    recibo,
                    id_evento,
                    codigo,
                    f"s1299_fechamento_{PER_APUR}_objetiva.xml",
                    json.dumps(dados, ensure_ascii=False, default=str),
                    f"s1299_fechamento_{PER_APUR}_objetiva.xml",
                    xml_assinado,
                    len(xml_assinado),
                    sha,
                ),
            )
            evento_db_id = int(cursor.fetchone()[0])
            cursor.execute(
                """
                INSERT INTO s1299_fechamento_status
                      (empresa_id, per_apur, fechado, protocolo, nr_recibo, origem, confirmado_em)
                VALUES (%s, %s, %s, %s, %s, 's1299_envio', NOW())
                ON CONFLICT (empresa_id, per_apur) DO UPDATE
                   SET fechado = EXCLUDED.fechado,
                       protocolo = EXCLUDED.protocolo,
                       nr_recibo = COALESCE(EXCLUDED.nr_recibo, s1299_fechamento_status.nr_recibo),
                       origem = 's1299_envio',
                       confirmado_em = NOW()
                """,
                (internal_empresa_id, PER_APUR, aceito, protocolo, recibo),
            )
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
    return {
        "evento_db_id": evento_db_id,
        "codigo": codigo,
        "descricao": descricao,
        "nr_recibo": recibo,
        "ocorrencias": ocorrencias,
        "aceito": aceito,
    }


def dry_run() -> dict[str, Any]:
    cert = _load_certificado(EMPRESA_ID, None)
    preflight = preflight_local()
    xmls = montar_xmls(cert)
    manifest = {
        "ok": True,
        "dry_run": True,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "empresa_id": EMPRESA_ID,
        "per_apur": PER_APUR,
        "cnpj": cert["cnpj"],
        "ambiente": AMBIENTE,
        "preflight": preflight,
        "xmls": xmls,
    }
    MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    return manifest


def execute() -> dict[str, Any]:
    cert = _load_certificado(EMPRESA_ID, None)
    preflight = preflight_local()
    xmls = montar_xmls(cert)
    xml_assinado = XML_SIGNED.read_bytes()
    id_evento = str(xmls["signed"]["id_evento"])
    evento = esocial_client.EventoLote(xml_bytes=xml_assinado, id_evento=id_evento)
    print(f"=> S-1299 fechamento OBJETIVA {PER_APUR} producao Id={id_evento}")
    envio = esocial_client.enviar_lote(
        [evento],
        cert_path=cert["cert_path"],
        cert_password=cert["senha"],
        cnpj_empregador=cert["cnpj"],
        ambiente=AMBIENTE,
        grupo=GRUPO,
    )
    print(
        "-> POST "
        f"http={envio.get('http_status')} cd={envio.get('codigo_resposta')} "
        f"desc={envio.get('descricao')} protocolo={envio.get('protocolo')}"
    )
    if envio.get("ocorrencias"):
        for ocorrencia in envio["ocorrencias"]:
            print(f"   OC {ocorrencia.get('codigo')}: {str(ocorrencia.get('descricao') or '')[:240]}")
    if not envio.get("sucesso"):
        salvo = salvar_fechamento(
            id_evento=id_evento,
            xml_assinado=xml_assinado,
            protocolo=envio.get("protocolo"),
            envio=envio,
            consulta=None,
        )
        return {"ok": False, "stage": "envio_lote", "id_evento": id_evento, "envio": envio, "salvo": salvo, "preflight": preflight}

    protocolo = envio.get("protocolo")
    consulta = None
    print(f"=> polling consultar_lote protocolo={protocolo}")
    for tentativa, wait_s in enumerate(POLL_WAITS, start=1):
        if tentativa > 1:
            time.sleep(wait_s)
        consulta = esocial_client.consultar_lote(
            protocolo,
            cert_path=cert["cert_path"],
            cert_password=cert["senha"],
            ambiente=AMBIENTE,
        )
        codigo_lote = consulta.get("codigo_lote")
        eventos = consulta.get("eventos") or []
        print(f"   [{tentativa}/{len(POLL_WAITS)}] cd_lote={codigo_lote} eventos={len(eventos)}")
        if codigo_lote == "201":
            break
        if codigo_lote and codigo_lote not in {"101", "104"}:
            break

    salvo = salvar_fechamento(
        id_evento=id_evento,
        xml_assinado=xml_assinado,
        protocolo=protocolo,
        envio=envio,
        consulta=consulta,
    )
    result = {
        "ok": bool(salvo.get("aceito")),
        "id_evento": id_evento,
        "protocolo": protocolo,
        "codigo_lote": (consulta or {}).get("codigo_lote"),
        "descricao_lote": (consulta or {}).get("descricao_lote"),
        "codigo": salvo.get("codigo"),
        "descricao": salvo.get("descricao"),
        "nr_recibo": salvo.get("nr_recibo"),
        "evento_db_id": salvo.get("evento_db_id"),
        "ocorrencias": salvo.get("ocorrencias"),
        "manifest": str(MANIFEST),
        "preflight": preflight,
    }
    manifest = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "empresa_id": EMPRESA_ID,
        "per_apur": PER_APUR,
        "cnpj": cert["cnpj"],
        "ambiente": AMBIENTE,
        "xmls": xmls,
        "resultado": result,
    }
    MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    return result


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
    result = execute()
    print(json.dumps(result, ensure_ascii=False, indent=2, default=str))
    return 0 if result.get("ok") else 2


if __name__ == "__main__":
    raise SystemExit(main())