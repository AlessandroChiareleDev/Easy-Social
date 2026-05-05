# COMO FAZER LOTE 1 (S-1210 retificação SEM planSaude)

> **Arquivo vivo.** Atualizar sempre que descobrir algo novo ou um ponto estiver errado. Histórico no final.

Última atualização: 2026-04-27 (pós envio Lote 1 Dezembro/2025)

---

## 1. Conceito do Lote 1 (fonte: frontend `RepositorioS1210PorLoteView.vue` + `S1210MissaoView.vue`)

- **Lote 1** — CPFs **sem operadora** na aba "Operadoras" do XLSX → S-1210 retif **sem** `<planSaude>`. **(este documento)**
- **Lote 2** — CPFs com operadora + rubricas com natureza correta → S-1210 retif **com** `<planSaude>` agregado por CNPJ.
- **Lote 3** — Mesma estrutura do Lote 2; rubricas 774/775/522 com natureza errada → depende de S-1010 reclass vigente.
- **Lote 4** — manuais.

**Regra chave do Lote 1:** o XML de retif **NÃO leva `<planSaude>`**. Backend simplesmente lê S-1210 original do ZIP, copia `info_pgtos`, seta `indRetif=2`, aplica chain walk de recibo, assina e envia. É o cenário mais simples.

Rubricas: irrelevante pra Lote 1 — não há agregação de plano de saúde.

---

## 2. O que NÃO fazer (lições gerais — vide LOTE3)

Cortar toda camada offline. Não codar:

- gerador XML S-3000 offline
- assinador standalone
- mini-CLI `enviar_retif.py --dry-run`

O endpoint `POST /api/s1210-repo/enviar-lote-cpfs` em `python-scripts/esocial/s1210_repo_routes.py` (linha ~1485) já faz tudo: lê S-1210 original, copia `info_pgtos`, seta `indRetif=2`, chain walk, assina, envia prod, polla e grava em `s1210_cpf_envios`. Aceita até 50 CPFs por POST num só `envioLoteEventos`.

---

## 3. Payload do endpoint `/api/s1210-repo/enviar-lote-cpfs` (Lote 1)

```jsonc
{
  "per_apur": "2025-12",
  "lote_num": 1,
  "cpfs": ["12345678900"],
  "confirmar_producao": true,

  // NÃO mandar plan_saude_por_cpf — Lote 1 não tem planSaude.
  // recibo_override_por_cpf: opcional. Se omitir, chain walk do backend.
}
```

**Diferença vs Lote 2/3:** simplesmente **não enviar** `plan_saude_por_cpf`. O backend detecta ausência e gera retif sem `<planSaude>`.

---

## 4. Fontes de dados

### XLSX do lote

- Nov/2025: `1º Lote Novembro 2025.xlsx`
- Dez/2025: `1º Lote Dezembro 2025.xlsx` (5.084 linhas, 5.083 CPFs únicos válidos)
- Mapeamento de colunas confirmado para Dezembro:
  - `col A (0)` → identificador (`"1º Lote"`)
  - `col B (1)` → mês (`"DEZEMBRO"`)
  - `col I (8)` → CPF
- **⚠️ Não confiar na col D** — tinha `202511` no XLSX de Dezembro. Fonte de verdade: col A + col B + filename.

### ZIP S-1210 original

- **Pasta master (sempre a mesma):** `C:\Users\xandao\Downloads\xmls do e social mes a mes.zip` (~4.95 GB)
  - Dentro tem **todos os meses 2025** já organizados:
    - `01-jan2025.zip`
    - `02-fev2025.zip`
    - `03-marc2025.zip`
    - `04-abril2025.zip`
    - `05-maio.zip`
    - `06-Jun2025.zip`
    - `07- Jul2025.zip` (atenção ao espaço extra)
    - `08- ago2025.zip` (atenção ao espaço extra)
    - `09-set2025.zip`
    - `10-out2025.zip`
    - `11-nov2025.zip`
    - `12-dez2025.zip`
- **Não procurar em outros lugares.** Sempre extrair desse master ZIP.
- Usado pelo backend para localizar o S-1210 original de cada CPF e extrair `info_pgtos` + `nrRecibo`.

### `s1210_operadoras`

- **Lote 1 NÃO usa.** Pode estar vazia.

---

## 5. Roteiro de execução (oficial — receita PC1, refinada Dez/2025)

Disciplina obrigatória: **1 → 10 → 500 → resto**, sequencial em workers.

### Parâmetros confirmados (Nov 95.61% / Dez 94.35%)

