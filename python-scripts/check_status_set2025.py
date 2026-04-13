"""SOMENTE LEITURA - estado de setembro/2025."""
import psycopg2, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from db_config import DB_CONFIG
conn2 = psycopg2.connect(**DB_CONFIG)
cur2 = conn2.cursor()

# S-1298/S-1299
cur2.execute("""
    SELECT tipo_evento, COUNT(*), MAX(created_at)
    FROM explorador_eventos 
    WHERE tipo_evento IN ('S-1298', 'S-1299') AND per_apur = '2025-09'
    GROUP BY tipo_evento
""")
print("=== Eventos fechamento set/2025 ===")
for row in cur2.fetchall():
    print(f"  {row[0]}: {row[1]} eventos, ultimo: {row[2]}")

# Last S-1298/S-1299
cur2.execute("""
    SELECT tipo_evento, nr_recibo, created_at
    FROM explorador_eventos 
    WHERE tipo_evento IN ('S-1298', 'S-1299') AND per_apur = '2025-09'
    ORDER BY created_at DESC
    LIMIT 5
""")
print("\n=== Ultimos eventos S-1298/S-1299 ===")
for row in cur2.fetchall():
    print(f"  {row[0]} recibo={row[1]} em {row[2]}")

# Count unique CPFs per event type
cur2.execute("""
    SELECT tipo_evento, COUNT(DISTINCT cpf), COUNT(*)
    FROM explorador_eventos 
    WHERE per_apur = '2025-09' AND tipo_evento IN ('S-1200', 'S-1210', 'S-1299', 'S-1298', 'S-3000')
    GROUP BY tipo_evento
    ORDER BY tipo_evento
""")
print("\n=== CPFs por tipo de evento (set/2025) ===")
for row in cur2.fetchall():
    print(f"  {row[0]}: {row[1]} CPFs distintos, {row[2]} eventos total")

# CPFs with S-1200 but missing S-1210
cur2.execute("""
    SELECT COUNT(*) FROM (
        SELECT DISTINCT cpf FROM explorador_eventos 
        WHERE tipo_evento = 'S-1200' AND per_apur = '2025-09'
        EXCEPT
        SELECT DISTINCT cpf FROM explorador_eventos 
        WHERE tipo_evento = 'S-1210' AND per_apur = '2025-09'
    ) sub
""")
print(f"\nCPFs com S-1200 mas SEM S-1210: {cur2.fetchone()[0]}")

# Total distinct CPFs in the period
cur2.execute("""
    SELECT COUNT(DISTINCT cpf) FROM explorador_eventos 
    WHERE per_apur = '2025-09' AND tipo_evento = 'S-1200'
""")
print(f"Total CPFs com S-1200 em set/2025: {cur2.fetchone()[0]}")

# Check S-3000 - what was excluded?
cur2.execute("""
    SELECT tipo_evento, COUNT(DISTINCT cpf), COUNT(*)
    FROM explorador_eventos 
    WHERE per_apur = '2025-09' AND tipo_evento = 'S-3000'
    GROUP BY tipo_evento
""")
print("\n=== S-3000 (exclusoes) ===")
for row in cur2.fetchall():
    print(f"  {row[0]}: {row[1]} CPFs, {row[2]} eventos")

# How many S-1210 are NET (after S-3000 exclusions)?
# S-1210 that still have valid recibos (not excluded)
cur2.execute("""
    SELECT COUNT(DISTINCT cpf) 
    FROM explorador_eventos 
    WHERE tipo_evento = 'S-1210' AND per_apur = '2025-09'
    AND nr_recibo NOT IN (
        SELECT nr_recibo FROM explorador_eventos 
        WHERE tipo_evento = 'S-3000' AND per_apur = '2025-09'
        AND nr_recibo IS NOT NULL
    )
""")
# This won't work because S-3000 has its own recibo, not the deleted one
# Let me just check the timeline
print("\n=== Timeline (ultimos 20 eventos set/2025) ===")
cur2.execute("""
    SELECT tipo_evento, cpf, nr_recibo, created_at
    FROM explorador_eventos 
    WHERE per_apur = '2025-09'
    ORDER BY created_at DESC
    LIMIT 20
""")
for row in cur2.fetchall():
    cpf_short = row[1][:3] + "..." + row[1][-3:] if row[1] else "N/A"
    rec_short = row[2][-10:] if row[2] else "N/A"
    print(f"  {row[0]} cpf={cpf_short} rec=...{rec_short} em {row[3]}")

# Check which run_ids exist
cur2.execute("""
    SELECT DISTINCT run_id FROM explorador_eventos 
    WHERE per_apur = '2025-09' 
    ORDER BY run_id
""")
runs = [r[0] for r in cur2.fetchall()]
print(f"\nRun IDs: {runs}")

# Check the S-1299 status - is the period OPEN or CLOSED?
cur2.execute("""
    SELECT tipo_evento, nr_recibo, created_at
    FROM explorador_eventos 
    WHERE per_apur = '2025-09' AND tipo_evento IN ('S-1298', 'S-1299')
    ORDER BY created_at
""")
print("\n=== Historico abertura/fechamento set/2025 ===")
for row in cur2.fetchall():
    print(f"  {row[0]} recibo={row[1]} em {row[2]}")

conn2.close()

conn.close()
