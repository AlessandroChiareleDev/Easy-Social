import psycopg2

conn = psycopg2.connect(host='localhost', port=5432, dbname='easy_social_db', user='easy_social_user', password='sua_senha_segura')
cur = conn.cursor()

# Buscar rubricas com DSR/DIF no nome que estao como VERIFICAR
cur.execute("""
    SELECT id, col_a, col_b, col_c, col_d, col_f 
    FROM analise_natureza 
    WHERE (UPPER(col_b) LIKE '%DSR%' OR UPPER(col_b) LIKE '%DIF%')
    AND UPPER(TRIM(col_d)) = 'VERIFICAR' 
    LIMIT 15
""")
rows = cur.fetchall()
print('=== Rubricas DSR/DIF com VERIFICAR ===')
for r in rows:
    print(f'id={r[0]} | cod={r[1]} | nome={r[2]}')
    print(f'  nat_atual={r[3]} | col_f={r[5]}')
    print()

# Buscar naturezas que tem relacao com DSR/descanso
cur.execute("""
    SELECT codigo, nome, data_fim
    FROM naturezas_esocial 
    WHERE LOWER(nome) LIKE '%descanso%' OR LOWER(nome) LIKE '%dsr%' 
    OR LOWER(descricao) LIKE '%descanso%' OR LOWER(descricao) LIKE '%dsr%'
    ORDER BY codigo
""")
rows2 = cur.fetchall()
print('=== Naturezas com DSR/descanso ===')
for r in rows2:
    ativo = "ATIVA" if r[2] is None else f"INATIVA ({r[2]})"
    print(f'  {r[0]} | {r[1]} | {ativo}')

# Naturezas com diferenca/DIF
cur.execute("""
    SELECT codigo, nome, data_fim
    FROM naturezas_esocial 
    WHERE LOWER(nome) LIKE '%diferenca%' OR LOWER(nome) LIKE '%diferença%'
    OR LOWER(descricao) LIKE '%diferenca%' OR LOWER(descricao) LIKE '%diferença%'
    ORDER BY codigo
""")
rows3 = cur.fetchall()
print('\n=== Naturezas com diferença ===')
for r in rows3:
    ativo = "ATIVA" if r[2] is None else f"INATIVA ({r[2]})"
    print(f'  {r[0]} | {r[1]} | {ativo}')

# Testar tokenização: simular o que o backend faz
import unicodedata, re
STOPWORDS = {"de","do","da","dos","das","em","no","na","nos","nas","por","para","com","sem","sob","sobre","entre","até","ao","aos","à","às","um","uma","uns","umas","o","a","os","as","e","ou","que","se","não","mes","mês","anterior","ref","outros","outras"}

def tokenize(text):
    normalized = unicodedata.normalize('NFD', text.lower())
    normalized = re.sub(r'[\u0300-\u036f]', '', normalized)
    normalized = re.sub(r'[^a-z0-9\s]', ' ', normalized).strip()
    return [t for t in normalized.split() if len(t) > 2 and t not in STOPWORDS]

# Testar com nomes DSR reais
for r in rows[:5]:
    nome = r[2]
    tokens = tokenize(nome)
    print(f'\nTokens de "{nome}": {tokens}')

# Verificar quantas rubricar VERIFICAR tem col_f vazia ou sem codigo
cur.execute("""
    SELECT 
        COUNT(*) as total,
        COUNT(CASE WHEN col_f IS NULL OR TRIM(col_f) = '' OR TRIM(col_f) = '-' THEN 1 END) as sem_sugestao,
        COUNT(CASE WHEN col_f IS NOT NULL AND TRIM(col_f) != '' AND TRIM(col_f) != '-' THEN 1 END) as com_sugestao
    FROM analise_natureza 
    WHERE UPPER(TRIM(col_d)) = 'VERIFICAR'
""")
r = cur.fetchone()
print(f'\n=== Status col_f das rubricas VERIFICAR ===')
print(f'Total: {r[0]} | Sem sugestão: {r[1]} | Com sugestão: {r[2]}')

# Exemplos de col_f sem código numérico
cur.execute("""
    SELECT col_a, col_b, col_f 
    FROM analise_natureza 
    WHERE UPPER(TRIM(col_d)) = 'VERIFICAR'
    AND col_f IS NOT NULL AND TRIM(col_f) != '' AND TRIM(col_f) != '-'
    LIMIT 20
""")
print('\n=== Exemplos de col_f (sugestões humanas) ===')
for r in cur.fetchall():
    print(f'  {r[0]} | {r[1]} | col_f="{r[2]}"')

cur.close()
conn.close()
