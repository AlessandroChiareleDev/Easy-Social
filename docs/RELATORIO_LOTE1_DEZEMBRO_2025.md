# Relatório — Envio Lote 1 Dezembro/2025

**Data execução:** 27/04/2026
**Período apuração (perApur):** `2025-12`
**Lote alvo:** `1` (1º Lote Dezembro 2025)
**Empresa:** CNPJ `05969071000110`
**Ambiente:** Produção (1)

---

## 1. Contexto

Continuação da campanha de envios em massa de S-1210. Após Lote 1 Novembro/2025 (95.61% OK em 25/04/2026), partimos para Dezembro/2025.

**Bloqueio inicial:** Folha 2025-12 estava **fechada** (S-1299 já transmitido). Primeira tentativa de envio retornou ocorrência **620** ("folha já fechada, precisa reabrir").

**Solução:** Transmissão do evento **S-1298 (Reabertura de Eventos Periódicos)** antes do envio do lote.

---

## 2. S-1298 — Reabertura da Folha

- **Script:** [python-scripts/\_enviar_s1298_dezembro.py](../python-scripts/_enviar_s1298_dezembro.py)
- **Schema:** `evtReabreEvPer` v_S_01_03_00
- **Carregamento do certificado:** `_load_cert_ativo()` (lê PFX + senha descriptografada do DB local `certificados_a1`)
- **Resultado:**
  - Recibo: `1.1.0000000040234461842`
  - Protocolo: `1.1.202604.0000000013074283602`
  - Status: ✅ Folha reaberta com sucesso

---

## 3. Ingest do XLSX

- **Script:** [python-scripts/\_ingest_lote1_dezembro.py](../python-scripts/_ingest_lote1_dezembro.py)
- **Arquivo origem:** `1º Lote Dezembro 2025.xlsx`, aba `Planilha1`
- **Mapeamento de colunas:**
  - `col A (0)` → identificador do lote (`"1º Lote"`)
  - `col B (1)` → mês (`"DEZEMBRO"`)
  - `col I (8)` → CPF
- **Filtro aplicado:** apenas linhas onde col A = `1º Lote`
- **Tabela destino:** `s1210_cpf_scope` (per_apur=`2025-12`, lote_num=`1`)
- **Resultado:** **5.083 CPFs únicos** inseridos (1 CPF inválido descartado de 5.084 linhas)

> **Nota crítica:** A coluna D do XLSX tem `202511` como valor legado do exportador — **NÃO refletir o período real**. A fonte de verdade é col A + col B + nome do arquivo.

---

## 4. Configuração Backend

- **bot_api Python (FastAPI/uvicorn):** porta `8000`
  - Variável: `ESOCIAL_DUMP_XML_DIR=C:\Users\xandao\Documents\GitHub\Easy-Social\ARQUIVOS_RETORNO\2025-12`
  - Registro novo em `FONTES["2025-12"]` em [python-scripts/esocial/s1210_missao_routes.py](../python-scripts/esocial/s1210_missao_routes.py)
- **Backend V1 Express:** porta `3333` (proxy para bot_api e endpoint de envio)
- **Endpoint envio:** `POST /api/s1210-repo/enviar-lote-cpfs`

---

## 5. Etapas Escalonadas (Validação Progressiva)

Estratégia "1 → 10 → 500 → cheio" para validar produção sem queimar 5k CPFs num go.

| Etapa               | CPFs             | Workers | Batch | OK   | ERR | Taxa OK    | Tempo           | cpf/s | Observação                                                             |
| ------------------- | ---------------- | ------- | ----- | ---- | --- | ---------- | --------------- | ----- | ---------------------------------------------------------------------- |
| 1 — smoke test      | 1                | 1       | 1     | 0    | 1   | 0%         | —               | —     | Erro **620** → disparou S-1298                                         |
| 2 — após reabertura | 10               | 1       | 10    | 9    | 1   | **90.0%**  | 15.9s           | 0.63  | OK pra prosseguir                                                      |
| 3 — stress          | 500              | 5       | 50    | 367  | 133 | **73.4%**  | 119.4s          | 4.19  | 216× ocorrência **1089** (concorrência interna). Workers=5 alto demais |
| 4 — envio cheio     | 4707 (pendentes) | **3**   | 50    | 4420 | 287 | **93.91%** | 1990.8s (33min) | 2.36  | Receita do Nov funcionou                                               |

