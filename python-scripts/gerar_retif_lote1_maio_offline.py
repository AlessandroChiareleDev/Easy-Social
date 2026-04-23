"""
Gerador OFFLINE de XML de retificacao S-1210 para Lote 1 / 2025-05.

USA O GERADOR PADRAO `S1210XMLGenerator.gerar()` - mesmo do Lote 3.
NAO copia inner do XML do ZIP. So extrai info_pgtos + info_ir_complem.
"""
import csv
import json
import os
import sys
import zipfile
from collections import defaultdict
from io import BytesIO

from lxml import etree

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from esocial.xml_s1210 import S1210XMLGenerator
from esocial.xml_payload_parser import extrair_s1210, extrair_s1210_ir_complem

ROOT      = os.path.dirname(os.path.abspath(__file__))
OUT_DIR   = os.path.join(ROOT, "saida_retif_lote1_maio")
XML_DIR   = os.path.join(OUT_DIR, "xml")
INDICE    = os.path.join(OUT_DIR, "_indice_s1210_maio.json")
ZIP_PATH  = r"C:\Users\NITRO\Downloads\29429551-maio.zip"
REPORT    = os.path.join(OUT_DIR, "relatorio.csv")

PERAPUR_ALVO = "2025-05"
EMPREGADOR = {"tpInsc": 1, "nrInsc": "05969071"}
TP_AMB = "1"  # producao

os.makedirs(XML_DIR, exist_ok=True)


def _navigate_inner(root):
    """Acha o elemento <evtPgtos> dentro do XML do ZIP (envelope de retorno)."""
    for el in root.iter():
        if etree.QName(el).localname == "evtPgtos":
            return el
    return None


def main() -> None:
    if not os.path.exists(INDICE):
        raise SystemExit(f"Indice nao encontrado: {INDICE}.")
    print(f"Carregando indice: {INDICE}")
    idx = json.load(open(INDICE, encoding="utf-8"))
    s1210 = idx["s1210"]
    print(f"  S-1210 totais : {len(s1210)}")

    eventos_05 = [e for e in s1210 if e["perApur"] == PERAPUR_ALVO]
    print(f"  S-1210 em {PERAPUR_ALVO}: {len(eventos_05)}")

    por_cpf = defaultdict(list)
    for e in eventos_05:
        por_cpf[e["cpf"]].append(e)
    print(f"  CPFs distintos: {len(por_cpf)}")

    sem_ativo = 0
    multi_ativo = 0
    gerados = 0
    falhas = 0
    rows = []

    with zipfile.ZipFile(ZIP_PATH) as z:
        for seq_idx, (cpf, evs) in enumerate(por_cpf.items(), start=1):
            ativos = [e for e in evs if e["ativo"]]
            if not ativos:
                sem_ativo += 1
                rows.append({"cpf": cpf, "status": "SEM_ATIVO", "recibo_escolhido": "", "n_ativos": 0, "xml": ""})
                continue
            if len(ativos) > 1:
                multi_ativo += 1
            escolhido = max(ativos, key=lambda e: e["dhProc"] or "")
            try:
                with z.open(escolhido["xml"]) as f:
                    raw = f.read()
                tree = etree.parse(BytesIO(raw))
                evt = _navigate_inner(tree.getroot())
                if evt is None:
                    raise ValueError("evtPgtos nao encontrado")

                info_pgtos = extrair_s1210(evt)
                info_ir = extrair_s1210_ir_complem(evt)
                if not info_pgtos:
                    raise ValueError("info_pgtos vazio")

                xml_bytes = S1210XMLGenerator.gerar(
                    empregador=EMPREGADOR,
                    beneficiario={"cpfBenef": cpf},
                    info_pgtos=info_pgtos,
                    per_apur=PERAPUR_ALVO,
                    ind_retif="2",
                    nr_recibo=escolhido["nrRecibo"],
                    info_ir_complem=info_ir,
                    plan_saude=None,
                    seq=seq_idx,
                    tp_amb=TP_AMB,
                )

                out_path = os.path.join(XML_DIR, f"{cpf}.xml")
                with open(out_path, "wb") as f:
                    f.write(xml_bytes)
                gerados += 1
                rows.append({
                    "cpf": cpf,
                    "status": "OK",
                    "recibo_escolhido": escolhido["nrRecibo"],
                    "n_ativos": len(ativos),
                    "xml": os.path.relpath(out_path, OUT_DIR),
                })
            except Exception as e:
                falhas += 1
                rows.append({"cpf": cpf, "status": f"FALHA: {e}", "recibo_escolhido": "", "n_ativos": len(ativos), "xml": ""})

    with open(REPORT, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["cpf", "status", "recibo_escolhido", "n_ativos", "xml"])
        w.writeheader()
        w.writerows(rows)

    print()
    print("=== RESULTADO ===")
    print(f"  Gerados:         {gerados}")
    print(f"  Sem ativo:       {sem_ativo}")
    print(f"  Multi ativo:     {multi_ativo}")
    print(f"  Falhas:          {falhas}")
    print(f"  Relatorio:       {REPORT}")
    print(f"  XMLs em:         {XML_DIR}")


if __name__ == "__main__":
    main()
