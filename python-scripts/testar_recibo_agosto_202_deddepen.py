from __future__ import annotations

import argparse
import getpass
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import psycopg2.extras


ROOT = Path(r"C:\Users\xandao\Documents\GitHub\Easy-Social")
BACKEND_V2 = Path(r"C:\Users\xandao\Documents\GitHub\Easy-eSocial-v2\backend")
if str(ROOT / "python-scripts") not in sys.path:
    sys.path.insert(0, str(ROOT / "python-scripts"))
if str(BACKEND_V2) not in sys.path:
    sys.path.insert(0, str(BACKEND_V2))

import enviar_correcao_agosto_jaque as envio_base  # noqa: E402
from app import db, tenant  # noqa: E402
from gerar_correcao_agosto_202_deddepen import prepare_xml  # noqa: E402
from preparar_correcao_agosto_202_deddepen import (  # noqa: E402
    EMPRESA_ID,
    OUT_DIR,
    PER_APUR,
    cpf11,
    load_event_rows,
    read_xml_event,
)


SUMMARY_PATH = OUT_DIR / "preflight_agosto_202_deddepen.json"
DEFAULT_CERT = ROOT / "_certificados_locais" / "SOLUCOES_SERVICOS_TERCEIRIZADOS_09445502000109.pfx"
TEST_DIR = OUT_DIR / "teste_recibo_override"


def _load_target(cpf: str) -> dict[str, Any]:
    summary = json.loads(SUMMARY_PATH.read_text(encoding="utf-8"))
    cpf = cpf11(cpf)
    for item in summary.get("evidence") or []:
        if cpf11(item.get("cpf")) != cpf:
            continue
        if item.get("confianca") != "alta" or not item.get("dedDepen_corrigir"):
            raise RuntimeError(f"CPF {cpf} nao e alvo alta confianca dedDepen")
        return item
    raise RuntimeError(f"CPF {cpf} nao encontrado no preflight")


def _criar_timeline_envio_teste(conn, cpf: str, recibo: str) -> tuple[int, int]:
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
              (%s, %s, 'envio_massa', 'em_andamento', now(), 1, 0, 0, %s)
            RETURNING id
            """,
            (
                mes_id,
                sequencia,
                psycopg2.extras.Json(
                    {
                        "rotulo": "teste_recibo_agosto_202_deddepen",
                        "empresa_id_externo": EMPRESA_ID,
                        "per_apur": PER_APUR,
                        "ambiente": "producao",
                        "cpf": cpf,
                        "recibo_override": recibo,
                        "origem": str(SUMMARY_PATH),
                    }
                ),
            ),
        )
        envio_id = int(cur.fetchone()["id"])
    conn.commit()
    return envio_id, mes_id


def _gerar_xml(cpf: str, recibo: str) -> dict[str, Any]:
    cpf = cpf11(cpf)
    item = _load_target(cpf)
    item = {**item, "recibo_ativo_local": recibo, "recibo_fonte_local": "override_usuario"}
    event_rows = load_event_rows([cpf], PER_APUR)
    event = event_rows.get(cpf)
    if not event:
        raise RuntimeError(f"S-1210 HEAD nao encontrado para {cpf}")
    conn = db.connect(empresa_id=EMPRESA_ID)
    try:
        xml_bytes = read_xml_event(conn, event)
    finally:
        conn.close()
    xml_out, meta = prepare_xml(xml_bytes, item, 1)
    TEST_DIR.mkdir(parents=True, exist_ok=True)
    out_path = TEST_DIR / f"S1210_{PER_APUR}_{cpf}_dedDepen202_recibo_override_unsigned.xml"
    out_path.write_bytes(xml_out)
    return {
        "cpf": cpf,
        "xml": str(out_path),
        "id_evento": meta["id_evento"],
        "evento_id": int(event["id"]),
        "nr_recibo": recibo,
        "source_recibo": event.get("nr_recibo"),
        "source_event_id": event.get("id_evento"),
        "source_zip": event.get("zip_nome"),
        "ded_count": meta["ded_count"],
        "dependentes": item.get("dedDepen_corrigir") or [],
        "notes": meta["notes"],
    }


def rodar(*, cpf: str, recibo: str, cert_path: Path, senha: str, cnpj: str) -> dict[str, Any]:
    target = _gerar_xml(cpf, recibo)
    conn_db = db.connect(empresa_id=EMPRESA_ID)
    conn_w = db.connect(empresa_id=EMPRESA_ID)
    try:
        envio_base._verificar_estado_atual(conn_db, [target])
        signed = envio_base._assinar_targets([target], cert_path, senha)
        envio_id, mes_id = _criar_timeline_envio_teste(conn_db, target["cpf"], recibo)
        item_ids = envio_base._criar_items(conn_db, envio_id, signed)
        envio_base._persistir_xmls_assinados(conn_db, conn_w, signed, item_ids)
        resultado = envio_base._processar_lote(
            signed,
            item_ids,
            cert_path=cert_path,
            senha=senha,
            cnpj=cnpj,
            conn_db=conn_db,
            conn_w=conn_w,
        )
        sucesso = int(resultado.get("sucesso") or 0)
        erro = int(resultado.get("erro") or 0)
        envio_base._atualizar_envio(
            conn_db,
            envio_id,
            status="concluido",
            sucesso=sucesso,
            erro=erro,
            resumo_extra={
                "protocolos": [resultado.get("protocolo")] if resultado.get("protocolo") else [],
                "histograma_erros": resultado.get("histograma") or {},
                "rotulo_final": "teste_recibo_agosto_202_deddepen",
                "cpf": target["cpf"],
                "recibo_override": recibo,
            },
        )
        with conn_db.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                """
                SELECT cpf, status, erro_codigo, erro_mensagem,
                       nr_recibo_anterior, nr_recibo_novo
                  FROM timeline_envio_item
                 WHERE timeline_envio_id=%s
                """,
                (envio_id,),
            )
            items = [dict(row) for row in cur.fetchall()]
        out = {
            "ok": True,
            "generated_at": datetime.now().isoformat(timespec="seconds"),
            "envio_id": envio_id,
            "timeline_mes_id": mes_id,
            "cpf": target["cpf"],
            "recibo_override": recibo,
            "source_recibo": target.get("source_recibo"),
            "protocolo": resultado.get("protocolo"),
            "sucesso": sucesso,
            "erro": erro,
            "histograma": resultado.get("histograma") or {},
            "items": items,
        }
        result_path = TEST_DIR / f"resultado_teste_recibo_{target['cpf']}.json"
        result_path.write_text(json.dumps(out, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
        print(json.dumps(out, ensure_ascii=False, indent=2, default=str))
        print(f"resultado_json={result_path}")
        return out
    except Exception:
        conn_db.rollback()
        conn_w.rollback()
        raise
    finally:
        conn_db.close()
        conn_w.close()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cpf", default="02254091786")
    parser.add_argument("--recibo", required=True)
    parser.add_argument("--cert", default=str(DEFAULT_CERT))
    parser.add_argument("--cnpj", default="09445502000109")
    parser.add_argument("--senha", default=os.getenv("ESOCIAL_CERT_SENHA") or "")
    args = parser.parse_args(argv)
    senha = args.senha or getpass.getpass("Senha do certificado A1 SOLUCOES: ")
    if not senha:
        raise SystemExit("Senha nao informada")
    rodar(cpf=args.cpf, recibo=args.recibo, cert_path=Path(args.cert), senha=senha, cnpj=args.cnpj)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())