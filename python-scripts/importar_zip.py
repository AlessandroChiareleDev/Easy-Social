"""
Importar XMLs direto de arquivo ZIP para o Supabase.
Nao precisa do servidor FastAPI rodando.

Uso:
  python importar_zip.py caminho_do_zip [periodo]
"""
import sys, os, json, time, re, zipfile, tempfile, shutil, logging
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from db_config import DB_CONFIG
import psycopg2
import psycopg2.extras

# Reusar o parser do explorador
from esocial.explorador_routes import _parse_xml_file, _init_db

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
log = logging.getLogger("importar_zip")


def _get_conn():
    return psycopg2.connect(
        **DB_CONFIG,
        keepalives=1, keepalives_idle=30,
        keepalives_interval=10, keepalives_count=3,
    )


def _parse_wrapper(filepath):
    try:
        from esocial.explorador_routes import _parse_xml_file
        data, err = _parse_xml_file(filepath)
        return (filepath, data, err)
    except Exception as e:
        return (filepath, None, f"{os.path.basename(filepath)}: {e}")


def importar_zip(zip_path: str, periodo_hint: str = None):
    if not os.path.exists(zip_path):
        log.error(f"Arquivo não encontrado: {zip_path}")
        return

    zip_name = os.path.basename(zip_path)
    log.info(f"{'='*70}")
    log.info(f"  IMPORTANDO: {zip_name}")
    log.info(f"{'='*70}")

    # Extrair XMLs para temp
    log.info("Extraindo XMLs do ZIP...")
    tmpdir = tempfile.mkdtemp(prefix="esocial_import_")
    t0 = time.time()

    try:
        with zipfile.ZipFile(zip_path, 'r') as zf:
            members = [m for m in zf.namelist() if m.lower().endswith('.xml')]
            log.info(f"  {len(members)} XMLs encontrados no ZIP")

            for member in members:
                safe_name = os.path.basename(member)
                if not safe_name:
                    continue
                data = zf.read(member)
                with open(os.path.join(tmpdir, safe_name), 'wb') as out:
                    out.write(data)

        xml_files = [os.path.join(tmpdir, f) for f in os.listdir(tmpdir) if f.lower().endswith('.xml')]
        elapsed_extract = time.time() - t0
        log.info(f"  Extraídos {len(xml_files)} XMLs em {elapsed_extract:.1f}s")

        # Criar registro de importação
        conn = _get_conn()
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO explorador_importacoes (pasta, periodo, total_arquivos) VALUES (%s, %s, %s) RETURNING id",
                (zip_name, periodo_hint, len(xml_files))
            )
            importacao_id = cur.fetchone()[0]
            conn.commit()
        log.info(f"  Importação ID: {importacao_id}")

        # Drop indexes para bulk insert mais rápido
        with conn.cursor() as cur:
            for idx in ["idx_expl_eventos_cpf", "idx_expl_eventos_tipo", "idx_expl_eventos_per",
                        "idx_expl_eventos_recibo", "idx_expl_rubricas_cod", "idx_expl_rubricas_irrf",
                        "idx_expl_rubricas_evt"]:
                cur.execute(f"DROP INDEX IF EXISTS {idx}")
            conn.commit()
        log.info("  Indexes dropped para bulk insert")

        # Parse em paralelo + insert em lotes
        workers = min(8, os.cpu_count() or 4)
        batch_size = 2000
        evento_batch = []
        rubrica_batch = []
        total_imported = 0
        total_errors = 0
        total_parsed = 0
        t_start = time.time()

        chunk_size = 3000
        for chunk_start in range(0, len(xml_files), chunk_size):
            chunk = xml_files[chunk_start:chunk_start + chunk_size]

            with ThreadPoolExecutor(max_workers=workers) as pool:
                futures = {pool.submit(_parse_wrapper, fp): fp for fp in chunk}
                for future in as_completed(futures):
                    filepath, data, err = future.result()
                    total_parsed += 1

                    if err or not data:
                        total_errors += 1
                        continue

                    evento_batch.append((
                        importacao_id,
                        data["tipo_evento"],
                        data["cpf"],
                        data["per_apur"],
                        data["nr_recibo"],
                        data["id_evento"],
                        data["dt_processamento"],
                        data["cd_resposta"],
                        data["arquivo_origem"],
                        json.dumps(data["dados_json"]) if data["dados_json"] else None,
                    ))

                    if data.get("rubricas"):
                        for rub in data["rubricas"]:
                            rubrica_batch.append((
                                None,  # placeholder for evento_id
                                rub.get("cod_rubr"),
                                rub.get("ide_tab_rubr"),
                                rub.get("nat_rubr"),
                                rub.get("tp_rubr"),
                                rub.get("cod_inc_cp"),
                                rub.get("cod_inc_irrf"),
                                rub.get("cod_inc_fgts"),
                                rub.get("vr_rubr"),
                                rub.get("ind_ap_ir"),
                            ))

                    # Flush batch
                    if len(evento_batch) >= batch_size:
                        _flush_batch(conn, evento_batch, importacao_id)
                        total_imported += len(evento_batch)
                        evento_batch = []

            # Progress
            elapsed = time.time() - t_start
            rate = total_parsed / elapsed if elapsed > 0 else 0
            pct = (total_parsed / len(xml_files)) * 100
            log.info(f"  Progresso: {total_parsed}/{len(xml_files)} ({pct:.0f}%) "
                     f"| Importados: {total_imported} | Erros: {total_errors} "
                     f"| {rate:.0f} xml/s | {elapsed:.0f}s")

        # Flush remaining
        if evento_batch:
            _flush_batch(conn, evento_batch, importacao_id)
            total_imported += len(evento_batch)

        # Recreate indexes
        log.info("  Recriando indexes...")
        with conn.cursor() as cur:
            cur.execute("CREATE INDEX IF NOT EXISTS idx_expl_eventos_cpf ON explorador_eventos(cpf)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_expl_eventos_tipo ON explorador_eventos(tipo_evento)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_expl_eventos_per ON explorador_eventos(per_apur)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_expl_eventos_recibo ON explorador_eventos(nr_recibo)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_expl_rubricas_cod ON explorador_rubricas(cod_rubr)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_expl_rubricas_irrf ON explorador_rubricas(cod_inc_irrf)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_expl_rubricas_evt ON explorador_rubricas(evento_id)")
            conn.commit()
        log.info("  Indexes recriados")

        conn.close()

        total_time = time.time() - t0
        log.info(f"\n{'='*70}")
        log.info(f"  IMPORTAÇÃO CONCLUÍDA: {zip_name}")
        log.info(f"  Total XMLs: {len(xml_files)}")
        log.info(f"  Importados: {total_imported}")
        log.info(f"  Erros parse: {total_errors}")
        log.info(f"  Tempo total: {total_time:.0f}s ({total_time/60:.1f} min)")
        log.info(f"{'='*70}")

        # Verificar contagem por tipo
        conn = _get_conn()
        with conn.cursor() as cur:
            per = periodo_hint
            if not per:
                cur.execute("""
                    SELECT per_apur FROM explorador_eventos
                    WHERE importacao_id = %s AND per_apur IS NOT NULL
                    LIMIT 1
                """, (importacao_id,))
                row = cur.fetchone()
                per = row[0] if row else None

            if per:
                cur.execute("""
                    SELECT tipo_evento, count(*)
                    FROM explorador_eventos
                    WHERE per_apur = %s
                    GROUP BY tipo_evento
                    ORDER BY tipo_evento
                """, (per,))
                rows = cur.fetchall()
                log.info(f"\n  Eventos em {per}:")
                for r in rows:
                    log.info(f"    {r[0]}: {r[1]}")

                # Contar CPFs distintos com S-1210
                cur.execute("""
                    SELECT count(DISTINCT cpf)
                    FROM explorador_eventos
                    WHERE tipo_evento = 'S-1210' AND per_apur = %s
                      AND cpf IS NOT NULL
                      AND COALESCE(dados_json->>'indRetif', '1') != '2'
                """, (per,))
                cpf_count = cur.fetchone()[0]
                log.info(f"\n  CPFs com S-1210 original: {cpf_count}")

                cur.execute("""
                    SELECT count(DISTINCT cpf)
                    FROM explorador_eventos
                    WHERE tipo_evento = 'S-5002' AND per_apur = %s AND cpf IS NOT NULL
                """, (per,))
                s5002_count = cur.fetchone()[0]
                log.info(f"  CPFs com S-5002: {s5002_count}")

        conn.close()

        return {
            "importacao_id": importacao_id,
            "total_xmls": len(xml_files),
            "importados": total_imported,
            "erros": total_errors,
            "tempo_s": round(total_time, 1),
        }

    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)
        log.info(f"Temp dir limpo: {tmpdir}")


def _flush_batch(conn, batch, importacao_id):
    """Insert batch of events into DB."""
    with conn.cursor() as cur:
        psycopg2.extras.execute_values(
            cur,
            """INSERT INTO explorador_eventos
                (importacao_id, tipo_evento, cpf, per_apur, nr_recibo,
                 id_evento, dt_processamento, cd_resposta, arquivo_origem, dados_json)
            VALUES %s""",
            batch,
            template="(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
            page_size=500,
        )
        conn.commit()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python importar_zip.py <caminho_do_zip> [periodo]")
        print("  Ex: python importar_zip.py downloads/jan2025.zip 2025-01")
        sys.exit(1)

    zip_path = sys.argv[1]
    periodo = sys.argv[2] if len(sys.argv) > 2 else None
    importar_zip(zip_path, periodo)
