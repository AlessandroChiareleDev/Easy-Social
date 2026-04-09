"""
Explorador de Eventos eSocial — Backend API
Importa XMLs baixados do portal e expõe endpoints de consulta.
"""
import os
import re
import json
import time
import logging
import threading
import psycopg2
import psycopg2.extras
from lxml import etree
from pathlib import Path
from datetime import datetime
from typing import Optional, List
from fastapi import APIRouter, Query, HTTPException, UploadFile, File
import tempfile
import shutil
from pydantic import BaseModel
from concurrent.futures import ThreadPoolExecutor, as_completed

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from db_config import DB_CONFIG

logger = logging.getLogger("explorador")
logger.setLevel(logging.INFO)
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("[explorador] %(levelname)s %(message)s"))
    logger.addHandler(handler)

router = APIRouter(prefix="/api/explorador", tags=["explorador"])

# ── Namespace maps for XML parsing ──────────────────────────────────────────
NS_DOWNLOAD = "http://www.esocial.gov.br/schema/download/retornoProcessamento/v1_0_0"
NS_RETORNO = "http://www.esocial.gov.br/schema/evt/retornoEvento/v1_3_0"

# Maps event type → inner xmlns suffix
EVENT_NS_MAP = {
    "S-1010": "evtTabRubrica",
    "S-1020": "evtTabLotacao",
    "S-1200": "evtRemun",
    "S-1210": "evtPgtos",
    "S-1298": "evtReabreEvPer",
    "S-1299": "evtFechaEvPer",
    "S-2200": "evtAdmissao",
    "S-2205": "evtAltCadastral",
    "S-2206": "evtAltContratual",
    "S-2210": "evtCAT",
    "S-2220": "evtMonit",
    "S-2230": "evtAfastTemp",
    "S-2240": "evtExpRisco",
    "S-2299": "evtDeslig",
    "S-2500": "evtProcTrab",
    "S-2501": "evtContProc",
    "S-3000": "evtExclusao",
    "S-5001": "evtBasesTrab",
    "S-5002": "evtIrrfBenef",
    "S-5003": "evtBasesFGTS",
    "S-5011": "evtCS",
    "S-5012": "evtIrrf",
    "S-5013": "evtFGTS",
    "S-5501": "evtProcTrabTot",
    "S-5503": "evtFGTSProcTrab",
}


# ── Database setup ──────────────────────────────────────────────────────────

INIT_SQL = """
CREATE TABLE IF NOT EXISTS explorador_importacoes (
    id              SERIAL PRIMARY KEY,
    pasta           TEXT NOT NULL,
    periodo         VARCHAR(7),
    total_arquivos  INT DEFAULT 0,
    importado_em    TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS explorador_eventos (
    id              SERIAL PRIMARY KEY,
    importacao_id   INT REFERENCES explorador_importacoes(id) ON DELETE CASCADE,
    tipo_evento     VARCHAR(10) NOT NULL,
    cpf             VARCHAR(11),
    per_apur        VARCHAR(7),
    nr_recibo       VARCHAR(40),
    id_evento       VARCHAR(80),
    dt_processamento TIMESTAMPTZ,
    cd_resposta     VARCHAR(10),
    arquivo_origem  VARCHAR(120),
    dados_json      JSONB,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS explorador_rubricas (
    id              SERIAL PRIMARY KEY,
    evento_id       INT REFERENCES explorador_eventos(id) ON DELETE CASCADE,
    cod_rubr        VARCHAR(30),
    ide_tab_rubr    VARCHAR(10),
    nat_rubr        VARCHAR(10),
    tp_rubr         VARCHAR(2),
    cod_inc_cp      VARCHAR(10),
    cod_inc_irrf    VARCHAR(10),
    cod_inc_fgts    VARCHAR(10),
    vr_rubr         NUMERIC(15,2),
    ind_ap_ir       VARCHAR(2)
);

DO $$ BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_indexes WHERE indexname = 'idx_expl_eventos_cpf') THEN
        CREATE INDEX idx_expl_eventos_cpf ON explorador_eventos(cpf);
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_indexes WHERE indexname = 'idx_expl_eventos_tipo') THEN
        CREATE INDEX idx_expl_eventos_tipo ON explorador_eventos(tipo_evento);
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_indexes WHERE indexname = 'idx_expl_eventos_per') THEN
        CREATE INDEX idx_expl_eventos_per ON explorador_eventos(per_apur);
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_indexes WHERE indexname = 'idx_expl_eventos_recibo') THEN
        CREATE INDEX idx_expl_eventos_recibo ON explorador_eventos(nr_recibo);
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_indexes WHERE indexname = 'idx_expl_rubricas_cod') THEN
        CREATE INDEX idx_expl_rubricas_cod ON explorador_rubricas(cod_rubr);
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_indexes WHERE indexname = 'idx_expl_rubricas_irrf') THEN
        CREATE INDEX idx_expl_rubricas_irrf ON explorador_rubricas(cod_inc_irrf);
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_indexes WHERE indexname = 'idx_expl_rubricas_evt') THEN
        CREATE INDEX idx_expl_rubricas_evt ON explorador_rubricas(evento_id);
    END IF;
END $$;
"""

def _get_conn():
    return psycopg2.connect(
        **DB_CONFIG,
        keepalives=1,
        keepalives_idle=30,
        keepalives_interval=10,
        keepalives_count=3,
    )

def _init_db():
    conn = _get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(INIT_SQL)
        conn.commit()
    finally:
        conn.close()

# Run on import
try:
    _init_db()
