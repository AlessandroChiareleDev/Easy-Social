from __future__ import annotations

import enviar_fechamento_janeiro_objetiva_s1299 as base

base.PER_APUR = "2025-03"
base.CONFIRM_TOKEN = "FECHAR_MARCO_OBJETIVA_S1299"
base.OUT_DIR = base.ROOT / "relatorio_ana" / "OBJETIVA_JAN_MAI_2025" / "fechamento_marco_s1299"
base.XML_UNSIGNED = base.OUT_DIR / "S1299_2025-03_OBJETIVA_unsigned.xml"
base.XML_SIGNED = base.OUT_DIR / "S1299_2025-03_OBJETIVA_signed.xml"
base.MANIFEST = base.OUT_DIR / "manifest_fechamento_s1299_marco_objetiva.json"


if __name__ == "__main__":
    raise SystemExit(base.main())