"""
Configuração centralizada de banco de dados.

DB_CONFIG       → Supabase (banco principal na nuvem)
LOCAL_DB_CONFIG → PostgreSQL local (apenas certificados A1)
"""
import os
from pathlib import Path

# Carregar .env se existir
_env_path = Path(__file__).parent / ".env"
if _env_path.exists():
    with open(_env_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, _, value = line.partition("=")
                os.environ.setdefault(key.strip(), value.strip())

# Supabase (Session Pooler) — banco principal
DB_CONFIG = {
    "host": os.environ.get("DB_HOST", "localhost"),
    "port": int(os.environ.get("DB_PORT", "5432")),
    "database": os.environ.get("DB_NAME", "easy_social_db"),
    "user": os.environ.get("DB_USER", "easy_social_user"),
    "password": os.environ.get("DB_PASSWORD", "sua_senha_segura"),
}

# Adicionar sslmode para Supabase (se DB_SSL=true)
if os.environ.get("DB_SSL", "").lower() == "true":
    DB_CONFIG["sslmode"] = "require"

# PostgreSQL LOCAL — exclusivo para certificados A1
LOCAL_DB_CONFIG = {
    "host": os.environ.get("LOCAL_DB_HOST", "localhost"),
    "port": int(os.environ.get("LOCAL_DB_PORT", "5432")),
    "database": os.environ.get("LOCAL_DB_NAME", "easy_social_db"),
    "user": os.environ.get("LOCAL_DB_USER", "easy_social_user"),
    "password": os.environ.get("LOCAL_DB_PASSWORD", "sua_senha_segura"),
}

if os.environ.get("LOCAL_DB_SSL", "").lower() == "true":
    LOCAL_DB_CONFIG["sslmode"] = "require"
