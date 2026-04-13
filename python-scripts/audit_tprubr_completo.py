"""
Auditoria COMPLETA de tpRubr para TODAS as rubricas do sistema.

Fontes consultadas:
1. cruzamento_eb — rubricas enviadas ao eSocial
2. explorador_rubricas — tpRubr real (importado dos XMLs do eSocial)
3. esocial_depara — mapeamento manual/automático de tpRubr
4. tabela_marcos — possível fonte adicional
5. esocial_envios — histórico de envios (para saber quais foram enviadas)
6. base_ficha_financeira / planilha_1 — podem ter info de tipo

Objetivo: para cada rubrica enviada, descobrir se tpRubr=1 estava ERRADO
(deveria ser 2=Desconto) e listar as que precisam correção.
"""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from db_config import DB_CONFIG
import psycopg2, psycopg2.extras

conn = psycopg2.connect(**DB_CONFIG, keepalives=1, keepalives_idle=30, keepalives_interval=10, keepalives_count=3)
cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

# ══════════════════════════════════════════════════════════════
# 1) Listar TODAS as tabelas disponíveis
# ══════════════════════════════════════════════════════════════
print("=" * 80)
print("AUDITORIA COMPLETA DE tpRubr")
print("=" * 80)

cur.execute("""
    SELECT table_name FROM information_schema.tables 
    WHERE table_schema = 'public' ORDER BY table_name
""")
all_tables = [r['table_name'] for r in cur.fetchall()]
print(f"\nTabelas no banco: {len(all_tables)}")
for t in all_tables:
    print(f"  {t}")

# ══════════════════════════════════════════════════════════════
# 2) Verificar tabela_marcos
# ══════════════════════════════════════════════════════════════
print(f"\n{'='*80}")
print("TABELA_MARCOS")
print(f"{'='*80}")
if 'tabela_marcos' in all_tables:
    cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'tabela_marcos' ORDER BY ordinal_position")
    cols = [r['column_name'] for r in cur.fetchall()]
    print(f"Colunas: {cols}")
    cur.execute("SELECT count(*) as cnt FROM tabela_marcos")
    print(f"Total registros: {cur.fetchone()['cnt']}")
    # Check if it has tipo/tpRubr info
    tipo_cols = [c for c in cols if 'tipo' in c.lower() or 'tp' in c.lower() or 'rubr' in c.lower()]
    print(f"Colunas com tipo/rubr: {tipo_cols}")
    if tipo_cols:
        cur.execute(f"SELECT {','.join(tipo_cols)} FROM tabela_marcos LIMIT 5")
        for r in cur.fetchall(): print(f"  {dict(r)}")
else:
    print("tabela_marcos NÃO EXISTE")

# ══════════════════════════════════════════════════════════════
# 3) Verificar tabela_eventos_gl (possível tabela do Marcos)
# ══════════════════════════════════════════════════════════════
print(f"\n{'='*80}")
print("TABELA_EVENTOS_GL")
print(f"{'='*80}")
if 'tabela_eventos_gl' in all_tables:
    cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'tabela_eventos_gl' ORDER BY ordinal_position")
    cols = [r['column_name'] for r in cur.fetchall()]
    print(f"Colunas: {cols}")
    cur.execute("SELECT count(*) as cnt FROM tabela_eventos_gl")
    print(f"Total registros: {cur.fetchone()['cnt']}")
    tipo_cols = [c for c in cols if 'tipo' in c.lower() or 'tp' in c.lower()]
    if tipo_cols:
        cur.execute(f"SELECT * FROM tabela_eventos_gl LIMIT 3")
        for r in cur.fetchall(): print(f"  {dict(r)}")
else:
    print("tabela_eventos_gl NÃO EXISTE")

# ══════════════════════════════════════════════════════════════
# 4) Verificar base_ficha_financeira
# ══════════════════════════════════════════════════════════════
print(f"\n{'='*80}")
print("BASE_FICHA_FINANCEIRA")
print(f"{'='*80}")
if 'base_ficha_financeira' in all_tables:
    cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'base_ficha_financeira' ORDER BY ordinal_position")
    cols = [r['column_name'] for r in cur.fetchall()]
    print(f"Colunas: {cols}")
    cur.execute("SELECT count(*) as cnt FROM base_ficha_financeira")
    print(f"Total registros: {cur.fetchone()['cnt']}")
    tipo_cols = [c for c in cols if 'tipo' in c.lower() or 'tp' in c.lower()]
    print(f"Colunas com tipo: {tipo_cols}")
    if tipo_cols:
        cur.execute(f"SELECT DISTINCT {','.join(tipo_cols)} FROM base_ficha_financeira LIMIT 10")
        for r in cur.fetchall(): print(f"  {dict(r)}")
