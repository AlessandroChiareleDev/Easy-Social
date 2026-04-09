"""
Verificação S-5002 pós-pipeline — versão SEGURA (máximo 2 consultas).

GARANTIA: Faz NO MÁXIMO 1 chamada a cada endpoint do eSocial.
  - 1x consultar_identificadores_trabalhador (endpoint Identificadores)
  - 1x solicitar_download_por_id (endpoint Download — o que tem limite 10/dia)
  Total: 2 consultas. ZERO retries automáticos.

Se qualquer chamada falhar, o script PARA e mostra o erro.

Após o download, compara automaticamente com os dados PRÉ-pipeline
documentados no prontuário.
"""
import sys, os, json, re
sys.path.insert(0, os.path.dirname(__file__))

import psycopg2
from db_config import DB_CONFIG, LOCAL_DB_CONFIG
from esocial.certificate_manager import CertificateManager
from esocial.esocial_client import ESocialClient
from esocial.envio_tracker import registrar_consulta

CPF = "08132588983"
PERIODO = "2024-12"

# Dados PRÉ-pipeline (extraídos do prontuário) para comparação automática
PRE_PIPELINE = {
    "nrRecArqBase": "1.1.0000000030328525269",
    "demonstrativos": {
        "10711884": {  # perRef 2024-11, dtPgto 2024-12-06
            "11": 3219.33,   # Rendimento tributável
            "7900": -270.99, # Contrib. previd. (INSS)
            "31": 65.34,     # IRRF retido
        },
        "10711933": {  # perRef 2024, dtPgto 2024-12-20 (13º)
            "7900": 0.40,    # Contrib. previd. (INSS)
            "12": 2106.33,   # Rendimento 13º
        },
    },
}

DRY_RUN = "--dry-run" in sys.argv


def check_cota_hoje(conn):
    """Checa quantas consultas/downloads já foram feitas hoje (no nosso banco)."""
    with conn.cursor() as cur:
        cur.execute("""
            SELECT COUNT(*) FROM esocial_envios
            WHERE tipo_evento IN ('CONSULTA-IDENT', 'DOWNLOAD-S5002', 'DOWNLOAD-S5001')
              AND created_at::date = CURRENT_DATE
              AND status != 'erro'
        """)
        return cur.fetchone()[0]


def comparar_pre_pos(xml_text: str):
    """Compara dados PRÉ vs PÓS do S-5002."""
    print("\n" + "=" * 60)
    print("  COMPARAÇÃO PRÉ vs PÓS PIPELINE")
    print("=" * 60)

    # nrRecArqBase
    rec_base_match = re.findall(r'<nrRecArqBase>([^<]+)</nrRecArqBase>', xml_text)
    novo_rec = rec_base_match[0] if rec_base_match else "NÃO ENCONTRADO"
    antigo_rec = PRE_PIPELINE["nrRecArqBase"]
    mudou = novo_rec != antigo_rec
    print(f"\n  nrRecArqBase:")
    print(f"    PRÉ:  {antigo_rec}")
    print(f"    PÓS:  {novo_rec}")
    print(f"    {'✅ MUDOU (novo recibo base)' if mudou else '⚠️  IGUAL (pode não ter recalculado)'}")

    # Extrair todos os infoIR do PÓS
    infos_pos = re.findall(
        r'<infoIR><tpInfoIR>(\d+)</tpInfoIR><valor>([^<]+)</valor></infoIR>',
        xml_text
    )

    desc_map = {
        "11": "Rend. tributável",
        "12": "Rend. 13º salário",
        "31": "IRRF retido",
        "41": "Ded. INSS (NOVO!)",
        "42": "Ded. INSS 13º (NOVO!)",
        "7900": "Contrib. previd.",
        "9": "Isento",
    }

    # Agrupar valores PÓS
    pos_values = {}
    for tp, val in infos_pos:
        pos_values.setdefault(tp, []).append(float(val))

    # Agrupar valores PRÉ (todos os demonstrativos)
    pre_values = {}
    for demo_data in PRE_PIPELINE["demonstrativos"].values():
        for tp, val in demo_data.items():
            pre_values.setdefault(tp, []).append(val)

    print(f"\n  {'tpInfoIR':<12} {'Descrição':<25} {'PRÉ':>12} {'PÓS':>12} {'DIFF':>12}  STATUS")
    print(f"  {'-'*12} {'-'*25} {'-'*12} {'-'*12} {'-'*12}  {'-'*10}")

    todos_tipos = sorted(set(list(pre_values.keys()) + list(pos_values.keys())))
    for tp in todos_tipos:
        desc = desc_map.get(tp, f"Tipo {tp}")
        pre_total = sum(pre_values.get(tp, [0]))
        pos_total = sum(pos_values.get(tp, [0]))
        diff = pos_total - pre_total

        if tp in pos_values and tp not in pre_values:
            status = "🆕 NOVO"
        elif abs(diff) < 0.01:
            status = "= IGUAL"
        else:
            status = "⚡ MUDOU"

        print(f"  {tp:<12} {desc:<25} {pre_total:>12.2f} {pos_total:>12.2f} {diff:>+12.2f}  {status}")

    # Verificação específica: tpInfoIR 41/42 (deduções INSS que DEVERIAM aparecer após correção)
    print(f"\n  --- VERIFICAÇÃO CHAVE ---")
    if "41" in pos_values:
        print(f"  ✅ tpInfoIR=41 (Ded. INSS) PRESENTE no PÓS: R$ {sum(pos_values['41']):.2f}")
    else:
        print(f"  ℹ️  tpInfoIR=41 (Ded. INSS) NÃO aparece no PÓS (pode continuar como 7900)")

    if "42" in pos_values:
        print(f"  ✅ tpInfoIR=42 (Ded. INSS 13º) PRESENTE no PÓS: R$ {sum(pos_values['42']):.2f}")
    else:
        print(f"  ℹ️  tpInfoIR=42 (Ded. INSS 13º) NÃO aparece no PÓS (pode continuar como 7900)")


