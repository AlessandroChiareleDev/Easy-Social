"""
Diagnóstico: quais rubricas causam o [1955] somatório negativo na incidência 33?

Para cada CPF com erro [1955], lista:
  - Todas as rubricas no S-1210 enviado
  - O tipo (tpRubr) e codIncIRRF de cada rubrica (do S-1010)
  - Calcula somatório por incidência como eSocial faz

Regra [1955]: Para cada grupo de incidência (31,32,33,34):
  Sum(rubricas tipo 2,4) >= Sum(rubricas tipo 1,3)
"""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from db_config import DB_CONFIG
import psycopg2, psycopg2.extras

PER_APUR = "2025-09"

def main():
    conn = psycopg2.connect(
        **DB_CONFIG,
        keepalives=1, keepalives_idle=30,
        keepalives_interval=10, keepalives_count=3,
    )
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            # 1) CPFs com erro 1955
            cur.execute("""
                SELECT cpf, nr_recibo_original
                FROM pipeline_cpf_results
                WHERE status = 'erro' AND erro_descricao LIKE '%%1955%%'
                ORDER BY cpf
                LIMIT 5
            """)
            cpfs = cur.fetchall()
            print(f"CPFs com erro [1955]: {len(cpfs)} (mostrando até 5)")
            print()

            # 2) Buscar todas rubricas S-1010 (com tpRubr e codIncIRRF)
            cur.execute("""
                SELECT dados_json
                FROM explorador_eventos
                WHERE tipo_evento = 'S-1010'
                ORDER BY id DESC
                LIMIT 2000
            """)
            rubrica_rows = cur.fetchall()

            # Parse rubricas → map codRubr → {tpRubr, codIncIRRF, ...}
            rubrica_map = {}
            for row in rubrica_rows:
                d = row["dados_json"]
                if isinstance(d, str):
                    d = json.loads(d)
                cod = d.get("codRubr")
                if cod:
                    rubrica_map[str(cod)] = {
                        "codRubr": cod,
                        "tpRubr": d.get("tpRubr"),
                        "dscRubr": d.get("dscRubr", ""),
                        "natRubr": d.get("natRubr"),
                        "codIncIRRF": d.get("codIncIRRF"),
                        "codIncCP": d.get("codIncCP"),
                    }

            print(f"Rubricas S-1010 carregadas: {len(rubrica_map)}")
            
            # Especificamente: rubricas com codIncIRRF in (31,32,33,34)
            ir_rubricas = {k: v for k, v in rubrica_map.items() 
                          if v.get("codIncIRRF") in ("31","32","33","34", 31,32,33,34)}
            print(f"Rubricas com codIncIRRF 31-34: {len(ir_rubricas)}")
            for k, v in sorted(ir_rubricas.items()):
                print(f"  codRubr={k}: tpRubr={v['tpRubr']}, codIncIRRF={v['codIncIRRF']}, "
                      f"dsc={v['dscRubr'][:60]}, natRubr={v.get('natRubr')}")
            print()

            # 3) Para cada CPF, analisar
            for cpf_row in cpfs:
                cpf = cpf_row["cpf"]
                recibo = cpf_row["nr_recibo_original"]
                print(f"{'='*70}")
                print(f"CPF: {cpf}  |  recibo: {recibo}")
                print(f"{'='*70}")

                # Buscar evento S-1210
                cur.execute("""
                    SELECT dados_json
                    FROM explorador_eventos
                    WHERE tipo_evento = 'S-1210'
                      AND per_apur = %s
                      AND cpf = %s
                      AND nr_recibo = %s
                    LIMIT 1
                """, (PER_APUR, cpf, recibo))
                evt = cur.fetchone()
                if not evt:
                    # Buscar qualquer evento S-1210
                    cur.execute("""
                        SELECT dados_json, nr_recibo
                        FROM explorador_eventos
                        WHERE tipo_evento = 'S-1210'
                          AND per_apur = %s
                          AND cpf = %s
                        ORDER BY id DESC
                        LIMIT 1
                    """, (PER_APUR, cpf))
                    evt = cur.fetchone()
                    if evt:
                        print(f"  (usando recibo alternativo: {evt.get('nr_recibo', '?')})")

                if not evt:
                    print(f"  SEM EVENTO S-1210!")
                    continue

                dados = evt["dados_json"]
                if isinstance(dados, str):
                    dados = json.loads(dados)

                pagamentos = dados.get("pagamentos", [])
                if not pagamentos and dados.get("dtPgto"):
                    pagamentos = [{
                        "dtPgto": dados.get("dtPgto", ""),
                        "ideDmDev": dados.get("ideDmDev", ""),
                        "vrLiq": dados.get("vrLiq", "0"),
                    }]

                # Extrair todas as rubricas do demonstrativo
                # Precisamos olhar a estrutura do XML/dados para encontrar as rubricas
                print(f"  Chaves no dados_json: {list(dados.keys())}")
                
                # Print raw pagamentos
                print(f"\n  Pagamentos ({len(pagamentos)}):")
                for i, pag in enumerate(pagamentos):
                    print(f"    [{i}] dtPgto={pag.get('dtPgto')}, ideDmDev={pag.get('ideDmDev')}, "
                          f"vrLiq={pag.get('vrLiq')}")
                    
                    # Verificar se tem detalhes de rubricas dentro
                    for key in pag:
                        if key not in ("dtPgto", "tpPgto", "ideDmDev", "vrLiq", "perRef"):
                            print(f"      {key}: {str(pag[key])[:200]}")

                # InfoIRCR
                info_ir = dados.get("infoIRCR", [])
                print(f"\n  infoIRCR ({len(info_ir)}):")
                for ir in info_ir:
                    print(f"    tpCR={ir.get('tpCR')}, vrCR={ir.get('vrCR')}, "
                          f"infoRRA={ir.get('infoRRA')}, dedDepen={ir.get('dedDepen')}")

                # Vamos ver tudo que parece rubrica
                print(f"\n  dados_json completo (detalhes):")
                for key, val in sorted(dados.items()):
                    if key in ("pagamentos", "infoIRCR"):
                        continue
                    print(f"    {key}: {str(val)[:200]}")

                # Agora vamos olhar diretamente o XML raw se existir
                cur.execute("""
                    SELECT xml_content
                    FROM explorador_eventos
                    WHERE tipo_evento = 'S-1210'
                      AND per_apur = %s
                      AND cpf = %s
                    ORDER BY id DESC
                    LIMIT 1
                """, (PER_APUR, cpf))
                xml_row = cur.fetchone()
                if xml_row and xml_row.get("xml_content"):
                    xml = xml_row["xml_content"]
                    # Extrair rubricas do XML
                    import re
                    # Look for <codRubr> and <vrRubr> tags
                    rubr_matches = re.findall(
                        r'<codRubr>(\d+)</codRubr>.*?<vrRubr>([\d.]+)</vrRubr>',
                        xml, re.DOTALL
                    )
                    print(f"\n  Rubricas no XML ({len(rubr_matches)}):")
                    
                    # Calculate sums per incidence
                    sums = {}  # incidencia -> {tipo_1_3: sum, tipo_2_4: sum}
                    for cod, valor in rubr_matches:
                        info = rubrica_map.get(str(cod), {})
                        tp = info.get("tpRubr", "?")
                        inc_ir = info.get("codIncIRRF", "?")
                        val = float(valor)
                        
                        print(f"    codRubr={cod}, vrRubr={valor}, tpRubr={tp}, "
                              f"codIncIRRF={inc_ir}, dsc={info.get('dscRubr','?')[:40]}")
                        
                        if str(inc_ir) in ("31","32","33","34"):
                            k = str(inc_ir)
                            if k not in sums:
                                sums[k] = {"tipo_1_3": 0, "tipo_2_4": 0}
                            if str(tp) in ("1","3"):
                                sums[k]["tipo_1_3"] += val
                            elif str(tp) in ("2","4"):
                                sums[k]["tipo_2_4"] += val
                    
                    print(f"\n  Somatórios por incidência IR (regra [1955]):")
                    for inc, vals in sorted(sums.items()):
                        diff = vals["tipo_2_4"] - vals["tipo_1_3"]
                        status = "OK" if diff >= 0 else "VIOLAÇÃO"
                        print(f"    Incidência {inc}: "
                              f"deduções(tipo2,4)={vals['tipo_2_4']:.2f} - "
                              f"proventos(tipo1,3)={vals['tipo_1_3']:.2f} = "
                              f"{diff:.2f}  [{status}]")
                else:
                    print(f"\n  (sem xml_content na explorador_eventos)")
                
                print()

    finally:
        conn.close()

if __name__ == "__main__":
    main()
