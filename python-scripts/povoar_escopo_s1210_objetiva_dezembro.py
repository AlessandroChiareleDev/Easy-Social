from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import time
import zipfile
from collections import Counter, defaultdict
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

import psycopg2
import psycopg2.extras
from psycopg2.extras import execute_values


V2_BACKEND = Path(r"C:\Users\xandao\Documents\GitHub\Easy-eSocial-v2\backend")
if str(V2_BACKEND) not in sys.path:
    sys.path.insert(0, str(V2_BACKEND))

from app import db, tenant  # noqa: E402
from app.esocial_parser import parse_xml_bytes  # noqa: E402
from app.xml_extractor import extrair_s1210, extrair_s5002  # noqa: E402


DEFAULT_ZIP = Path(r"C:\Users\xandao\Downloads\mes a mes Objetiva zip\01-01 ate 31-01  2026  objetiva.zip")
EMPRESA_ID = 3
TARGET_MONTH = "2025-12"
EXPECTED_S1210 = 2431
EXPECTED_CPFS = 1284
BATCH_SIZE = 100


INSERT_SQL = """
    INSERT INTO explorador_eventos
      (importacao_id, tipo_evento, cpf, per_apur,
       nr_recibo, id_evento, dt_processamento,
       cd_resposta, arquivo_origem, dados_json,
       zip_id, xml_entry_name, referenciado_recibo,
       xml_bytes, xml_size_bytes, xml_sha256)
    VALUES %s
    ON CONFLICT (id_evento) WHERE id_evento IS NOT NULL DO UPDATE
      SET dados_json = CASE
            WHEN explorador_eventos.dados_json IS NULL
              OR NOT (
                explorador_eventos.dados_json ? 'pagamentos'
                OR explorador_eventos.dados_json ? 'infoIRCR'
                OR explorador_eventos.dados_json ? 'infoIR'
                OR explorador_eventos.dados_json ? 'totApurMen_CRMen'
              )
            THEN EXCLUDED.dados_json
            ELSE explorador_eventos.dados_json
          END,
          zip_id = COALESCE(explorador_eventos.zip_id, EXCLUDED.zip_id),
          xml_entry_name = COALESCE(explorador_eventos.xml_entry_name, EXCLUDED.xml_entry_name),
          arquivo_origem = COALESCE(explorador_eventos.arquivo_origem, EXCLUDED.arquivo_origem),
          referenciado_recibo = COALESCE(explorador_eventos.referenciado_recibo, EXCLUDED.referenciado_recibo),
          xml_size_bytes = COALESCE(explorador_eventos.xml_size_bytes, EXCLUDED.xml_size_bytes),
          xml_sha256 = COALESCE(explorador_eventos.xml_sha256, EXCLUDED.xml_sha256)
      WHERE explorador_eventos.tipo_evento IN ('S-1210','S-5002')
        AND (
          explorador_eventos.dados_json IS NULL
          OR NOT (
            explorador_eventos.dados_json ? 'pagamentos'
            OR explorador_eventos.dados_json ? 'infoIRCR'
            OR explorador_eventos.dados_json ? 'infoIR'
            OR explorador_eventos.dados_json ? 'totApurMen_CRMen'
          )
          OR explorador_eventos.zip_id IS NULL
          OR explorador_eventos.xml_entry_name IS NULL
          OR explorador_eventos.arquivo_origem IS NULL
          OR explorador_eventos.xml_size_bytes IS NULL
          OR explorador_eventos.xml_sha256 IS NULL
        )
    RETURNING (xmax = 0) AS inserted_new
"""


RE_XML_TYPE = re.compile(r"(S-\d{4})\.xml$", re.I)
RE_PER_APUR = re.compile(rb"<perApur>([^<]+)</perApur>")
RE_CPF_BENEF = re.compile(rb"<cpfBenef>([^<]+)</cpfBenef>")
RE_CPF_TRAB = re.compile(rb"<cpfTrab>([^<]+)</cpfTrab>")
RE_DH_PROCESSAMENTO = re.compile(rb"<dhProcessamento>([^<]+)</dhProcessamento>|<dtProcessamento>([^<]+)</dtProcessamento>")
RE_ID_TS = re.compile(r"ID\d{15}(\d{14})\d{5}\.S-1210\.xml$", re.I)


