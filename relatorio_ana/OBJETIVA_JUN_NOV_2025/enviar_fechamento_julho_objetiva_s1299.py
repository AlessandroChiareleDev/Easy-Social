from __future__ import annotations

import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1] / "OBJETIVA_JAN_MAI_2025"
sys.path.insert(0, str(BASE_DIR))

import enviar_fechamento_janeiro_objetiva_s1299 as base

base.PER_APUR = "2025-07"
base.CONFIRM_TOKEN = "FECHAR_JULHO_OBJETIVA_S1299"
base.OUT_DIR = base.ROOT / "relatorio_ana" / "OBJETIVA_JUN_NOV_2025" / "2025-07" / "fechamento_julho_s1299"
base.XML_UNSIGNED = base.OUT_DIR / "S1299_2025-07_OBJETIVA_unsigned.xml"
base.XML_SIGNED = base.OUT_DIR / "S1299_2025-07_OBJETIVA_signed.xml"
base.MANIFEST = base.OUT_DIR / "manifest_fechamento_s1299_julho_objetiva.json"


if __name__ == "__main__":
    raise SystemExit(base.main())