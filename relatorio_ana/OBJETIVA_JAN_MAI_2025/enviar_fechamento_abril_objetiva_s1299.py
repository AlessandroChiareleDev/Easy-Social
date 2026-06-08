from __future__ import annotations

import enviar_fechamento_janeiro_objetiva_s1299 as base

base.PER_APUR = "2025-04"
base.CONFIRM_TOKEN = "FECHAR_ABRIL_OBJETIVA_S1299"
base.OUT_DIR = base.ROOT / "relatorio_ana" / "OBJETIVA_JAN_MAI_2025" / "fechamento_abril_s1299"
base.XML_UNSIGNED = base.OUT_DIR / "S1299_2025-04_OBJETIVA_unsigned.xml"
base.XML_SIGNED = base.OUT_DIR / "S1299_2025-04_OBJETIVA_signed.xml"
base.MANIFEST = base.OUT_DIR / "manifest_fechamento_s1299_abril_objetiva.json"


if __name__ == "__main__":
    raise SystemExit(base.main())