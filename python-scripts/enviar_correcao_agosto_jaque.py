from __future__ import annotations

import argparse
import getpass
import json
import os
import sys
import time
from pathlib import Path
from typing import Any

import psycopg2.extras


BACKEND_V2 = Path(r"C:\Users\xandao\Documents\GitHub\Easy-eSocial-v2\backend")
if str(BACKEND_V2) not in sys.path:
    sys.path.insert(0, str(BACKEND_V2))

from app import db, esocial_client, tenant  # noqa: E402
from app.xml_signer import S1010XMLSigner  # noqa: E402


EMPRESA_ID = 2
PER_APUR = "2025-08"
ROOT = Path(r"C:\Users\xandao\Documents\GitHub\Easy-Social")
OUT_DIR = ROOT / "relatorio_ana" / "CORRECAO_AGOSTO_JAQUE"
PREFLIGHT = OUT_DIR / "preflight_correcao_agosto_jaque.json"
DEFAULT_CERT = ROOT / "_certificados_locais" / "SOLUCOES_SERVICOS_TERCEIRIZADOS_09445502000109.pfx"
CFG_GRUPO = 3
CFG_LOTE_MAX = 40
POLL_TENTATIVAS = 12
POLL_INTERVALO_S = 8


def _load_targets() -> list[dict[str, Any]]:
    if not PREFLIGHT.exists():
        raise RuntimeError(f"preflight nao encontrado: {PREFLIGHT}")
    summary = json.loads(PREFLIGHT.read_text(encoding="utf-8"))
    targets = [item for item in summary.get("generated", []) if item.get("generated")]
    if len(targets) != 99:
        raise RuntimeError(f"esperado 99 XMLs gerados; encontrado {len(targets)}")
    for item in targets:
        xml_path = Path(item.get("xml") or "")
        if not xml_path.exists():
            raise RuntimeError(f"XML nao encontrado para CPF {item.get('cpf')}: {xml_path}")
        if not item.get("evento_id") or not item.get("nr_recibo"):
            raise RuntimeError(f"preflight sem evento_id/nr_recibo para CPF {item.get('cpf')}")
    return sorted(targets, key=lambda item: item["cpf"])


def _verificar_estado_atual(conn, targets: list[dict[str, Any]]) -> None:
    internal_empresa_id = tenant.internal_empresa_id(EMPRESA_ID)
    cpfs = [item["cpf"] for item in targets]
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(
            """
            SELECT DISTINCT ON (it.cpf)
                   it.cpf, it.status, it.erro_codigo, it.erro_mensagem,
                   it.criado_em, it.id AS item_id, te.id AS envio_id
              FROM timeline_envio_item it
              JOIN timeline_envio te ON te.id=it.timeline_envio_id
              JOIN timeline_mes tm ON tm.id=te.timeline_mes_id
             WHERE tm.empresa_id=%s
               AND tm.per_apur=%s
               AND it.tipo_evento='S-1210'
               AND it.cpf = ANY(%s)
             ORDER BY it.cpf, it.criado_em DESC NULLS LAST, it.id DESC
            """,
            (internal_empresa_id, PER_APUR, cpfs),
        )
        latest = {row["cpf"]: dict(row) for row in cur.fetchall()}
    ja_sucesso = [cpf for cpf, row in latest.items() if row.get("status") == "sucesso"]
    if ja_sucesso:
        raise RuntimeError(
            "Abortado: ha CPFs do alvo cujo ultimo status ja e sucesso: "
            + ", ".join(ja_sucesso[:20])
        )


def _assinar_targets(targets: list[dict[str, Any]], cert_path: Path, senha: str) -> list[dict[str, Any]]:
    pfx_data = cert_path.read_bytes()
    signed: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    for item in targets:
        unsigned_xml = Path(item["xml"]).read_bytes()
        xml_assinado = S1010XMLSigner.assinar(unsigned_xml, pfx_data, senha)
        id_evento = esocial_client._extrair_id(xml_assinado)
        if not id_evento:
            raise RuntimeError(f"Id nao encontrado apos assinatura para CPF {item['cpf']}")
        if id_evento in seen_ids:
            raise RuntimeError(f"Id duplicado apos assinatura: {id_evento}")
        seen_ids.add(id_evento)
        signed.append({**item, "xml_assinado": xml_assinado, "id_evento_assinado": id_evento})
    return signed