else:
    print("base_ficha_financeira NÃO EXISTE")

# ══════════════════════════════════════════════════════════════
# 5) Verificar planilha_1
# ══════════════════════════════════════════════════════════════
print(f"\n{'='*80}")
print("PLANILHA_1")
print(f"{'='*80}")
if 'planilha_1' in all_tables:
    cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'planilha_1' ORDER BY ordinal_position")
    cols = [r['column_name'] for r in cur.fetchall()]
    print(f"Colunas: {cols}")
    cur.execute("SELECT count(*) as cnt FROM planilha_1")
    print(f"Total registros: {cur.fetchone()['cnt']}")
    tipo_cols = [c for c in cols if 'tipo' in c.lower() or 'tp' in c.lower() or 'rubr' in c.lower() or 'cod' in c.lower()]
    print(f"Colunas relevantes: {tipo_cols}")
else:
    print("planilha_1 NÃO EXISTE")

# ══════════════════════════════════════════════════════════════
# 6) FONTE PRINCIPAL: explorador_rubricas (dados reais do eSocial)
# ══════════════════════════════════════════════════════════════
print(f"\n{'='*80}")
print("EXPLORADOR_RUBRICAS — tpRubr real do eSocial")
print(f"{'='*80}")

# Buscar o tpRubr correto para todas as rubricas (mais recente por cod_rubr)
cur.execute("""
    SELECT DISTINCT ON (cod_rubr) cod_rubr, tp_rubr, nat_rubr, cod_inc_irrf
    FROM explorador_rubricas
    WHERE tp_rubr IS NOT NULL
    ORDER BY cod_rubr, id DESC
""")
explorador_map = {}
for r in cur.fetchall():
    explorador_map[r['cod_rubr']] = {
        'tp_rubr': r['tp_rubr'],
        'nat_rubr': r['nat_rubr'],
        'cod_inc_irrf': r['cod_inc_irrf'],
    }
print(f"Rubricas com tpRubr no explorador: {len(explorador_map)}")

# Contagem por tipo
tipo_1 = sum(1 for v in explorador_map.values() if v['tp_rubr'] == '1')
tipo_2 = sum(1 for v in explorador_map.values() if v['tp_rubr'] == '2')
tipo_3 = sum(1 for v in explorador_map.values() if v['tp_rubr'] == '3')
tipo_4 = sum(1 for v in explorador_map.values() if v['tp_rubr'] == '4')
print(f"  Tipo 1 (Vencimento): {tipo_1}")
print(f"  Tipo 2 (Desconto):   {tipo_2}")
print(f"  Tipo 3 (Informativa): {tipo_3}")
print(f"  Tipo 4 (Informativa dedutora): {tipo_4}")

# ══════════════════════════════════════════════════════════════
# 7) DEPARA: esocial_depara tpRubr
# ══════════════════════════════════════════════════════════════
print(f"\n{'='*80}")
print("ESOCIAL_DEPARA — mapeamento tpRubr")
print(f"{'='*80}")
cur.execute("""
    SELECT cod_rubrica, valor_anterior, valor_novo, status
    FROM esocial_depara
    WHERE campo = 'tpRubr'
    ORDER BY cod_rubrica
""")
depara_map = {}
for r in cur.fetchall():
    depara_map[r['cod_rubrica']] = {
        'valor_anterior': r['valor_anterior'],
        'valor_novo': r['valor_novo'],
        'status': r['status'],
    }
print(f"Rubricas com depara tpRubr: {len(depara_map)}")
# Contagem
depara_1 = sum(1 for v in depara_map.values() if v['valor_novo'] == '1')
depara_2 = sum(1 for v in depara_map.values() if v['valor_novo'] == '2')
print(f"  Para tipo 1: {depara_1}")
print(f"  Para tipo 2: {depara_2}")

# ══════════════════════════════════════════════════════════════
# 8) CRUZAMENTO: rubricas enviadas ao eSocial (cruzamento_eb)
# ══════════════════════════════════════════════════════════════
print(f"\n{'='*80}")
print("CRUZAMENTO_EB — rubricas enviadas ao eSocial")
print(f"{'='*80}")
cur.execute("""
    SELECT cod_rubrica, descricao, envio_status, cod_natureza
    FROM cruzamento_eb
    WHERE envio_status IN ('enviado', 'feito')
    ORDER BY cod_rubrica::int
""")
enviadas = cur.fetchall()
print(f"Total rubricas com envio_status='enviado'/'feito': {len(enviadas)}")

