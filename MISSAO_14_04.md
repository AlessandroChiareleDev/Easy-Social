# MISSÃO 14/04/2026 — RESULTADO DA INVESTIGAÇÃO

---

## TAREFA 1: PlanSaude com valor ERRADO

### O que eu fiz

Construí `plansaude_map_jan2025.json` (10.443 CPFs) e `plansaude_map_fev2025.json` (10.311 CPFs) extraindo `vlrSaudeTit` do `<planSaude>` do S-1210 original que veio no ZIP.

Enviei esses valores na retificação.

### Impacto

- **Jan**: 10.112 CPFs passaram como "ok" usando valor do mapa
- **Fev**: 8.958 CPFs passaram como "ok" usando valor do mapa
- **Total potencialmente errado**: até 19.070 CPFs com vlrSaudeTit possivelmente incorreto no eSocial

### O que descobri

Tentei comparar o valor do mapa com a rubrica `codIncIRRF=67` do S-1200 no banco. **Resultado: ZERO CPFs tem rubrica com codIncIRRF=67 no explorador_rubricas**. Ou seja, não temos esse dado no banco para comparar automaticamente.

O valor correto (ex: 24.70 para CPF 006.556.045-02) aparece no portal do eSocial como "67 - Plano privado coletivo de assistência à saúde" na seção de deduções do IR (detDed/infoIRComplem), NÃO na tabela explorador_rubricas.

### Caso concreto — CPF 006.556.045-02

- Mapa Jan: **367.30** (enviado como vlrSaudeTit) ← ERRADO
- Portal mostra: rubrica 67 = **24.70** ← CORRETO
- Portal mostra planSaude: **367.30** (esse é o valor que JÁ EXISTIA, que eu copiei)
- Mapa Fev: **796.14** (também potencialmente errado)
- Pipeline: Run 3 (Jan) = erro → Run 6 (Jan) = ok (aceitou o errado)

### O que falta para resolver

1. Não temos os dados de detDed/codIncIRRF=67 no banco — precisamos extrair do ZIP original ou do portal
2. Precisamos reconstruir os mapas com o valor CORRETO (rubrica 67, não vlrSaudeTit do S-1210)
3. Depois: re-retificar todos os CPFs que foram enviados com valor errado

---

## TAREFA 2: Recibo desconhecido (100 Jan + 53 Fev)

### O que aconteceu

100 CPFs de Jan com erro 106 (duplicidade) + 53 de Fev com erro 459 (recibo não localizado). Alguém retificou esses S-1210 por fora — o recibo que temos no banco não é mais válido.

### Investigação — CPF 003.864.459-23

Histórico no pipeline:

- **Run 3** (Jan): erro 459 — recibo `1.1.0000000030913596357` não localizado
- **Run 6** (Jan): erro 459 — mesmo recibo, ainda não localizado
- **Run 7** (Jan): erro 106 — duplicidade (alguém retificou por fora entre run 6 e 7)
- **Run 8** (Jan): erro 106 — duplicidade (mesmo)
- **Run 4** (Fev): OK — recibo `1.1.0000000031450234208` → novo `1.1.0000000039950833619`

Recibos:

- No nosso banco (explorador): `1.1.0000000030913596357` ← desatualizado
- Fornecido pelo Alex: `1.1.0000000039932809804` ← esse é o recibo que o eSocial tem atualmente
- São DIFERENTES — confirma que precisa do recibo atualizado

### Conclusão

O teste manual vai funcionar se usarmos o recibo `1.1.0000000039932809804`. Mas NÃO posso executar sem autorização explícita — isso consome envio ao eSocial.

Para resolver os 100+53: precisamos obter os recibos atualizados — via download pelo portal (Ana) ou via ConsultarIdentificadoresEmpregador (Strategy A, 1 consulta).

---

## TAREFA 3: Pipeline Fev 2025

### Resultado

Pipeline Fev **COMPLETOU**. Zero pendentes.

| Status    | Qtd        |
| --------- | ---------- |
| ok        | 9.625      |
| erro      | 1.175      |
| **Total** | **10.800** |

### Breakdown dos 1.175 erros

| Tipo       | Qtd   | Descrição                                           |
| ---------- | ----- | --------------------------------------------------- |
| planSaude  | 1.069 | Grupo 'Plano de saúde coletivo' deve ser preenchido |
| recibo_459 | 53    | Recibo não localizado                               |
| outro      | 52    | Outros erros                                        |
| pensao     | 1     | Pensão alimentícia                                  |

### Observação

Os 1.069 erros de planSaude são CPFs que NÃO estavam no mapa (sem vlrSaudeTit). Ou seja, o importador não extraiu planSaude pra eles do ZIP. Situação igual aos 49 de Jan que davam o mesmo erro.

---

## RESUMO CONSOLIDADO

### Jan 2025

| Status                 | Qtd        |
| ---------------------- | ---------- |
| ok                     | 11.126     |
| erro planSaude         | 49         |
| erro duplicidade (106) | 100        |
| outros erros           | 15         |
| **Total**              | **11.290** |

### Fev 2025

| Status            | Qtd        |
| ----------------- | ---------- |
| ok                | 9.625      |
| erro planSaude    | 1.069      |
| erro recibo (459) | 53         |
| outros erros      | 53         |
| **Total**         | **10.800** |

### Próximos passos (quando autorizado)

1. **PlanSaude**: Reconstruir mapas com valor correto da rubrica 67 (não do S-1210). Precisa extrair do ZIP ou portal.
2. **Recibo**: Testar retificação do CPF 003.864.459-23 com recibo fornecido. Depois obter recibos dos demais.
3. **PlanSaude erros**: Resolver os 49 Jan + 1.069 Fev que não tinham planSaude no mapa.
4. **Re-retificar**: Os ~19.000 CPFs "ok" que podem ter vlrSaudeTit errado.
