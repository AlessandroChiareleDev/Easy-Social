"""Pre-flight check: verify all pipeline tracking infrastructure is ready."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import psycopg2
import psycopg2.extras
from db_config import DB_CONFIG

def check():
    errors = []
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    # 1. Check pipeline_runs table
    cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name='pipeline_runs' ORDER BY ordinal_position")
    cols = [r["column_name"] for r in cur.fetchall()]
    expected_runs = ["id","per_apur","status","total_cpfs","cpfs_ok","cpfs_erro","cpfs_ignorados",
                     "s1298_done","s1298_recibo","s1299_done","s1299_recibo","lote_atual","total_lotes",
                     "started_at","finished_at","erro_fatal"]
    missing = [c for c in expected_runs if c not in cols]
    if missing:
        errors.append(f"pipeline_runs missing cols: {missing}")
    print(f"1. pipeline_runs: {len(cols)} columns ({'OK' if not missing else 'MISSING: '+str(missing)})")

    # 2. Check pipeline_cpf_results table
    cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name='pipeline_cpf_results' ORDER BY ordinal_position")
    cols2 = [r["column_name"] for r in cur.fetchall()]
    expected_cpf = ["id","run_id","cpf","status","nr_recibo_original","nr_recibo_novo",
                    "pagamentos","info_ir_cr","erro_descricao","lote_num","processed_at"]
    missing2 = [c for c in expected_cpf if c not in cols2]
    if missing2:
        errors.append(f"pipeline_cpf_results missing cols: {missing2}")
    print(f"2. pipeline_cpf_results: {len(cols2)} columns ({'OK' if not missing2 else 'MISSING: '+str(missing2)})")

    # 3. Check indexes
    cur.execute("SELECT indexname FROM pg_indexes WHERE tablename='pipeline_cpf_results'")
    indexes = [r["indexname"] for r in cur.fetchall()]
    print(f"3. Indexes on pipeline_cpf_results: {indexes}")

    # 4. Check S-1210 data available
    cur.execute("""
        SELECT COUNT(DISTINCT cpf) as cpfs, COUNT(*) as eventos
        FROM explorador_eventos
        WHERE tipo_evento = 'S-1210' AND per_apur = '2025-09'
          AND cpf IS NOT NULL AND nr_recibo IS NOT NULL
          AND COALESCE(dados_json->>'indRetif', '1') != '2'
    """)
    row = cur.fetchone()
    print(f"4. S-1210 originals (2025-09): {row['cpfs']} CPFs, {row['eventos']} events")
    if row["cpfs"] == 0:
        errors.append("No S-1210 data for 2025-09!")

    # 5. Check existing runs (should be 0)
    cur.execute("SELECT COUNT(*) as cnt FROM pipeline_runs")
    cnt = cur.fetchone()["cnt"]
    print(f"5. Existing pipeline_runs: {cnt}")

    # 6. Check batch script imports can resolve
    print("6. Checking batch script imports...")
    try:
        from esocial.xml_s1210 import S1210XMLGenerator
        from esocial.xml_s1298 import S1298XMLGenerator
        from esocial.xml_s1299 import S1299XMLGenerator
        from esocial.xml_signer import S1010XMLSigner as XMLSigner
        from esocial.soap_builder import SOAPEnvelopeBuilder
        from esocial.certificate_manager import CertificateManager
        from esocial.esocial_client import ESocialClient
        print("   XML generators + signer + SOAP builder + cert + client: OK")
    except ImportError as e:
        errors.append(f"Import error: {e}")
        print(f"   IMPORT ERROR: {e}")

    # 7. Check certificate
    try:
        from esocial.certificate_manager import CertificateManager
        cert = CertificateManager.get_active()
        if cert:
            print(f"7. Active cert: id={cert.get('id')}, cnpj={cert.get('cnpj')}, valid until {cert.get('validade')}")
        else:
            errors.append("No active certificate!")
            print("7. NO ACTIVE CERTIFICATE!")
    except Exception as e:
        print(f"7. Cert check: {e}")

    # 8. Check API endpoints accessible
    print("8. Checking API endpoints...")
    import urllib.request
    endpoints = [
        "/api/pipeline-batch/periodos",
        "/api/pipeline-batch/runs",
    ]
    for ep in endpoints:
        try:
            req = urllib.request.urlopen(f"http://localhost:8000{ep}", timeout=5)
            print(f"   {ep}: {req.status} OK")
        except Exception as e:
            errors.append(f"API {ep} failed: {e}")
            print(f"   {ep}: FAILED - {e}")

    conn.close()

    print(f"\n{'='*50}")
    if errors:
        print(f"ERRORS ({len(errors)}):")
        for e in errors:
            print(f"  ✗ {e}")
    else:
        print("ALL CHECKS PASSED ✓ — Ready to execute pipeline!")
    print(f"{'='*50}")
    return len(errors) == 0

if __name__ == "__main__":
    ok = check()
    sys.exit(0 if ok else 1)
