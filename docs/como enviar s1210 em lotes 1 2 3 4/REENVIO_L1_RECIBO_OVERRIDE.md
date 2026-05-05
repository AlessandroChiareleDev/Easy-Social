# Reenvio L1 com `recibo_override_por_cpf` — guia parametrizado

> **Caso real desta sessão (30/04/2026):** L1 Nov/2025 ficou com 208 erros após primeiro envio. Ana trouxe XLSX `Recibos 112025  final.xlsx` com **130 recibos novos** (col 2) para os CPFs com erro `401/459`. Esse documento é o passo-a-passo para reusar o mesmo padrão em qualquer mês.
>
> Doc-irmão: [COMO_FAZER_LOTE1.md](COMO_FAZER_LOTE1.md) · [COMO_FAZER_LOTE3.md](COMO_FAZER_LOTE3.md)

---

## 1. Contexto — o que esse fluxo resolve

Quando o L1 (envio "espelho", sem operadora) volta com erro `401/459`:

> _Não foi localizado um evento para o recibo de entrega informado ou o mesmo foi excluído/retificado._

Significa que o recibo que **nós usamos** (chain walk do backend → tabelas `s1210_cpf_recibo` / `pipeline_cpf_results` / `explorador_eventos`) **não é mais o ATIVO no AN**. A APPA retificou externamente (no portal eSocial) entre nosso pull do ZIP e nosso reenvio, então o recibo "ativo" agora só existe no portal.

Solução: a Ana exporta a lista de recibos ativos do portal, e a gente força esse recibo no envio via parâmetro `recibo_override_por_cpf` do endpoint `/api/s1210-repo/enviar-lote-cpfs` — bypass do chain walk.

**Esse padrão JÁ é usado em L3** (ver [envio_lote3_novembro.py](../../python-scripts/envio_lote3_novembro.py) e flag `--recibos-xlsx`). Esse doc estende para **L1** com ergonomia direta.

---

## 2. Inputs (parametrizados)

Substituir os valores entre `{{ }}` para cada execução.

| Parâmetro       | Valor (Nov/2025)                                        | Descrição                                                    |
| --------------- | ------------------------------------------------------- | ------------------------------------------------------------ |
| `PER_APUR`      | `2025-11`                                               | competência YYYY-MM                                          |
| `LOTE_NUM`      | `1`                                                     | 1 = espelho, 2 = com operadora, 3 = reclass inversa          |
| `EMPRESA_ID`    | `1`                                                     | APPA                                                         |
| `XLSX_RECIBOS`  | `C:\Users\xandao\Downloads\Recibos 112025  final.xlsx`  | XLSX da Ana com recibos ativos                               |
| `XLSX_SHEET`    | `Planilha1`                                             | nome da aba                                                  |
| `COL_CPF`       | `1`                                                     | índice 0-based da coluna do CPF (formatado `nnn.nnn.nnn-nn`) |
| `COL_RECIBO`    | `2`                                                     | índice 0-based da coluna do recibo `1.1.0000...`             |
| `COL_CODIGO`    | `8`                                                     | índice 0-based do código (`401/459`, `401/8`, etc)           |
| `FILTRO_CODIGO` | `401/459`                                               | qual erro queremos corrigir (só esse precisa override)       |
| `BATCH_SIZE`    | `50`                                                    | CPFs por POST (limite endpoint)                              |
| `API_URL`       | `http://localhost:8000/api/s1210-repo/enviar-lote-cpfs` | endpoint                                                     |
| `TIMEOUT`       | `600`                                                   | segundos por POST                                            |

> **Cuidado com nome de arquivo:** `Recibos 112025  final.xlsx` tem **DOIS espaços** entre `112025` e `final`. Sempre conferir no PowerShell: `Get-ChildItem -Path "$HOME\Downloads" -Filter "*Recibos*"`.

---

## 3. Estrutura do XLSX (formato Ana — Nov/2025)