def json_default(value: Any) -> Any:
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, memoryview):
        return f"<memoryview {len(value)} bytes>"
    if isinstance(value, bytes):
        return f"<bytes {len(value)} bytes>"
    return str(value)


def first_regex(pattern: re.Pattern[bytes], data: bytes) -> str | None:
    match = pattern.search(data)
    if not match:
        return None
    value = next((group for group in match.groups() if group), None)
    return value.decode("utf-8", "ignore") if value else None


def tipo_por_nome(filename: str) -> str | None:
    base = filename.replace("\\", "/").split("/")[-1].upper()
    match = RE_XML_TYPE.search(base)
    return match.group(1) if match else None


def id_timestamp(filename: str) -> str:
    base = filename.replace("\\", "/").split("/")[-1]
    match = RE_ID_TS.search(base)
    return match.group(1) if match else ""


def zip_dates(path: Path) -> tuple[date, date]:
    match = re.search(r"(\d{2})-(\d{2}).*?(\d{2})-(\d{2}).*?(20\d{2})", path.name)
    if match:
        start_day, start_month, end_day, end_month, year = match.groups()
        return date(int(year), int(start_month), int(start_day)), date(int(year), int(end_month), int(end_day))
    today = date.today()
    return today, today


def sha256_file(path: Path) -> tuple[str, int]:
    digest = hashlib.sha256()
    total = 0
    with path.open("rb") as file:
        while True:
            chunk = file.read(8 * 1024 * 1024)
            if not chunk:
                break
            digest.update(chunk)
            total += len(chunk)
    return digest.hexdigest(), total


def local_preflight(path: Path, target_month: str) -> dict[str, Any]:
    by_cpf: dict[str, list[dict[str, Any]]] = defaultdict(list)
    per_counts: Counter[str] = Counter()
    tipo_counts: Counter[str] = Counter()
    total_xmls = 0
    missing_dt_processamento = 0

    with zipfile.ZipFile(path, "r") as zip_file:
        for info in zip_file.infolist():
            if not info.filename.lower().endswith(".xml"):
                continue
            total_xmls += 1
            tipo = tipo_por_nome(info.filename) or "UNKNOWN"
            tipo_counts[tipo] += 1
            if tipo != "S-1210":
                continue
            data = zip_file.read(info)
            per_apur = first_regex(RE_PER_APUR, data)
            if per_apur:
                per_counts[per_apur] += 1
            if per_apur != target_month:
                continue
            cpf = first_regex(RE_CPF_BENEF, data) or first_regex(RE_CPF_TRAB, data) or "SEM_CPF"
            dt_processamento = first_regex(RE_DH_PROCESSAMENTO, data)
            if not dt_processamento:
                missing_dt_processamento += 1
            by_cpf[cpf].append(
                {
                    "entry": info.filename.replace("\\", "/"),
                    "dt_processamento": dt_processamento,
                    "id_timestamp": id_timestamp(info.filename),
                }
            )

    head_rows = []
    for cpf, rows in by_cpf.items():
        chosen = sorted(
            rows,
            key=lambda row: ((row.get("dt_processamento") or ""), row.get("id_timestamp") or "", row.get("entry") or ""),
            reverse=True,
        )[0]
        head_rows.append({"cpf": cpf, **chosen})

    duplicate_distribution = Counter(len(rows) for rows in by_cpf.values())
    return {
        "zip": str(path),
        "total_xmls": total_xmls,
        "tipo_counts": dict(sorted(tipo_counts.items())),
        "s1210_per_apur": dict(sorted(per_counts.items())),
        "target_month": target_month,
        "target_s1210": sum(len(rows) for rows in by_cpf.values()),
        "target_cpfs": len(by_cpf),
        "duplicate_distribution": dict(sorted(duplicate_distribution.items())),
        "cpfs_com_2_ou_mais": sum(1 for rows in by_cpf.values() if len(rows) >= 2),
        "missing_dt_processamento": missing_dt_processamento,
        "head_count": len(head_rows),
        "head_samples": head_rows[:5],
    }


