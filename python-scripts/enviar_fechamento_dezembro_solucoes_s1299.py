from __future__ import annotations

import enviar_fechamento_agosto_solucoes_s1299 as base


base.PER_APUR = "2025-12"
base.CONFIRM_TOKEN = "FECHAR_DEZEMBRO_SOLUCOES_S1299"
base.OUT_DIR = base.ROOT / "relatorio_ana" / "FECHAMENTO_DEZEMBRO_SOLUCOES"
base.XML_UNSIGNED = base.OUT_DIR / "S1299_2025-12_SOLUCOES_unsigned.xml"
base.XML_SIGNED = base.OUT_DIR / "S1299_2025-12_SOLUCOES_signed.xml"
base.MANIFEST = base.OUT_DIR / "manifest_fechamento_s1299_dezembro_solucoes.json"


if __name__ == "__main__":
    raise SystemExit(base.main())