except Exception as e:
    print(f"[explorador] DB init warning: {e}")


# ── XML Parsing helpers ─────────────────────────────────────────────────────

def _detect_event_type(filename: str) -> Optional[str]:
    """Extract event type from filename like ID...S-1200.xml"""
    m = re.search(r'\.(S-\d+)\.xml$', filename, re.IGNORECASE)
    return m.group(1) if m else None


def _text(el, tag, ns=None):
    """Get text content of a child element."""
    if ns:
        child = el.find(f'{{{ns}}}{tag}')
    else:
        # Try without namespace first
        child = el.find(tag)
        if child is None:
            # Try with wildcard namespace
            child = el.find(f'{{*}}{tag}')
    return child.text.strip() if child is not None and child.text else None


_xpath_cache = {}

def _get_xpath(local_name):
    """Get or create a compiled XPath for the given local-name."""
    if local_name not in _xpath_cache:
        _xpath_cache[local_name] = etree.XPath(f'.//*[local-name()="{local_name}"]')
    return _xpath_cache[local_name]


def _xpath_text(el, local_name):
    """Get text of first descendant matching local-name (namespace-agnostic)."""
    hits = _get_xpath(local_name)(el)
    if hits and hits[0].text:
        return hits[0].text.strip()
    return None


def _xpath_all(el, local_name):
    """Find all descendants matching local-name (namespace-agnostic)."""
    return _get_xpath(local_name)(el)


def _extract_cpf(root_evento):
    """Extract CPF from various event types."""
    for tag in ["cpfTrab", "cpfBenef"]:
        val = _xpath_text(root_evento, tag)
        if val:
            return val
    return None


def _extract_per_apur(root_evento):
    """Extract perApur from event."""
    return _xpath_text(root_evento, "perApur")


def _extract_rubricas_s1010(root_evento):
    """Extract rubrica definition from S-1010 event."""
    rubricas = []
    for dados in _xpath_all(root_evento, "dadosRubrica"):
        parent = dados.getparent()
        ide_els = parent.xpath('.//*[local-name()="ideRubrica"]') if parent is not None else []
        ide = ide_els[0] if ide_els else None
        rub = {
            "cod_rubr": _xpath_text(ide, "codRubr") if ide is not None else None,
            "ide_tab_rubr": _xpath_text(ide, "ideTabRubr") if ide is not None else None,
            "nat_rubr": _xpath_text(dados, "natRubr"),
            "tp_rubr": _xpath_text(dados, "tpRubr"),
            "cod_inc_cp": _xpath_text(dados, "codIncCP"),
            "cod_inc_irrf": _xpath_text(dados, "codIncIRRF"),
            "cod_inc_fgts": _xpath_text(dados, "codIncFGTS"),
        }
        if rub["cod_rubr"]:
            rubricas.append(rub)
    return rubricas


def _extract_rubricas_s1200(root_evento):
    """Extract itensRemun from S-1200 event."""
    rubricas = []
    for item in _xpath_all(root_evento, "itensRemun"):
        rub = {
            "cod_rubr": _xpath_text(item, "codRubr"),
            "ide_tab_rubr": _xpath_text(item, "ideTabRubr"),
            "vr_rubr": _xpath_text(item, "vrRubr"),
            "ind_ap_ir": _xpath_text(item, "indApurIR"),
        }
        if rub["cod_rubr"]:
            rubricas.append(rub)
    return rubricas


def _extract_rubricas_recibo(root_recibo):
    """Extract rubrica refs from recibo section (some have rubrica attributes)."""
    rubricas = []
    for rub_el in root_recibo.xpath('.//*[local-name()="rubrica"]'):
        rub = {
            "cod_rubr": rub_el.get("cdR"),
            "ide_tab_rubr": rub_el.get("idT"),
            "nat_rubr": rub_el.get("ntR"),
            "tp_rubr": rub_el.get("tpR"),
            "cod_inc_irrf": rub_el.get("inIR"),
            "cod_inc_cp": rub_el.get("inCP"),
            "cod_inc_fgts": rub_el.get("inFGTS"),
        }
        if rub["cod_rubr"]:
            rubricas.append(rub)
    return rubricas


def _extract_info_ir(root_evento):
    """Extract infoIR entries from S-5002."""
    items = []
    for ir in _xpath_all(root_evento, "infoIR"):
        items.append({
            "tpInfoIR": _xpath_text(ir, "tpInfoIR"),
            "valor": _xpath_text(ir, "valor"),
        })
    return items