def validate_preflight(scan: dict[str, Any], expected_s1210: int, expected_cpfs: int) -> list[str]:
    errors: list[str] = []
    if int(scan["target_s1210"]) != expected_s1210:
        errors.append(f"target_s1210 esperado={expected_s1210} encontrado={scan['target_s1210']}")
    if int(scan["target_cpfs"]) != expected_cpfs:
        errors.append(f"target_cpfs esperado={expected_cpfs} encontrado={scan['target_cpfs']}")
    per_counts = scan.get("s1210_per_apur") or {}
    if set(per_counts) != {scan["target_month"]}:
        errors.append(f"S-1210 com per_apur inesperado: {per_counts}")
    if int(scan.get("missing_dt_processamento") or 0) != 0:
        errors.append(f"ha S-1210 sem dh/dtProcessamento: {scan['missing_dt_processamento']}")
    if int(scan.get("head_count") or 0) != expected_cpfs:
        errors.append(f"head_count esperado={expected_cpfs} encontrado={scan['head_count']}")
    return errors


def fetch_all(cur, sql: str, args: tuple[Any, ...] = ()) -> list[dict[str, Any]]:
    cur.execute(sql, args)
    return [dict(row) for row in cur.fetchall()]


def fetch_one(cur, sql: str, args: tuple[Any, ...] = ()) -> dict[str, Any] | None:
    cur.execute(sql, args)
    row = cur.fetchone()
    return dict(row) if row else None


def ensure_columns(conn) -> None:
    with conn.cursor() as cur:
        cur.execute("ALTER TABLE explorador_eventos ADD COLUMN IF NOT EXISTS xml_bytes BYTEA")
        cur.execute("ALTER TABLE empresa_zips_brutos ADD COLUMN IF NOT EXISTS extracao_progresso JSONB")
    conn.commit()


def create_importacao(conn, path: Path) -> int:
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(
            "INSERT INTO explorador_importacoes (pasta, periodo, total_arquivos) VALUES (%s, %s, 0) RETURNING id",
            (path.name, TARGET_MONTH),
        )
        importacao_id = int(cur.fetchone()["id"])
    conn.commit()
    return importacao_id


def upload_zip_if_needed(conn, path: Path, internal_empresa_id: int) -> tuple[int, bool, str, int]:
    sha, size = sha256_file(path)
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(
            """
            SELECT id, nome_arquivo_original, extracao_status
              FROM empresa_zips_brutos
             WHERE empresa_id = %s AND sha256 = %s
             ORDER BY id
             LIMIT 1
            """,
            (internal_empresa_id, sha),
        )
        existing = cur.fetchone()
        if existing:
            print(
                f"UPLOAD_SKIP zip_id={existing['id']} file={path.name} "
                f"existing={existing['nome_arquivo_original']} status={existing['extracao_status']}",
                flush=True,
            )
            return int(existing["id"]), False, sha, size

    d_ini, d_fim = zip_dates(path)
    print(f"UPLOAD_START file={path.name} bytes={size}", flush=True)
    oid = None
    try:
        large_object = conn.lobject(0, "wb")
        oid = large_object.oid
        written = 0
        last = time.time()
        with path.open("rb") as file:
            while True:
                chunk = file.read(4 * 1024 * 1024)
                if not chunk:
                    break
                large_object.write(chunk)
                written += len(chunk)
                if time.time() - last > 10:
                    last = time.time()
                    print(f"UPLOAD_PROGRESS file={path.name} {written}/{size}", flush=True)
        large_object.close()
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                """
                INSERT INTO empresa_zips_brutos
                  (empresa_id, dt_ini, dt_fim, sequencial_esocial,
                   nome_arquivo_original, sha256, tamanho_bytes, conteudo_oid,
                   extracao_status, extracao_progresso)
                VALUES (%s, %s, %s, NULL, %s, %s, %s, %s, 'pendente', %s)
                RETURNING id
                """,
                (
                    internal_empresa_id,
                    d_ini,
                    d_fim,
                    path.name,
                    sha,
                    size,
                    oid,
                    json.dumps({"etapa": "upload concluido", "processados": 0, "total": 0}),
                ),
            )
            zip_id = int(cur.fetchone()["id"])
        conn.commit()
        print(f"UPLOAD_DONE zip_id={zip_id} file={path.name}", flush=True)
        return zip_id, True, sha, size
    except Exception:
        conn.rollback()
        if oid:
            try:
                conn.lobject(oid, "n").unlink()
                conn.commit()
            except Exception:
                conn.rollback()
        raise


