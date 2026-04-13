"""Investigar por que 95 CPFs tem S-1200 mas nunca entraram no pipeline."""
import psycopg2, sys, os
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

# Checar quantos S-1200 cada um tem
cur.execute("""
    SELECT cpf, COUNT(*), array_agg(nr_recibo ORDER BY created_at DESC)
    FROM explorador_eventos
    WHERE cpf = ANY(%s) AND per_apur = '2025-09' AND tipo_evento = 'S-1200'
    GROUP BY cpf
    ORDER BY cpf
""", (CPFS_95,))
print("S-1200 por CPF:")
for r in cur.fetchall():
    print(f"  {r[0]}: {r[1]} evento(s), recibos={r[2][:2]}")

# Checar se tem S-3000 pra eles
cur.execute("""
    SELECT cpf, COUNT(*)
    FROM explorador_eventos
    WHERE cpf = ANY(%s) AND per_apur = '2025-09' AND tipo_evento = 'S-3000'
    GROUP BY cpf
""", (CPFS_95,))
s3000 = cur.fetchall()
print(f"\nCPFs com S-3000: {len(s3000)}")

# Checar se estao na tabela de trabalhadores/folha
try:
    cur.execute("""
        SELECT column_name FROM information_schema.columns
        WHERE table_name = 'pipeline_cpf_results' ORDER BY ordinal_position
    """)
    cols = [r[0] for r in cur.fetchall()]
    print(f"\npipeline_cpf_results columns: {cols}")
except:
    pass

# Ver total de CPFs no pipeline vs total de S-1200
cur.execute("SELECT COUNT(DISTINCT cpf) FROM pipeline_cpf_results")
total_pipeline = cur.fetchone()[0]
cur.execute("""
    SELECT COUNT(DISTINCT cpf) FROM explorador_eventos
    WHERE per_apur = '2025-09' AND tipo_evento = 'S-1200'
""")
total_s1200 = cur.fetchone()[0]
print(f"\nTotal CPFs pipeline: {total_pipeline}")
print(f"Total CPFs S-1200: {total_s1200}")
print(f"Diferenca: {total_s1200 - total_pipeline}")

# Checar quais S-1200 desses 95 foram do pipeline (Oct 24) vs originais (Oct 2/6)
cur.execute("""
    SELECT cpf, created_at, nr_recibo
    FROM explorador_eventos
    WHERE cpf = ANY(%s) AND per_apur = '2025-09' AND tipo_evento = 'S-1200'
    ORDER BY cpf, created_at
""", (CPFS_95,))
print(f"\nDetalhe S-1200 dos 95 CPFs:")
for r in cur.fetchall():
    print(f"  {r[0]} created={r[1]} recibo={r[2]}")

# Checar se tem eventos de QUALQUER tipo pra primeiro CPF
sample = CPFS_95[0]
cur.execute("""
    SELECT tipo_evento, nr_recibo, created_at
    FROM explorador_eventos
    WHERE cpf = %s AND per_apur = '2025-09'
    ORDER BY created_at
""", (sample,))
print(f"\nTodos eventos para {sample}:")
for r in cur.fetchall():
    print(f"  {r[0]} recibo={r[1]} em {r[2]}")

conn.close()