```
Sheet: Planilha1  |  146 linhas (1 header) + status='erro'
[0] # ordem
[1] CPF formatado (000.000.000-00)
[2] RECIBO ATIVO  ← este é o override
[3] —
[4] —
[5] status (sempre 'erro')
[7] data
[8] código (401/459 | 401/8 | —/—)
[9] descrição
[10] ação (Enviar)
```

**Distribuição típica do XLSX desta sessão:**

- `401/459` = **130** → reenvio com override (este doc)
- `401/8` = 9 → não é override, é reclassificação L1→L2 (plano de saúde mal-categorizado)
- `—/—` = 7 → bloqueios anteriores (rever caso a caso)

> **Layouts variam.** No L3 a Ana mandou abas separadas por mês com colunas diferentes — sempre rodar um inspector antes (ver `_ler_recibos_nov.py` e `_analisa_recibos_nov.py` desta sessão).

---

## 4. Pipeline de execução

### 4.1 Inspecionar XLSX

```powershell
$VENV = "C:\Users\xandao\Documents\GitHub\Easy-Social\.venv\Scripts\python.exe"
& $VENV C:\Users\xandao\Documents\GitHub\Easy-Social\python-scripts\_ler_recibos_nov.py
```

Confere: sheets, header, contagem, samples.

### 4.2 Cruzar com erros reais (XLSX da Ana de envios)

Saber se o set de recibos cobre 100% dos `459` que temos em DB.

```powershell
& $VENV C:\Users\xandao\Documents\GitHub\Easy-Social\python-scripts\_analisa_recibos_nov.py
```

Saída esperada: `intersecção 130/130, só_xls=0, recibos_diferentes=130`.

### 4.3 Construir `override_map`

Pseudo-código (já existe variante para L3 — adaptar para L1 mudando `LOTE_NUM=1`):

```python
from openpyxl import load_workbook
import re

XLSX = r"C:\...\Recibos 112025  final.xlsx"
SHEET = "Planilha1"
COL_CPF, COL_RECIBO, COL_CODIGO = 1, 2, 8
FILTRO = "401/459"

wb = load_workbook(XLSX, data_only=True, read_only=True)
ws = wb[SHEET]
override = {}
for r in ws.iter_rows(min_row=2, values_only=True):
    if not r or r[COL_CODIGO] != FILTRO:
        continue
    cpf_norm = re.sub(r"\D", "", str(r[COL_CPF] or ""))
    rec = (r[COL_RECIBO] or "").strip()
    if len(cpf_norm) == 11 and rec.startswith("1.1."):
        override[cpf_norm] = rec
print(f"override={len(override)} CPFs")
```

### 4.4 POST em batches de 50

```python
import requests, json, time

API_URL = "http://localhost:8000/api/s1210-repo/enviar-lote-cpfs"
PER_APUR = "2025-11"
LOTE_NUM = 1
BATCH = 50

cpfs = list(override.keys())
for i in range(0, len(cpfs), BATCH):
    sl = cpfs[i:i+BATCH]
    payload = {
        "per_apur": PER_APUR,
        "lote_num": LOTE_NUM,
        "cpfs": sl,
        "confirmar_producao": True,
        "recibo_override_por_cpf": {c: override[c] for c in sl},
    }
    r = requests.post(API_URL, json=payload, timeout=600)
    r.raise_for_status()
    out = r.json()
    print(f"batch {i//BATCH+1}: ok={out.get('ok')} erro={out.get('erro')}")
    with open(f"saida_l1_nov_override/batch_{i//BATCH+1:02d}.json", "w") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    time.sleep(1)
```

### 4.5 Validar pós-envio

Rodar de novo o gerador do relatório L1:

```powershell
& $VENV C:\Users\xandao\Documents\GitHub\Easy-Social\python-scripts\_gen_rel_l1_nov.py
```

Esperado: `ok=4794 (4664+130)  erro=78 (208-130)  oc top=[('1089',56),('8',9),...]`.

