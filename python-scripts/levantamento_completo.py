"""
Levantamento completo de todos os problemas que impedem o envio S-1010.
Analisa cada dimensão: natRubr, tpRubr, codIncCP, codIncIRRF, codIncFGTS, codIncPisPasep, dscRubr.
"""
import psycopg2
import json

conn = psycopg2.connect(
    host='localhost', port=5432, dbname='easy_social_db',
    user='easy_social_user', password='sua_senha_segura'
)
cur = conn.cursor()

print("=" * 80)
print("LEVANTAMENTO COMPLETO — PROBLEMAS PRÉ-ENVIO S-1010")
print("=" * 80)

# 1. VISÃO GERAL
print("\n### 1. VISÃO GERAL ###")
cur.execute("SELECT status, COUNT(*) FROM rubrica_corrections GROUP BY status ORDER BY status")
for row in cur.fetchall():
    print(f"  rubrica_corrections — status={row[0]}: {row[1]}")

cur.execute("SELECT COUNT(*) FROM tabela_eventos_gl")
print(f"  tabela_eventos_gl: {cur.fetchone()[0]} registros")

cur.execute("SELECT COUNT(*) FROM esocial_tabela3_natureza")
print(f"  esocial_tabela3_natureza: {cur.fetchone()[0]} registros")

cur.execute("SELECT COUNT(*) FROM esocial_tabela3_natureza WHERE dt_fim IS NULL")
print(f"  esocial_tabela3_natureza vigentes: {cur.fetchone()[0]}")

# 2. PROBLEMA 1: natRubr EXPIRADO
print("\n### 2. PROBLEMA: natRubr EXPIRADO (Tabela 3) ###")
cur.execute("""
SELECT (te.raw_data->>'Cód. Natureza')::int AS nat, t3.nome, t3.dt_fim, COUNT(*) AS qtd
FROM rubrica_corrections rc
JOIN tabela_eventos_gl te ON te.raw_data->>'Código' = rc.cod_rubrica
LEFT JOIN esocial_tabela3_natureza t3 ON t3.codigo = (te.raw_data->>'Cód. Natureza')::int
WHERE rc.status = 'pendente' AND t3.dt_fim IS NOT NULL
GROUP BY nat, t3.nome, t3.dt_fim
ORDER BY qtd DESC
""")
total_expirado = 0
for row in cur.fetchall():
    print(f"  natRubr={row[0]} ({row[1]}) — expirou {row[2]} — {row[3]} rubricas")
    total_expirado += row[3]
print(f"  TOTAL com natRubr expirado: {total_expirado}")

# 3. PROBLEMA 2: natRubr INEXISTENTE na Tabela 3
print("\n### 3. PROBLEMA: natRubr INEXISTENTE na Tabela 3 ###")
cur.execute("""
SELECT (te.raw_data->>'Cód. Natureza')::int AS nat, COUNT(*) AS qtd
FROM rubrica_corrections rc
JOIN tabela_eventos_gl te ON te.raw_data->>'Código' = rc.cod_rubrica
LEFT JOIN esocial_tabela3_natureza t3 ON t3.codigo = (te.raw_data->>'Cód. Natureza')::int
WHERE rc.status = 'pendente' AND t3.codigo IS NULL
GROUP BY nat ORDER BY qtd DESC
""")
rows = cur.fetchall()
if rows:
    for row in rows:
        print(f"  natRubr={row[0]} — {row[1]} rubricas (NÃO EXISTE na Tabela 3)")
else:
    print("  Nenhum — todos os códigos existem na Tabela 3")

# 4. PROBLEMA 3: tpRubr (tipo) — verificar se existe nos dados
print("\n### 4. PROBLEMA: tpRubr (tipo da rubrica) ###")
cur.execute("""
SELECT raw_data->>'tpRubr' AS tp, COUNT(*) 
FROM tabela_eventos_gl 
GROUP BY tp ORDER BY COUNT(*) DESC LIMIT 10
""")
rows = cur.fetchall()
if rows and rows[0][0] is not None:
    print("  tpRubr encontrado nos dados:")
    for row in rows:
        print(f"    tpRubr={row[0]}: {row[1]} rubricas")
