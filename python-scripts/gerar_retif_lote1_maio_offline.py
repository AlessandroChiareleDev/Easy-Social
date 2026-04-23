"""
Gerador OFFLINE de XML de retificacao S-1210 para Lote 1 / 2025-05.

NAO ENVIA NADA. Apenas:
1. Le o ZIP `29429551-maio.zip` (cache via _indice_s1210_maio.json)
2. Pra cada CPF com >=1 recibo ATIVO em 2025-05 (S-5002 presente):
   - Escolhe o recibo ATIVO mais recente (dhProc max)
   - Extrai <evtPgtos> do XML original
   - Transforma em retificacao:
       indRetif = 2
       nrRecibo (do S-1210 a retificar) - tag nova
       remove qualquer detPlanSaude (Lote 1 = sem plano saude)
       gera novo Id (placeholder)
   - NAO assina (sera assinado em outra etapa antes do envio)
   - Salva em saida_retif_lote1_maio/xml/<cpf>.xml
3. Gera relatorio CSV em saida_retif_lote1_maio/relatorio.csv

Autorizado pelo PC1 em Mensagem-PC1-11.md.
"""
import csv
import json
import os
import re
import zipfile
from collections import defaultdict
from datetime import datetime

ROOT      = os.path.dirname(os.path.abspath(__file__))
OUT_DIR   = os.path.join(ROOT, "saida_retif_lote1_maio")
XML_DIR   = os.path.join(OUT_DIR, "xml")
INDICE    = os.path.join(OUT_DIR, "_indice_s1210_maio.json")
ZIP_PATH  = r"C:\Users\NITRO\Downloads\29429551-maio.zip"
REPORT    = os.path.join(OUT_DIR, "relatorio.csv")

PERAPUR_ALVO = "2025-05"

os.makedirs(XML_DIR, exist_ok=True)

# Captura tudo dentro de <evtPgtos ...>...</evtPgtos>
RE_EVTPGTOS = re.compile(r"<evtPgtos\b[^>]*>(.*?)</evtPgtos>", re.DOTALL)
RE_EVT_ID   = re.compile(r'<evtPgtos\s+Id="([^"]+)"')
# Para remover qualquer bloco de plano de saude (Lote 1 nao deve ter)
RE_DETPLANSAUDE = re.compile(r"<detPlanSaude>.*?</detPlanSaude>", re.DOTALL)
RE_INFOPLANSAUDE = re.compile(r"<infoPlanSaude>.*?</infoPlanSaude>", re.DOTALL)
# indRetif e perApur (dentro de ideEvento)
RE_IDEEVENTO = re.compile(r"<ideEvento>(.*?)</ideEvento>", re.DOTALL)


def construir_id_retif(cnpj8: str = "05969071") -> str:
    """Gera Id placeholder no padrao do eSocial (40 chars).
    Formato: ID + 1 (tpInsc) + cnpj com 14 digitos + AAAAMMDDHHMMSS + sequencial 5 digitos
    """
    ts = datetime.now().strftime("%Y%m%d%H%M%S")
    nr = "00000"
    return f"ID1{cnpj8.ljust(14, '0')}{ts}{nr}"