def _build_dados_json(tipo_evento, root_evento, root_recibo):
    """Build a summary JSON with key fields depending on event type."""
    dados = {}

    if tipo_evento == "S-1010":
        for op in ["inclusao", "alteracao", "exclusao"]:
            if _xpath_all(root_evento, op):
                dados["operacao"] = op
                break
        dados["dscRubr"] = _xpath_text(root_evento, "dscRubr") or ""
        dados["iniValid"] = _xpath_text(root_evento, "iniValid") or ""

    elif tipo_evento == "S-1200":
        dados["matricula"] = _xpath_text(root_evento, "matricula") or ""
        dados["codCateg"] = _xpath_text(root_evento, "codCateg") or ""
        dados["indRetif"] = _xpath_text(root_evento, "indRetif") or ""
        dados["ideDmDev"] = _xpath_text(root_evento, "ideDmDev") or ""

    elif tipo_evento == "S-1210":
        dados["dtPgto"] = _xpath_text(root_evento, "dtPgto") or ""
        dados["tpPgto"] = _xpath_text(root_evento, "tpPgto") or ""
        dados["vrLiq"] = _xpath_text(root_evento, "vrLiq") or ""
        dados["tpCR"] = _xpath_text(root_evento, "tpCR") or ""

    elif tipo_evento == "S-5002":
        dados["infoIR"] = _extract_info_ir(root_evento)
        tot_els = _xpath_all(root_evento, "totApurMen")
        if tot_els:
            for child in tot_els[0]:
                tag = etree.QName(child.tag).localname
                if child.text:
                    dados[f"totApurMen_{tag}"] = child.text.strip()

    elif tipo_evento == "S-5001":
        items = []
        for cp in _xpath_all(root_evento, "infoCpCalc"):
            item = {}
            for child in cp:
                tag = etree.QName(child.tag).localname
                if child.text:
                    item[tag] = child.text.strip()
            if item:
                items.append(item)
        if items:
            dados["infoCpCalc"] = items

    # Common: recibo info
    if root_recibo is not None:
        dados["cdResposta"] = _xpath_text(root_recibo, "cdResposta") or ""
        dados["descResposta"] = _xpath_text(root_recibo, "descResposta") or ""

    return dados


def _parse_xml_file(filepath: str):
    """Parse a single eSocial download XML and return structured data."""
    filename = os.path.basename(filepath)
    tipo_evento = _detect_event_type(filename)
    if not tipo_evento:
        return None, f"Tipo evento não detectado: {filename}"

    try:
        tree = etree.parse(filepath)
        root = tree.getroot()
    except Exception as e:
        return None, f"XML inválido: {filename}: {e}"

    # Navigate: retornoProcessamentoDownload > evento > eSocial (inner)
    evento_wrapper = root.find(f'{{{NS_DOWNLOAD}}}retornoProcessamentoDownload/{{{NS_DOWNLOAD}}}evento')
    recibo_wrapper = root.find(f'{{{NS_DOWNLOAD}}}retornoProcessamentoDownload/{{{NS_DOWNLOAD}}}recibo')

    if evento_wrapper is None:
        return None, f"Sem retornoProcessamentoDownload/evento: {filename}"

    # The inner eSocial element (the actual event)
    inner_esocial = None
    for child in evento_wrapper:
        if 'eSocial' in child.tag:
            inner_esocial = child
            break

    if inner_esocial is None:
        return None, f"Sem eSocial interno: {filename}"

    # Extract CPF
    cpf = _extract_cpf(inner_esocial)

    # Extract perApur
    per_apur = _extract_per_apur(inner_esocial)

    # Extract event ID
    id_evento = None
    for el in inner_esocial.iter():
        evt_id = el.get("Id")
        if evt_id:
            id_evento = evt_id
            break

    # Extract recibo info
    nr_recibo = None
    dt_processamento = None
    cd_resposta = None
    recibo_inner = None

    if recibo_wrapper is not None:
        for child in recibo_wrapper:
            if 'eSocial' in child.tag:
                recibo_inner = child
                break

        if recibo_inner is not None:
            nr_recibo = _xpath_text(recibo_inner, "nrRecibo")

            dt_val = _xpath_text(recibo_inner, "dhProcessamento")
            if dt_val:
                try:
                    dt_processamento = datetime.fromisoformat(dt_val)
                except ValueError:
                    pass

            cd_resposta = _xpath_text(recibo_inner, "cdResposta")

    # Build dados_json
    dados_json = _build_dados_json(tipo_evento, inner_esocial, recibo_inner)

    # Extract rubricas
    rubricas = []
    if tipo_evento == "S-1010":
        rubricas = _extract_rubricas_s1010(inner_esocial)
    elif tipo_evento == "S-1200":
        rubricas = _extract_rubricas_s1200(inner_esocial)

    # Also try recibo rubricas
    if recibo_inner is not None:
        recibo_rubricas = _extract_rubricas_recibo(recibo_inner)
        if recibo_rubricas:
            rubricas.extend(recibo_rubricas)

    return {
        "tipo_evento": tipo_evento,
        "cpf": cpf,
        "per_apur": per_apur,
        "nr_recibo": nr_recibo,
        "id_evento": id_evento,
        "dt_processamento": dt_processamento,
        "cd_resposta": cd_resposta,
        "arquivo_origem": filename,
        "dados_json": dados_json,
        "rubricas": rubricas,
    }, None


# ── Import endpoint ────────────────────────────────────────────────────────

class ImportRequest(BaseModel):
    pasta: str
    periodo: Optional[str] = None

class ImportStatus(BaseModel):
    importacao_id: int
    total_arquivos: int
    importados: int
    erros: int
    tempo_seg: float

# Simple in-memory progress tracker
_import_progress = {
    "running": False,
    "total": 0,
    "processed": 0,
    "importacao_id": None,
    "errors": 0,
    "last_error": "",
    "imported": 0,
    "elapsed": 0,
    "rate": 0,
}


def _parse_file_wrapper(filepath):
    """Wrapper for parallel parsing — returns (filepath, data_or_None, error_msg)."""
    try:
        data, err = _parse_xml_file(filepath)
        return (filepath, data, err)
    except Exception as e:
        return (filepath, None, f"{os.path.basename(filepath)}: {type(e).__name__}: {e}")