| Parâmetro                 | Valor                                                  |
| ------------------------- | ------------------------------------------------------ |
| Batch size                | **50 CPFs por POST**                                   |
| Workers script            | **3** (sweet spot — workers=5 dá 216× ocorrência 1089) |
| Workers internos endpoint | 16 (ThreadPool)                                        |
| Retry no script           | não tem                                                |
| Sleep entre POSTs         | não tem                                                |
| `timeout` requests        | **600s** (subir pra 900 se estourar)                   |
| Throughput real           | **~2,3 CPFs/s** (~140/min) com workers=3               |
| `tp_amb` no payload       | NÃO mandar (backend é prod hardcoded)                  |
| `confirmar_producao`      | `True`                                                 |

### Passo 0 — Pré-check

```sql
SELECT COUNT(*) FROM s1210_cpf_scope
 WHERE per_apur='2025-12' AND lote_num=1 AND empresa_id=1;  -- esperado ~5083
```

Se for 0 → upload do XLSX + ZIP precisa ser feito ANTES.

### Passo 1 — Upload (pré-requisito)

1. **XLSX de scope** → popula `s1210_cpf_scope`. Use `_ingest_lote1_<mes>.py` ou rota `/api/s1210-repo/ingestao-scope-xlsx`.
2. **ZIP** → popula `s1210_zip_eventos` (chain walk de recibo).
3. **S-1298 reabertura** se folha já está fechada (vide Passo 1.5).

### Passo 1.5 — S-1298 (se folha fechada)

Se 1º CPF retornar `ocorrência 620` → folha já fechada → enviar S-1298 antes:

- Script: `python-scripts/_enviar_s1298_<mes>.py`
- Schema: `evtReabreEvPer` v_S_01_03_00
- Cert: usar `_load_cert_ativo()` (lê PFX + senha do DB local `certificados_a1`) — **não** depender de `.env`.
- `IND_APURACAO="1"`, `AMBIENTE="1"`, `PER_APUR="2025-MM"`.

Exemplo Dez/2025:

- Recibo gerado: `1.1.0000000040234461842`
- Protocolo: `1.1.202604.0000000013074283602`

### Passo 2 — 1 CPF teste

```powershell
cd python-scripts
..\.venv\Scripts\python.exe _envio_lote1_dezembro.py --max 1 --workers 1 --batch 1
```

### Passo 3 — Interpretar resposta

| Código                            | Significado                                       | Ação                                                                    |
| --------------------------------- | ------------------------------------------------- | ----------------------------------------------------------------------- |
| `cdResp=201` sucesso              | OK                                                | Escala 10 → 500 → resto                                                 |
| `ocorr=620` folha fechada         | Falta S-1298                                      | Reabrir (Passo 1.5) e retomar                                           |
| `ocorr=459` recibo não ativo      | Chain walk desatualizado / timeout falso anterior | Rebaixar ZIP, reindexar                                                 |
| `ocorr=1089` concorrência interna | Lock eSocial                                      | Esperar 30s, retry — geralmente 1º já processou                         |
| `sem_recibo_zip`                  | CPF não tem S-1210 prévio nesse perApur           | **Esperado** — não dá pra retificar o que não existe. Marcar NAO_ENVIAR |

### Passo 4 — Escalar

```powershell
..\.venv\Scripts\python.exe _envio_lote1_dezembro.py --max 10 --workers 1 --batch 10
..\.venv\Scripts\python.exe _envio_lote1_dezembro.py --max 500 --workers 5 --batch 50  # stress test (opcional)
..\.venv\Scripts\python.exe _envio_lote1_dezembro.py --workers 3 --batch 50           # resto (PRODUÇÃO)
```

### Passo 5 — Retry de `ocorr=1089`

Basta rerodar — script pega só o que está com status<>'ok':

```powershell
..\.venv\Scripts\python.exe _envio_lote1_dezembro.py --workers 3 --batch 50
```

### Monitorar

```sql
WITH lv AS (
  SELECT DISTINCT ON (cpf) cpf, status, codigo_resposta, erro_descricao
  FROM s1210_cpf_envios
  WHERE empresa_id=1 AND per_apur='2025-12' AND lote_num=1
  ORDER BY cpf, enviado_em DESC NULLS LAST
)
SELECT
  COUNT(*) FILTER (WHERE lv.status='ok')    AS ok,
  COUNT(*) FILTER (WHERE lv.status='erro')  AS erro,
  COUNT(*) FILTER (WHERE lv.status IS NULL) AS nunca,
  COUNT(*)                                  AS total
FROM s1210_cpf_scope s
LEFT JOIN lv ON lv.cpf = s.cpf
WHERE s.empresa_id=1 AND s.per_apur='2025-12' AND s.lote_num=1;
```

