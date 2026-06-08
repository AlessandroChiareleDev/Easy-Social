from __future__ import annotations

import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1] / "OBJETIVA_JAN_MAI_2025"
sys.path.insert(0, str(BASE_DIR))

import enviar_67_fevereiro_persistir_v2 as base

base.PER_APUR = "2025-10"
base.OUT_ROOT = base.ROOT / "relatorio_ana" / "OBJETIVA_JUN_NOV_2025" / "2025-10" / "xmls_outubro_93_corrigidos"
base.MANIFEST = base.OUT_ROOT / "manifest_93_xmls_corrigidos.json"
base.RUN_DIR = base.OUT_ROOT / "retorno_envio_93_outubro"
base.RESULT_PATH = base.RUN_DIR / "resultado_envio_93_outubro.json"


if __name__ == "__main__":
    base.main()