def zip_is_ok(conn, zip_id: int) -> bool:
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(
            "SELECT extracao_status, total_xmls, extracao_progresso FROM empresa_zips_brutos WHERE id=%s",
            (zip_id,),
        )
        row = cur.fetchone()
    if not row or row.get("extracao_status") != "ok":
        return False
    progress = row.get("extracao_progresso") or {}
    if isinstance(progress, str):
        try:
            progress = json.loads(progress)
        except json.JSONDecodeError:
            progress = {}
    processados = int(progress.get("processados") or 0)
    total = int(row.get("total_xmls") or 0)
    return total > 0 and (processados == total or processados == 0)


def update_progress(conn, zip_id: int, payload: dict[str, Any]) -> None:
    with conn.cursor() as cur:
        cur.execute(
            "UPDATE empresa_zips_brutos SET extracao_status='extraindo', extracao_erro=NULL, extracao_progresso=%s WHERE id=%s",
            (json.dumps(payload), zip_id),
        )
    conn.commit()


def flush_events(conn, batch: list[tuple]) -> tuple[int, int]:
    if not batch:
        return 0, 0
    with conn.cursor() as cur:
        returned = execute_values(cur, INSERT_SQL, batch, fetch=True, page_size=BATCH_SIZE)
    inserted_new = sum(1 for row in returned if row[0])
    conn.commit()
    return inserted_new, len(batch) - inserted_new


def extract_zip(conn, zip_id: int, path: Path) -> dict[str, Any]:
    importacao_id = create_importacao(conn, path)
    total = ok = duplicados = falhas = 0
    per_counter: Counter[str] = Counter()
    batch: list[tuple] = []
    last = time.time()
    print(f"EXTRACT_START zip_id={zip_id} file={path.name}", flush=True)
    with zipfile.ZipFile(path, "r") as zip_file:
        names = [name for name in zip_file.namelist() if name.lower().endswith(".xml")]
        total_est = len(names)
        update_progress(
            conn,
            zip_id,
            {"etapa": "extraindo", "processados": 0, "total": total_est, "ok": 0, "duplicados": 0, "falhas": 0},
        )
        for name in names:
            total += 1
            try:
                data = zip_file.read(name)
                evt = parse_xml_bytes(data)
                if evt is None:
                    falhas += 1
                    continue
                tipo_nome = tipo_por_nome(name)
                if tipo_nome:
                    evt.tipo_evento = tipo_nome
                if evt.per_apur:
                    per_counter[evt.per_apur] += 1
                dados = {"nome_tecnico": evt.nome_tecnico}
                try:
                    if evt.tipo_evento == "S-1210":
                        parsed = extrair_s1210(data) or {}
                        dados.update(
                            {
                                "pagamentos": parsed.get("info_pgtos") or [],
                                "infoIRCR": (parsed.get("info_ir_complem") or {}).get("infoIRCR") or [],
                                "planSaude": parsed.get("plan_saude"),
                                "indRetif": parsed.get("ind_retif_atual"),
                                "nrReciboAtual": parsed.get("nr_recibo_atual"),
                            }
                        )
                    elif evt.tipo_evento == "S-5002":
                        parsed = extrair_s5002(data) or {}
                        dados.update(
                            {
                                "infoIR": parsed.get("infoIR") or [],
                                "totApurMen_CRMen": parsed.get("totApurMen_CRMen"),
                                "totApurMen_vlrRendTrib": parsed.get("totApurMen_vlrRendTrib"),
                                "totApurMen_vlrPrevOficial": parsed.get("totApurMen_vlrPrevOficial"),
                                "totApurMen_vlrCRMen": parsed.get("totApurMen_vlrCRMen"),
                            }
                        )
                except Exception as enrich_error:  # noqa: BLE001
                    print(f"WARN_ENRICH tipo={evt.tipo_evento} entry={name} error={enrich_error}", flush=True)

                batch.append(
                    (
                        importacao_id,
                        evt.tipo_evento,
                        evt.cpf,
                        evt.per_apur,
                        evt.nr_recibo,
                        evt.id_evento,
                        evt.dt_processamento,
                        evt.cd_resposta,
                        name,
                        json.dumps(dados),
                        zip_id,
                        name,
                        evt.referenciado_recibo,
                        None,
                        len(data),
                        hashlib.sha256(data).hexdigest(),
                    )
                )
                if len(batch) >= BATCH_SIZE:
                    inserted, duplicate = flush_events(conn, batch)
                    ok += inserted
                    duplicados += duplicate
                    batch.clear()
            except Exception as item_error:  # noqa: BLE001
                falhas += 1
                batch.clear()
                try:
                    conn.rollback()
                except Exception:  # noqa: BLE001
                    pass
                print(f"WARN_XML file={path.name} entry={name} error={item_error}", flush=True)
            if time.time() - last > 10:
                last = time.time()
                update_progress(
                    conn,
                    zip_id,
                    {
                        "etapa": "extraindo",
                        "processados": total,
                        "total": total_est,
                        "ok": ok,
                        "duplicados": duplicados,
                        "falhas": falhas,
                    },
                )
                print(f"EXTRACT_PROGRESS zip_id={zip_id} {total}/{total_est} ok={ok} dup={duplicados} falhas={falhas}", flush=True)
        if batch:
            inserted, duplicate = flush_events(conn, batch)
            ok += inserted
            duplicados += duplicate
            batch.clear()

    per_dom = per_counter.most_common(1)[0][0] if per_counter else None
    payload = {"etapa": "ok", "processados": total, "total": total, "ok": ok, "duplicados": duplicados, "falhas": falhas}
    with conn.cursor() as cur:
        cur.execute(
            """
            UPDATE empresa_zips_brutos
               SET extracao_status='ok', extraido_em=now(), total_xmls=%s,
                   perapur_dominante=%s, extracao_erro=NULL, extracao_progresso=%s
             WHERE id=%s
            """,
            (total, per_dom, json.dumps(payload), zip_id),
        )
        cur.execute(
            "UPDATE explorador_importacoes SET total_arquivos=%s, importado_em=now() WHERE id=%s",
            (total, importacao_id),
        )
    conn.commit()
    print(f"EXTRACT_DONE zip_id={zip_id} total={total} ok={ok} dup={duplicados} falhas={falhas} per_dom={per_dom}", flush=True)
    return {"zip_id": zip_id, "total": total, "ok": ok, "duplicados": duplicados, "falhas": falhas, "perapur_dominante": per_dom}