else:
    print("  tpRubr NÃO existe nos dados da tabela_eventos_gl!")
    # Tentar buscar nos raw_data keys
    cur.execute("SELECT jsonb_object_keys(raw_data) FROM tabela_eventos_gl LIMIT 1")
    keys = [r[0] for r in cur.fetchall()]
    print(f"  Keys disponíveis: {keys}")
    cur.execute("SELECT DISTINCT jsonb_object_keys(raw_data) FROM tabela_eventos_gl")
    all_keys = sorted([r[0] for r in cur.fetchall()])
    print(f"  Todas as keys: {all_keys}")

# 5. PROBLEMA 4: codIncPisPasep — campo novo obrigatório no S-1.3
print("\n### 5. PROBLEMA: codIncPisPasep (novo campo S-1.3) ###")
cur.execute("""
SELECT raw_data->>'codIncPisPasep' AS pis, COUNT(*) 
FROM tabela_eventos_gl 
GROUP BY pis ORDER BY COUNT(*) DESC LIMIT 10
""")
rows = cur.fetchall()
if rows and rows[0][0] is not None:
    print("  codIncPisPasep encontrado nos dados:")
    for row in rows:
        print(f"    codIncPisPasep={row[0]}: {row[1]} rubricas")
else:
    print("  codIncPisPasep NÃO existe nos dados!")
    print("  → Campo OBRIGATÓRIO no S-1.3, precisa ser definido para CADA rubrica")

# 6. PROBLEMA 5: codIncCP (INSS) — valores válidos vs. dados
print("\n### 6. VERIFICAÇÃO: codIncCP (INSS - Tabela 04) ###")
cur.execute("""
SELECT te.raw_data->>'codIncCP' AS cp, COUNT(*) 
FROM rubrica_corrections rc
JOIN tabela_eventos_gl te ON te.raw_data->>'Código' = rc.cod_rubrica
WHERE rc.status = 'pendente'
GROUP BY cp ORDER BY COUNT(*) DESC
""")
print("  Valores de codIncCP nas pendentes:")
for row in cur.fetchall():
    print(f"    codIncCP={row[0]}: {row[1]} rubricas")

# 7. PROBLEMA 6: codIncIRRF — valores
print("\n### 7. VERIFICAÇÃO: codIncIRRF (IRRF - Tabela 21) ###")
cur.execute("""
SELECT te.raw_data->>'codIncIRRF' AS irrf, COUNT(*) 
FROM rubrica_corrections rc
JOIN tabela_eventos_gl te ON te.raw_data->>'Código' = rc.cod_rubrica
WHERE rc.status = 'pendente'
GROUP BY irrf ORDER BY COUNT(*) DESC
""")
print("  Valores de codIncIRRF nas pendentes:")
for row in cur.fetchall():
    print(f"    codIncIRRF={row[0]}: {row[1]} rubricas")

# 8. PROBLEMA 7: codIncFGTS — valores
print("\n### 8. VERIFICAÇÃO: codIncFGTS (FGTS - Tabela 22) ###")
cur.execute("""
SELECT te.raw_data->>'codIncFGTS' AS fgts, COUNT(*) 
FROM rubrica_corrections rc
JOIN tabela_eventos_gl te ON te.raw_data->>'Código' = rc.cod_rubrica
WHERE rc.status = 'pendente'
GROUP BY fgts ORDER BY COUNT(*) DESC
""")
print("  Valores de codIncFGTS nas pendentes:")
for row in cur.fetchall():
    print(f"    codIncFGTS={row[0]}: {row[1]} rubricas")

