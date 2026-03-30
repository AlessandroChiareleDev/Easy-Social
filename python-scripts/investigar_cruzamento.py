"""
Investigar se os códigos de natureza expirados já foram resolvidos 
nas tabelas de cruzamento / analise_natureza_certo / correcoes_staging.

Hipótese: as 91 rubricas VERIFICAR foram corrigidas no Validador,
gerando naturezas novas. Essas naturezas foram usadas no cruzamento.
Se alguma das 48 rubricas com natRubr expirado está entre essas 91,
o problema já pode estar resolvido.
"""
import psycopg2
import json

conn = psycopg2.connect(
    host='localhost', port=5432, dbname='easy_social_db',
    user='easy_social_user', password='sua_senha_segura'
)
cur = conn.cursor()

print("=" * 80)
print("INVESTIGAÇÃO: Naturezas corrigidas no Validador vs. Problemas natRubr")
print("=" * 80)

# 1. Ver tabelas relacionadas
print("\n### 1. TABELAS DISPONÍVEIS ###")
cur.execute("""
SELECT table_name FROM information_schema.tables 
WHERE table_schema='public' 
AND (table_name LIKE '%natureza%' OR table_name LIKE '%cruzamento%' 
     OR table_name LIKE '%staging%' OR table_name LIKE '%certo%')
ORDER BY table_name
""")
for r in cur.fetchall():
    cur.execute(f"SELECT COUNT(*) FROM {r[0]}")
    cnt = cur.fetchone()[0]
    print(f"  {r[0]}: {cnt} registros")

# 2. analise_natureza_certo — as correções do Validador
print("\n### 2. ANALISE_NATUREZA_CERTO (correções do Validador) ###")
cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name='analise_natureza_certo' ORDER BY ordinal_position")
cols = [r[0] for r in cur.fetchall()]
print(f"  Colunas: {cols}")

cur.execute("SELECT COUNT(*) FROM analise_natureza_certo")
total_certo = cur.fetchone()[0]
print(f"  Total registros: {total_certo}")

# Amostra
cur.execute("SELECT * FROM analise_natureza_certo LIMIT 3")
col_names = [d[0] for d in cur.description]
rows = cur.fetchall()
print(f"  Colunas: {col_names}")
for row in rows:
    print(f"  -> {dict(zip(col_names, row))}")

# 3. correcoes_staging
print("\n### 3. CORRECOES_STAGING ###")
cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name='correcoes_staging' ORDER BY ordinal_position")
cols = [r[0] for r in cur.fetchall()]
print(f"  Colunas: {cols}")

cur.execute("SELECT COUNT(*) FROM correcoes_staging")
print(f"  Total: {cur.fetchone()[0]}")

cur.execute("SELECT * FROM correcoes_staging LIMIT 3")
col_names = [d[0] for d in cur.description]
rows = cur.fetchall()
for row in rows:
    d = dict(zip(col_names, row))
    print(f"  -> cod={d.get('col_a','?')} nat_anterior={d.get('natureza_anterior','?')} nat_nova={d.get('natureza_nova','?')}")

# 4. cruzamento_resultado
print("\n### 4. CRUZAMENTO_RESULTADO ###")
cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name='cruzamento_resultado' ORDER BY ordinal_position")
cols = [r[0] for r in cur.fetchall()]
print(f"  Colunas: {cols}")

cur.execute("SELECT COUNT(*) FROM cruzamento_resultado")
total_cruz = cur.fetchone()[0]
print(f"  Total: {total_cruz}")

cur.execute("SELECT * FROM cruzamento_resultado LIMIT 3")
col_names = [d[0] for d in cur.description]
rows = cur.fetchall()
for row in rows:
    d = dict(zip(col_names, row))
    # Print relevant fields
    for k in ['codigo', 'nome_evento', 'natureza_esocial', 'cod_inss', 'cod_irrf', 'cod_fgts']:
        if k in d:
            print(f"    {k}: {d[k]}")
    print("    ---")

# 5. CRUZAR: quais das 48 bloqueadas (natRubr expirado) têm natureza corrigida no staging?
print("\n### 5. CRUZAMENTO: Bloqueadas × Correções do Validador ###")

