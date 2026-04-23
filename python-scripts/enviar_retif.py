"""
Mini-CLI offline para envio de S-1210 RETIF (Lote 1 / 2025-05).

Uso:
  python enviar_retif.py --cpf 11067218700 --dry-run
  python enviar_retif.py --cpf 11067218700              # ENVIA EM PRODUCAO
  python enviar_retif.py --cpf 11067218700 --print-xml  # so imprime XML

Pre-requisitos:
  - XML retif ja gerado em python-scripts/saida_retif_lote1_maio/xml/<cpf>.xml
    (rodar antes: python gerar_retif_lote1_maio_offline.py)
  - Cert A1 ativo no DB (mesma fonte usada pelo bot_api)
"""
from __future__ import annotations

import argparse
import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
XML_DIR = os.path.join(ROOT, "saida_retif_lote1_maio", "xml")

# Garantir que esocial.* importa (mesmo sys.path do bot_api)
sys.path.insert(0, ROOT)


def main() -> int:
    ap = argparse.ArgumentParser(description="Envio offline de S-1210 RETIF")
    ap.add_argument("--cpf", required=True, help="CPF (11 digitos)")
    ap.add_argument("--dry-run", action="store_true",
                    help="Assina + monta SOAP mas NAO envia. Imprime envelope.")
    ap.add_argument("--print-xml", action="store_true",
                    help="So imprime o XML pre-assinatura e sai")
    ap.add_argument("--pfx", default=os.path.join(ROOT, "certificados",
                    "cert_05969071000110_45C7EBE84F3FE665.pfx"),
                    help="Caminho do .pfx (default: APPA local)")
    ap.add_argument("--senha", default=os.environ.get("CERT_PFX_PASSWORD"),
                    help="Senha do PFX (ou env CERT_PFX_PASSWORD)")
    ap.add_argument("--cnpj", default="05969071000110",
                    help="CNPJ do empregador (default APPA)")
    args = ap.parse_args()

    cpf = args.cpf.strip()
    if not (cpf.isdigit() and len(cpf) == 11):
        print(f"ERRO: CPF invalido: {cpf}")
        return 2

    xml_path = os.path.join(XML_DIR, f"{cpf}.xml")
    if not os.path.exists(xml_path):
        print(f"ERRO: XML nao encontrado para CPF {cpf}: {xml_path}")
        print("Rode antes: python gerar_retif_lote1_maio_offline.py")
        return 2

    with open(xml_path, "rb") as f:
        xml_bytes = f.read()

    print(f"=== CPF {cpf} ===")
    print(f"XML origem: {xml_path}  ({len(xml_bytes)} bytes)")

    if args.print_xml:
        print("\n--- XML PRE-ASSINATURA ---")
        print(xml_bytes.decode("utf-8"))
        return 0

    # ── 1) Carregar cert A1 ────────────────────────────────────
    print("\n[1/4] Carregando certificado A1 do disco...")
    if not os.path.exists(args.pfx):
        print(f"ERRO: PFX nao encontrado: {args.pfx}")
        return 3
    if not args.senha:
        print("ERRO: senha do PFX ausente. Use --senha ou env CERT_PFX_PASSWORD")
        return 3
    try:
        with open(args.pfx, "rb") as f:
            pfx_data = f.read()
        # Validar (carrega + checa senha)
        from esocial.certificate_manager import CertificateManager
        info = CertificateManager.validate_pfx(pfx_data, args.senha)
        cnpj = (info.get("cnpj") or args.cnpj).rjust(14, "0")[-14:]
        senha = args.senha
    except Exception as e:
        print(f"ERRO carregando cert: {e}")
        return 3
    print(f"  cnpj={cnpj}  titular={info.get('nome_titular')}  serie={info.get('numero_serie')}  validade={info.get('validade')}")

    # ── 2) Assinar XML ───────────────────────────────────────────
    print("\n[2/4] Assinando XML...")
    try:
        from esocial.xml_signer import S1010XMLSigner
        xml_assinado = S1010XMLSigner.assinar(xml_bytes, pfx_data, senha)
    except Exception as e:
        print(f"ERRO assinando: {e}")
        return 4
    print(f"  XML assinado: {len(xml_assinado)} bytes")

    # ── 3) Montar envelope SOAP ──────────────────────────────────
    print("\n[3/4] Montando envelope SOAP...")
    try:
        from esocial.soap_builder import SOAPEnvelopeBuilder
        empregador = {"tpInsc": 1, "nrInsc": cnpj}
        soap = SOAPEnvelopeBuilder.montar_envio(
            [xml_assinado], empregador, empregador.copy(), grupo="3"  # periodicos
        )
        url_envio = SOAPEnvelopeBuilder.url_envio(producao=True)
    except Exception as e:
        print(f"ERRO montando SOAP: {e}")
        return 5
    print(f"  SOAP: {len(soap)} bytes")
    print(f"  URL envio: {url_envio}")

    # ── 4) Enviar ou dry-run ─────────────────────────────────────
    if args.dry_run:
        print("\n[4/4] DRY-RUN -- NAO ENVIA. Envelope SOAP:\n")
        print(soap)
        print("\n=== DRY-RUN OK ===")
        return 0

    # ── ENVIO REAL ────────────────────────────────────────────────
    print("\n[4/4] *** ENVIANDO EM PRODUCAO ***")
    try:
        from esocial.esocial_client import ESocialClient
        resultado = ESocialClient.enviar_lote(soap, pfx_data, senha, url=url_envio)
    except Exception as e:
        print(f"ERRO no envio: {e}")
        return 6

    print("\n--- RESULTADO ENVIO ---")
    for k, v in resultado.items():
        print(f"  {k}: {v}")

    if not resultado.get("sucesso"):
        print("\n*** ENVIO REJEITADO ***")
        return 7

    # ── 5) Polling consulta ───────────────────────────────────────
    print("\n[5/5] Aguardando processamento (polling)...")
    import time
    protocolo = resultado.get("protocolo")
    url_consulta = SOAPEnvelopeBuilder.url_consulta(producao=True)
    for tentativa in range(15):
        time.sleep(5)
        try:
            consulta = ESocialClient.consultar_lote(protocolo, pfx_data, senha, url=url_consulta)
        except Exception as e:
            print(f"  tentativa {tentativa+1}: erro consulta: {e}")
            continue
        eventos = consulta.get("eventos") or []
        if eventos:
            evt = eventos[0]
            print(f"\n--- RESULTADO PROCESSAMENTO ---")
            for k, v in evt.items():
                print(f"  {k}: {v}")
            if evt.get("nr_recibo"):
                print("\n=== ENVIO E PROCESSAMENTO OK ===")
                return 0
            print("\n*** PROCESSADO MAS SEM RECIBO (rejeitado pelo eSocial) ***")
            return 8
        print(f"  tentativa {tentativa+1}/15: ainda processando...")

    print("\n*** TIMEOUT POLLING (15 tentativas, 75s) ***")
    return 9


if __name__ == "__main__":
    sys.exit(main())