---

## 5. Restrições importantes

- **NUNCA** consultar AN/eSocial sem permissão explícita (cota 10/dia — ver `/memories/esocial-critical-rules.md`).
- Backend tem que estar rodando em `localhost:8000` (path absoluto: `C:\Users\xandao\Documents\GitHub\Easy-Social\python-scripts\bot_api.py`).
- Sempre usar venv absoluto: `C:\Users\xandao\Documents\GitHub\Easy-Social\.venv\Scripts\python.exe`.
- `openpyxl` em `read_only=True` **não tem** `.dimensions` / `.max_row` — usar `iter_rows(values_only=True)` direto.
- Override mata chain walk; se o recibo passado também estiver inválido → continua dando 459. Ana tem que ter exportado **dia da operação**, não dias antes.
- `confirmar_producao=True` é obrigatório (ambiente real).
- **Nunca** mandar `tp_amb` no payload — produção é hardcoded no backend.

---

## 6. Onde está o código backend

- Endpoint: [s1210_repo_routes.py L1486](../../python-scripts/esocial/s1210_repo_routes.py)
  - Modelo: `EnviarLoteCpfsReq`
  - Campo: `recibo_override_por_cpf: Optional[dict[str, str]] = None`
- Aplicação override: [s1210_repo_routes.py L1623](../../python-scripts/esocial/s1210_repo_routes.py)
  - `override = (req.recibo_override_por_cpf or {}).get(cpf)`

Histórico de uso (template para criar novos scripts):

- [envio_lote3_novembro.py](../../python-scripts/envio_lote3_novembro.py) — flag `--recibos-xlsx --aba --col-recibo`
- [envio_lote3_dezembro.py](../../python-scripts/envio_lote3_dezembro.py)
- [envio_lote3_outubro.py](../../python-scripts/envio_lote3_outubro.py)
- [\_envia_set_l3_63_recibos.py](../../python-scripts/_envia_set_l3_63_recibos.py)

---

## 7. Por que esse doc existe agora (transição de algoritmo)

Estamos em ~99% no algoritmo atual (chain walk do DB → fallback override manual). O **próximo algoritmo** deve eliminar o passo 4 deste doc (ler XLSX da Ana) integrando direto:

1. **Consulta automática `WsConsultarIdentificadores`** filtrada por CPF+período → AN devolve recibo ATIVO.
2. **Cache local de recibo ativo** com TTL curto (24h?) tabelado em `s1210_cpf_recibo_ativo_an`.
3. **Override interno** quando 459 detectado → 1 retry automático com recibo do AN.

Quando isso entrar, **este fluxo (override via XLSX) vira fallback manual** — não some, mas deixa de ser o caminho normal. Por isso este doc fica parametrizado: muda só os valores no topo, o resto é o mesmo.

---

## 8. Casos pendentes (Nov/2025) que NÃO usam override

| Erro       | Qtd | Ação                                                              |
| ---------- | --: | ----------------------------------------------------------------- |
| `401/459`  | 130 | **Este doc — override XLSX**                                      |
| `401/1089` |  56 | Retry direto (sem override) — chain walk resolve                  |
| `401/8`    |   9 | Reclassificar para L2 (plano coletivo) — não é problema de recibo |
| sem-código |  13 | Auditoria caso a caso                                             |

---

## 9. Inputs verificados nesta sessão

- XLSX: `C:\Users\xandao\Downloads\Recibos 112025  final.xlsx` (19384 bytes, 146 linhas dados, 130 com `401/459`).
- Backend rodando: `localhost:8000` (último restart async, path absoluto).
- DB remoto: `python-scripts/db_config.py`, `empresa_id=1`.
- Relatório baseline: [docs/RELATORIOS_L1_2025/RELATORIO_ERROS_S1210_L1_NOV2025.md](../RELATORIOS_L1_2025/RELATORIO_ERROS_S1210_L1_NOV2025.md).