# Pegar códigos das 48 rubricas bloqueadas
cur.execute("""
SELECT rc.cod_rubrica, te.raw_data->>'Cód. Natureza' AS nat_gl
FROM rubrica_corrections rc
JOIN tabela_eventos_gl te ON te.raw_data->>'Código' = rc.cod_rubrica
LEFT JOIN esocial_tabela3_natureza t3 ON t3.codigo = (te.raw_data->>'Cód. Natureza')::int
WHERE rc.status = 'pendente' AND t3.dt_fim IS NOT NULL
ORDER BY rc.cod_rubrica::int
""")
bloqueadas = cur.fetchall()
bloq_codes = [r[0] for r in bloqueadas]
print(f"  Rubricas bloqueadas (natRubr expirado): {len(bloq_codes)}")

# Verificar no correcoes_staging
cur.execute("SELECT codigoevento, natureza_anterior, natureza_nova_codigo, natureza_nova_nome, status FROM correcoes_staging")
staging_map = {}
for row in cur.fetchall():
    staging_map[str(row[0])] = {'anterior': row[1], 'nova_codigo': row[2], 'nova_nome': row[3], 'status': row[4]}

print(f"  Correções no staging: {len(staging_map)}")

# Verificar no cruzamento_resultado
cur.execute("SELECT codigo, natureza_esocial FROM cruzamento_resultado")
cruz_map = {}
for row in cur.fetchall():
    cruz_map[str(row[0])] = row[1]

print(f"  Registros no cruzamento_resultado: {len(cruz_map)}")

# Cruzar
print(f"\n  === RESULTADO DO CRUZAMENTO ===")
resolvidas = 0
nao_resolvidas = 0
for cod, nat_gl in bloqueadas:
    staging = staging_map.get(cod)
    cruz = cruz_map.get(cod)
    
    # Extrair código numérico da natureza no cruzamento
    nat_cruz_code = None
    if cruz:
        # Formato pode ser "1016 - Férias" ou "1016-Férias"
        parts = str(cruz).split('-')
        if parts[0].strip().isdigit():
            nat_cruz_code = int(parts[0].strip())
    
    # Verificar se a natureza no cruzamento é diferente e vigente
    status = "?"
    nat_nova = None
    if staging and staging['nova_codigo']:
        nat_nova = int(staging['nova_codigo']) if str(staging['nova_codigo']).isdigit() else None
    
    # Verificar vigência da nova natureza
    vigente = False
    check_code = nat_nova or nat_cruz_code
    if check_code and check_code != int(nat_gl):
        cur.execute("SELECT dt_fim FROM esocial_tabela3_natureza WHERE codigo = %s", (check_code,))
        result = cur.fetchone()
        if result and result[0] is None:
            vigente = True
            status = "RESOLVIDO"
            resolvidas += 1
        elif result and result[0] is not None:
            status = f"NOVA TAMBEM EXPIRADA ({check_code})"
            nao_resolvidas += 1
        else:
            status = f"NOVA NAO ENCONTRADA ({check_code})"
            nao_resolvidas += 1
    else:
        status = "NÃO CORRIGIDO"
        nao_resolvidas += 1
    
    staging_info = f"staging: {staging['anterior']}→{staging['nova_codigo']}-{staging['nova_nome']} ({staging['status']})" if staging else "sem staging"
    cruz_info = f"cruz: {cruz}" if cruz else "sem cruzamento"
    
    print(f"  Rub {cod:>5} | GL={nat_gl} | {staging_info} | {cruz_info} | {status}")

print(f"\n  RESOLVIDAS pelo Validador: {resolvidas}/{len(bloqueadas)}")
print(f"  NÃO RESOLVIDAS: {nao_resolvidas}/{len(bloqueadas)}")

# 6. ANÁLISE EXTRA: Ver TODAS as correções do staging para entender o padrão
print("\n### 6. TODAS AS CORREÇÕES DO STAGING ###")
cur.execute("""
SELECT codigoevento, natureza_anterior, natureza_nova_codigo, natureza_nova_nome, status 
FROM correcoes_staging 
ORDER BY codigoevento::int
""")
for row in cur.fetchall():
    print(f"  Cod {row[0]:>5} | {row[1]} → {row[2]}-{row[3]} | status={row[4]}")

conn.close()