---

## 6. Bugs conhecidos / pegadinhas

- **Backend sem `--reload`**: `bot_api.py:199`. Mudanças em `esocial/*` só valem após restart (~5s downtime).
- **`ESOCIAL_DUMP_XML_DIR`**: setar **antes** de subir o bot_api pra dump dos XMLs ir na pasta certa.
  ```powershell
  $env:ESOCIAL_DUMP_XML_DIR="C:\Users\xandao\Documents\GitHub\Easy-Social\ARQUIVOS_RETORNO\2025-12"
  ```
- **`FONTES["AAAA-MM"]`** em `python-scripts/esocial/s1210_missao_routes.py` precisa ter entrada do mês alvo (`xlsx`, `zip`, `aba_geral`, `total_lote1`, `col_lote`, `col_cpf`). Se faltar → endpoint quebra.
- **PowerShell 5.1 cp1252**: forçar `sys.stdout.reconfigure(encoding="utf-8")` no topo dos scripts.
- **PowerShell não tem `&&`**: usar `;`.

---

## 7. Estado atual (Lote 1, empresa_id=1)

| per_apur |  scope |    OK | ERR |    Taxa OK | Status                                                           |
| -------- | -----: | ----: | --: | ---------: | ---------------------------------------------------------------- |
| 2025-11  | ~4.730 | 4.522 | 208 |     95,61% | ✅ fechado (workers=3, batch=50)                                 |
| 2025-12  |  5.083 | 4.796 | 287 | **94,35%** | ✅ fechado (workers=3, batch=50). 282 sem_recibo_zip + 5 oc_1089 |
| 2025-10  |      — |     — |   — |          — | (verificar se aplicável)                                         |

Scripts de referência:

- `python-scripts/_ingest_lote1_dezembro.py` — ingest XLSX → `s1210_cpf_scope`
- `python-scripts/_envio_lote1_dezembro.py` — disparo (CLI: `--max --workers --batch --dry-run`)
- `python-scripts/_enviar_s1298_dezembro.py` — reabertura folha
- `python-scripts/_envio_lote1_novembro.py` — referência Nov
- `python-scripts/esocial/s1210_repo_routes.py:1485` — endpoint
- `python-scripts/esocial/s1210_missao_routes.py` — `FONTES`, `_load_cert_ativo`

---

## 8. Pendências / perguntas em aberto

1. **Retry dos 5 `oc_1089`** Dezembro — basta rerodar `_envio_lote1_dezembro.py --workers 3 --batch 50`.
2. **Decidir** se vale tentar S-1210 **original** (não retif) para os 282 CPFs `sem_recibo_zip` Dez/2025 — depende de regra de negócio.
3. **Existem Lotes 2/3/4 para Dezembro/2025?** — XLSX só trouxe "1º Lote". Confirmar com Ana.
4. **S-1299 refechamento Dezembro** — quando todos os lotes Dez estiverem fechados.

---

## 9. Lições aprendidas

1. **workers=3 é o sweet spot** para o webservice eSocial nessa empresa. workers=5 já gera muito `1089` (216× em 500 CPFs = 43% dos blocos).
2. **Folha fechada + S-1298 funciona em produção** sem efeito colateral (recibo gerado, sem ocorrências).
3. **Não confiar em colunas legadas do XLSX** (col D tinha `202511` no Dez). Fonte de verdade: col A/B + filename.
4. **Cert via DB** (`_load_cert_ativo`) é mais seguro que `.env` — evita variável desatualizada/inexistente.
5. **Validação escalonada (1 → 10 → 500 → cheio)** pega problema cedo, antes de queimar 5k CPFs.
6. **`sem_recibo_zip` é estrutural** — não é bug nosso. CPF nunca teve S-1210 prévio nesse perApur. ~5% dos casos.

---

## 10. Histórico de correções

- **2026-04-25:** envio Lote 1 Novembro/2025 — 95,61% OK com workers=3 batch=50. Receita inicial.
- **2026-04-27:** envio Lote 1 Dezembro/2025. S-1298 reabertura disparada (folha estava fechada). Stress test com workers=5 mostrou degradação (216× oc_1089). Voltado pra workers=3, fechou em 33min com 94,35% OK. Documento criado seguindo padrão do `COMO_FAZER_LOTE3.md`.
