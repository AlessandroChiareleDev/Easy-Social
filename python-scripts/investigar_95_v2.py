"""
Investiga os 95 CPFs: verifica se tem S-1210 em outros periodos,
se o S-1200 deles tem dados de remuneração, e se S-1299 exige match.
"""
import psycopg2, json, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from db_config import DB_CONFIG

conn = psycopg2.connect(**DB_CONFIG, keepalives=1, keepalives_idle=30,
                        keepalives_interval=10, keepalives_count=3)
cur = conn.cursor()

CPFS_95 = [
    "00461533731","01279031603","02257065123","02364249635","03041655900",
    "03051738123","03295891729","04183457165","04207536647","04290812511",
    "04392879283","04695980932","04801791158","04919191669","05010712539",
    "05082777955","05141932125","05403290702","05490841770","05849050175",
    "05934498517","06184644173","06414328790","06512320662","06805381193",
    "07153625771","07391181617","07436843621","07525539502","07548205724",
    "07718690610","08676969744","08895733525","08994040730","09015688729",
    "09222639731","09542003730","09989762104","10100241670","10161816630",
    "10303614790","10454176619","10495889750","11064476627","12527304702",
    "12856662676","13277593657","13390020438","13508277704","13764774754",
    "13825584739","13871389609","14036243640","14128742708","14360221770",
    "14630384707","15047289710","15780991618","16189196799","16276547638",
    "17146741770","17673464764","18611197712","19119141700","20459500775",
    "20613816773","21279608587","21822341795","21839114843","23300584892",
    "27073887850","28268263873","32340870836","36062807850","40896047881",
    "41156927587","41599656876","51321262191","53978250772","55064162880",
    "67067581915","70195999665","70299054403","70403722667","79099866615",
    "80039022749","81261411587","82157260544","83502262268","86422009526",
    "86473438599","86540357575","88282767620","96756322672","97427632591",
]

# 1) Check S-1200 dados_json para um sample de CPFs (ver se tem remuneracao)
print("=" * 60)
print("AMOSTRA: dados_json dos S-1200 (primeiros 3 CPFs)")
print("=" * 60)
for cpf in CPFS_95[:3]:
    cur.execute("""
        SELECT nr_recibo, dados_json, created_at
        FROM explorador_eventos
        WHERE cpf = %s AND per_apur = '2025-09' AND tipo_evento = 'S-1200'
        ORDER BY created_at DESC LIMIT 1
    """, (cpf,))
    row = cur.fetchone()
    if row:
        dados = row[1] if isinstance(row[1], dict) else json.loads(row[1] or '{}')
        print(f"\nCPF {cpf} (recibo={row[0]}):")
        # Just print first 500 chars of dados
        dados_str = json.dumps(dados, indent=2, ensure_ascii=False)
        print(dados_str[:800])

# 2) Do these CPFs have S-1210 in ANY period?
print("\n" + "=" * 60)
print("S-1210 em QUALQUER periodo para os 95 CPFs:")
print("=" * 60)
cur.execute("""
    SELECT cpf, per_apur, COUNT(*)
    FROM explorador_eventos
    WHERE cpf = ANY(%s) AND tipo_evento = 'S-1210'
    GROUP BY cpf, per_apur
    ORDER BY cpf, per_apur
""", (CPFS_95,))
rows = cur.fetchall()
if rows:
    for r in rows:
        print(f"  {r[0]} per={r[1]} count={r[2]}")
else:
    print("  NENHUM S-1210 em qualquer periodo!")

# 3) Check: quantos CPFs tem S-1210 mas NÃO tem S-1200 em 2025-09?
print("\n" + "=" * 60)
print("CPFs com S-1210 mas sem S-1200 em 2025-09:")
print("=" * 60)
cur.execute("""
    SELECT COUNT(DISTINCT cpf) FROM explorador_eventos
    WHERE per_apur = '2025-09' AND tipo_evento = 'S-1210'
      AND cpf NOT IN (
          SELECT DISTINCT cpf FROM explorador_eventos
          WHERE per_apur = '2025-09' AND tipo_evento = 'S-1200'
      )
""")
cnt = cur.fetchone()[0]
print(f"  {cnt} CPFs com S-1210 sem S-1200")

# 4) Check the S-1299 events - errors from previous attempts
print("\n" + "=" * 60)
print("S-1299 existentes em 2025-09:")
print("=" * 60)
cur.execute("""
    SELECT nr_recibo, created_at, dados_json
    FROM explorador_eventos
    WHERE per_apur = '2025-09' AND tipo_evento = 'S-1299'
    ORDER BY created_at
""")
for r in cur.fetchall():
    print(f"  recibo={r[0]} em {r[1]}")

# 5) Check pipeline_runs table
print("\n" + "=" * 60)
print("pipeline_runs:")
print("=" * 60)
cur.execute("""
    SELECT id, per_apur, status, total_cpfs, cpfs_ok, cpfs_erro, 
           created_at, lote_atual, total_lotes
    FROM pipeline_runs
    ORDER BY created_at
""")
for r in cur.fetchall():
    print(f"  id={r[0]} per={r[1]} status={r[2]} total={r[3]} ok={r[4]} erro={r[5]} lote={r[7]}/{r[8]} created={r[6]}")

conn.close()
