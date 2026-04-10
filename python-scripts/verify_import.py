import sys, json
sys.path.insert(0, "/opt/easy-social/python-scripts")
from db_config import DB_CONFIG
import psycopg2, psycopg2.extras

conn = psycopg2.connect(**DB_CONFIG, keepalives=1, keepalives_idle=30, keepalives_interval=10, keepalives_count=3)
with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
    # Stats
    cur.execute("""
        SELECT tipo_evento, COUNT(*) as cnt, COUNT(DISTINCT cpf) as cpfs
        FROM explorador_eventos
        WHERE per_apur = '2025-09'
        GROUP BY tipo_evento ORDER BY tipo_evento
    """)
    print("=== STATS 2025-09 ===")
    for r in cur.fetchall():
        print(f"  {r['tipo_evento']}: {r['cnt']} events, {r['cpfs']} CPFs")

    # Check S-1210 data quality (pagamentos field)
    cur.execute("""
        SELECT cpf, nr_recibo, dados_json
        FROM explorador_eventos
        WHERE tipo_evento = 'S-1210' AND per_apur = '2025-09'
          AND COALESCE(dados_json->>'indRetif', '1') != '2'
        LIMIT 5
    """)
    print("\n=== SAMPLE S-1210 (first 5) ===")
    for r in cur.fetchall():
        d = r['dados_json'] if isinstance(r['dados_json'], dict) else json.loads(r['dados_json'] or '{}')
        pgtos = d.get('pagamentos', [])
        ircr = d.get('infoIRCR', [])
        print(f"  CPF={r['cpf']} recibo={r['nr_recibo']} pgtos={len(pgtos)} irCR={len(ircr)}")
        for p in pgtos[:3]:
            print(f"    ideDmDev={p.get('ideDmDev')} dtPgto={p.get('dtPgto')} vrLiq={p.get('vrLiq')} perRef={p.get('perRef')}")
        for ir in ircr[:2]:
            print(f"    tpCR={ir.get('tpCR')} vrCR={ir.get('vrCR')}")

    # Count CPFs with multiple pagamentos
    cur.execute("""
        SELECT COUNT(*) FROM (
            SELECT cpf FROM explorador_eventos
            WHERE tipo_evento = 'S-1210' AND per_apur = '2025-09'
              AND COALESCE(dados_json->>'indRetif', '1') != '2'
              AND jsonb_array_length(COALESCE(dados_json->'pagamentos', '[]'::jsonb)) > 1
        ) sub
    """)
    multi = cur.fetchone()['count']
    print(f"\nCPFs with multiple pagamentos: {multi}")

    # Total valid for pipeline
    cur.execute("""
        SELECT COUNT(DISTINCT cpf) FROM explorador_eventos
        WHERE tipo_evento = 'S-1210' AND per_apur = '2025-09'
          AND cpf IS NOT NULL AND nr_recibo IS NOT NULL
          AND COALESCE(dados_json->>'indRetif', '1') != '2'
    """)
    total_valid = cur.fetchone()['count']
    print(f"Total CPFs valid for pipeline: {total_valid}")

conn.close()