**Decisão chave:** Após Etapa 3, baixei workers de 5 para 3 (mesma config que rendeu 95.61% no Nov). Resultado consistente.

---

## 6. Resultado Final Consolidado

| Métrica         | Valor              |
| --------------- | ------------------ |
| **Scope total** | 5.083 CPFs         |
| **OK**          | **4.796 (94.35%)** |
| **ERR**         | 287 (5.65%)        |

### Quebra dos erros (287)

| Tipo             | Qtd | Causa                                                       | Ação                                                 |
| ---------------- | --- | ----------------------------------------------------------- | ---------------------------------------------------- |
| `sem_recibo_zip` | 282 | CPF não tem S-1210 prévio (nunca foi enviado nesse perApur) | **Esperado** — não dá pra retificar o que não existe |
| `oc_1089`        | 5   | Concorrência interna eSocial (lock)                         | **Retry-able** — basta rerodar                       |

---

## 7. Comparação Nov vs Dez

| Período     | Scope     | OK        | Taxa OK    | Workers | Batch |
| ----------- | --------- | --------- | ---------- | ------- | ----- |
| 2025-11     | ~4.730    | 4.522     | 95.61%     | 3       | 50    |
| **2025-12** | **5.083** | **4.796** | **94.35%** | 3       | 50    |

Qualidade equivalente. Pequena variação atribuída a maior volume de CPFs sem S-1210 prévio em Dezembro.

---

## 8. Artefatos Gerados

### Scripts criados

- [python-scripts/\_ingest_lote1_dezembro.py](../python-scripts/_ingest_lote1_dezembro.py) — ingest XLSX → scope
- [python-scripts/\_envio_lote1_dezembro.py](../python-scripts/_envio_lote1_dezembro.py) — disparo dos blocos (CLI: `--max --workers --batch --dry-run`)
- [python-scripts/\_enviar_s1298_dezembro.py](../python-scripts/_enviar_s1298_dezembro.py) — reabertura da folha

### Scripts editados

- [python-scripts/esocial/s1210_missao_routes.py](../python-scripts/esocial/s1210_missao_routes.py) — adicionado `FONTES["2025-12"]`

### Logs e resumos

- `python-scripts/envio_dez_full.log` — log completo do envio cheio
- `python-scripts/bot_api_dez.log` — log do bot_api durante a janela
- `ARQUIVOS_RETORNO/2025-12/resumo/envio_20260427_183829.jsonl` — resumo bloco a bloco do envio cheio
- `ARQUIVOS_RETORNO/2025-12/*.xml` — XMLs enviados/respondidos (dump)

---

## 9. Visualização Frontend

Frontend V1 (porta `5173`) já lê os dados de `s1210_cpf_envios`:

- `http://localhost:5173/repositorio-s1210-por-lote` — visão por lote × período (recomendado)
- `http://localhost:5173/repositorio-s1210` — repositório geral
- `http://localhost:5173/s1210-anual` — visão anual por CPF
- `http://localhost:5173/pipeline` — pipeline S-1298 → S-1210 → S-1299

---

## 10. Pendências

- [ ] **Retry dos 5 `oc_1089`**: rerodar `python python-scripts\_envio_lote1_dezembro.py --workers 3 --batch 50` (pega só o que está pendente)
- [ ] **Confirmar com usuário** se existem Lotes 2/3/4 para Dezembro (XLSX só trouxe "1º Lote")
- [ ] **S-1299 (refechamento)** quando todos os lotes Dez estiverem fechados
- [ ] Decidir se vale tentar enviar S-1210 para os 282 CPFs `sem_recibo_zip` (envio original em vez de retificação) — depende de regra de negócio

---

## 11. Lições Aprendidas

1. **workers=3 é o sweet spot** para o webservice eSocial nessa empresa. workers=5 já gera muito `1089`.
2. **Folha fechada + S-1298 funciona em produção** sem efeito colateral (recibo gerado, sem ocorrências).
3. **Não confiar em colunas legadas do XLSX** (col D tinha `202511`). Fonte de verdade: col A/B + filename.
4. **Carregamento de cert via DB** (`_load_cert_ativo`) é mais seguro que `.env` — evita depender de variável que pode estar desatualizada.
5. **Validação escalonada (1 → 10 → 500 → cheio)** pegou o problema de concorrência cedo, antes de queimar os 5k CPFs.