@router.post("/importar")
async def importar_xmls(req: ImportRequest):
    """Import all XML files from a local folder into the database (background)."""
    pasta = req.pasta.strip()
    if not os.path.isdir(pasta):
        raise HTTPException(status_code=400, detail=f"Pasta não encontrada: {pasta}")

    if _import_progress["running"]:
        raise HTTPException(status_code=409, detail="Uma importação já está em andamento")

    # List XML files
    xml_files = [
        os.path.join(pasta, f)
        for f in os.listdir(pasta)
        if f.lower().endswith('.xml')
    ]

    if not xml_files:
        raise HTTPException(status_code=400, detail="Nenhum arquivo XML encontrado na pasta")

    _import_progress["running"] = True
    _import_progress["total"] = len(xml_files)
    _import_progress["processed"] = 0
    _import_progress["errors"] = 0
    _import_progress["imported"] = 0
    _import_progress["last_error"] = ""
    _import_progress["elapsed"] = 0
    _import_progress["rate"] = 0
    _import_progress["finished"] = False
    _import_progress["result"] = None

    # Launch background thread
    t = threading.Thread(
        target=_run_import,
        args=(xml_files, pasta, req.periodo),
        daemon=True,
    )
    t.start()

    return {"status": "started", "total": len(xml_files)}


# ── Upload-based import (drag & drop) ──────────────────────────────────────

# Temp storage for multi-batch upload sessions
_upload_session = {
    "active": False,
    "tmpdir": None,
    "files": [],
    "total_received": 0,
}


@router.post("/upload-batch")
async def upload_batch(files: List[UploadFile] = File(...)):
    """
    Receive a batch of XML files. Can be called multiple times.
    Files accumulate in a temp directory until /upload-start is called.
    """
    if _import_progress["running"]:
        raise HTTPException(status_code=409, detail="Uma importação já está em andamento")

    # Create temp dir on first batch
    if not _upload_session["active"] or not _upload_session["tmpdir"]:
        tmpdir = tempfile.mkdtemp(prefix="esocial_upload_")
        _upload_session["active"] = True
        _upload_session["tmpdir"] = tmpdir
        _upload_session["files"] = []
        _upload_session["total_received"] = 0

    tmpdir = _upload_session["tmpdir"]

    saved = 0
    for upload_file in files:
        if not upload_file.filename:
            continue
        fname = upload_file.filename
        # Handle folder structure: "subdir/file.xml" → just use filename
        safe_name = os.path.basename(fname)
        if not safe_name.lower().endswith('.xml'):
            continue
        dest = os.path.join(tmpdir, safe_name)
        with open(dest, "wb") as out:
            content = await upload_file.read()
            out.write(content)
        _upload_session["files"].append(dest)
        saved += 1

    _upload_session["total_received"] += saved

    return {
        "saved": saved,
        "total_accumulated": _upload_session["total_received"],
    }


@router.post("/upload-start")
async def upload_start_import():
    """
    Finish uploading and start the import process.
    Auto-detects period from XML content.
    """
    if _import_progress["running"]:
        raise HTTPException(status_code=409, detail="Uma importação já está em andamento")

    if not _upload_session["active"] or not _upload_session["files"]:
        raise HTTPException(status_code=400, detail="Nenhum arquivo foi enviado. Use /upload-batch primeiro.")

    xml_files = _upload_session["files"]
    tmpdir = _upload_session["tmpdir"]

    # Auto-detect period from first few XMLs
    detected_periodo = None
    for fpath in xml_files[:20]:
        try:
            data, err = _parse_xml_file(fpath)
            if data and data.get("per_apur"):
                detected_periodo = data["per_apur"]
                break
        except Exception:
            continue

    logger.info(f"Upload import: {len(xml_files)} XMLs, periodo detectado: {detected_periodo}")

    # Initialize progress
    _import_progress["running"] = True
    _import_progress["total"] = len(xml_files)
    _import_progress["processed"] = 0
    _import_progress["errors"] = 0
    _import_progress["imported"] = 0
    _import_progress["last_error"] = ""
    _import_progress["elapsed"] = 0
    _import_progress["rate"] = 0
    _import_progress["finished"] = False
    _import_progress["result"] = None

    # Reset upload session
    _upload_session["active"] = False
    files_copy = list(xml_files)
    _upload_session["files"] = []
    _upload_session["total_received"] = 0

    pasta_label = f"upload ({len(files_copy)} arquivos)"

    # Launch background thread
    t = threading.Thread(
        target=_run_import_uploaded,
        args=(files_copy, tmpdir, detected_periodo, pasta_label),
        daemon=True,
    )
    t.start()

    return {
        "status": "started",
        "total": len(files_copy),
        "periodo_detectado": detected_periodo,
    }


@router.delete("/upload-cancel")
async def upload_cancel():
    """Cancel an upload session and clean up temp files."""
    if _upload_session["active"] and _upload_session["tmpdir"]:
        shutil.rmtree(_upload_session["tmpdir"], ignore_errors=True)
    _upload_session["active"] = False
    _upload_session["tmpdir"] = None
    _upload_session["files"] = []
    _upload_session["total_received"] = 0
    return {"status": "cancelled"}


def _run_import_uploaded(xml_files, tmpdir, periodo, pasta_label):
    """Wrapper that runs import from uploaded files and cleans up temp dir after."""
    try:
        _run_import(xml_files, pasta_label, periodo)
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)
        logger.info(f"Cleaned up temp dir: {tmpdir}")


