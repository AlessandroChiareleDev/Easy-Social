"""
Read the actual S-3000 XML files to understand what was excluded.
Also check if there are newer retification S-1210 events (indRetif=2) 
in the XML files that we might have missed.
"""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from db_config import DB_CONFIG
import psycopg2, psycopg2.extras
from lxml import etree
import glob

XML_DIR = "/opt/easy-social/xmls_set2025"

conn = psycopg2.connect(**DB_CONFIG)
cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

# Get sample CPFs
cur.execute("""
    SELECT cpf, nr_recibo_original
    FROM pipeline_cpf_results
    WHERE run_id = 1 AND status = 'erro' AND erro_descricao LIKE '%%459%%'
    ORDER BY cpf LIMIT 3
""")
sample_cpfs = cur.fetchall()

for sample in sample_cpfs:
    cpf = sample['cpf']
    wrong_recibo = sample['nr_recibo_original']
    
    print(f"\n{'='*70}")
    print(f"CPF: {cpf} | Pipeline recibo: {wrong_recibo}")
    
    # Get S-3000 arquivo_origem
    cur.execute("""
        SELECT arquivo_origem FROM explorador_eventos
        WHERE cpf = %s AND tipo_evento = 'S-3000' AND per_apur = '2025-09'
    """, (cpf,))
    s3000_rows = cur.fetchall()
    
    for s3 in s3000_rows:
        xml_path = os.path.join(XML_DIR, s3['arquivo_origem'])
        print(f"\n  S-3000 XML: {s3['arquivo_origem']}")
        try:
            tree = etree.parse(xml_path)
            root = tree.getroot()
            xml_str = etree.tostring(root, pretty_print=True, encoding='unicode')
            print(f"  Content (first 1500 chars):")
            print(f"  {xml_str[:1500]}")
            
            # Extract nrRecEvt (the recibo being excluded)
            ns = {'e': 'http://www.esocial.gov.br/schema/evt/evtExclusao/v_S_01_02_00'}
            nrRecEvt_els = root.findall('.//{*}nrRecEvt')
            for el in nrRecEvt_els:
                print(f"\n  >>> nrRecEvt (excluded): {el.text}")
        except FileNotFoundError:
            print(f"  FILE NOT FOUND: {xml_path}")
        except Exception as e:
            print(f"  ERROR: {e}")
    
    # Also look for any retification S-1210 (indRetif=2) in the XMls
    cur.execute("""
        SELECT arquivo_origem, nr_recibo, dados_json
        FROM explorador_eventos
        WHERE cpf = %s AND tipo_evento = 'S-1210' AND per_apur = '2025-09'
        ORDER BY id
    """, (cpf,))
    s1210_rows = cur.fetchall()
    
    print(f"\n  S-1210 events:")
    for s in s1210_rows:
        xml_path = os.path.join(XML_DIR, s['arquivo_origem'])
        print(f"\n    File: {s['arquivo_origem']} recibo={s['nr_recibo']}")
        try:
            tree = etree.parse(xml_path)
            root = tree.getroot()
            
            # Check indRetif and nrRecArqBase
            for el in root.iter():
                if 'indRetif' in el.tag:
                    print(f"    indRetif: {el.text}")
                if 'nrRecArqBase' in el.tag:
                    print(f"    nrRecArqBase: {el.text}")
        except FileNotFoundError:
            print(f"    FILE NOT FOUND")
        except Exception as e:
            print(f"    ERROR: {e}")

conn.close()
