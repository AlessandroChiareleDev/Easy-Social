"""
Multi-tenant: roteia conexao para o banco correto dado um empresa_id.

Convencao:
  empresa_id=1  -> APPA      -> SUPABASE  (DB_CONFIG)
  empresa_id=2  -> SOLUCOES  -> LOCAL Postgres database 'easy_social_solucoes'

Outros empresa_id futuros leem master_empresas.db_name no Supabase
e usam Postgres LOCAL (host/port/user da LOCAL_DB_CONFIG).
"""
from __future__ import annotations
from typing import Optional
import psycopg2
from db_config import DB_CONFIG, LOCAL_DB_CONFIG

DEFAULT_EMPRESA_ID = 1


def _local_with_db(db_name: str) -> dict:
    cfg = dict(LOCAL_DB_CONFIG)
    cfg["database"] = db_name
    return cfg


def get_db_config_for_empresa(empresa_id: Optional[int]) -> dict:
    """Retorna o DB_CONFIG dict adequado pra empresa.

    Empresa 1 (APPA) fica no Supabase pra nao quebrar V1.
    Empresa 2 (SOLUCOES) e demais futuras vao pra LOCAL/<db_name>.
    """
    eid = int(empresa_id) if empresa_id is not None else DEFAULT_EMPRESA_ID
    if eid == 1:
        return DB_CONFIG
    if eid == 2:
        return _local_with_db("easy_social_solucoes")
    # fallback: le master_empresas.db_name no Supabase
    try:
        with psycopg2.connect(**DB_CONFIG) as c:
            with c.cursor() as cur:
                cur.execute("SELECT db_name FROM master_empresas WHERE id=%s", (eid,))
                row = cur.fetchone()
        if row and row[0]:
            return _local_with_db(row[0])
    except Exception:
        pass
    return DB_CONFIG


def connect_for_empresa(empresa_id: Optional[int]):
    cfg = get_db_config_for_empresa(empresa_id)
    conn = psycopg2.connect(**cfg)
    conn.autocommit = False
    return conn


def db_kind_for_empresa(empresa_id: Optional[int]) -> str:
    cfg = get_db_config_for_empresa(empresa_id)
    host = (cfg.get("host") or "").lower()
    return "supabase" if "supabase" in host else "local"
