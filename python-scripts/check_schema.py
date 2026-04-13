import psycopg2, psycopg2.extras
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from db_config import DB_CONFIG

conn = psycopg2.connect(**DB_CONFIG, keepalives=1, keepalives_idle=30, keepalives_interval=10, keepalives_count=3)
cur = conn.cursor()

# Columns of explorador_eventos
cur.execute("SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'explorador_eventos' ORDER BY ordinal_position")
print("=== explorador_eventos columns ===")
for r in cur.fetchall(): print(r)

# Check S-1010 events
cur.execute("SELECT count(*) FROM explorador_eventos WHERE tipo_evento = 'S-1010'")
print(f"\nS-1010 events: {cur.fetchone()[0]}")

# Check rubrica tables
cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' AND (table_name LIKE '%rubr%' OR table_name LIKE '%s1010%' OR table_name LIKE '%rubrica%')")
print("\nRubrica/S-1010 tables:")
for r in cur.fetchall(): print(r)

# Check all tables
cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' ORDER BY table_name")
print("\nAll tables:")
for r in cur.fetchall(): print(r)

# Sample S-1210 to check columns
cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'explorador_eventos' AND column_name LIKE '%xml%'")
print("\nXML columns:")
for r in cur.fetchall(): print(r)

conn.close()
