from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import time
import zipfile
from collections import Counter
from datetime import date, datetime
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


ZIP_DIR_DEFAULT = Path(r"C:\Users\xandao\Downloads\todos os meses 2025 SOLUCOES")
INTERNAL_EMPRESA_ID = 1
BATCH_SIZE = 50

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


def json_default(value: Any) -> Any:
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    return str(value)


def ym_next(ym: str) -> str:
    year, month = [int(part) for part in ym.split("-")]
    month += 1
    if month == 13:
        year += 1
        month = 1
    return f"{year:04d}-{month:02d}"


def zip_month(path: Path) -> str | None:
    match = re.search(r"(20\d{2})-(\d{2})", path.name)
    if not match:
        return None
    return f"{match.group(1)}-{match.group(2)}"


def zip_dates(path: Path) -> tuple[date, date]:
    ym = zip_month(path)
    if not ym:
        today = date.today()
        return today, today
    year, month = [int(part) for part in ym.split("-")]
    match = re.search(r"\((\d{2})-(\d{2})\)", path.name)
    if not match:
        return date(year, month, 1), date(year, month, 28)
    start_day = int(match.group(1))
    end_day = int(match.group(2))
    return date(year, month, start_day), date(year, month, end_day)


def tipo_por_nome(filename: str) -> str | None:
    base = filename.replace("\\", "/").split("/")[-1].upper()
    match = re.search(r"(S-\d{4})\.XML$", base)
    return match.group(1) if match else None


def sha256_file(path: Path) -> tuple[str, int]:
    h = hashlib.sha256()
    total = 0
    with path.open("rb") as file:
        while True:
            chunk = file.read(8 * 1024 * 1024)
            if not chunk:
                break
            h.update(chunk)
            total += len(chunk)
    return h.hexdigest(), total


def selected_zip_paths(zip_dir: Path, target_months: list[str]) -> list[Path]:
    wanted = set(target_months)
    wanted.update(ym_next(month) for month in target_months)
    paths = []
    for path in sorted(zip_dir.glob("*.zip"), key=lambda item: item.name):
        if zip_month(path) in wanted:
            paths.append(path)
    return paths


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


def upload_zip_if_needed(conn, path: Path) -> tuple[int, bool, str, int]:
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
            (INTERNAL_EMPRESA_ID, sha),
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
        lo = conn.lobject(0, "wb")
        oid = lo.oid
        written = 0
        last = time.time()
        with path.open("rb") as file:
            while True:
                chunk = file.read(4 * 1024 * 1024)
                if not chunk:
                    break
                lo.write(chunk)
                written += len(chunk)
                if time.time() - last > 10:
                    last = time.time()
                    print(f"UPLOAD_PROGRESS file={path.name} {written}/{size}", flush=True)
        lo.close()
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
                    INTERNAL_EMPRESA_ID,
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
    if not row:
        return False
    if row.get("extracao_status") != "ok":
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


def create_importacao(conn, path: Path) -> int:
    periodo = zip_month(path) or path.stem
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(
            "INSERT INTO explorador_importacoes (pasta, periodo, total_arquivos) VALUES (%s, %s, 0) RETURNING id",
            (path.name, periodo),
        )
        importacao_id = int(cur.fetchone()["id"])
    conn.commit()
    return importacao_id


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
    with zipfile.ZipFile(path, "r") as zf:
        names = [name for name in zf.namelist() if name.lower().endswith(".xml")]
        total_est = len(names)
        update_progress(
            conn,
            zip_id,
            {"etapa": "extraindo", "processados": 0, "total": total_est, "ok": 0, "duplicados": 0, "falhas": 0},
        )
        for name in names:
            total += 1
            try:
                data = zf.read(name)
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
                print(
                    f"EXTRACT_PROGRESS zip_id={zip_id} {total}/{total_est} ok={ok} dup={duplicados} falhas={falhas}",
                    flush=True,
                )
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