# ══════════════════════════════════════════════════════════════
# 9) ANÁLISE FINAL: quais foram enviadas com tpRubr ERRADO?
# ══════════════════════════════════════════════════════════════
print(f"\n{'='*80}")
print("ANÁLISE FINAL — Rubricas enviadas com tpRubr ERRADO")
print(f"{'='*80}")

erradas = []
corretas = []
sem_referencia = []

for rub in enviadas:
    cod = rub['cod_rubrica']
    desc = rub['descricao'] or ''
    
    # Determinar o tpRubr REAL
    tp_real = None
    fonte = None
    
    # Prioridade: explorador_rubricas (dados reais do eSocial)
    if cod in explorador_map:
        tp_real = explorador_map[cod]['tp_rubr']
        fonte = 'explorador'
    # Fallback: esocial_depara
    elif cod in depara_map:
        tp_real = depara_map[cod]['valor_novo']
        fonte = 'depara'
    
    # Se não achou em nenhum lugar, tentar inferir pela natureza/descrição
    if not tp_real:
        # Natureza 9xxx geralmente é desconto
        nat = (rub['cod_natureza'] or '').split(' - ')[0].strip()
        if nat.startswith('9'):
            tp_real = '2'
            fonte = 'inferido_nat9xxx'
        # Descrição com "DESC" geralmente é desconto
        elif desc.upper().startswith('DESC'):
            tp_real = '2'
            fonte = 'inferido_desc'
        else:
            sem_referencia.append(cod)
            continue
    
    # TODAS foram enviadas como tpRubr=1 pelo bug
    tp_enviado = '1'
    
    if tp_real != tp_enviado:
        erradas.append({
            'cod': cod,
            'desc': desc[:60],
            'tp_enviado': tp_enviado,
            'tp_real': tp_real,
            'fonte': fonte,
            'nat': explorador_map.get(cod, {}).get('nat_rubr', ''),
        })
    else:
        corretas.append(cod)

print(f"\n  Total enviadas: {len(enviadas)}")
print(f"  Corretas (já eram tipo 1): {len(corretas)}")
print(f"  ERRADAS (enviadas como 1, deveriam ser outro): {len(erradas)}")
print(f"  Sem referência (tipo desconhecido): {len(sem_referencia)}")

if erradas:
    print(f"\n{'─'*80}")
    print(f"RUBRICAS COM tpRubr ERRADO (todas enviadas como 1, deveria ser diferente):")
    print(f"{'─'*80}")
    print(f"{'Cod':<8} {'tpEnviado':<10} {'tpCorreto':<10} {'Fonte':<15} {'NatRubr':<8} {'Descrição'}")
    print(f"{'─'*8} {'─'*9} {'─'*9} {'─'*14} {'─'*7} {'─'*40}")
    for e in erradas:
        print(f"{e['cod']:<8} {e['tp_enviado']:<10} {e['tp_real']:<10} {e['fonte']:<15} {e['nat']:<8} {e['desc']}")

if sem_referencia:
    print(f"\n{'─'*80}")
    print(f"RUBRICAS SEM REFERÊNCIA DE TIPO (cods): {sem_referencia}")
    print(f"(Estas precisam verificação manual)")

# Listar também as corretas para referência
if corretas:
    print(f"\n{'─'*80}")
    print(f"RUBRICAS QUE JÁ ESTAVAM CORRETAS (tipo 1 = Vencimento):")
    print(f"{'─'*80}")
    for cod in corretas:
        info = explorador_map.get(cod, depara_map.get(cod, {}))
        desc_rub = next((r['descricao'] for r in enviadas if r['cod_rubrica'] == cod), '')
        print(f"  {cod}: {desc_rub[:60]}")

# ══════════════════════════════════════════════════════════════
# 10) Verificar se 571/572 já foram corrigidas
# ══════════════════════════════════════════════════════════════
print(f"\n{'='*80}")
print("STATUS 571/572 (já corrigidas hoje)")
print(f"{'='*80}")
for cod in ['571', '572']:
    if cod in [e['cod'] for e in erradas]:
        print(f"  {cod}: AINDA NA LISTA DE ERRADAS (mas já foi reenviada com tpRubr=2)")
    else:
        print(f"  {cod}: não está na lista de erradas")

conn.close()