def audit_month(cur, internal_empresa_id: int, target_month: str) -> dict[str, Any]:
    timeline = fetch_all(
        cur,
        """
        SELECT tm.id AS timeline_mes_id, tm.head_envio_id,
               te.id AS envio_id, te.sequencia, te.tipo, te.status,
               te.total_tentados, te.total_sucesso, te.total_erro
          FROM timeline_mes tm
          LEFT JOIN timeline_envio te ON te.timeline_mes_id = tm.id
         WHERE tm.empresa_id = %s AND tm.per_apur = %s
         ORDER BY te.sequencia NULLS FIRST, te.id
        """,
        (internal_empresa_id, target_month),
    )
    raw = fetch_one(
        cur,
        """
        SELECT COUNT(*) AS linhas,
               COUNT(DISTINCT e.cpf) AS cpfs,
               COUNT(*) FILTER (WHERE e.retificado_por_id IS NULL) AS heads_linhas,
               COUNT(DISTINCT e.cpf) FILTER (WHERE e.retificado_por_id IS NULL) AS heads_cpfs,
               COUNT(*) FILTER (WHERE e.origem_envio_id IS NOT NULL) AS com_origem,
               COUNT(DISTINCT e.zip_id) AS zips
          FROM explorador_eventos e
          JOIN empresa_zips_brutos z ON z.id = e.zip_id
         WHERE z.empresa_id = %s AND e.tipo_evento = 'S-1210' AND e.per_apur = %s
        """,
        (internal_empresa_id, target_month),
    )
    dtpgto = fetch_one(
        cur,
        """
        SELECT COUNT(DISTINCT e.id) AS eventos,
               COUNT(DISTINCT e.cpf) AS cpfs,
               COUNT(*) AS pagamentos,
               COUNT(DISTINCT e.zip_id) AS zips
          FROM explorador_eventos e
          JOIN empresa_zips_brutos z ON z.id = e.zip_id
          JOIN LATERAL jsonb_array_elements(COALESCE(e.dados_json->'pagamentos', '[]'::jsonb)) p(item) ON TRUE
         WHERE z.empresa_id = %s
           AND e.tipo_evento = 'S-1210'
           AND e.per_apur = %s
           AND LEFT(p.item->>'dtPgto', 7) = %s
        """,
        (internal_empresa_id, target_month, target_month),
    )
    overview = fetch_one(
        cur,
        """
        WITH tm AS (
            SELECT id FROM timeline_mes WHERE empresa_id = %s AND per_apur = %s LIMIT 1
        ),
        scope AS (
            SELECT DISTINCT ON (ev.cpf) ev.cpf
              FROM explorador_eventos ev, tm
             WHERE ev.tipo_evento = 'S-1210'
               AND ev.per_apur = %s
               AND ev.retificado_por_id IS NULL
               AND ev.cpf IS NOT NULL
             ORDER BY ev.cpf, ev.dt_processamento DESC NULLS LAST, ev.id DESC
        ),
        ult AS (
            SELECT DISTINCT ON (it.cpf) it.cpf, it.status, it.erro_codigo
              FROM timeline_envio_item it
              JOIN timeline_envio te ON te.id = it.timeline_envio_id
              JOIN timeline_mes tm2 ON tm2.id = te.timeline_mes_id
             WHERE tm2.empresa_id = %s AND tm2.per_apur = %s AND it.tipo_evento = 'S-1210'
             ORDER BY it.cpf, it.criado_em DESC, it.id DESC
        )
        SELECT COUNT(*) AS total,
               COUNT(*) FILTER (WHERE u.status = 'sucesso') AS ok,
               COUNT(*) FILTER (WHERE u.status LIKE 'erro%%') AS erro,
               COUNT(*) FILTER (WHERE u.status IN ('enviando','processando')) AS enviando,
               COUNT(*) FILTER (WHERE u.status = 'sem_mudanca') AS na,
               COUNT(*) FILTER (
                 WHERE u.status IS NULL
                    OR u.status NOT IN ('sucesso','enviando','processando','sem_mudanca')
                       AND u.status NOT LIKE 'erro%%'
               ) AS pendente,
               COUNT(*) FILTER (WHERE u.status LIKE 'erro%%' AND u.erro_codigo IN ('401','459')) AS recibo_retificado,
               COUNT(*) FILTER (WHERE u.erro_codigo = '202') AS aceito_com_aviso
          FROM scope s
          LEFT JOIN ult u ON u.cpf = s.cpf
        """,
        (internal_empresa_id, target_month, target_month, internal_empresa_id, target_month),
    )
    duplicates = fetch_all(
        cur,
        """
        WITH por_cpf AS (
            SELECT e.cpf, COUNT(*) AS eventos
              FROM explorador_eventos e
              JOIN empresa_zips_brutos z ON z.id = e.zip_id
             WHERE z.empresa_id = %s
               AND e.tipo_evento = 'S-1210'
               AND e.per_apur = %s
               AND e.cpf IS NOT NULL
             GROUP BY e.cpf
        )
        SELECT eventos, COUNT(*) AS cpfs
          FROM por_cpf
         GROUP BY eventos
         ORDER BY eventos
        """,
        (internal_empresa_id, target_month),
    )
    return {"timeline": timeline, "raw_per_apur": raw, "dtpgto_match": dtpgto, "overview": overview, "duplicates": duplicates}


