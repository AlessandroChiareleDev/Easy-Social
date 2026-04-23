"""
Envia em lote (sequencial) N CPFs de S-1210 retif do Lote 1 / 2025-05.
Le XMLs ja gerados em saida_retif_lote1_maio/xml/<cpf>.xml.

Uso:
  python enviar_retif_batch.py --n 10
  python enviar_retif_batch.py --cpfs 11067218700,12345678901
"""
from __future__ import annotations

import argparse
import csv
import os
import sys
import time

ROOT = os.path.dirname(os.path.abspath(__file__))
XML_DIR = os.path.join(ROOT, "saida_retif_lote1_maio", "xml")
REPORT = os.path.join(ROOT, "saida_retif_lote1_maio", "relatorio.csv")
LOG_OUT = os.path.join(ROOT, "saida_retif_lote1_maio", "envios_producao.csv")
sys.path.insert(0, ROOT)


def _carregar_cpfs_ordenados() -> list[str]:
    """CPFs com status OK no CSV de geracao, ordem do arquivo."""
    cpfs = []
    with open(REPORT, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row["status"] == "OK":
                cpfs.append(row["cpf"])
    return cpfs


def _ja_enviados() -> set[str]:
    if not os.path.exists(LOG_OUT):
        return set()
    out = set()
    with open(LOG_OUT, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row.get("status_proc") == "ok":
                out.add(row["cpf"])
    return out


def _append_log(row: dict) -> None:
    novo = not os.path.exists(LOG_OUT)
    with open(LOG_OUT, "a", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=[
            "cpf", "status_envio", "protocolo", "status_proc",
            "nr_recibo_novo", "cod_resp", "descricao", "ts"
        ])
        if novo:
            w.writeheader()
        w.writerow(row)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=10, help="quantos CPFs (default 10)")
    ap.add_argument("--cpfs", help="lista vazia separada por virgula (override --n)")
    ap.add_argument("--pfx", default=os.path.join(ROOT, "certificados",
                    "cert_05969071000110_45C7EBE84F3FE665.pfx"))
    ap.add_argument("--senha", default=os.environ.get("CERT_PFX_PASSWORD"))
    ap.add_argument("--cnpj", default="05969071000110")
    ap.add_argument("--sleep", type=float, default=1.0,
                    help="pausa entre CPFs (s)")
    args = ap.parse_args()

    if not args.senha:
        print("ERRO: senha PFX ausente (--senha ou CERT_PFX_PASSWORD)")
        return 2

    if args.cpfs:
        cpfs_alvo = [c.strip() for c in args.cpfs.split(",") if c.strip()]
    else:
        todos = _carregar_cpfs_ordenados()
        ja = _ja_enviados()
        pendentes = [c for c in todos if c not in ja]
        cpfs_alvo = pendentes[:args.n]
        print(f"Pool: {len(todos)} CPFs OK | ja enviados: {len(ja)} | "
              f"pendentes: {len(pendentes)} | nesta rodada: {len(cpfs_alvo)}")

    if not cpfs_alvo:
        print("Nenhum CPF pra enviar.")
        return 0

    # cert + libs (1 vez so)
    print("Carregando cert...")
    with open(args.pfx, "rb") as f:
        pfx_data = f.read()
    from esocial.certificate_manager import CertificateManager
    info = CertificateManager.validate_pfx(pfx_data, args.senha)
    cnpj = (info.get("cnpj") or args.cnpj).rjust(14, "0")[-14:]
    print(f"  cnpj={cnpj} validade={info.get('validade')}")
    senha = args.senha
    empregador = {"tpInsc": 1, "nrInsc": cnpj}

    from esocial.xml_signer import S1010XMLSigner
    from esocial.soap_builder import SOAPEnvelopeBuilder
    from esocial.esocial_client import ESocialClient

    url_envio = SOAPEnvelopeBuilder.url_envio(producao=True)
    url_consulta = SOAPEnvelopeBuilder.url_consulta(producao=True)

    ok = 0
    rej = 0
    errs = 0

    for i, cpf in enumerate(cpfs_alvo, start=1):
        ts = time.strftime("%Y-%m-%d %H:%M:%S")
        xml_path = os.path.join(XML_DIR, f"{cpf}.xml")
        print(f"\n[{i}/{len(cpfs_alvo)}] CPF {cpf}")
        if not os.path.exists(xml_path):
            print(f"  XML nao encontrado: {xml_path}")
            errs += 1
            _append_log({"cpf": cpf, "status_envio": "no_xml", "protocolo": "",
                         "status_proc": "erro", "nr_recibo_novo": "", "cod_resp": "",
                         "descricao": "xml ausente", "ts": ts})
            continue

        try:
            with open(xml_path, "rb") as f:
                xml_bytes = f.read()
            xml_assinado = S1010XMLSigner.assinar(xml_bytes, pfx_data, senha)
            soap = SOAPEnvelopeBuilder.montar_envio(
                [xml_assinado], empregador, empregador.copy(), grupo="3"
            )
            resultado = ESocialClient.enviar_lote(soap, pfx_data, senha, url=url_envio)
        except Exception as e:
            print(f"  EXCEPTION envio: {e}")
            errs += 1
            _append_log({"cpf": cpf, "status_envio": "exc", "protocolo": "",
                         "status_proc": "erro", "nr_recibo_novo": "", "cod_resp": "",
                         "descricao": str(e)[:200], "ts": ts})
            continue

        protocolo = resultado.get("protocolo")
        if not resultado.get("sucesso") or not protocolo:
            print(f"  envio recusado: {resultado.get('descricao')}")
            rej += 1
            _append_log({"cpf": cpf, "status_envio": "rej",
                         "protocolo": protocolo or "", "status_proc": "erro",
                         "nr_recibo_novo": "",
                         "cod_resp": str(resultado.get("codigo_resposta", "")),
                         "descricao": str(resultado.get("descricao", ""))[:200],
                         "ts": ts})
            continue

        # poll
        evt = None
        for tentativa in range(20):
            time.sleep(4)
            try:
                consulta = ESocialClient.consultar_lote(
                    protocolo, pfx_data, senha, url=url_consulta
                )
            except Exception as e:
                print(f"  poll {tentativa+1}: {e}")
                continue
            eventos = consulta.get("eventos") or []
            if eventos:
                evt = eventos[0]
                break
        if evt is None:
            print("  TIMEOUT polling")
            errs += 1
            _append_log({"cpf": cpf, "status_envio": "ok", "protocolo": protocolo,
                         "status_proc": "timeout", "nr_recibo_novo": "",
                         "cod_resp": "", "descricao": "timeout polling",
                         "ts": ts})
            continue

        nr_recibo = evt.get("nr_recibo")
        cod = str(evt.get("codigo_resposta", ""))
        desc = str(evt.get("descricao", ""))
        if nr_recibo:
            print(f"  OK recibo={nr_recibo}")
            ok += 1
            _append_log({"cpf": cpf, "status_envio": "ok", "protocolo": protocolo,
                         "status_proc": "ok", "nr_recibo_novo": nr_recibo,
                         "cod_resp": cod, "descricao": desc[:200], "ts": ts})
        else:
            print(f"  REJEITADO cod={cod} desc={desc}")
            rej += 1
            _append_log({"cpf": cpf, "status_envio": "ok", "protocolo": protocolo,
                         "status_proc": "rej", "nr_recibo_novo": "",
                         "cod_resp": cod, "descricao": desc[:200], "ts": ts})

        if args.sleep:
            time.sleep(args.sleep)

    print(f"\n=== FIM === ok={ok} rej={rej} errs={errs} (de {len(cpfs_alvo)})")
    print(f"Log: {LOG_OUT}")
    return 0 if errs == 0 and rej == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
