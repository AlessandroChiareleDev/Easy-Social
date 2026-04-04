"""Verificar S-5002 pós-pipeline para CPF 08132588983, períodos 2024-12 e 2025-01."""
import sys, os, json, re
sys.path.insert(0, os.path.dirname(__file__))

import psycopg2
from db_config import LOCAL_DB_CONFIG
from esocial.certificate_manager import CertificateManager
from esocial.esocial_client import ESocialClient

CPF = "08132588983"
PERIODOS = ["2024-12", "2025-01"]

print("=" * 60)
print("  VERIFICAÇÃO PÓS-PIPELINE — S-5002")
print("=" * 60)

# 1. Carregar certificado
conn_local = psycopg2.connect(**LOCAL_DB_CONFIG)
try:
    with conn_local.cursor() as cur:
        cur.execute("SELECT cnpj, arquivo_path, senha_encrypted FROM certificados_a1 WHERE ativo = TRUE LIMIT 1")
        cnpj, arquivo_path, senha_enc = cur.fetchone()
finally:
    conn_local.close()

senha = CertificateManager.decrypt_password(senha_enc)
with open(arquivo_path, "rb") as f:
    pfx_data = f.read()

empregador = {"tpInsc": 1, "nrInsc": cnpj[:8]}
print(f"CPF: {CPF}")
print(f"CNPJ: {cnpj}")

# 2. Consultar identificadores do trabalhador para cada período
for per_apur in PERIODOS:
    print(f"\n{'='*60}")
    print(f"  PERÍODO: {per_apur}")
    print(f"{'='*60}")

    dt_ini = f"{per_apur}-01T00:00:00"
    dt_fim = f"{per_apur}-31T23:59:59"

    print(f"\n--- Consultando identificadores ({dt_ini} a {dt_fim}) ---")
    result = ESocialClient.consultar_identificadores_trabalhador(
        cpf=CPF,
        dt_ini=dt_ini,
        dt_fim=dt_fim,
        pfx_data=pfx_data,
        password=senha,
        empregador=empregador,
        producao=True,
    )

    if not result.get("sucesso"):
        print(f"  FALHA: {result.get('erro') or result.get('descricao')}")
        print(f"  Result: {json.dumps(result, indent=2, default=str)[:500]}")
        continue

    eventos = result.get("eventos", [])
    print(f"  Total eventos encontrados: {len(eventos)}")

    # Classificar por tipo
    por_tipo = {}
    for ev in eventos:
        tp = ev.get("tipo", "?")
        por_tipo.setdefault(tp, []).append(ev)

    for tp, evs in sorted(por_tipo.items()):
        print(f"    {tp}: {len(evs)} evento(s)")

    # Filtrar S-5002
    s5002_events = por_tipo.get("S-5002", [])
    if not s5002_events:
        print("  NENHUM S-5002 encontrado neste período!")
        continue

    # Download do S-5002 por ID
    ids_5002 = [e["id"] for e in s5002_events if e.get("id")]
    nr_recibos_5002 = [e.get("nrRec") or e.get("nr_recibo") for e in s5002_events]
    print(f"\n  S-5002 IDs: {ids_5002}")
    print(f"  S-5002 Recibos: {nr_recibos_5002}")

    print(f"\n--- Download cirúrgico S-5002 ({per_apur}) ---")
    if ids_5002:
        dl = ESocialClient.solicitar_download_por_id(
            ids=ids_5002,
            pfx_data=pfx_data,
            password=senha,
            empregador=empregador,
            producao=True,
        )
    elif nr_recibos_5002:
        dl = ESocialClient.solicitar_download_por_nrrecibo(
            nr_recibos=[r for r in nr_recibos_5002 if r],
            pfx_data=pfx_data,
            password=senha,
            empregador=empregador,
            producao=True,
        )
    else:
        print("  Sem IDs ou recibos para download.")
        continue

    if not dl.get("sucesso"):
        print(f"  Download FALHOU: {dl.get('erro') or dl.get('descricao')}")
        print(f"  Result: {json.dumps(dl, indent=2, default=str)[:500]}")
        continue

    arquivos = dl.get("arquivos", [])
    print(f"  Arquivos baixados: {len(arquivos)}")

    for i, arq in enumerate(arquivos):
        xml_content = arq.get("evento_xml") or arq.get("xml_evento") or ""
        nr_rec = arq.get("nr_recibo", "?")
        print(f"\n  --- Arquivo {i+1} (Recibo: {nr_rec}) ---")

        if xml_content:
            # Extrair nome do trabalhador
            nm_trab = re.findall(r'<nmTrab>([^<]+)</nmTrab>', xml_content)
            if nm_trab:
                print(f"  FUNCIONÁRIO: {nm_trab[0]}")

            # Extrair codIncIRRF de cada rubrica
            cod_matches = re.findall(r'<codRubr>(\d+)</codRubr>', xml_content)
            cod_irrf = re.findall(r'<codIncIRRF>(\d+)</codIncIRRF>', xml_content)
            print(f"  Rubricas encontradas (codRubr): {cod_matches}")
            print(f"  codIncIRRF encontrados: {cod_irrf}")

            # Buscar pares rubrica/codIncIRRF via regex mais detalhado
            # Procurar dentro de <infoCRIRRF>
            blocos = re.findall(r'<infoCRIRRF>(.*?)</infoCRIRRF>', xml_content, re.DOTALL)
            if blocos:
                print(f"\n  Detalhamento IRRF ({len(blocos)} blocos):")
                for bloco in blocos:
                    cod = re.findall(r'<codCR>(\d+)</codCR>', bloco)
                    vr = re.findall(r'<vrCR>([^<]+)</vrCR>', bloco)
                    print(f"    codCR={cod} vrCR={vr}")

            # Procurar basesIrrf com codIncIRRF
            bases = re.findall(r'<basesIrrf>(.*?)</basesIrrf>', xml_content, re.DOTALL)
            if bases:
                print(f"\n  Bases IRRF ({len(bases)} blocos):")
                for base in bases:
                    tp_valor = re.findall(r'<tpValor>(\d+)</tpValor>', base)
                    valor = re.findall(r'<valor>([^<]+)</valor>', base)
                    print(f"    tpValor={tp_valor} valor={valor}")

            # Salvar XML
            filename = f"s5002_{per_apur}_verificacao_{i+1}.xml"
            with open(filename, "w", encoding="utf-8") as f:
                f.write(xml_content)
            print(f"  XML salvo em {filename}")
        else:
            print(f"  Sem conteúdo XML - keys: {arq.keys()}")
            print(f"  Arq: {json.dumps(arq, indent=2, default=str)[:500]}")

print("\n" + "=" * 60)
print("  VERIFICAÇÃO CONCLUÍDA")
print("=" * 60)