# 9. CAMPO dscRubr — verificar tamanho
print("\n### 9. VERIFICAÇÃO: dscRubr (descrição, max 100 chars) ###")
cur.execute("""
SELECT rc.cod_rubrica, LENGTH(te.raw_data->>'dscRubr') AS len, LEFT(te.raw_data->>'dscRubr', 50)
FROM rubrica_corrections rc
JOIN tabela_eventos_gl te ON te.raw_data->>'Código' = rc.cod_rubrica
WHERE rc.status = 'pendente' AND LENGTH(te.raw_data->>'dscRubr') > 100
""")
rows = cur.fetchall()
if rows:
    print(f"  {len(rows)} rubricas com dscRubr > 100 chars:")
    for r in rows:
        print(f"    Rubrica {r[0]}: {r[1]} chars — '{r[2]}...'")
else:
    print("  Todas dentro do limite de 100 chars ✓")

# 10. Validação de codIncCP vs tabela_corrections target
print("\n### 10. DIVERGÊNCIAS: codIncCP atual vs. correção proposta ###")
cur.execute("""
SELECT 
    rc.cod_rubrica,
    te.raw_data->>'codIncCP' AS cp_atual,
    rc.correcao_inss AS cp_correcao,
    te.raw_data->>'codIncIRRF' AS irrf_atual,
    rc.correcao_irrf AS irrf_correcao,
    te.raw_data->>'codIncFGTS' AS fgts_atual,
    rc.correcao_fgts AS fgts_correcao
FROM rubrica_corrections rc
JOIN tabela_eventos_gl te ON te.raw_data->>'Código' = rc.cod_rubrica
WHERE rc.status = 'pendente'
LIMIT 5
""")
print("  Amostra (5 primeiras):")
for r in cur.fetchall():
    print(f"    Rub {r[0]}: INSS {r[1]}→{r[2]}  IRRF {r[3]}→{r[4]}  FGTS {r[5]}→{r[6]}")

# 11. Estatísticas de divergência por tipo
print("\n### 11. DIVERGÊNCIAS POR TIPO ###")
cur.execute("""
SELECT 
    SUM(CASE WHEN te.raw_data->>'codIncCP' != rc.correcao_inss THEN 1 ELSE 0 END) AS div_inss,
    SUM(CASE WHEN te.raw_data->>'codIncIRRF' != rc.correcao_irrf THEN 1 ELSE 0 END) AS div_irrf,
    SUM(CASE WHEN te.raw_data->>'codIncFGTS' != rc.correcao_fgts THEN 1 ELSE 0 END) AS div_fgts,
    COUNT(*) AS total
FROM rubrica_corrections rc
JOIN tabela_eventos_gl te ON te.raw_data->>'Código' = rc.cod_rubrica
WHERE rc.status = 'pendente'
""")
row = cur.fetchone()
print(f"  INSS divergente: {row[0]}/{row[3]}")
print(f"  IRRF divergente: {row[1]}/{row[3]}")
print(f"  FGTS divergente: {row[2]}/{row[3]}")

# 12. RESUMO EXECUTIVO
print("\n" + "=" * 80)
print("RESUMO EXECUTIVO — O QUE PRECISA SER RESOLVIDO")
print("=" * 80)

cur.execute("SELECT COUNT(*) FROM rubrica_corrections WHERE status = 'pendente'")
total_pend = cur.fetchone()[0]

print(f"""
Total de rubricas pendentes: {total_pend}

BLOQUEADORES (impedem envio):
  1. natRubr EXPIRADO: {total_expirado} rubricas precisam de remapeamento
  2. codIncPisPasep: Campo OBRIGATÓRIO no S-1.3 que NÃO existe nos dados
  3. tpRubr: Verificar se está disponível nos dados

PRONTAS PARA ENVIO (após resolver bloqueadores acima):
  {total_pend - total_expirado} rubricas com natRubr OK

CAMPOS JÁ MAPEADOS (correções do Ponto 1):
  - codIncCP (INSS): correção via rubrica_corrections.correcao_inss
  - codIncIRRF (IRRF): correção via rubrica_corrections.correcao_irrf
  - codIncFGTS (FGTS): correção via rubrica_corrections.correcao_fgts
""")

conn.close()
