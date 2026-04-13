"""Pre-flight check: estado do periodo setembro 2025 antes de fechar."""
import psycopg2, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from db_config import DB_CONFIG

conn = psycopg2.connect(**DB_CONFIG, keepalives=1, keepalives_idle=30,
                        keepalives_interval=10, keepalives_count=3)
cur = conn.cursor()

print("=" * 60)
print("  PRE-FLIGHT CHECK — FECHAR SETEMBRO 2025")
print("=" * 60)

# S-1298 (reaberturas)
cur.execute("""
    SELECT nr_recibo, created_at FROM explorador_eventos
    WHERE per_apur='2025-09' AND tipo_evento='S-1298'
    ORDER BY created_at
""")
rows = cur.fetchall()
print(f"\nS-1298 (reaberturas): {len(rows)}")
for r in rows:
    print(f"  recibo={r[0]} em {r[1]}")

# S-1299 (fechamentos)
cur.execute("""
    SELECT nr_recibo, created_at FROM explorador_eventos
    WHERE per_apur='2025-09' AND tipo_evento='S-1299'
    ORDER BY created_at
""")
rows = cur.fetchall()
print(f"\nS-1299 (fechamentos): {len(rows)}")
for r in rows:
    print(f"  recibo={r[0]} em {r[1]}")

# Contagem por tipo
cur.execute("""
    SELECT tipo_evento, COUNT(*)
    FROM explorador_eventos
    WHERE per_apur = '2025-09'
    GROUP BY tipo_evento
    ORDER BY tipo_evento
""")
print("\nContagem por tipo de evento:")
for r in cur.fetchall():
    print(f"  {r[0]}: {r[1]}")

# Pipeline status
cur.execute("SELECT status, cpfs_ok, cpfs_erro, total_cpfs FROM pipeline_runs WHERE id=1")
r = cur.fetchone()
print(f"\nPipeline run: status={r[0]}, ok={r[1]}, erro={r[2]}, total={r[3]}")

# S-1200 vs S-1210 match
cur.execute("SELECT COUNT(DISTINCT cpf) FROM explorador_eventos WHERE per_apur='2025-09' AND tipo_evento='S-1200'")
s1200 = cur.fetchone()[0]
cur.execute("SELECT COUNT(DISTINCT cpf) FROM explorador_eventos WHERE per_apur='2025-09' AND tipo_evento='S-1210'")
s1210 = cur.fetchone()[0]
print(f"\nS-1200 CPFs: {s1200}")
print(f"S-1210 CPFs: {s1210}")
print(f"S-1200 sem S-1210: {s1200 - s1210 if s1200 > s1210 else 0} (95 conhecidos)")
print(f"S-1210 sem S-1200: {s1210 - s1200 if s1210 > s1200 else 0}")

# Sequence check: S-1298 > S-1299 means period is OPEN
seq_check = "ABERTO" if len(rows) < len([1 for r2 in cur.execute("""SELECT 1 FROM explorador_eventos WHERE per_apur='2025-09' AND tipo_evento='S-1298'""") or []]) else "?"
# Simpler: check if last S-1298 is after last S-1299
cur.execute("""
    SELECT tipo_evento, created_at FROM explorador_eventos
    WHERE per_apur='2025-09' AND tipo_evento IN ('S-1298','S-1299')
    ORDER BY created_at DESC LIMIT 1
""")
ultimo = cur.fetchone()
if ultimo:
    print(f"\nUltimo evento de periodo: {ultimo[0]} em {ultimo[1]}")
    if ultimo[0] == 'S-1298':
        print("=> Periodo ABERTO (ultimo foi reabertura)")
    else:
        print("=> Periodo FECHADO (ultimo foi fechamento)")
else:
    print("\nNenhum S-1298/S-1299 encontrado")

print("\n" + "=" * 60)
print("  RESULTADO: ", end="")
print("PRONTO PARA FECHAR" if ultimo and ultimo[0] == 'S-1298' else "VERIFICAR!")
print("=" * 60)

conn.close()