def _run_import(xml_files, pasta, periodo):
    """Heavy import work — runs in a background thread."""
    start_time = time.time()
    conn = _get_conn()

    logger.info(f"Iniciando importação: {len(xml_files)} arquivos de {pasta}")

    try:
        with conn.cursor() as cur:
            # Create importacao record
            cur.execute(
                "INSERT INTO explorador_importacoes (pasta, periodo, total_arquivos) VALUES (%s, %s, %s) RETURNING id",
                (pasta, periodo, len(xml_files))
            )
            importacao_id = cur.fetchone()[0]
            _import_progress["importacao_id"] = importacao_id
            conn.commit()

            # Drop indexes for faster bulk insert (recreated after)
            cur.execute("DROP INDEX IF EXISTS idx_expl_eventos_cpf")
            cur.execute("DROP INDEX IF EXISTS idx_expl_eventos_tipo")
            cur.execute("DROP INDEX IF EXISTS idx_expl_eventos_per")
            cur.execute("DROP INDEX IF EXISTS idx_expl_eventos_recibo")
            cur.execute("DROP INDEX IF EXISTS idx_expl_rubricas_cod")
            cur.execute("DROP INDEX IF EXISTS idx_expl_rubricas_irrf")
            cur.execute("DROP INDEX IF EXISTS idx_expl_rubricas_evt")
            conn.commit()
            logger.info("Indexes dropped for bulk import")

            batch_size = 2000
            evento_batch = []
            rubrica_batch = []
            batch_evento_count = 0
            total_imported = 0
            total_errors = 0
            error_samples = []
            _indexes_dropped = True

            # Parse files in parallel using ThreadPool, insert in batches
            workers = min(8, os.cpu_count() or 4)
            chunk_size = 2000
            processed_count = 0

            with ThreadPoolExecutor(max_workers=workers) as pool:
              for chunk_start in range(0, len(xml_files), chunk_size):
                chunk = xml_files[chunk_start:chunk_start + chunk_size]

                futures = {pool.submit(_parse_file_wrapper, fp): fp for fp in chunk}
                for future in as_completed(futures):
                        filepath, data, err = future.result()
                        processed_count += 1

                        if data is None:
                            total_errors += 1
                            if err and len(error_samples) < 10:
                                error_samples.append(err)
                            _import_progress["last_error"] = err or "parse failed"
                        else:
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
                                json.dumps(data["dados_json"], ensure_ascii=False) if data["dados_json"] else None,
                            ))
                            batch_evento_count += 1

                            if data["rubricas"]:
                                for rub in data["rubricas"]:
                                    rubrica_batch.append((
                                        batch_evento_count - 1,
                                        rub.get("cod_rubr"),
                                        rub.get("ide_tab_rubr"),
                                        rub.get("nat_rubr"),
                                        rub.get("tp_rubr"),
                                        rub.get("cod_inc_cp"),
                                        rub.get("cod_inc_irrf"),
                                        rub.get("cod_inc_fgts"),
                                        float(rub["vr_rubr"]) if rub.get("vr_rubr") else None,
                                        rub.get("ind_ap_ir"),
                                    ))

                        # Update progress
                        elapsed = time.time() - start_time
                        _import_progress["processed"] = processed_count
                        _import_progress["errors"] = total_errors
                        _import_progress["imported"] = processed_count - total_errors
                        _import_progress["elapsed"] = round(elapsed, 1)
                        _import_progress["rate"] = round(processed_count / elapsed, 0) if elapsed > 0 else 0

                        # Flush batch
                        if len(evento_batch) >= batch_size:
                            _flush_batch(cur, evento_batch, rubrica_batch)
                            total_imported += len(evento_batch)
                            evento_batch = []
                            rubrica_batch = []
                            batch_evento_count = 0
                            conn.commit()

            # Final flush
            if evento_batch:
                _flush_batch(cur, evento_batch, rubrica_batch)
                total_imported += len(evento_batch)

            # Recreate indexes after bulk insert
            cur.execute("CREATE INDEX IF NOT EXISTS idx_expl_eventos_cpf ON explorador_eventos(cpf)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_expl_eventos_tipo ON explorador_eventos(tipo_evento)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_expl_eventos_per ON explorador_eventos(per_apur)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_expl_eventos_recibo ON explorador_eventos(nr_recibo)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_expl_rubricas_cod ON explorador_rubricas(cod_rubr)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_expl_rubricas_irrf ON explorador_rubricas(cod_inc_irrf)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_expl_rubricas_evt ON explorador_rubricas(evento_id)")
            logger.info("Indexes recreated after import")

        conn.commit()
        elapsed = time.time() - start_time

        logger.info(f"Importação concluída: {total_imported} importados, {total_errors} erros em {elapsed:.1f}s")
        if error_samples:
            logger.warning(f"Exemplos de erros: {error_samples[:3]}")

        _import_progress["result"] = {
            "importacao_id": importacao_id,
            "total_arquivos": len(xml_files),
            "importados": total_imported,
            "erros": total_errors,
            "tempo_seg": round(elapsed, 2),
        }

    except Exception as e:
        logger.error(f"Erro fatal na importação: {e}", exc_info=True)
        _import_progress["last_error"] = f"FATAL: {e}"

    finally:
        # Always recreate indexes even on crash
        try:
            with conn.cursor() as cur:
                cur.execute("CREATE INDEX IF NOT EXISTS idx_expl_eventos_cpf ON explorador_eventos(cpf)")
                cur.execute("CREATE INDEX IF NOT EXISTS idx_expl_eventos_tipo ON explorador_eventos(tipo_evento)")
                cur.execute("CREATE INDEX IF NOT EXISTS idx_expl_eventos_per ON explorador_eventos(per_apur)")
                cur.execute("CREATE INDEX IF NOT EXISTS idx_expl_eventos_recibo ON explorador_eventos(nr_recibo)")
                cur.execute("CREATE INDEX IF NOT EXISTS idx_expl_rubricas_cod ON explorador_rubricas(cod_rubr)")
                cur.execute("CREATE INDEX IF NOT EXISTS idx_expl_rubricas_irrf ON explorador_rubricas(cod_inc_irrf)")
                cur.execute("CREATE INDEX IF NOT EXISTS idx_expl_rubricas_evt ON explorador_rubricas(evento_id)")
            conn.commit()
            logger.info("Indexes ensured in finally block")
        except Exception as idx_err:
            logger.warning(f"Could not recreate indexes in finally: {idx_err}")
        conn.close()
        _import_progress["finished"] = True
        _import_progress["running"] = False


