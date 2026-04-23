# Regras do Lote 2 — extraídas da call com Ana (22/04/2026)

Fonte: transcrição da call. Este arquivo é **a regra definitiva** pro parser e montagem do `<planSaude>` no S-1210 do Lote 2 (e vale também pros outros lotes quando houver rubrica de plano de saúde).

---

## 1. Quais rubricas viram `<planSaude>`?

**Não é por código de rubrica. É pelo preenchimento da coluna `Cód Operadora` (CNPJ) na aba Operadoras do XLSX.**

| Coluna `Cód Operadora`                 | Resultado                                                                    |
| -------------------------------------- | ---------------------------------------------------------------------------- |
| CNPJ válido (ex: `63.554.067/0001-98`) | **VIRA** `<planSaude>`                                                       |
| Valor `-` (traço)                      | **NÃO VIRA** — já está configurado corretamente dentro do eSocial, não mexer |

Rubricas que _podem_ aparecer com CNPJ válido no Lote 2 (conforme call): **516, 605, 607, 619, 631, 638, 775**.
Mas o filtro real é o **CNPJ preenchido**, não a lista de códigos.

> Citação Ana (01:02):
> "Tem na coluna código de operador, o que está com traço não é plano de saúde. Pode se apresentar um CNPJ para o plano de saúde, um CNPJ para o plano odontológico, para o mesmo trabalhador. Então ele vai precisar entender que **a soma tem que ser feita por CNPJ, independente dos códigos de rubricas**."

---

## 2. Regra de agregação quando o CPF tem múltiplas linhas

**Agrupar por CNPJ da operadora. Um `<planSaude>` por CNPJ distinto. Somar todos os valores daquele CNPJ, independente da rubrica.**

### Exemplo

CPF `123.456.789-00` tem na aba Operadoras:

| Rubrica | CNPJ                 | Cod ANS | ValorEvento |
| ------- | -------------------- | ------- | ----------- |
| 775     | `63.554.067/0001-98` | 368253  | 2000        |
| 607     | `63.554.067/0001-98` | 368253  | 3500        |
| 631     | `12.345.678/0001-00` | 999999  | 1000        |

Resultado no XML:

```xml
<planSaude>
  <cnpjOper>63554067000198</cnpjOper>
  <regANS>368253</regANS>
  <vlrSaudeTit>55.00</vlrSaudeTit>  <!-- 2000 + 3500 = 5500 centavos = R$ 55,00 -->
</planSaude>
<planSaude>
  <cnpjOper>12345678000100</cnpjOper>
  <regANS>999999</regANS>
  <vlrSaudeTit>10.00</vlrSaudeTit>
</planSaude>
```

---

## 3. Rubricas informativas — IGNORAR

**9279** e **9281** aparecem em Mar/Abr mas **NÃO ENTRAM** no `<planSaude>`. São rubricas informativas, já classificadas corretamente nas suas naturezas. O parser deve pular.

> Citação Ana (01:45):
> "Elas são só rubricas informativas, elas não precisam [somar], vão estar aí dentro, mas não tem somatória para o plano de saúde. Elas já estão nas suas naturezas corretas."

Filtro prático no parser: se rubrica ∈ {9279, 9281} → **ignorar**.

---

## 4. Valor sempre em centavos

Coluna `ValorEvento` do XLSX vem **em centavos**. Dividir por 100 antes de colocar no XML.

- `28001` → `R$ 280,01` → `<vlrSaudeTit>280.01</vlrSaudeTit>`

---

## 5. Cobertura <100% é esperada

Nem todo CPF do scope tem linha na aba Operadoras. É normal por conta de demissões, transferências, funcionários sem plano de saúde etc. Não é bug.

No preview de Fev: 1161 / 1390 CPFs do L2 tem rubrica 775 com CNPJ (83% de cobertura). Os 17% restantes simplesmente não têm plano de saúde naquele mês — vão pra S-1210 sem `<planSaude>`.

---

## 6. Pseudocódigo da agregação

```python
# Para cada CPF do Lote 2:
linhas_do_cpf = [
    linha for linha in aba_operadoras
    if linha.cpf == cpf_alvo
    and linha.rubrica not in (9279, 9281)
    and linha.cnpj_operadora not in (None, "", "-")
]

# Agrupar por CNPJ
por_cnpj = defaultdict(lambda: {"cnpj": None, "regANS": None, "soma_centavos": 0})
for linha in linhas_do_cpf:
    chave = linha.cnpj_operadora  # normalizar dígitos
    por_cnpj[chave]["cnpj"] = chave
    por_cnpj[chave]["regANS"] = linha.cod_ans
    por_cnpj[chave]["soma_centavos"] += int(linha.valor_evento)

plan_saude_list = [
    {
        "cnpjOper": entry["cnpj"].replace(".", "").replace("/", "").replace("-", ""),
        "regANS": str(entry["regANS"]),
        "vlrSaudeTit": f"{entry['soma_centavos'] / 100:.2f}",
    }
    for entry in por_cnpj.values()
]
```

---

## 7. Checklist de implementação

- [ ] User adiciona coluna `CPF` nas 3 abas Operadoras dos XLSX de Fev/Mar/Abr (evita cruzamento por matrícula).
- [ ] Criar parser `_parse_and_populate_operadoras` em `python-scripts/esocial/s1210_repo_routes.py` — grava linha a linha em `s1210_operadoras`, com `(empresa_id, per_apur, cpf, rubrica, cnpj_operadora, reg_ans, valor_centavos)`. Ignora rubricas 9279/9281 e linhas com CNPJ = "-".
- [ ] Re-ingerir os 3 XLSX via `/xlsx/ingest`.
- [ ] Em `s1210_batch._processar_um_cpf`, quando `lote_num=2`: SELECT agregado de `s1210_operadoras` agrupado por CNPJ → montar `plan_saude=[...]` antes de chamar `_build_plan_saude`.
- [ ] Teste manual com 1 CPF que tenha múltiplos CNPJs → validar XML tem 2+ `<planSaude>`.
- [ ] Só depois: batch do Lote 2 (mediante OK da Ana que terminou reclassificação 9219→9299 no eSocial).

---

## 8. O que **NÃO** fazer

- ❌ Filtrar por lista hardcoded de rubricas. Filtrar por CNPJ presente.
- ❌ Gerar um `<planSaude>` por linha do XLSX. Agrupar por CNPJ primeiro.
- ❌ Incluir rubricas 9279/9281 na soma.
- ❌ Enviar Lote 2 antes de Ana confirmar que terminou a reclassificação no eSocial (senão queima CPFs).
