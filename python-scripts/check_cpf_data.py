import psycopg2, os
from dotenv import load_dotenv
load_dotenv()

conn = psycopg2.connect(
    host="localhost",
    port=5432,
    dbname="easy_social_db",
    user="easy_social_user",
    password="sua_senha_segura"
)
cur = conn.cursor()

print("=== Event types and CPF status ===")
cur.execute("""
    SELECT tipo_evento, 
           CASE WHEN cpf IS NULL THEN 'NULL' ELSE 'HAS_CPF' END as cpf_status, 
           COUNT(*) 
    FROM explorador_eventos 
    GROUP BY tipo_evento, cpf_status 
    ORDER BY tipo_evento, count DESC
""")
for r in cur.fetchall():
    print(r)

print("\n=== Sample events with CPF 08132588983 ===")
cur.execute("""
    SELECT id, tipo_evento, cpf, per_apur, detalhes_resumo 
    FROM explorador_eventos 
    WHERE cpf = '08132588983' 
    LIMIT 5
""")
for r in cur.fetchall():
    print(r)

print("\n=== Total events by CPF filter ===")
cur.execute("SELECT COUNT(*) FROM explorador_eventos WHERE cpf = '08132588983'")
print(f"Events with CPF 08132588983: {cur.fetchone()[0]}")
cur.execute("SELECT COUNT(*) FROM explorador_eventos WHERE cpf IS NULL")
print(f"Events with NULL CPF: {cur.fetchone()[0]}")
cur.execute("SELECT COUNT(*) FROM explorador_eventos")
print(f"Total events: {cur.fetchone()[0]}")

conn.close()
