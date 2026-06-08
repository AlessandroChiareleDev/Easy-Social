from __future__ import annotations

import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent / "OBJETIVA_JAN_MAI_2025"
sys.path.insert(0, str(BASE_DIR))

import enviar_67_fevereiro_persistir_v2 as base

base.PER_APUR = "2025-12"
base.OUT_ROOT = base.ROOT / "relatorio_ana" / "OBJETIVA_DEZEMBRO_2025" / "xmls_dezembro_72_corrigidos"
base.MANIFEST = base.OUT_ROOT / "manifest_72_xmls_corrigidos.json"
base.RUN_DIR = base.OUT_ROOT / "retorno_envio_72_dezembro"
base.RESULT_PATH = base.RUN_DIR / "resultado_envio_72_dezembro.json"


if __name__ == "__main__":
    base.main()