def audit_month(cur, target_month: str) -> dict[str, Any]:
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
        (INTERNAL_EMPRESA_ID, target_month),
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
        (INTERNAL_EMPRESA_ID, target_month),
    )
    cash = fetch_one(
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
           AND LEFT(p.item->>'dtPgto', 7) = %s
        """,
        (INTERNAL_EMPRESA_ID, target_month),
    )
    match = fetch_one(
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
        (INTERNAL_EMPRESA_ID, target_month, target_month),
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
        (INTERNAL_EMPRESA_ID, target_month, target_month, INTERNAL_EMPRESA_ID, target_month),
    )
    zips = fetch_all(
        cur,
        """
        SELECT z.id, z.nome_arquivo_original, z.perapur_dominante, z.extracao_status,
               COUNT(DISTINCT e.id) AS eventos, COUNT(DISTINCT e.cpf) AS cpfs
          FROM explorador_eventos e
          JOIN empresa_zips_brutos z ON z.id = e.zip_id
          JOIN LATERAL jsonb_array_elements(COALESCE(e.dados_json->'pagamentos', '[]'::jsonb)) p(item) ON TRUE
         WHERE z.empresa_id = %s
           AND e.tipo_evento = 'S-1210'
           AND LEFT(p.item->>'dtPgto', 7) = %s
         GROUP BY z.id, z.nome_arquivo_original, z.perapur_dominante, z.extracao_status
         ORDER BY z.id
        """,
        (INTERNAL_EMPRESA_ID, target_month),
    )
    return {"timeline": timeline, "raw_per_apur": raw, "cash_dtpgto": cash, "cash_and_per_apur": match, "overview": overview, "zips_dtpgto": zips}


def backfill_cash_month(conn, target_month: str) -> dict[str, Any]:
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    try:
        before = audit_month(cur, target_month)
        cur.execute(
            """
            INSERT INTO timeline_mes (empresa_id, per_apur)
            VALUES (%s, %s)
            ON CONFLICT (empresa_id, per_apur) DO UPDATE SET per_apur = EXCLUDED.per_apur
            RETURNING id
            """,
            (INTERNAL_EMPRESA_ID, target_month),
        )
        timeline_mes_id = int(cur.fetchone()["id"])
        cur.execute(
            """
            SELECT COUNT(DISTINCT e.id) AS eventos
              FROM explorador_eventos e
              JOIN empresa_zips_brutos z ON z.id = e.zip_id
              JOIN LATERAL jsonb_array_elements(COALESCE(e.dados_json->'pagamentos', '[]'::jsonb)) p(item) ON TRUE
             WHERE z.empresa_id = %s
               AND e.tipo_evento = 'S-1210'
               AND e.per_apur = %s
               AND LEFT(p.item->>'dtPgto', 7) = %s
            """,
            (INTERNAL_EMPRESA_ID, target_month, target_month),
        )
        total_s1210 = int((cur.fetchone() or {}).get("eventos") or 0)
        cur.execute(
            "SELECT id FROM timeline_envio WHERE timeline_mes_id=%s AND sequencia=0",
            (timeline_mes_id,),
        )
        row = cur.fetchone()
        if row:
            envio_id = int(row["id"])
            cur.execute(
                """
                UPDATE timeline_envio
                   SET tipo='zip_inicial', status='em_andamento',
                       total_tentados=%s, total_sucesso=0, total_erro=0,
                       finalizado_em=NULL
                 WHERE id=%s
                """,
                (total_s1210, envio_id),
            )
        else:
            cur.execute(
                """
                INSERT INTO timeline_envio
                  (timeline_mes_id, sequencia, tipo, status,
                   total_tentados, total_sucesso, total_erro, finalizado_em)
                VALUES (%s, 0, 'zip_inicial', 'em_andamento', %s, 0, 0, NULL)
                RETURNING id
                """,
                (timeline_mes_id, total_s1210),
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
            (envio_id, INTERNAL_EMPRESA_ID, target_month, target_month, envio_id),
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
            (INTERNAL_EMPRESA_ID, INTERNAL_EMPRESA_ID, target_month, target_month),
        )
        chains = cur.rowcount
        cur.execute(
            """
            UPDATE timeline_mes m
               SET head_envio_id = sub.id
              FROM (
                SELECT te.id
                  FROM timeline_envio te
                 WHERE te.timeline_mes_id = %s
                 ORDER BY te.sequencia DESC, te.id DESC
                 LIMIT 1
              ) sub
             WHERE m.id = %s
            """,
            (timeline_mes_id, timeline_mes_id),
        )
        conn.commit()
        after = audit_month(cur, target_month)
        return {
            "target_month": target_month,
            "timeline_mes_id": timeline_mes_id,
            "envio_id": envio_id,
            "total_s1210_eventos_dtpgto": total_s1210,
            "origem_set": origem_set,
            "chains": chains,
            "before": before,
            "after": after,
        }
    finally:
        cur.close()


def main() -> int:
    parser = argparse.ArgumentParser(description="Povoa escopo S-1210 SOLUCOES por mês-caixa dtPgto.")
    parser.add_argument("--zip-dir", type=Path, default=ZIP_DIR_DEFAULT)
    parser.add_argument("--empresa-id", type=int, default=2)
    parser.add_argument("--target-month", action="append", default=[])
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    if int(args.empresa_id) != tenant.SOLUCOES_ID:
        print(json.dumps({"ok": False, "error": "este script foi feito para empresa_id=2 SOLUCOES"}, indent=2))
        return 2
    target_months = args.target_month or ["2025-11", "2025-12"]
    zip_paths = selected_zip_paths(args.zip_dir, target_months)
    if not zip_paths:
        print(json.dumps({"ok": False, "error": "nenhum zip candidato encontrado", "zip_dir": str(args.zip_dir)}, indent=2))
        return 1

    conn = db.connect(empresa_id=args.empresa_id)
    conn.autocommit = False
    try:
        ensure_columns(conn)
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            tenant_info = fetch_one(cur, "SELECT current_schema() AS schema, current_setting('search_path') AS search_path")
            before = {month: audit_month(cur, month) for month in target_months}

        selected = []
        for path in zip_paths:
            sha, size = sha256_file(path)
            selected.append({"path": str(path), "file": path.name, "month": zip_month(path), "sha256": sha, "bytes": size})

        if not args.apply:
            print(json.dumps({"mode": "dry-run", "tenant": tenant_info, "selected_zips": selected, "before": before}, ensure_ascii=False, default=json_default, indent=2))
            conn.rollback()
            return 0

        zip_results = []
        for path in zip_paths:
            zip_id, uploaded, sha, size = upload_zip_if_needed(conn, path)
            if zip_is_ok(conn, zip_id):
                print(f"EXTRACT_SKIP zip_id={zip_id} file={path.name} status=ok", flush=True)
                zip_results.append({"zip_id": zip_id, "file": path.name, "uploaded": uploaded, "extracted": False, "sha256": sha, "bytes": size})
            else:
                extracted = extract_zip(conn, zip_id, path)
                zip_results.append({"zip_id": zip_id, "file": path.name, "uploaded": uploaded, "extracted": True, "sha256": sha, "bytes": size, "extract": extracted})

        backfills = [backfill_cash_month(conn, month) for month in target_months]
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            final = {month: audit_month(cur, month) for month in target_months}
        print(json.dumps({"mode": "apply", "tenant": tenant_info, "zip_results": zip_results, "backfills": backfills, "final": final}, ensure_ascii=False, default=json_default, indent=2))
        return 0
    except Exception as exc:  # noqa: BLE001
        conn.rollback()
        print(json.dumps({"ok": False, "error": type(exc).__name__, "message": str(exc)}, ensure_ascii=False, indent=2))
        return 1
    finally:
        conn.close()


if __name__ == "__main__":
    raise SystemExit(main())