def transformar_para_retif(evtpgtos_inner: str, nrRecibo_a_retif: str, novo_id: str) -> str:
    """Recebe o conteudo INTERNO de <evtPgtos>...</evtPgtos> do XML original
    e devolve o XML retif completo (string), pronto pra empacotar/assinar depois.
    """
    inner = evtpgtos_inner

    # 1) Remover plano de saude (Lote 1)
    inner = RE_DETPLANSAUDE.sub("", inner)
    inner = RE_INFOPLANSAUDE.sub("", inner)

    # 2) Trocar indRetif=1 por indRetif=2 dentro de ideEvento
    def _sub_ideevento(m: re.Match) -> str:
        ide = m.group(1)
        # forcar indRetif=2
        if "<indRetif>" in ide:
            ide = re.sub(r"<indRetif>\d+</indRetif>", "<indRetif>2</indRetif>", ide)
        else:
            ide = "<indRetif>2</indRetif>" + ide
        # garantir nrRecibo (tag opcional - obrigatoria em retif)
        if "<nrRecibo>" in ide:
            ide = re.sub(r"<nrRecibo>[\d.]+</nrRecibo>", f"<nrRecibo>{nrRecibo_a_retif}</nrRecibo>", ide)
        else:
            # inserir antes de </ideEvento>; o leiaute manda colocar APOS perApur
            # ordem leiaute v_S_01_03_00: indRetif, nrRecibo?, indApuracao, perApur, tpAmb, procEmi, verProc
            ide = re.sub(
                r"(</perApur>)",
                f"\\1<tpAmbReplace/>",
                ide,
                count=1,
            )  # marker
            # melhor: inserir nrRecibo logo depois de indRetif
            ide = re.sub(
                r"(<indRetif>\d+</indRetif>)",
                f"\\1<nrRecibo>{nrRecibo_a_retif}</nrRecibo>",
                ide,
                count=1,
            )
            ide = ide.replace("<tpAmbReplace/>", "")
        return f"<ideEvento>{ide}</ideEvento>"

    inner = RE_IDEEVENTO.sub(_sub_ideevento, inner)

    # 3) Montar XML completo - empacotamento padrao do leiaute v_S_01_03_00
    xml = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<eSocial xmlns="http://www.esocial.gov.br/schema/evt/evtPgtos/v_S_01_03_00">'
        f'<evtPgtos Id="{novo_id}">'
        f'{inner}'
        '</evtPgtos>'
        '</eSocial>'
    )
    return xml


def main() -> None:
    if not os.path.exists(INDICE):
        raise SystemExit(f"Indice nao encontrado: {INDICE}. Rode antes a indexacao.")
    print(f"Carregando indice: {INDICE}")
    idx = json.load(open(INDICE, encoding="utf-8"))
    recibos_ativos = set(idx["recibos_ativos"])
    s1210 = idx["s1210"]
    print(f"  recibos ATIVOS: {len(recibos_ativos)}")
    print(f"  S-1210 totais : {len(s1210)}")

    # Filtra perApur 2025-05
    eventos_05 = [e for e in s1210 if e["perApur"] == PERAPUR_ALVO]
    print(f"  S-1210 em {PERAPUR_ALVO}: {len(eventos_05)}")

    por_cpf = defaultdict(list)
    for e in eventos_05:
        por_cpf[e["cpf"]].append(e)
    print(f"  CPFs distintos: {len(por_cpf)}")

    # Estatisticas de saida
    sem_ativo = 0
    multi_ativo = 0
    gerados = 0
    falhas = 0

    rows = []  # pro CSV

    with zipfile.ZipFile(ZIP_PATH) as z:
        for cpf, evs in por_cpf.items():
            ativos = [e for e in evs if e["ativo"]]
            if not ativos:
                sem_ativo += 1
                rows.append({"cpf": cpf, "status": "SEM_ATIVO", "recibo_escolhido": "", "n_ativos": 0, "xml": ""})
                continue
            if len(ativos) > 1:
                multi_ativo += 1
            # escolhe o ATIVO mais recente (dhProc max)
            escolhido = max(ativos, key=lambda e: e["dhProc"] or "")
            try:
                with z.open(escolhido["xml"]) as f:
                    raw = f.read().decode("utf-8", errors="replace")
                m = RE_EVTPGTOS.search(raw)
                if not m:
                    raise ValueError("evtPgtos nao encontrado no XML original")
                inner = m.group(1)
                novo_id = construir_id_retif()
                # garantir Id unico por CPF: append do CPF
                novo_id = novo_id[:-11] + cpf
                xml_retif = transformar_para_retif(inner, escolhido["nrRecibo"], novo_id)
                out_path = os.path.join(XML_DIR, f"{cpf}.xml")
                with open(out_path, "w", encoding="utf-8") as f:
                    f.write(xml_retif)
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

    # Relatorio CSV
    with open(REPORT, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["cpf", "status", "recibo_escolhido", "n_ativos", "xml"])
        w.writeheader()
        w.writerows(rows)

    print()
    print(f"=== RESULTADO ===")
    print(f"  Gerados:         {gerados}")
    print(f"  Sem ativo:       {sem_ativo}")
    print(f"  Multi ativo:     {multi_ativo} (escolhi o mais recente)")
    print(f"  Falhas:          {falhas}")
    print(f"  Relatorio:       {REPORT}")
    print(f"  XMLs em:         {XML_DIR}")


if __name__ == "__main__":
    main()
