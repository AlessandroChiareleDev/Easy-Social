"""
API REST para gestão de certificados A1 — eSocial
Endpoints: upload, listar ativo, remover

Integra com bot_api.py (mesma instância FastAPI na porta 8000).
"""

from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from .certificate_manager import CertificateManager
import psycopg2
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from db_config import LOCAL_DB_CONFIG

router = APIRouter(prefix="/api/certificados", tags=["certificados"])

# Certificados ficam SEMPRE no banco LOCAL (nunca na nuvem)
DB_CONFIG = LOCAL_DB_CONFIG

INIT_SQL = """
CREATE TABLE IF NOT EXISTS certificados_a1 (
    id SERIAL PRIMARY KEY,
    cnpj VARCHAR(14) NOT NULL,
    titular VARCHAR(255),
    emissor VARCHAR(255),
    numero_serie VARCHAR(100),
    validade_inicio TIMESTAMP,
    validade_fim TIMESTAMP,
    arquivo_path VARCHAR(500) NOT NULL,
    senha_encrypted TEXT NOT NULL,
    ativo BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS senha_certificado_salva (
    id SERIAL PRIMARY KEY,
    senha_encrypted TEXT NOT NULL,
    saved_at TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP NOT NULL
);
"""


def _get_conn():
    return psycopg2.connect(**DB_CONFIG)


def _ensure_table():
    conn = _get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(INIT_SQL)
        conn.commit()
    finally:
        conn.close()


_ensure_table()


@router.post("/upload")
async def upload_certificate(file: UploadFile = File(...), senha: str = Form(default="")):
    fname = (file.filename or "").lower()
    if not fname.endswith(".pfx") and not fname.endswith(".p12"):
        raise HTTPException(status_code=400, detail="Arquivo deve ser .pfx ou .p12")

    pfx_data = await file.read()
    if len(pfx_data) == 0:
        raise HTTPException(status_code=400, detail="Arquivo vazio")

    # Se não informou senha, tentar usar a senha salva
    if not senha:
        saved = _get_saved_senha()
        if not saved:
            raise HTTPException(status_code=400, detail="Senha não informada e nenhuma senha salva encontrada")
        senha = saved

    try:
        info = CertificateManager.validate_pfx(pfx_data, senha)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Certificado inv\u00e1lido: {e}")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Erro ao ler certificado: {type(e).__name__}: {e}")

    try:
        filepath = CertificateManager.save_certificate(
            pfx_data, info["cnpj"] or "unknown", info["numero_serie"]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao salvar arquivo: {type(e).__name__}: {e}")

    senha_encrypted = CertificateManager.encrypt_password(senha)

    try:
        conn = _get_conn()
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Banco de dados indispon\u00edvel: {type(e).__name__}: {e}")

    try:
        with conn.cursor() as cur:
            # Desativar certificados anteriores
            cur.execute("UPDATE certificados_a1 SET ativo = FALSE WHERE ativo = TRUE")
            cur.execute(
                """INSERT INTO certificados_a1
                   (cnpj, titular, emissor, numero_serie, validade_fim,
                    arquivo_path, senha_encrypted, ativo)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, TRUE)
                   RETURNING id""",
                (
                    info["cnpj"],
                    info["nome_titular"],
                    info["emissor"],
                    info["numero_serie"],
                    info["validade"],
                    filepath,
                    senha_encrypted,
                ),
            )
            cert_id = cur.fetchone()[0]
        conn.commit()
    finally:
        conn.close()

    return {
        "id": cert_id,
        "cnpj": info["cnpj"],
        "titular": info["nome_titular"],
        "emissor": info["emissor"],
        "validade": info["validade"].isoformat(),
        "ativo": True,
    }


@router.get("/ativo")
async def get_active_certificate():
    conn = _get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """SELECT id, cnpj, titular, emissor, numero_serie,
                          validade_fim, ativo, created_at
                   FROM certificados_a1
                   WHERE ativo = TRUE
                   LIMIT 1"""
            )
            row = cur.fetchone()
    finally:
        conn.close()

    if not row:
        raise HTTPException(status_code=404, detail="Nenhum certificado ativo")

    return {
        "id": row[0],
        "cnpj": row[1],
        "titular": row[2],
        "emissor": row[3],
        "numero_serie": row[4],
        "validade": row[5].isoformat() if row[5] else None,
        "ativo": row[6],
        "created_at": row[7].isoformat() if row[7] else None,
    }


@router.delete("/{cert_id}")
async def delete_certificate(cert_id: int):
    conn = _get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT arquivo_path FROM certificados_a1 WHERE id = %s", (cert_id,)
            )
            row = cur.fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="Certificado não encontrado")

            filepath = row[0]
            if filepath and os.path.exists(filepath):
                os.remove(filepath)

            cur.execute("DELETE FROM certificados_a1 WHERE id = %s", (cert_id,))
        conn.commit()
    finally:
        conn.close()

    return {"deleted": True, "id": cert_id}


# ── Senha salva ───────────────────────────────────────────────────

def _get_saved_senha() -> str | None:
    """Retorna a senha salva (decriptada) se existir e não estiver expirada."""
    conn = _get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT senha_encrypted FROM senha_certificado_salva "
                "WHERE expires_at > NOW() ORDER BY id DESC LIMIT 1"
            )
            row = cur.fetchone()
    finally:
        conn.close()
    if not row:
        return None
    return CertificateManager.decrypt_password(row[0])


@router.post("/senha/salvar")
async def salvar_senha(senha: str = Form(...), duracao_horas: int = Form(default=24)):
    """Salva a senha do certificado para uso futuro (padrão 24h)."""
    if duracao_horas < 1 or duracao_horas > 720:
        raise HTTPException(status_code=400, detail="Duração deve ser entre 1 e 720 horas")

    senha_encrypted = CertificateManager.encrypt_password(senha)
    conn = _get_conn()
    try:
        with conn.cursor() as cur:
            # Remove senhas anteriores
            cur.execute("DELETE FROM senha_certificado_salva")
            cur.execute(
                "INSERT INTO senha_certificado_salva (senha_encrypted, expires_at) "
                "VALUES (%s, NOW() + make_interval(hours => %s)) "
                "RETURNING saved_at, expires_at",
                (senha_encrypted, duracao_horas),
            )
            row = cur.fetchone()
        conn.commit()
    finally:
        conn.close()

    return {
        "saved": True,
        "saved_at": row[0].isoformat(),
        "expires_at": row[1].isoformat(),
    }


@router.get("/senha/status")
async def status_senha():
    """Verifica se existe uma senha salva e válida."""
    conn = _get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT saved_at, expires_at FROM senha_certificado_salva "
                "WHERE expires_at > NOW() ORDER BY id DESC LIMIT 1"
            )
            row = cur.fetchone()
    finally:
        conn.close()

    if not row:
        return {"saved": False}

    return {
        "saved": True,
        "saved_at": row[0].isoformat(),
        "expires_at": row[1].isoformat(),
    }


@router.delete("/senha/remover")
async def remover_senha():
    """Remove a senha salva."""
    conn = _get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM senha_certificado_salva")
        conn.commit()
    finally:
        conn.close()

    return {"removed": True}
