from __future__ import annotations

import json
import argparse
import math
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import psycopg2.extras

V2_BACKEND = Path(r"C:\Users\xandao\Documents\GitHub\Easy-eSocial-v2\backend")
sys.path.insert(0, str(V2_BACKEND))

from app import db, esocial_client, tenant  # noqa: E402
from app.envio_paralelo_v2 import rodar_paralelo  # noqa: E402
from app.envio_s1298 import _load_certificado, _salvar_reabertura  # noqa: E402
from app.xml_s1298 import S1298XMLGenerator  # noqa: E402
from app.xml_signer import S1010XMLSigner  # noqa: E402

EMPRESA_ID = 3
PER_APUR = "2025-12"
CNPJ_ESPERADO = "10874523000110"
AMBIENTE = "producao"
GRUPO = 3
META_TOTAL = 100
CHUNK_SIZE = 50
WORKERS = 1
BATCH_SIZE = 50
MAX_ERROR_RATE = 0.20
S1298_POLL_ATTEMPTS = 60
S1298_POLL_WAIT_S = 15

REPORT_DIR = Path("relatorio_ana")
REPORT_DIR.mkdir(exist_ok=True)
REPORT_JSON = REPORT_DIR / "OBJETIVA_DEZEMBRO_2025_CICLO100_RESULTADO.json"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Envio controlado S-1210 Objetiva dezembro/2025")
    parser.add_argument("--meta-total", type=int, default=META_TOTAL)
    parser.add_argument("--chunk-size", type=int, default=CHUNK_SIZE)
    parser.add_argument("--workers", type=int, default=WORKERS)
    parser.add_argument("--batch-size", type=int, default=BATCH_SIZE)
    parser.add_argument("--max-error-rate", type=float, default=MAX_ERROR_RATE)
    parser.add_argument("--report-json", default=str(REPORT_JSON))
    parser.add_argument("--rotulo", default="ciclo_100_concluido")
    return parser.parse_args(argv)


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def redact_xml_retorno(value):
    if isinstance(value, dict):
        return {
            key: ("[omitido_no_relatorio]" if key == "xml_retorno" and isinstance(item, str) else redact_xml_retorno(item))
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [redact_xml_retorno(item) for item in value]
    return value


def clean_cnpj(value: str | None) -> str:
    return "".join(ch for ch in str(value or "") if ch.isdigit())


def get_fechamento_status() -> dict | None:
    internal = tenant.internal_empresa_id(EMPRESA_ID)
    conn = db.connect(empresa_id=EMPRESA_ID)
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                """
                SELECT empresa_id, per_apur, fechado, protocolo, nr_recibo, origem, confirmado_em
                  FROM s1299_fechamento_status
                 WHERE empresa_id=%s AND per_apur=%s
                """,
                (internal, PER_APUR),
            )
            row = cur.fetchone()
            return dict(row) if row else None
    finally:
        conn.close()


def is_open_confirmed(status: dict | None) -> bool:
    return bool(status and status.get("fechado") is False and status.get("nr_recibo"))


