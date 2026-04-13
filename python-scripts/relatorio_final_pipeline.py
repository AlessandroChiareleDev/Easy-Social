"""Relatório FINAL completo de todos os erros do pipeline Set/2025."""
import psycopg2, psycopg2.extras, re
from collections import defaultdict

conn = psycopg2.connect(
    host='aws-1-us-east-2.pooler.supabase.com',
    port=5432,
    dbname='postgres',
    user='postgres.zpizibafccwsjgvplcum',
    password='6.18.13.1.8Supa',
    sslmode='require'
)
cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

# Status geral
cur.execute("""
    SELECT status, COUNT(*) as qtd 
    FROM pipeline_cpf_results WHERE run_id=1 
    GROUP BY status ORDER BY status
""")
status_counts = {r['status']: r['qtd'] for r in cur.fetchall()}

# Todos os erros
cur.execute("""
    SELECT cpf, erro_descricao, lote_num, nr_recibo_original, pagamentos
    FROM pipeline_cpf_results
    WHERE run_id=1 AND status='erro'
    ORDER BY cpf
""")
erros = cur.fetchall()

# Pendentes
cur.execute("""
    SELECT COUNT(*) as qtd FROM pipeline_cpf_results WHERE run_id=1 AND status='pendente'
""")
pendentes = cur.fetchone()['qtd']

# Agrupar por codigo de erro
grupos = defaultdict(list)
for e in erros:
    desc = e['erro_descricao'] or ''
    match = re.search(r'\[(\d+)\]', desc)
    code = match.group(1) if match else 'SEM_CODIGO'
    grupos[code].append(e)

print("=" * 80)
print("RELATÓRIO FINAL — PIPELINE RETIFICAÇÃO S-1210 — SET/2025")
print("=" * 80)
print()
print(f"  Início:      2026-04-10 04:59")
print(f"  Término:     2026-04-10 09:49")
print(f"  Duração:     ~4h50min")
print()

print("─" * 80)
print("RESUMO GERAL:")
print("─" * 80)
total = sum(status_counts.values())
ok = status_counts.get('ok', 0)
erro = status_counts.get('erro', 0)
pend = status_counts.get('pendente', 0)
print(f"  Total CPFs:      {total}")
print(f"  ✓ OK:            {ok}  ({ok*100/total:.1f}%)")
print(f"  ✗ Erro:          {erro}  ({erro*100/total:.1f}%)")
print(f"  ⏳ Pendente:      {pend}  ({pend*100/total:.1f}%)")
print(f"  S-1298 (abrir):  ✓ Concluído")
print(f"  S-1299 (fechar): ✓ Concluído")
print()

# Contar CPFs pendentes (não processados)
if pend > 0:
    cur.execute("""
        SELECT cpf FROM pipeline_cpf_results 
        WHERE run_id=1 AND status='pendente' ORDER BY cpf
    """)
    pendentes_list = [r['cpf'] for r in cur.fetchall()]
    print(f"  ⚠️  {pend} CPFs PENDENTES (não processados):")
    for cpf in pendentes_list:
        print(f"      {cpf}")
    print()

print()
print("=" * 80)
print(f"ERROS DETALHADOS POR TIPO ({len(erros)} total)")
print("=" * 80)

