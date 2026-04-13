"""Teste rápido: gera XML S-1210 retificação para 1 CPF com penAlim e valida."""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from db_config import DB_CONFIG
import psycopg2
import psycopg2.extras
from esocial.xml_s1210 import S1210XMLGenerator

PER_APUR = "2025-09"
TEST_CPF = "10466052758"  # CPF que você verificou manualmente

conn = psycopg2.connect(**DB_CONFIG)
try:
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute("""
            SELECT e.cpf, e.nr_recibo, e.dados_json
            FROM explorador_eventos e
            WHERE e.tipo_evento = 'S-1210'
              AND e.per_apur = %s AND e.cpf = %s
              AND e.nr_recibo IS NOT NULL
              AND COALESCE(e.dados_json->>'indRetif', '1') != '2'
            ORDER BY e.dt_processamento DESC LIMIT 1
        """, (PER_APUR, TEST_CPF))
        row = cur.fetchone()
        if not row:
            print("CPF não encontrado!")
            sys.exit(1)

        dados = row["dados_json"] if isinstance(row["dados_json"], dict) else json.loads(row["dados_json"])
        pagamentos = dados.get("pagamentos", [])
        info_ir_cr = dados.get("infoIRCR", [])

        # Show penAlim data
        for cr in info_ir_cr:
            if cr.get("penAlim"):
                print(f"penAlim encontrado no infoIRCR (tpCR={cr['tpCR']}):")
                for pa in cr["penAlim"]:
                    print(f"  tpRend={pa['tpRend']} cpfDep={pa['cpfDep']} vlrDedPenAlim={pa['vlrDedPenAlim']}")

        info_ir_complem = {"infoIRCR": info_ir_cr} if info_ir_cr else None

        xml_bytes = S1210XMLGenerator.gerar(
            empregador={"tpInsc": 1, "nrInsc": "05969071"},
            beneficiario={"cpfBenef": TEST_CPF},
            info_pgtos=pagamentos,
            per_apur=PER_APUR,
            ind_retif="2",
            nr_recibo=row["nr_recibo"],
            info_ir_complem=info_ir_complem,
            seq=1,
            tp_amb="2",  # TESTE - restrito
        )

        xml_str = xml_bytes.decode("utf-8")
        if "<penAlim>" in xml_str:
            print("\n✓ XML contém <penAlim>!")
            # Extract penAlim section
            import re
            matches = re.findall(r'<penAlim>.*?</penAlim>', xml_str)
            for m in matches:
                print(f"  {m}")
        else:
            print("\n✗ XML NÃO contém <penAlim> — PROBLEMA!")

        if "<dedDepen>" in xml_str:
            matches = re.findall(r'<dedDepen>.*?</dedDepen>', xml_str)
            print(f"\n✓ XML contém {len(matches)} <dedDepen>")

        print(f"\nXML total: {len(xml_str)} bytes")
finally:
    conn.close()
