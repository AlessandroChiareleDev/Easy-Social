import urllib.request
import urllib.parse
import json

BASE = "http://localhost:3333/api/naturezas/buscar-similares"

test_cases = [
    ("DIF. D.S.R.", "35"),
    ("D.S.R. S/HORA EXTRA", "135"),
    ("DIF. FERIAS", "156"),
    ("DEVOLUCAO FALTAS / DSR", "339"),
    ("DIF. CESTA BASICA CCT", "342"),
    ("DESC. DEV. HE/A.N./DSR - MES ANT", "509"),
    ("DESC. DIF. SALARIO", "524"),
    ("DIFERENCA CCT", "746"),
]

for nome, cod in test_cases:
    params = urllib.parse.urlencode({"nomeEvento": nome, "topN": 10, "codigoEvento": cod})
    url = f"{BASE}?{params}"
    try:
        r = urllib.request.urlopen(url)
        data = json.loads(r.read())
        humana = data.get("sugestaoHumana")
        resultados = data.get("resultados", [])
        
        print(f'\n=== {nome} (cod={cod}) ===')
        if humana:
            print(f'  ⭐ HUMANA: {humana["codigo"]} - {humana["nome"]} (score={humana["score"]})')
        else:
            print(f'  ⭐ HUMANA: --- nenhuma ---')
        
        score_results = [r for r in resultados if r["origem"] == "score"]
        pop_results = [r for r in resultados if r["origem"] == "popular"]
        
        if score_results:
            print(f'  📊 SCORE ({len(score_results)}):')
            for s in score_results[:5]:
                print(f'    {s["codigo"]} - {s["nome"]} (score={s["score"]})')
        else:
            print(f'  📊 SCORE: --- nenhum match ---')
        
        if pop_results:
            print(f'  🔥 POPULAR ({len(pop_results)}):')
            for s in pop_results[:3]:
                print(f'    {s["codigo"]} - {s["nome"]}')
    except Exception as e:
        print(f'\n=== {nome} (cod={cod}) === ERRO: {e}')