def _flush_batch(cur, evento_batch, rubrica_batch):
    """Insert a batch of events and their rubricas using execute_values (fast bulk insert)."""
    if not evento_batch:
        return

    # Insert events and get their IDs — execute_values is 2-5x faster than mogrify+VALUES
    new_ids = [row[0] for row in psycopg2.extras.execute_values(
        cur,
        """INSERT INTO explorador_eventos
            (importacao_id, tipo_evento, cpf, per_apur, nr_recibo, id_evento,
             dt_processamento, cd_resposta, arquivo_origem, dados_json)
        VALUES %s RETURNING id""",
        evento_batch,
        page_size=500,
        fetch=True,
    )]

    # Insert rubricas with correct evento_id
    if rubrica_batch:
        rub_inserts = []
        for (evt_idx, cod_rubr, ide_tab, nat, tp, cp, irrf, fgts, vr, ind_ir) in rubrica_batch:
            if evt_idx < len(new_ids):
                rub_inserts.append((
                    new_ids[evt_idx], cod_rubr, ide_tab, nat, tp, cp, irrf, fgts, vr, ind_ir
                ))

        if rub_inserts:
            psycopg2.extras.execute_values(
                cur,
                """INSERT INTO explorador_rubricas
                    (evento_id, cod_rubr, ide_tab_rubr, nat_rubr, tp_rubr,
                     cod_inc_cp, cod_inc_irrf, cod_inc_fgts, vr_rubr, ind_ap_ir)
                VALUES %s""",
                rub_inserts,
                page_size=500,
            )


@router.get("/progresso")
async def progresso_importacao():
    """Check import progress."""
    return _import_progress


# ── Query endpoints ─────────────────────────────────────────────────────────

@router.get("/importacoes")
async def listar_importacoes():
    """List all imports."""
    conn = _get_conn()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("""
                SELECT i.*,
                    (SELECT COUNT(*) FROM explorador_eventos WHERE importacao_id = i.id) as total_eventos,
                    (SELECT COUNT(DISTINCT cpf) FROM explorador_eventos WHERE importacao_id = i.id AND cpf IS NOT NULL) as cpfs_unicos
                FROM explorador_importacoes i
                ORDER BY i.importado_em DESC
            """)
            return cur.fetchall()
    finally:
        conn.close()


@router.delete("/importacoes/{importacao_id}")
async def deletar_importacao(importacao_id: int):
    """Delete an import and all its events."""
    conn = _get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM explorador_importacoes WHERE id = %s RETURNING id", (importacao_id,))
            if cur.fetchone() is None:
                raise HTTPException(status_code=404, detail="Importação não encontrada")
        conn.commit()
        return {"ok": True}
    finally:
        conn.close()


@router.get("/eventos")
async def buscar_eventos(
    cpf: Optional[str] = Query(None),
    tipo_evento: Optional[str] = Query(None),
    per_apur: Optional[str] = Query(None),
    cod_rubr: Optional[str] = Query(None),
    cod_inc_irrf: Optional[str] = Query(None),
    nr_recibo: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
):
    """Search events with filters. Supports pagination."""
    conn = _get_conn()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            conditions = []
            params = []

            if cpf:
                conditions.append("e.cpf = %s")
                params.append(cpf.replace(".", "").replace("-", "").strip())
            if tipo_evento:
                conditions.append("e.tipo_evento = %s")
                params.append(tipo_evento)
            if per_apur:
                conditions.append("e.per_apur = %s")
                params.append(per_apur)
            if nr_recibo:
                conditions.append("e.nr_recibo = %s")
                params.append(nr_recibo)

            # Rubrica-level filters require a JOIN
            join_rubricas = ""
            if cod_rubr or cod_inc_irrf:
                join_rubricas = "INNER JOIN explorador_rubricas r ON r.evento_id = e.id"
                if cod_rubr:
                    conditions.append("r.cod_rubr = %s")
                    params.append(cod_rubr)
                if cod_inc_irrf:
                    conditions.append("r.cod_inc_irrf = %s")
                    params.append(cod_inc_irrf)

            where = "WHERE " + " AND ".join(conditions) if conditions else ""
            offset = (page - 1) * page_size

            # Count total
            cur.execute(f"""
                SELECT COUNT(DISTINCT e.id)
                FROM explorador_eventos e
                {join_rubricas}
                {where}
            """, params)
            total = cur.fetchone()["count"]

            # Get events
            cur.execute(f"""
                SELECT DISTINCT e.*
                FROM explorador_eventos e
                {join_rubricas}
                {where}
                ORDER BY e.dt_processamento DESC NULLS LAST, e.id DESC
                LIMIT %s OFFSET %s
            """, params + [page_size, offset])
            eventos = cur.fetchall()

            # Get rubricas for these events
            if eventos:
                evt_ids = [e["id"] for e in eventos]
                cur.execute("""
                    SELECT * FROM explorador_rubricas
                    WHERE evento_id = ANY(%s)
                    ORDER BY evento_id, id
                """, (evt_ids,))
                rubricas = cur.fetchall()

                # Group by evento_id
                rub_map = {}
                for r in rubricas:
                    rub_map.setdefault(r["evento_id"], []).append(dict(r))

                for e in eventos:
                    e["rubricas"] = rub_map.get(e["id"], [])

            return {
                "total": total,
                "page": page,
                "page_size": page_size,
                "pages": (total + page_size - 1) // page_size if total > 0 else 0,
                "eventos": [dict(e) for e in eventos],
            }
    finally:
        conn.close()