def backfill_month(conn, internal_empresa_id: int, target_month: str) -> dict[str, Any]:
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        before = audit_month(cur, internal_empresa_id, target_month)
        cur.execute(
            """
            INSERT INTO timeline_mes (empresa_id, per_apur)
            VALUES (%s, %s)
            ON CONFLICT (empresa_id, per_apur) DO UPDATE SET per_apur = EXCLUDED.per_apur
            RETURNING id
            """,
            (internal_empresa_id, target_month),
        )
        timeline_mes_id = int(cur.fetchone()["id"])
        cur.execute(
            """
            SELECT COUNT(DISTINCT e.id) AS eventos,
                   COUNT(DISTINCT e.cpf) AS cpfs
              FROM explorador_eventos e
              JOIN empresa_zips_brutos z ON z.id = e.zip_id
              JOIN LATERAL jsonb_array_elements(COALESCE(e.dados_json->'pagamentos', '[]'::jsonb)) p(item) ON TRUE
             WHERE z.empresa_id = %s
               AND e.tipo_evento = 'S-1210'
               AND e.per_apur = %s
               AND LEFT(p.item->>'dtPgto', 7) = %s
            """,
            (internal_empresa_id, target_month, target_month),
        )
        totals = dict(cur.fetchone() or {})
        total_eventos = int(totals.get("eventos") or 0)
        total_cpfs = int(totals.get("cpfs") or 0)
        if total_eventos != EXPECTED_S1210 or total_cpfs != EXPECTED_CPFS:
            raise RuntimeError(f"totais no banco nao batem: eventos={total_eventos} cpfs={total_cpfs}")

        cur.execute("SELECT id FROM timeline_envio WHERE timeline_mes_id=%s AND sequencia=0", (timeline_mes_id,))
        row = cur.fetchone()
        resumo = psycopg2.extras.Json(
            {
                "rotulo": "zip_inicial_objetiva_dezembro_2025",
                "fonte": "ZIP local jan/2026 Objective",
                "bruto_s1210": total_eventos,
                "escopo_cpfs_head": total_cpfs,
                "criterio_head": "DISTINCT ON cpf ORDER BY dt_processamento DESC NULLS LAST, id DESC",
            }
        )
        if row:
            envio_id = int(row["id"])
            cur.execute(
                """
                UPDATE timeline_envio
                   SET tipo='zip_inicial', status='concluido',
                       total_tentados=%s, total_sucesso=%s, total_erro=0,
                       iniciado_em=COALESCE(iniciado_em, now()), finalizado_em=now(), resumo=%s
                 WHERE id=%s
                """,
                (total_eventos, total_eventos, resumo, envio_id),
            )
        else:
            cur.execute(
                """
                INSERT INTO timeline_envio
                  (timeline_mes_id, sequencia, tipo, status,
                   iniciado_em, finalizado_em, total_tentados, total_sucesso, total_erro, resumo)
                VALUES (%s, 0, 'zip_inicial', 'concluido', now(), now(), %s, %s, 0, %s)
                RETURNING id
                """,
                (timeline_mes_id, total_eventos, total_eventos, resumo),
            )
            envio_id = int(cur.fetchone()["id"])

        cur.execute(
            """
            UPDATE explorador_eventos AS e
               SET origem_envio_id = %s
              FROM empresa_zips_brutos z
             WHERE z.id = e.zip_id
               AND z.empresa_id = %s
               AND e.tipo_evento = 'S-1210'
               AND e.per_apur = %s
               AND EXISTS (
                   SELECT 1
                     FROM jsonb_array_elements(COALESCE(e.dados_json->'pagamentos', '[]'::jsonb)) p(item)
                    WHERE LEFT(p.item->>'dtPgto', 7) = %s
               )
               AND (e.origem_envio_id IS NULL OR e.origem_envio_id = %s)
            """,
            (envio_id, internal_empresa_id, target_month, target_month, envio_id),
        )
        origem_set = cur.rowcount
        cur.execute(
            """
            UPDATE explorador_eventos AS antigo
               SET retificado_por_id = novo.id
              FROM explorador_eventos AS novo,
                   empresa_zips_brutos z_a, empresa_zips_brutos z_n
             WHERE z_a.id = antigo.zip_id
               AND z_n.id = novo.zip_id
               AND z_a.empresa_id = %s
               AND z_n.empresa_id = %s
               AND antigo.per_apur = %s
               AND novo.per_apur = %s
               AND antigo.tipo_evento = 'S-1210'
               AND novo.tipo_evento = 'S-1210'
               AND antigo.cpf = novo.cpf
               AND novo.referenciado_recibo IS NOT NULL
               AND novo.referenciado_recibo = antigo.nr_recibo
               AND antigo.id <> novo.id
               AND antigo.retificado_por_id IS NULL
            """,
            (internal_empresa_id, internal_empresa_id, target_month, target_month),
        )
        chains = cur.rowcount
        cur.execute("UPDATE timeline_mes SET head_envio_id=%s WHERE id=%s", (envio_id, timeline_mes_id))
        after = audit_month(cur, internal_empresa_id, target_month)
    conn.commit()
    return {
        "timeline_mes_id": timeline_mes_id,
        "envio_id": envio_id,
        "total_eventos": total_eventos,
        "total_cpfs": total_cpfs,
        "origem_set": origem_set,
        "chains": chains,
        "before": before,
        "after": after,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Povoa escopo S-1210 dezembro/2025 da Objective a partir do ZIP local jan/2026.")
    parser.add_argument("--zip", type=Path, default=DEFAULT_ZIP)
    parser.add_argument("--empresa-id", type=int, default=EMPRESA_ID)
    parser.add_argument("--target-month", default=TARGET_MONTH)
    parser.add_argument("--expected-s1210", type=int, default=EXPECTED_S1210)
    parser.add_argument("--expected-cpfs", type=int, default=EXPECTED_CPFS)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    if int(args.empresa_id) != EMPRESA_ID:
        print(json.dumps({"ok": False, "error": "este script foi travado para empresa_id=3 OBJECTIVE"}, indent=2))
        return 2
    if args.target_month != TARGET_MONTH:
        print(json.dumps({"ok": False, "error": "este script foi travado para per_apur=2025-12"}, indent=2))
        return 2
    if not args.zip.exists():
        print(json.dumps({"ok": False, "error": "ZIP nao encontrado", "zip": str(args.zip)}, indent=2))
        return 1

    local_scan = local_preflight(args.zip, args.target_month)
    validation_errors = validate_preflight(local_scan, args.expected_s1210, args.expected_cpfs)
    if validation_errors:
        print(json.dumps({"ok": False, "stage": "local_preflight", "errors": validation_errors, "scan": local_scan}, ensure_ascii=False, indent=2))
        return 1

    internal_empresa_id = tenant.internal_empresa_id(args.empresa_id)
    conn = db.connect(empresa_id=args.empresa_id)
    conn.autocommit = False
    try:
        ensure_columns(conn)
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            tenant_info = fetch_one(cur, "SELECT current_schema() AS schema, current_setting('search_path') AS search_path, current_database() AS database")
            before = audit_month(cur, internal_empresa_id, args.target_month)

        sha, size = sha256_file(args.zip)
        dry_payload = {
            "mode": "dry-run" if not args.apply else "apply",
            "tenant": tenant_info,
            "zip": {"path": str(args.zip), "file": args.zip.name, "sha256": sha, "bytes": size},
            "local_preflight": local_scan,
            "before": before,
        }
        if not args.apply:
            conn.rollback()
            print(json.dumps(dry_payload, ensure_ascii=False, default=json_default, indent=2))
            return 0

        zip_id, uploaded, zip_sha, zip_size = upload_zip_if_needed(conn, args.zip, internal_empresa_id)
        if zip_is_ok(conn, zip_id):
            print(f"EXTRACT_SKIP zip_id={zip_id} file={args.zip.name} status=ok", flush=True)
            extract_result = {"zip_id": zip_id, "file": args.zip.name, "uploaded": uploaded, "extracted": False, "sha256": zip_sha, "bytes": zip_size}
        else:
            extracted = extract_zip(conn, zip_id, args.zip)
            extract_result = {"zip_id": zip_id, "file": args.zip.name, "uploaded": uploaded, "extracted": True, "sha256": zip_sha, "bytes": zip_size, "extract": extracted}

        backfill = backfill_month(conn, internal_empresa_id, args.target_month)
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            final = audit_month(cur, internal_empresa_id, args.target_month)
        print(
            json.dumps(
                {
                    **dry_payload,
                    "zip_result": extract_result,
                    "backfill": backfill,
                    "final": final,
                },
                ensure_ascii=False,
                default=json_default,
                indent=2,
            )
        )
        return 0
    except Exception as exc:  # noqa: BLE001
        conn.rollback()
        print(json.dumps({"ok": False, "error": type(exc).__name__, "message": str(exc)}, ensure_ascii=False, indent=2))
        return 1
    finally:
        conn.close()


if __name__ == "__main__":
    raise SystemExit(main())