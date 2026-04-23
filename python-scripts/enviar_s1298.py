"""
Mini-CLI para enviar S-1298 (reabertura de folha) em PRODUCAO.

Uso:
  python enviar_s1298.py --per-apur 2025-05 --dry-run
  python enviar_s1298.py --per-apur 2025-05         # ENVIA EM PRODUCAO

Sem flag de prod/homolog: ja vai pra producao (--ambiente 2 pra homolog).
"""
from __future__ import annotations

import argparse
import os
import sys
import time

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)


def main() -> int:
    ap = argparse.ArgumentParser(description="Envio S-1298 reabertura folha")
    ap.add_argument("--per-apur", required=True, help="AAAA-MM (ex: 2025-05)")
    ap.add_argument("--ind-apuracao", default="1", choices=["1", "2"],
                    help="1=mensal (default), 2=13o")
    ap.add_argument("--ambiente", default="1", choices=["1", "2"],
                    help="1=Producao (default), 2=Homologacao")
    ap.add_argument("--dry-run", action="store_true",
                    help="Assina + monta SOAP mas NAO envia")
    ap.add_argument("--pfx", default=os.path.join(ROOT, "certificados",
                    "cert_05969071000110_45C7EBE84F3FE665.pfx"))
    ap.add_argument("--senha", default=os.environ.get("CERT_PFX_PASSWORD"))
    ap.add_argument("--cnpj", default="05969071000110")
    args = ap.parse_args()

    per_apur = args.per_apur.strip()
    if len(per_apur) != 7 or per_apur[4] != "-":
        print(f"ERRO: per_apur invalido: {per_apur}")
        return 2

    print(f"=== S-1298 reabertura folha {per_apur} ===")

    if not os.path.exists(args.pfx):
        print(f"ERRO: PFX nao encontrado: {args.pfx}")
        return 3
    if not args.senha:
        print("ERRO: senha PFX ausente. --senha ou env CERT_PFX_PASSWORD")
        return 3

    # 1) Cert
    print("\n[1/5] Carregando cert...")
    with open(args.pfx, "rb") as f:
        pfx_data = f.read()
    from esocial.certificate_manager import CertificateManager
    info = CertificateManager.validate_pfx(pfx_data, args.senha)
    cnpj = (info.get("cnpj") or args.cnpj).rjust(14, "0")[-14:]
    print(f"  cnpj={cnpj} validade={info.get('validade')}")
    senha = args.senha
    empregador = {"tpInsc": 1, "nrInsc": cnpj}

    # 2) Gerar XML S-1298
    print("\n[2/5] Gerando XML S-1298...")
    from esocial.xml_s1298 import S1298XMLGenerator
    xml_bytes = S1298XMLGenerator.gerar(
        empregador=empregador,
        per_apur=per_apur,
        ind_apuracao=args.ind_apuracao,
        seq=1,
        tp_amb=args.ambiente,
    )
    print(f"  XML: {len(xml_bytes)} bytes")
    print(f"  --- XML ---\n{xml_bytes.decode('utf-8')}")

    # 3) Assinar
    print("\n[3/5] Assinando...")
    from esocial.xml_signer import S1010XMLSigner
    xml_assinado = S1010XMLSigner.assinar(xml_bytes, pfx_data, senha)
    print(f"  Assinado: {len(xml_assinado)} bytes")

    # 4) SOAP
    print("\n[4/5] Montando SOAP (grupo=3 periodicos)...")
    from esocial.soap_builder import SOAPEnvelopeBuilder
    soap = SOAPEnvelopeBuilder.montar_envio(
        [xml_assinado], empregador, empregador.copy(), grupo="3"
    )
    is_prod = (args.ambiente == "1")
    url_envio = SOAPEnvelopeBuilder.url_envio(producao=is_prod)
    url_consulta = SOAPEnvelopeBuilder.url_consulta(producao=is_prod)
    print(f"  SOAP: {len(soap)} bytes")
    print(f"  URL: {url_envio}")

    if args.dry_run:
        print("\n[5/5] DRY-RUN -- NAO ENVIA")
        print(soap)
        print("\n=== DRY-RUN OK ===")
        return 0

    # 5) Envio
    amb_label = "PRODUCAO" if is_prod else "HOMOLOG"
    print(f"\n[5/5] *** ENVIANDO EM {amb_label} ***")
    from esocial.esocial_client import ESocialClient
    resultado = ESocialClient.enviar_lote(soap, pfx_data, senha, url=url_envio)
    print("\n--- RESULTADO ENVIO ---")
    for k, v in resultado.items():
        print(f"  {k}: {v}")
    if not resultado.get("sucesso"):
        return 7
    protocolo = resultado.get("protocolo")
    print("\nPolling consulta...")
    for tentativa in range(15):
        time.sleep(5)
        try:
            consulta = ESocialClient.consultar_lote(protocolo, pfx_data, senha, url=url_consulta)
        except Exception as e:
            print(f"  {tentativa+1}: erro: {e}")
            continue
        eventos = consulta.get("eventos") or []
        if eventos:
            evt = eventos[0]
            print("\n--- PROCESSAMENTO ---")
            for k, v in evt.items():
                print(f"  {k}: {v}")
            if evt.get("nr_recibo"):
                print("\n=== S-1298 RECEBIDO E ACEITO ===")
                return 0
            print("\n*** REJEITADO ***")
            return 8
        print(f"  {tentativa+1}/15: processando...")
    print("\n*** TIMEOUT ***")
    return 9


if __name__ == "__main__":
    sys.exit(main())