def send_and_confirm_s1298(cert: dict) -> dict:
    status_before = get_fechamento_status()
    if is_open_confirmed(status_before):
        return {"skipped": True, "reason": "already_open_confirmed", "status": status_before}

    cnpj = clean_cnpj(cert["cnpj"])
    cnpj_raiz = cnpj[:8]
    with open(cert["cert_path"], "rb") as fh:
        pfx_data = fh.read()

    xml_bytes = S1298XMLGenerator.gerar(
        empregador={"tpInsc": 1, "nrInsc": cnpj_raiz},
        per_apur=PER_APUR,
        ind_apuracao="1",
        seq=1,
        tp_amb="1",
    )
    xml_assinado = S1010XMLSigner.assinar(xml_bytes, pfx_data, cert["senha"])
    id_evento = esocial_client._extrair_id(xml_assinado)
    evento = esocial_client.EventoLote(xml_bytes=xml_assinado, id_evento=id_evento)

    print(f"[S1298] enviando reabertura {PER_APUR} id={id_evento}", flush=True)
    envio = esocial_client.enviar_lote(
        [evento],
        cert_path=cert["cert_path"],
        cert_password=cert["senha"],
        cnpj_empregador=cnpj,
        ambiente=AMBIENTE,
        grupo=GRUPO,
    )
    print(
        f"[S1298] POST cd={envio.get('codigo_resposta')} desc={envio.get('descricao')} proto={envio.get('protocolo')}",
        flush=True,
    )
    if not envio.get("sucesso"):
        return {"skipped": False, "ok": False, "stage": "post_s1298", "envio": envio}

    protocolo = envio.get("protocolo")
    consulta_final = None
    evento_final = None
    for attempt in range(1, S1298_POLL_ATTEMPTS + 1):
        time.sleep(S1298_POLL_WAIT_S)
        consulta = esocial_client.consultar_lote(
            protocolo,
            cert_path=cert["cert_path"],
            cert_password=cert["senha"],
            ambiente=AMBIENTE,
        )
        consulta_final = consulta
        eventos = consulta.get("eventos") or []
        for event_return in eventos:
            if not id_evento or event_return.get("id_evento") == id_evento:
                evento_final = event_return
                break
        cd_lote = consulta.get("codigo_lote")
        cd_evento = (evento_final or {}).get("codigo")
        recibo = (evento_final or {}).get("nr_recibo")
        print(
            f"[S1298] poll {attempt}/{S1298_POLL_ATTEMPTS} lote={cd_lote} eventos={len(eventos)} evento={cd_evento} recibo={'sim' if recibo else 'nao'}",
            flush=True,
        )
        if evento_final and cd_evento in {"201", "202"} and recibo:
            salvo = _salvar_reabertura(
                empresa_id=EMPRESA_ID,
                per_apur=PER_APUR,
                id_evento=id_evento,
                xml_assinado=xml_assinado,
                protocolo=protocolo,
                envio=envio,
                consulta=consulta,
            )
            return {
                "skipped": False,
                "ok": True,
                "id_evento": id_evento,
                "protocolo": protocolo,
                "attempts": attempt,
                "evento": evento_final,
                "salvo": salvo,
                "status_after": get_fechamento_status(),
            }
        if evento_final and cd_evento and cd_evento not in {"101", "104", "201", "202"}:
            break

    return {
        "skipped": False,
        "ok": False,
        "stage": "confirm_s1298",
        "id_evento": id_evento,
        "protocolo": protocolo,
        "consulta_final": consulta_final,
        "evento_final": evento_final,
        "status_after": get_fechamento_status(),
    }


def envio_status(envio_id: int) -> dict:
    conn = db.connect(empresa_id=EMPRESA_ID)
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                """
                SELECT status, COUNT(*) AS n
                  FROM timeline_envio_item
                 WHERE timeline_envio_id=%s
                 GROUP BY status
                 ORDER BY n DESC
                """,
                (envio_id,),
            )
            by_status = {row["status"]: int(row["n"]) for row in cur.fetchall()}
            cur.execute(
                """
                SELECT COALESCE(erro_codigo, '(sem_codigo)') AS erro_codigo, COUNT(*) AS n
                  FROM timeline_envio_item
                 WHERE timeline_envio_id=%s AND status <> 'sucesso'
                 GROUP BY erro_codigo
                 ORDER BY n DESC
                """,
                (envio_id,),
            )
            by_error = {row["erro_codigo"]: int(row["n"]) for row in cur.fetchall()}
            cur.execute(
                """
                SELECT erro_codigo, erro_mensagem, COUNT(*) AS n
                  FROM timeline_envio_item
                 WHERE timeline_envio_id=%s AND status <> 'sucesso'
                 GROUP BY erro_codigo, erro_mensagem
                 ORDER BY n DESC
                 LIMIT 10
                """,
                (envio_id,),
            )
            samples = [dict(row) for row in cur.fetchall()]
            return {"by_status": by_status, "by_error": by_error, "error_samples": samples}
    finally:
        conn.close()


def run_chunk(cert: dict, chunk_index: int, chunk_limit: int) -> dict:
    print(f"[S1210] chunk {chunk_index}: enviando ate {chunk_limit} CPFs", flush=True)
    started = time.time()
    result = rodar_paralelo(
        empresa_id=EMPRESA_ID,
        per_apur=PER_APUR,
        limite=chunk_limit,
        cert_path=cert["cert_path"],
        cert_password=cert["senha"],
        cnpj=clean_cnpj(cert["cnpj"]),
        ambiente=AMBIENTE,
        pular_ja_tentados=True,
        workers=WORKERS,
        batch_size=BATCH_SIZE,
        progress_every=50,
    )
    elapsed = time.time() - started
    envio_id = result.get("envio_id")
    status = envio_status(int(envio_id)) if envio_id else {}
    tentados = int(result.get("sucesso") or 0) + int(result.get("erro") or 0) + int(result.get("pendente_consulta") or 0)
    non_success = int(result.get("erro") or 0) + int(result.get("pendente_consulta") or 0)
    rate = (non_success / tentados) if tentados else 1.0
    return {
        "chunk_index": chunk_index,
        "started_at": now_iso(),
        "elapsed_s": elapsed,
        "result": result,
        "status": status,
        "tentados": tentados,
        "non_success": non_success,
        "error_rate": rate,
    }