@router.get("/estatisticas")
async def estatisticas(per_apur: Optional[str] = Query(None)):
    """Get statistics for the dashboard cards."""
    conn = _get_conn()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            where = ""
            params = []
            if per_apur:
                where = "WHERE per_apur = %s"
                params = [per_apur]

            # Total events by type
            cur.execute(f"""
                SELECT tipo_evento, COUNT(*) as total
                FROM explorador_eventos
                {where}
                GROUP BY tipo_evento
                ORDER BY total DESC
            """, params)
            por_tipo = cur.fetchall()

            # Total unique CPFs
            cur.execute(f"""
                SELECT COUNT(DISTINCT cpf) as total_cpfs
                FROM explorador_eventos
                {where.replace('per_apur', 'per_apur') if where else ''}
                {"AND" if where else "WHERE"} cpf IS NOT NULL
            """.replace("WHERE AND", "WHERE"), params)
            total_cpfs = cur.fetchone()["total_cpfs"]

            # Available periods
            cur.execute("""
                SELECT DISTINCT per_apur
                FROM explorador_eventos
                WHERE per_apur IS NOT NULL
                ORDER BY per_apur DESC
            """)
            periodos = [r["per_apur"] for r in cur.fetchall()]

            # Total events
            cur.execute(f"SELECT COUNT(*) as total FROM explorador_eventos {where}", params)
            total_eventos = cur.fetchone()["total"]

            # Rubricas with codIncIRRF=11 (problem indicator)
            irrf_where = where.replace("per_apur", "e.per_apur") if where else ""
            cur.execute(f"""
                SELECT COUNT(DISTINCT e.cpf) as cpfs_afetados
                FROM explorador_eventos e
                INNER JOIN explorador_rubricas r ON r.evento_id = e.id
                {irrf_where.replace("WHERE", "WHERE r.cod_inc_irrf = '11' AND") if irrf_where else "WHERE r.cod_inc_irrf = '11'"}
            """, params)
            cpfs_irrf11 = cur.fetchone()["cpfs_afetados"]

            return {
                "total_eventos": total_eventos,
                "total_cpfs": total_cpfs,
                "periodos": periodos,
                "por_tipo": por_tipo,
                "cpfs_irrf_11": cpfs_irrf11,
            }
    finally:
        conn.close()


@router.get("/cpfs")
async def listar_cpfs(
    q: Optional[str] = Query(None),
    per_apur: Optional[str] = Query(None),
    limit: int = Query(20, ge=1, le=100),
):
    """Search CPFs for autocomplete."""
    conn = _get_conn()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            conditions = ["cpf IS NOT NULL"]
            params = []

            if q:
                clean = q.replace(".", "").replace("-", "").strip()
                conditions.append("cpf LIKE %s")
                params.append(f"%{clean}%")
            if per_apur:
                conditions.append("per_apur = %s")
                params.append(per_apur)

            where = "WHERE " + " AND ".join(conditions)

            cur.execute(f"""
                SELECT cpf, COUNT(*) as total_eventos
                FROM explorador_eventos
                {where}
                GROUP BY cpf
                ORDER BY total_eventos DESC
                LIMIT %s
            """, params + [limit])
            return cur.fetchall()
    finally:
        conn.close()


# ── Dados Funcionários endpoints ────────────────────────────────────────────

@router.get("/dados-funcionarios/estatisticas")
async def dados_funcionarios_stats(per_apur: Optional[str] = Query(None)):
    """Employee data statistics — S-1200 and S-1210 aggregation."""
    conn = _get_conn()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            conditions = ["e.tipo_evento IN ('S-1200', 'S-1210')"]
            params = []
            if per_apur:
                conditions.append("e.per_apur = %s")
                params.append(per_apur)
            where = "WHERE " + " AND ".join(conditions)

            cur.execute(f"""
                SELECT
                    COUNT(DISTINCT e.cpf) FILTER (WHERE e.cpf IS NOT NULL) as total_cpfs,
                    COUNT(*) FILTER (WHERE e.tipo_evento = 'S-1200') as total_s1200,
                    COUNT(*) FILTER (WHERE e.tipo_evento = 'S-1210') as total_s1210,
                    COUNT(DISTINCT e.cpf) FILTER (WHERE e.tipo_evento = 'S-1200' AND e.cpf IS NOT NULL) as cpfs_com_s1200,
                    COUNT(DISTINCT e.cpf) FILTER (WHERE e.tipo_evento = 'S-1210' AND e.cpf IS NOT NULL) as cpfs_com_s1210,
                    COUNT(DISTINCT e.per_apur) as total_periodos,
                    COUNT(DISTINCT e.cpf) FILTER (
                        WHERE e.tipo_evento = 'S-1210'
                        AND e.dados_json->>'indRetif' = '2'
                    ) as cpfs_retificados
                FROM explorador_eventos e
                {where}
            """, params)
            row = cur.fetchone()

            # Available periods (from S-1200/S-1210 only)
            cur.execute(f"""
                SELECT DISTINCT e.per_apur
                FROM explorador_eventos e
                {where} AND e.per_apur IS NOT NULL
                ORDER BY e.per_apur DESC
            """, params)
            row["periodos"] = [r["per_apur"] for r in cur.fetchall()]

            return row
    finally:
        conn.close()


