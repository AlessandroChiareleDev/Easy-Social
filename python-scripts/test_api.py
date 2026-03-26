import urllib.request, json

def test(nome, cod):
    encoded_nome = urllib.request.quote(nome, safe='')
    url = f'http://localhost:3333/api/naturezas/buscar-similares/{encoded_nome}?topN=30&codigoEvento={cod}'
    r = urllib.request.urlopen(url)
    data = json.loads(r.read())
    
    print(f"\n{'='*60}")
    print(f"  RUBRICA: cod {cod} - {nome}")
    print(f"{'='*60}")
    
    sh = data.get('sugestaoHumana')
    if sh:
        print(f"  🎯 SUGESTAO HUMANA: {sh['codigo']} - {sh['nome']}")
        print(f"     Texto: {data.get('sugestaoTexto')}")
    else:
        print("  ❌ SEM SUGESTAO HUMANA")
    
    scores = [s for s in data['resultados'] if s['origem'] == 'score']
    pops = [s for s in data['resultados'] if s['origem'] == 'popular']
    print(f"\n  📊 POR SCORE: {len(scores)}")
    for s in scores[:5]:
        print(f"    {s['codigo']} {s['nome']} (score={s['score']})")
    if len(scores) > 5:
        print(f"    ... +{len(scores)-5} mais")
    
    print(f"\n  📈 POPULARES: {len(pops)}")
    for s in pops[:5]:
        print(f"    {s['codigo']} {s['nome']}")
    if len(pops) > 5:
        print(f"    ... +{len(pops)-5} mais")
    
    print(f"\n  TOTAL: 1 humana + {len(scores)} score + {len(pops)} popular = {1 if sh else 0 + len(scores) + len(pops)}")

test("REEMB. VALE TRANSPORTE", "13")
test("D.S.R. S/ADICIONAL", "136")
test("DESC. FALTAS (DIAS)", "500")
test("ADICIONAL DE SALARIO", "18")