def _criar_timeline_envio(conn, total: int) -> tuple[int, int]:
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
                            (%s, %s, 'envio_massa', 'em_andamento',
               now(), %s, 0, 0, %s)
            RETURNING id
            """,
            (
                mes_id,
                sequencia,
                total,
                psycopg2.extras.Json(
                    {
                        "rotulo": "correcao_agosto_jaque_plano_pensao",
                        "empresa_id_externo": EMPRESA_ID,
                        "per_apur": PER_APUR,
                        "ambiente": "producao",
                        "origem": str(PREFLIGHT),
                        "total_xmls_locais": total,
                    }
                ),
            ),
        )
        envio_id = int(cur.fetchone()["id"])
    conn.commit()
    return envio_id, mes_id


def _criar_items(conn, envio_id: int, signed: list[dict[str, Any]]) -> dict[str, int]:
    item_ids: dict[str, int] = {}
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        for item in signed:
            cur.execute(
                """
                INSERT INTO timeline_envio_item
                  (timeline_envio_id, cpf, tipo_evento, status,
                   versao_anterior_id, nr_recibo_anterior, xml_enviado_oid)
                VALUES (%s, %s, 'S-1210', 'pendente', %s, %s, NULL)
                RETURNING id
                """,
                (envio_id, item["cpf"], item["evento_id"], item["nr_recibo"]),
            )
            item_ids[item["cpf"]] = int(cur.fetchone()["id"])
    conn.commit()
    return item_ids


def _gravar_xml_enviado(conn_w, xml_bytes: bytes) -> int:
    lo = conn_w.lobject(0, mode="wb")
    oid = lo.oid
    try:
        lo.write(xml_bytes)
    finally:
        lo.close()
    return int(oid)


def _gravar_xml_retorno(conn_w, xml_str: str) -> int:
    lo = conn_w.lobject(0, mode="wb")
    oid = lo.oid
    try:
        lo.write(xml_str.encode("utf-8"))
    finally:
        lo.close()
    return int(oid)


def _atualizar_item(
    conn,
    item_id: int,
    *,
    status: str,
    erro_codigo: str | None = None,
    erro_mensagem: str | None = None,
    nr_recibo_novo: str | None = None,
    xml_retorno_oid: int | None = None,
    duracao_ms: int | None = None,
) -> None:
    with conn.cursor() as cur:
        cur.execute(
            """
            UPDATE timeline_envio_item
               SET status=%s,
                   erro_codigo=%s,
                   erro_mensagem=%s,
                   nr_recibo_novo=%s,
                   xml_retorno_oid=%s,
                   duracao_ms=%s
             WHERE id=%s
            """,
            (status, erro_codigo, erro_mensagem, nr_recibo_novo, xml_retorno_oid, duracao_ms, item_id),
        )
    conn.commit()


def _set_xml_enviado_oid(conn, item_id: int, oid: int) -> None:
    with conn.cursor() as cur:
        cur.execute("UPDATE timeline_envio_item SET xml_enviado_oid=%s WHERE id=%s", (oid, item_id))
    conn.commit()


def _atualizar_envio(conn, envio_id: int, *, status: str, sucesso: int, erro: int, resumo_extra: dict) -> None:
    with conn.cursor() as cur:
        cur.execute(
            """
            UPDATE timeline_envio
               SET status=%s,
                   finalizado_em=now(),
                   total_sucesso=%s,
                   total_erro=%s,
                   resumo = resumo || %s::jsonb
             WHERE id=%s
            """,
            (status, sucesso, erro, psycopg2.extras.Json(resumo_extra), envio_id),
        )
    conn.commit()


def _persistir_xmls_assinados(conn_db, conn_w, signed: list[dict[str, Any]], item_ids: dict[str, int]) -> None:
    for item in signed:
        oid = _gravar_xml_enviado(conn_w, item["xml_assinado"])
        conn_w.commit()
        _set_xml_enviado_oid(conn_db, item_ids[item["cpf"]], oid)


def _processar_lote(
    lote: list[dict[str, Any]],
    item_ids: dict[str, int],
    *,
    cert_path: Path,
    senha: str,
    cnpj: str,
    conn_db,
    conn_w,
) -> dict[str, Any]:
    eventos = [
        esocial_client.EventoLote(xml_bytes=item["xml_assinado"], id_evento=item["id_evento_assinado"])
        for item in lote
    ]
    started = time.time()
    print(f"  -> POST EnviarLoteEventos producao ({len(eventos)} eventos)")
    envio = esocial_client.enviar_lote(
        eventos,
        cert_path=str(cert_path),
        cert_password=senha,
        cnpj_empregador=cnpj,
        ambiente="producao",
        grupo=CFG_GRUPO,
    )
    envio_ms = int((time.time() - started) * 1000)
    print(
        "     retorno envio "
        f"http={envio.get('http_status')} cd={envio.get('codigo_resposta')} "
        f"desc={envio.get('descricao')} protocolo={envio.get('protocolo')}"
    )

    if not envio.get("sucesso"):
        codigo = envio.get("codigo_resposta") or "ERRO_LOTE"
        mensagem = envio.get("descricao") or envio.get("erro") or "lote rejeitado pelo eSocial"
        ocorrencias = envio.get("ocorrencias") or []
        if ocorrencias:
            mensagem += " | " + "; ".join(f"{oc['codigo']}: {oc['descricao']}" for oc in ocorrencias[:5])
        retorno_oid = None
        if envio.get("response_xml"):
            retorno_oid = _gravar_xml_retorno(conn_w, envio["response_xml"])
            conn_w.commit()
        for item in lote:
            _atualizar_item(
                conn_db,
                item_ids[item["cpf"]],
                status="erro_esocial" if envio.get("http_status") == 200 else "falha_rede",
                erro_codigo=str(codigo)[:32],
                erro_mensagem=str(mensagem)[:1000],
                xml_retorno_oid=retorno_oid,
                duracao_ms=envio_ms // max(len(lote), 1),
            )
        return {"sucesso": 0, "erro": len(lote), "protocolo": None, "histograma": {str(codigo): len(lote)}}

    protocolo = envio["protocolo"]
    consulta = None
    print(f"     consultando processamento protocolo={protocolo}")
    for tentativa in range(POLL_TENTATIVAS):
        time.sleep(POLL_INTERVALO_S)
        consulta = esocial_client.consultar_lote(
            protocolo,
            cert_path=str(cert_path),
            cert_password=senha,
            ambiente="producao",
        )
        codigo_lote = consulta.get("codigo_lote")
        print(
            f"       [{tentativa + 1}/{POLL_TENTATIVAS}] "
            f"cd_lote={codigo_lote} eventos={len(consulta.get('eventos') or [])}"
        )
        if codigo_lote == "201":
            break
        if codigo_lote and codigo_lote != "101":
            break

    eventos_retorno = (consulta or {}).get("eventos") or []
    retorno_por_id = {ev["id_evento"]: ev for ev in eventos_retorno if ev.get("id_evento")}
    sucesso = 0
    erro = 0
    histograma: dict[str, int] = {}

    for item in lote:
        retorno = retorno_por_id.get(item["id_evento_assinado"])
        item_id = item_ids[item["cpf"]]
        duracao = (envio_ms + POLL_INTERVALO_S * 1000) // max(len(lote), 1)
        if not retorno:
            _atualizar_item(
                conn_db,
                item_id,
                status="pendente",
                erro_codigo="SEM_RETORNO",
                erro_mensagem="protocolo nao trouxe retornoEvento para este Id",
                duracao_ms=duracao,
            )
            erro += 1
            histograma["SEM_RETORNO"] = histograma.get("SEM_RETORNO", 0) + 1
            continue

        retorno_oid = None
        if retorno.get("xml_retorno"):
            retorno_oid = _gravar_xml_retorno(conn_w, retorno["xml_retorno"])
            conn_w.commit()

        codigo = str(retorno.get("codigo") or "")
        if codigo in {"201", "202"}:
            erro_codigo = None
            erro_mensagem = None
            if codigo == "202":
                partes = [f"{codigo}: {retorno.get('descricao')}"]
                for oc in retorno.get("ocorrencias") or []:
                    partes.append(f"{oc.get('codigo')}: {oc.get('descricao')}")
                erro_codigo = codigo[:32]
                erro_mensagem = " | ".join(partes)[:1000]
            _atualizar_item(
                conn_db,
                item_id,
                status="sucesso",
                erro_codigo=erro_codigo,
                erro_mensagem=erro_mensagem,
                nr_recibo_novo=retorno.get("nr_recibo"),
                xml_retorno_oid=retorno_oid,
                duracao_ms=duracao,
            )
            sucesso += 1
        else:
            partes = [f"{codigo}: {retorno.get('descricao')}"]
            for oc in retorno.get("ocorrencias") or []:
                partes.append(f"{oc.get('codigo')}: {oc.get('descricao')}")
            _atualizar_item(
                conn_db,
                item_id,
                status="erro_esocial",
                erro_codigo=codigo[:32],
                erro_mensagem=" | ".join(partes)[:1000],
                xml_retorno_oid=retorno_oid,
                duracao_ms=duracao,
            )
            erro += 1
            histograma[codigo or "SEM_CODIGO"] = histograma.get(codigo or "SEM_CODIGO", 0) + 1

    return {"sucesso": sucesso, "erro": erro, "protocolo": protocolo, "histograma": histograma}


def rodar(*, cert_path: Path, senha: str, cnpj: str) -> dict[str, Any]:
    targets = _load_targets()
    if not cert_path.exists():
        raise RuntimeError(f"certificado nao encontrado: {cert_path}")
    print(f"=> alvos: {len(targets)} XMLs S-1210 retificacao {PER_APUR}")
    print(f"=> certificado: {cert_path}")
    conn_db = db.connect(empresa_id=EMPRESA_ID)
    conn_w = db.connect(empresa_id=EMPRESA_ID)
    try:
        _verificar_estado_atual(conn_db, targets)
        print("=> estado atual conferido: nenhum alvo esta com ultimo status sucesso")
        signed = _assinar_targets(targets, cert_path, senha)
        print(f"=> assinados localmente: {len(signed)} XMLs")
        envio_id, mes_id = _criar_timeline_envio(conn_db, len(signed))
        print(f"=> timeline_envio criado id={envio_id} timeline_mes={mes_id}")
        item_ids = _criar_items(conn_db, envio_id, signed)
        print(f"=> timeline_envio_item criados: {len(item_ids)}")
        _persistir_xmls_assinados(conn_db, conn_w, signed, item_ids)
        print("=> XMLs assinados gravados e vinculados aos items")

        sucesso_total = 0
        erro_total = 0
        protocolos: list[str] = []
        histograma: dict[str, int] = {}

        for idx in range(0, len(signed), CFG_LOTE_MAX):
            lote = signed[idx:idx + CFG_LOTE_MAX]
            print(f"\n>> lote {idx // CFG_LOTE_MAX + 1} ({len(lote)} eventos)")
            resultado = _processar_lote(
                lote,
                item_ids,
                cert_path=cert_path,
                senha=senha,
                cnpj=cnpj,
                conn_db=conn_db,
                conn_w=conn_w,
            )
            sucesso_total += int(resultado["sucesso"])
            erro_total += int(resultado["erro"])
            if resultado.get("protocolo"):
                protocolos.append(str(resultado["protocolo"]))
            for codigo, total in resultado.get("histograma", {}).items():
                histograma[codigo] = histograma.get(codigo, 0) + int(total)

        status = "concluido"
        _atualizar_envio(
            conn_db,
            envio_id,
            status=status,
            sucesso=sucesso_total,
            erro=erro_total,
            resumo_extra={
                "protocolos": protocolos,
                "histograma_erros": histograma,
                "plan_saude": 95,
                "pensao": 4,
            },
        )
        print("\n=== RESUMO ENVIO CORRECAO AGOSTO JAQUE ===")
        print(f"envio_id  : {envio_id}")
        print(f"protocolos: {protocolos}")
        print(f"sucesso   : {sucesso_total}")
        print(f"erro      : {erro_total}")
        print(f"histograma: {histograma}")
        return {
            "ok": True,
            "envio_id": envio_id,
            "sucesso": sucesso_total,
            "erro": erro_total,
            "protocolos": protocolos,
            "histograma": histograma,
        }
    except Exception:
        conn_db.rollback()
        conn_w.rollback()
        raise
    finally:
        conn_db.close()
        conn_w.close()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cert", default=str(DEFAULT_CERT))
    parser.add_argument("--cnpj", default="09445502000109")
    parser.add_argument("--senha", default=os.getenv("ESOCIAL_CERT_SENHA") or "")
    args = parser.parse_args(argv)

    senha = args.senha
    if not senha:
        senha = getpass.getpass("Senha do certificado A1 SOLUCOES: ")
    if not senha:
        raise SystemExit("Senha nao informada")
    rodar(cert_path=Path(args.cert), senha=senha, cnpj=args.cnpj)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())