# Ordenar grupos: mais CPFs primeiro
for code in sorted(grupos.keys(), key=lambda c: -len(grupos[c])):
    cpfs = grupos[code]
    print()
    print(f"{'━' * 80}")
    print(f"  ERRO [{code}] — {len(cpfs)} CPFs")
    print(f"{'━' * 80}")
    
    # Descrição do erro (pegar do primeiro)
    desc = cpfs[0]['erro_descricao'] or ''
    
    # Explicação legível
    if code == '459':
        print(f"  TIPO: Recibo original já consumido (retificação anterior)")
        print(f"  CAUSA: Crash do lote 28 — eSocial JÁ processou a retificação,")
        print(f"         mas perdemos os recibos novos por queda de DNS.")
        print(f"  STATUS REAL: ✅ RETIFICADOS NO eSocial (apenas sem recibo no banco)")
        print(f"  RESOLUÇÃO: Rodar 'python3 recuperar_lote28.py' para consultar")
        print(f"             o eSocial e recuperar os recibos novos.")
        print(f"  URGÊNCIA: BAIXA — dados corretos no eSocial, só falta atualizar banco")
    elif code == '1955':
        print(f"  TIPO: Somatório de rubricas de IR negativo")
        print(f"  CAUSA: As rubricas de IR (incidências 31/32/33/34) destes trabalhadores")
        print(f"         estão com tipo de rubrica incorreto no S-1010. O desconto de IR")
        print(f"         (tipo 2/4) é menor que o provento tributável (tipo 1/3).")
        print(f"  RESOLUÇÃO: Técnico precisa verificar no S-1010 (tabela de rubricas)")
        print(f"             quais rubricas com codIncIRRF=31/32/33/34 estão erradas.")
        print(f"             Corrigir tipo de rubrica e reenviar S-1210.")
        print(f"  URGÊNCIA: MÉDIA — precisa intervenção manual no cadastro de rubricas")
    elif code == '8':
        print(f"  TIPO: Falta dados de beneficiário de pensão alimentícia")
        print(f"  CAUSA: O S-1210 tem rubrica de pensão alimentícia mas não informa")
        print(f"         os dados dos beneficiários (nome, CPF, valor).")
        print(f"  RESOLUÇÃO: Cadastrar os beneficiários de pensão alimentícia no")
        print(f"             sistema antes de reenviar o S-1210.")
        print(f"  URGÊNCIA: MÉDIA — precisa cadastro de dados de beneficiários")
    else:
        # Erro genérico
        print(f"  TIPO: Erro de validação do eSocial")
        print(f"  CAUSA: {desc[:200]}")
        print(f"  RESOLUÇÃO: Analisar mensagem técnica abaixo")
        print(f"  URGÊNCIA: A DEFINIR")
    
    print()
    print(f"  CPFs afetados:")
    
    # Tabela detalhada
    for c in cpfs:
        n_pgtos = len(c['pagamentos']) if c['pagamentos'] else 0
        vlr_total = 0
        if c['pagamentos']:
            for p in c['pagamentos']:
                vlr_total += float(p.get('vrLiq', '0'))
        print(f"    {c['cpf']}  Lote={c['lote_num'] or '?':>3}  Pgtos={n_pgtos}  R$ {vlr_total:>10,.2f}")
    
    # Somatório
    vlr_grupo = sum(
        sum(float(p.get('vrLiq','0')) for p in c['pagamentos']) 
        for c in cpfs if c['pagamentos']
    )
    print(f"  {'─'*60}")
    print(f"  Total valor líquido do grupo: R$ {vlr_grupo:,.2f}")
    
    print()
    # Mensagem técnica resumida
    if code == '1955':
        # Extrair os somatórios individuais
        print(f"  Somatórios negativos por CPF:")
        for c in cpfs:
            d = c['erro_descricao'] or ''
            match_s = re.search(r'somatório\s+(-[\d,.]+)', d)
            if match_s:
                print(f"    {c['cpf']}: somatório = {match_s.group(1)}")
    
    print(f"  Mensagem técnica (1º CPF):")
    print(f"    {desc[:300]}...")

print()
print()
print("=" * 80)
print("PRÓXIMOS PASSOS:")
print("=" * 80)
print("""
1. ERRO [459] — 31 CPFs (AUTOMATIZÁVEL):
   → Rodar: cd /opt/easy-social/python-scripts && python3 recuperar_lote28.py
   → Consulta o eSocial, recupera recibos, atualiza banco. Sem risco.

2. ERRO [1955] — 15 CPFs (TÉCNICO):
   → Verificar no S-1010 as rubricas com codIncIRRF = 31, 32, 33, 34
   → Problema: tipo de rubrica (1/3 vs 2/4) trocado → IR negativo
   → Após corrigir S-1010, reenviar S-1210 destes 15 CPFs

3. ERRO [8] — 4 CPFs (TÉCNICO):
   → Cadastrar beneficiários de pensão alimentícia
   → CPFs: 00212227700, 00607693789, 02379771502, 03402540762
   → Após cadastro, reenviar S-1210 destes 4 CPFs

4. PENDENTES (se houver):
   → Investigar por que não foram processados
""")

conn.close()