def main():
    print("=" * 60)
    print("  VERIFICAÇÃO S-5002 PÓS-PIPELINE (versão segura)")
    print(f"  CPF: {CPF} | Período: {PERIODO}")
    print(f"  Modo: {'🔒 DRY-RUN (sem consultar eSocial)' if DRY_RUN else '🔴 PRODUÇÃO (vai gastar consultas)'}")
    print("=" * 60)

    # Setup certificado
    local_conn = psycopg2.connect(**LOCAL_DB_CONFIG)
    cur = local_conn.cursor()
    cur.execute("SELECT cnpj, arquivo_path, senha_encrypted FROM certificados_a1 WHERE ativo = TRUE LIMIT 1")
    row = cur.fetchone()
    local_conn.close()

    if not row:
        print("\n  ❌ Nenhum certificado A1 ativo encontrado!")
        return

    cnpj, arquivo_path, senha_enc = row
    conn = psycopg2.connect(**DB_CONFIG)

    # PRE-CHECK: consultas usadas hoje
    usadas_hoje = check_cota_hoje(conn)
    print(f"\n  📊 Consultas registradas hoje: {usadas_hoje}")
    print(f"  📊 Limite governo (Download): 10/dia")
    print(f"  📊 Este script vai usar: 2 consultas")
    print(f"  📊 Restará após execução: ~{10 - usadas_hoje - 2} consultas")

    if usadas_hoje >= 8:
        print(f"\n  ⚠️  ATENÇÃO: Já foram usadas {usadas_hoje} consultas hoje!")
        print(f"  ⚠️  Com mais 2, ficará com {10 - usadas_hoje - 2} restantes.")

    if DRY_RUN:
        print("\n  🔒 DRY-RUN: Parando aqui. Remova --dry-run para executar de verdade.")
        conn.close()
        return

    # Setup crypto
    senha = CertificateManager.decrypt_password(senha_enc)
    with open(arquivo_path, "rb") as f:
        pfx_data = f.read()
    empregador = {"tpInsc": 1, "nrInsc": cnpj[:8]}

    # ══════════════════════════════════════════════
    # CONSULTA 1/2: Buscar identificadores
    # ══════════════════════════════════════════════
    print(f"\n  [1/2] Consultando identificadores do CPF {CPF} em {PERIODO}...")

    result = ESocialClient.consultar_identificadores_trabalhador(
        cpf=CPF,
        dt_ini=f"{PERIODO}-01T00:00:00",
        dt_fim=f"{PERIODO}-28T23:59:59",
        pfx_data=pfx_data,
        password=senha,
        empregador=empregador,
        producao=True,
    )

    # Registrar no banco (independente de sucesso/falha)
    registrar_consulta(
        conn,
        tipo_consulta="CONSULTA-IDENT",
        ambiente="1",
        resultado=result,
        cpf=CPF,
        per_apur=PERIODO,
        xml_resposta=result.get("xml_resposta"),
        origem="verificar_s5002_safe",
    )

    if not result.get("sucesso"):
        erro = result.get("descricao") or result.get("erro", "Erro desconhecido")
        print(f"\n  ❌ FALHA na consulta de identificadores!")
        print(f"  Erro: {erro}")
        print(f"  Consultas gastas: 1 (esta falha pode ou não ter contado)")
        print(f"\n  PARANDO. Não vai tentar de novo para não gastar cota.")
        conn.close()
        return

    eventos = result.get("eventos", [])
    print(f"  ✅ {len(eventos)} eventos encontrados")

    por_tipo = {}
    for ev in eventos:
        tp = ev.get("tipo", "?")
        por_tipo.setdefault(tp, []).append(ev)

    for tp, evs in sorted(por_tipo.items()):
        print(f"    {tp}: {len(evs)}")

    s5002 = por_tipo.get("S-5002", [])
    if not s5002:
        print(f"\n  ⚠️  Nenhum S-5002 encontrado para {PERIODO}!")
        print(f"  Consultas gastas: 1 (apenas identificadores)")
        print(f"  Não vai chamar download — economia de 1 consulta!")
        conn.close()
        return

    ids = [e["id"] for e in s5002 if e.get("id")]
    print(f"\n  S-5002 encontrados: {len(ids)} (IDs: {ids})")

    # ══════════════════════════════════════════════
    # CONSULTA 2/2: Download dos S-5002
    # ══════════════════════════════════════════════
    print(f"\n  [2/2] Baixando {len(ids)} S-5002...")

    dl = ESocialClient.solicitar_download_por_id(
        ids=ids,
        pfx_data=pfx_data,
        password=senha,
        empregador=empregador,
        producao=True,
    )

    # Registrar download no banco
    registrar_consulta(
        conn,
        tipo_consulta="DOWNLOAD-S5002",
        ambiente="1",
        resultado=dl,
        cpf=CPF,
        per_apur=PERIODO,
        xml_resposta=dl.get("xml_resposta"),
        origem="verificar_s5002_safe",
    )

    if not dl.get("sucesso"):
        erro = dl.get("descricao") or dl.get("erro", "Erro desconhecido")
        print(f"\n  ❌ FALHA no download!")
        print(f"  Erro: {erro}")
        if "10 solicitações" in str(erro) or "limite" in str(erro).lower():
            print(f"  🚫 COTA ESGOTADA — você já usou as 10 consultas de hoje!")
        print(f"  Consultas gastas: 2 (identificadores OK + download falhou)")
        print(f"\n  PARANDO. Não vai tentar de novo.")
        conn.close()
        return

    # SUCESSO — processar resultados
    arquivos = dl.get("arquivos", [])
    print(f"  ✅ Download OK! {len(arquivos)} arquivo(s) recebido(s)")
    print(f"\n  📊 TOTAL CONSULTAS GASTAS: 2 ✅")

    for i, arq in enumerate(arquivos):
        xml = arq.get("evento_xml") or arq.get("xml_evento") or ""
        nr = arq.get("nr_recibo", "?")
        print(f"\n  === S-5002 #{i+1} (recibo: {nr}) ===")

        if xml:
            # Salvar XML
            fname = f"s5002_POS_pipeline_{PERIODO}_{i+1}.xml"
            fpath = os.path.join(os.path.dirname(__file__), fname)
            with open(fpath, "w", encoding="utf-8") as f:
                f.write(xml)
            print(f"  💾 Salvo: {fname}")

            # Mostrar dados brutos
            nm = re.findall(r'<nmTrab>([^<]+)</nmTrab>', xml)
            if nm:
                print(f"  Nome: {nm[0]}")

            infos = re.findall(
                r'<infoIR><tpInfoIR>(\d+)</tpInfoIR><valor>([^<]+)</valor></infoIR>',
                xml
            )
            if infos:
                desc_map = {
                    "11": "Rend. tributável", "12": "Rend. 13º", "31": "IRRF retido",
                    "7900": "Contrib. previd.", "41": "Ded. INSS", "42": "Ded. INSS 13º",
                    "9": "Isento",
                }
                print(f"  infoIR:")
                for tp, val in infos:
                    print(f"    tpInfoIR={tp} ({desc_map.get(tp, '?')}) = R$ {val}")

            # Comparação automática PRÉ vs PÓS
            comparar_pre_pos(xml)
        else:
            print(f"  ⚠️  XML vazio no arquivo {i+1}")

    conn.close()
    print(f"\n{'=' * 60}")
    print(f"  CONCLUÍDO — 2 consultas gastas, 0 retries")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