def main(argv: list[str] | None = None) -> int:
    global META_TOTAL, CHUNK_SIZE, WORKERS, BATCH_SIZE, MAX_ERROR_RATE, REPORT_JSON
    args = parse_args(argv)
    META_TOTAL = args.meta_total
    CHUNK_SIZE = args.chunk_size
    WORKERS = args.workers
    BATCH_SIZE = args.batch_size
    MAX_ERROR_RATE = args.max_error_rate
    REPORT_JSON = Path(args.report_json)
    REPORT_JSON.parent.mkdir(parents=True, exist_ok=True)

    overall_started = time.time()
    report: dict = {
        "empresa_id": EMPRESA_ID,
        "per_apur": PER_APUR,
        "ambiente": AMBIENTE,
        "meta_total": META_TOTAL,
        "chunk_size": CHUNK_SIZE,
        "workers": WORKERS,
        "batch_size": BATCH_SIZE,
        "max_error_rate": MAX_ERROR_RATE,
        "started_at": now_iso(),
        "chunks": [],
        "stopped": False,
        "stop_reason": None,
    }

    cert = _load_certificado(EMPRESA_ID, None)
    cert_cnpj = clean_cnpj(cert["cnpj"])
    report["certificado"] = {"id": cert["id"], "cnpj": cert_cnpj}
    if cert_cnpj != CNPJ_ESPERADO:
        report["stopped"] = True
        report["stop_reason"] = f"certificado_cnpj_inesperado:{cert_cnpj}"
        print(json.dumps(report, ensure_ascii=False, default=str, indent=2), flush=True)
        REPORT_JSON.write_text(json.dumps(report, ensure_ascii=False, default=str, indent=2), encoding="utf-8")
        return 2

    reabertura = send_and_confirm_s1298(cert)
    report["s1298"] = redact_xml_retorno(reabertura)
    if not (reabertura.get("skipped") or reabertura.get("ok")):
        report["stopped"] = True
        report["stop_reason"] = "s1298_nao_confirmado_com_recibo"
        report["finished_at"] = now_iso()
        report["elapsed_s"] = time.time() - overall_started
        REPORT_JSON.write_text(json.dumps(report, ensure_ascii=False, default=str, indent=2), encoding="utf-8")
        print(json.dumps(report, ensure_ascii=False, default=str, indent=2), flush=True)
        return 3

    cumulative_tentados = 0
    cumulative_non_success = 0
    total_chunks = math.ceil(META_TOTAL / CHUNK_SIZE) if META_TOTAL > 0 else 0
    for chunk_index in range(1, total_chunks + 1):
        remaining_target = META_TOTAL - cumulative_tentados
        chunk_limit = min(CHUNK_SIZE, remaining_target)
        chunk = run_chunk(cert, chunk_index, chunk_limit)
        report["chunks"].append(chunk)
        if not chunk.get("result", {}).get("ok"):
            report["stopped"] = True
            report["stop_reason"] = "nenhum_evento_selecionavel_ou_falha_chunk"
            break
        cumulative_tentados += int(chunk["tentados"])
        cumulative_non_success += int(chunk["non_success"])
        cumulative_rate = (cumulative_non_success / cumulative_tentados) if cumulative_tentados else 1.0
        report["cumulative"] = {
            "tentados": cumulative_tentados,
            "non_success": cumulative_non_success,
            "error_rate": cumulative_rate,
            "success": cumulative_tentados - cumulative_non_success,
        }
        REPORT_JSON.write_text(json.dumps(report, ensure_ascii=False, default=str, indent=2), encoding="utf-8")
        print(
            f"[GUARD] apos {cumulative_tentados} CPFs: nao_sucesso={cumulative_non_success} taxa={cumulative_rate:.2%}",
            flush=True,
        )
        if cumulative_rate > MAX_ERROR_RATE:
            report["stopped"] = True
            report["stop_reason"] = f"taxa_erro_acima_de_20pct_apos_{cumulative_tentados}"
            break

    report["finished_at"] = now_iso()
    report["elapsed_s"] = time.time() - overall_started
    if not report.get("stopped"):
        report["stop_reason"] = args.rotulo
    REPORT_JSON.write_text(json.dumps(report, ensure_ascii=False, default=str, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, default=str, indent=2), flush=True)
    return 0 if not report.get("stopped") else 4


if __name__ == "__main__":
    raise SystemExit(main())