@router.get("/dados-funcionarios")
async def dados_funcionarios(
    per_apur: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    cpf: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
):
    """Aggregate employee data per CPF for S-1200 and S-1210 events."""
    conn = _get_conn()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            conditions = ["e.tipo_evento IN ('S-1200', 'S-1210')", "e.cpf IS NOT NULL"]
            params = []
            if per_apur:
                conditions.append("e.per_apur = %s")
                params.append(per_apur)
            if cpf:
                clean = cpf.replace(".", "").replace("-", "").strip()
                conditions.append("e.cpf LIKE %s")
                params.append(f"%{clean}%")
            where = "WHERE " + " AND ".join(conditions)

            # Count total unique CPFs
            cur.execute(f"""
                SELECT COUNT(DISTINCT e.cpf) as total
                FROM explorador_eventos e
                {where}
            """, params)
            total = cur.fetchone()["total"]

            # Get per-CPF aggregation
            offset = (page - 1) * page_size
            having_clause = ""
            if status == "retificado":
                having_clause = "HAVING bool_or(e.tipo_evento = 'S-1210' AND (e.dados_json->>'indRetif') = '2')"
            elif status == "pendente":
                having_clause = "HAVING NOT bool_or(e.tipo_evento = 'S-1210' AND (e.dados_json->>'indRetif') = '2')"

            cur.execute(f"""
                SELECT
                    e.cpf,
                    COUNT(*) FILTER (WHERE e.tipo_evento = 'S-1200') as qtd_s1200,
                    COUNT(*) FILTER (WHERE e.tipo_evento = 'S-1210') as qtd_s1210,
                    MAX(CASE WHEN e.tipo_evento = 'S-1200' THEN e.dados_json->>'matricula' END) as matricula,
                    MAX(CASE WHEN e.tipo_evento = 'S-1200' THEN e.dados_json->>'codCateg' END) as cod_categ,
                    MAX(CASE WHEN e.tipo_evento = 'S-1200' THEN e.dados_json->>'ideDmDev' END) as ide_dm_dev_s1200,
                    MAX(CASE WHEN e.tipo_evento = 'S-1210' THEN e.dados_json->>'dtPgto' END) as dt_pgto,
                    MAX(CASE WHEN e.tipo_evento = 'S-1210' THEN e.dados_json->>'vrLiq' END) as vr_liq,
                    MAX(CASE WHEN e.tipo_evento = 'S-1210' THEN e.dados_json->>'tpCR' END) as tp_cr,
                    bool_or(e.tipo_evento = 'S-1210' AND (e.dados_json->>'indRetif') = '2') as retificado,
                    ARRAY_AGG(DISTINCT e.per_apur) FILTER (WHERE e.per_apur IS NOT NULL) as periodos,
                    MAX(e.nr_recibo) FILTER (WHERE e.tipo_evento = 'S-1210') as nr_recibo_s1210,
                    MAX(e.dt_processamento) as ultimo_processamento
                FROM explorador_eventos e
                {where}
                GROUP BY e.cpf
                {having_clause}
                ORDER BY e.cpf
                LIMIT %s OFFSET %s
            """, params + [page_size, offset])
            rows = cur.fetchall()

            # If using HAVING, recalculate total
            if having_clause:
                cur.execute(f"""
                    SELECT COUNT(*) as cnt FROM (
                        SELECT e.cpf
                        FROM explorador_eventos e
                        {where}
                        GROUP BY e.cpf
                        {having_clause}
                    ) sub
                """, params)
                total = cur.fetchone()["cnt"]

            return {
                "total": total,
                "page": page,
                "page_size": page_size,
                "total_pages": (total + page_size - 1) // page_size if total > 0 else 0,
                "items": rows,
            }
    finally:
        conn.close()


@router.get("/dados-funcionarios/{cpf_param}")
async def dados_funcionario_detalhe(cpf_param: str, per_apur: Optional[str] = Query(None)):
    """Detailed S-1200 and S-1210 events for a specific CPF."""
    conn = _get_conn()
    cpf_clean = cpf_param.replace(".", "").replace("-", "").strip()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            conditions = ["e.cpf = %s", "e.tipo_evento IN ('S-1200', 'S-1210')"]
            params = [cpf_clean]
            if per_apur:
                conditions.append("e.per_apur = %s")
                params.append(per_apur)
            where = "WHERE " + " AND ".join(conditions)

            cur.execute(f"""
                SELECT e.*
                FROM explorador_eventos e
                {where}
                ORDER BY e.tipo_evento, e.dt_processamento DESC NULLS LAST
            """, params)
            eventos = cur.fetchall()

            # Get rubricas for these events
            if eventos:
                evt_ids = [ev["id"] for ev in eventos]
                cur.execute("""
                    SELECT * FROM explorador_rubricas
                    WHERE evento_id = ANY(%s)
                    ORDER BY evento_id, id
                """, (evt_ids,))
                rubricas = cur.fetchall()
                rub_map = {}
                for r in rubricas:
                    rub_map.setdefault(r["evento_id"], []).append(dict(r))
                for ev in eventos:
                    ev["rubricas"] = rub_map.get(ev["id"], [])

            return eventos
    finally:
        conn.close()
