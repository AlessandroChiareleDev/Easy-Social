"""
Análise final: para cada rubrica bloqueada (natRubr expirado na GL),
verificar se a tabela analise_natureza_certo E cruzamento_resultado 
já contêm a natureza CORRETA vigente.
"""
import psycopg2

conn = psycopg2.connect(
    host='localhost', port=5432, dbname='easy_social_db',
    user='easy_social_user', password='sua_senha_segura'
)
cur = conn.cursor()

# As 48 bloqueadas
cur.execute("""
SELECT rc.cod_rubrica, rc.descricao, te.raw_data->>'Cód. Natureza' AS nat_gl
FROM rubrica_corrections rc
JOIN tabela_eventos_gl te ON te.raw_data->>'Código' = rc.cod_rubrica
LEFT JOIN esocial_tabela3_natureza t3 ON t3.codigo = (te.raw_data->>'Cód. Natureza')::int
WHERE rc.status = 'pendente' AND t3.dt_fim IS NOT NULL
ORDER BY rc.cod_rubrica::int
""")
bloqueadas = cur.fetchall()

print("=" * 120)
print(f"{'Rub':>5} | {'Descrição':<35} | {'GL(expirado)':>12} | {'AN_Certo':>30} | {'Cruzamento':>30} | {'Staging':>15} | Status")
print("-" * 120)

resolvido = 0
parcial = 0
nao_resolvido = 0

for cod, desc, nat_gl in bloqueadas:
    # analise_natureza_certo — col_c contém a natureza (pode ter sido corrigida)
    cur.execute("SELECT col_c, natureza_nova FROM analise_natureza_certo WHERE col_a = %s", (cod,))
    an_row = cur.fetchone()
    an_nat = an_row[0] if an_row else None
    an_nova = an_row[1] if an_row else None
    
    # cruzamento_resultado
    cur.execute("SELECT natureza_esocial FROM cruzamento_resultado WHERE codigo = %s", (cod,))
    cruz_row = cur.fetchone()
    cruz_nat = cruz_row[0] if cruz_row else None
    
    # correcoes_staging
    cur.execute("SELECT natureza_nova_codigo, natureza_nova_nome FROM correcoes_staging WHERE codigoevento = %s", (str(cod),))
    stg_row = cur.fetchone()
    stg = f"{stg_row[0]}-{stg_row[1][:15]}" if stg_row else "-"
    
    # Determinar a natureza final (prioridade: staging > an_nova > cruz > an)
    nat_final = None
    fonte = None
    
    if stg_row and stg_row[0]:
        nat_code = int(stg_row[0]) if str(stg_row[0]).isdigit() else None
        if nat_code:
            cur.execute("SELECT dt_fim FROM esocial_tabela3_natureza WHERE codigo = %s", (nat_code,))
            t3 = cur.fetchone()
            if t3 and t3[0] is None:
                nat_final = nat_code
                fonte = "STAGING"
    
    if not nat_final and an_nova:
        parts = str(an_nova).split('-')
        if parts[0].strip().isdigit():
            nat_code = int(parts[0].strip())
            cur.execute("SELECT dt_fim FROM esocial_tabela3_natureza WHERE codigo = %s", (nat_code,))
            t3 = cur.fetchone()
            if t3 and t3[0] is None:
                nat_final = nat_code
                fonte = "AN_NOVA"
    
    if not nat_final and cruz_nat:
        parts = str(cruz_nat).split('-')
        if parts[0].strip().isdigit():
            nat_code = int(parts[0].strip())
            if nat_code != int(nat_gl):  # diferente do expirado
                cur.execute("SELECT dt_fim FROM esocial_tabela3_natureza WHERE codigo = %s", (nat_code,))
                t3 = cur.fetchone()
                if t3 and t3[0] is None:
                    nat_final = nat_code
                    fonte = "CRUZAMENTO"
    
    if not nat_final and an_nat:
        parts = str(an_nat).split('-')
        if parts[0].strip().isdigit():
            nat_code = int(parts[0].strip())
            if nat_code != int(nat_gl):
                cur.execute("SELECT dt_fim FROM esocial_tabela3_natureza WHERE codigo = %s", (nat_code,))
                t3 = cur.fetchone()
                if t3 and t3[0] is None:
                    nat_final = nat_code
                    fonte = "AN_CERTO"
    
    if nat_final:
        status = f"RESOLVIDO ({fonte}→{nat_final})"
        resolvido += 1
    else:
        status = "PENDENTE"
        nao_resolvido += 1
    
    an_display = str(an_nat)[:30] if an_nat else "-"
    cruz_display = str(cruz_nat)[:30] if cruz_nat else "-"
    
    print(f"{cod:>5} | {desc[:35]:<35} | {nat_gl:>12} | {an_display:>30} | {cruz_display:>30} | {stg:>15} | {status}")

print("-" * 120)
print(f"\nRESUMO:")
print(f"  RESOLVIDO (natureza nova vigente encontrada): {resolvido}/48")
print(f"  PENDENTE (sem correção disponível):           {nao_resolvido}/48")

# Agora mostrar quais das NÃO-bloqueadas (335 OK na GL) também têm natureza
# diferente no cruzamento/staging
print("\n\n" + "=" * 80)
print("BÔNUS: Rubricas com natRubr OK na GL mas que foram corrigidas no Validador")
print("=" * 80)
cur.execute("""
SELECT rc.cod_rubrica, te.raw_data->>'Cód. Natureza' AS nat_gl,
       cr.natureza_esocial AS nat_cruz
FROM rubrica_corrections rc
JOIN tabela_eventos_gl te ON te.raw_data->>'Código' = rc.cod_rubrica
LEFT JOIN esocial_tabela3_natureza t3 ON t3.codigo = (te.raw_data->>'Cód. Natureza')::int
LEFT JOIN cruzamento_resultado cr ON cr.codigo = rc.cod_rubrica
WHERE rc.status = 'pendente' AND t3.dt_fim IS NULL AND t3.codigo IS NOT NULL
AND cr.natureza_esocial IS NOT NULL
ORDER BY rc.cod_rubrica::int
LIMIT 20
""")
print("Amostra (20 primeiras):")
different = 0
for row in cur.fetchall():
    cruz_code = row[2].split('-')[0].strip() if row[2] else None
    marker = " *DIFERENTE*" if cruz_code and cruz_code != row[1] else ""
    if marker:
        different += 1
    print(f"  Rub {row[0]:>5} | GL={row[1]} | Cruz={row[2]}{marker}")

cur.execute("""
SELECT COUNT(*) FROM rubrica_corrections rc
JOIN tabela_eventos_gl te ON te.raw_data->>'Código' = rc.cod_rubrica
LEFT JOIN cruzamento_resultado cr ON cr.codigo = rc.cod_rubrica
WHERE rc.status = 'pendente' 
AND cr.natureza_esocial IS NOT NULL
AND SPLIT_PART(cr.natureza_esocial, '-', 1) != te.raw_data->>'Cód. Natureza'
""")
total_diff = cur.fetchone()[0]
print(f"\nTotal rubricas pendentes onde o cruzamento tem natRubr DIFERENTE da GL: {total_diff}")

conn.close()
