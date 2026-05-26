from __future__ import annotations

import enviar_fechamento_agosto_solucoes_s1299 as base


base.PER_APUR = "2025-11"
base.CONFIRM_TOKEN = "FECHAR_NOVEMBRO_SOLUCOES_S1299"
base.OUT_DIR = base.ROOT / "relatorio_ana" / "FECHAMENTO_NOVEMBRO_SOLUCOES"
base.XML_UNSIGNED = base.OUT_DIR / "S1299_2025-11_SOLUCOES_unsigned.xml"
base.XML_SIGNED = base.OUT_DIR / "S1299_2025-11_SOLUCOES_signed.xml"
base.MANIFEST = base.OUT_DIR / "manifest_fechamento_s1299_novembro_solucoes.json"


if __name__ == "__main__":
    raise SystemExit(base.main())