# PLANO DE PERFORMANCE — Envio S-1210 em Lote

**Status:** aguardando confirmação visual do usuário antes de implementar.  
**Data:** 22/04/2026  
**Baseline medido:** 50 CPFs em ~195s (≈3,9 s/CPF) — 1.835 OK em 121 min (2000 CPFs).  
**Meta:** baixar para **≤ 60s por batch de 50** (≈1,2 s/CPF) → 2000 CPFs em **~40 min** (3× mais rápido).

---

## 1. Onde está o tempo hoje (decomposição)

Perfil estimado de um batch de 50 (195s total):

| Fase                                     |     Tempo |   % | Natureza                          | Preserva dados? |
| ---------------------------------------- | --------: | --: | --------------------------------- | :-------------: |
| **Fase 1 — Build+Sign 50 XMLs** (serial) | **~120s** | 62% | CPU-bound (XMLDSig, cryptography) |       ✅        |
| **Fase 2 — Enviar SOAP ao eSocial**      |       ~8s |  4% | Rede (1 POST)                     |       ✅        |
| **Fase 3 — Polling consultar_lote**      |      ~55s | 28% | `sleep(5)` fixo + 1..N chamadas   |       ✅        |
| **Fase 4 — Persistir no banco**          |       ~5s |  3% | 50 UPDATEs sequenciais            |       ✅        |
| **Overhead interno** (logs, validações)  |       ~7s |  3% | —                                 |       ✅        |

**Gargalo principal:** Fase 1 (serial) e primeira espera da Fase 3 (5s fixo).

---

## 2. Otimizações propostas (todas sem perder informação)

### 🟢 **O1 — Paralelizar Fase 1 (build + sign) com ProcessPool**

**Ganho estimado: −80 a −90s/batch (3×–6×)**

Hoje: 50 CPFs processados em loop serial.  
Mudança: usar `concurrent.futures.ProcessPoolExecutor(max_workers=8)` para paralelizar **`gerar_xml` + `assinar_xml`** (ambos CPU-bound, liberam o GIL via subprocessos).

- O certificado (`pfx_data`, `senha`) é passado ao pool uma vez.
- A chamada `_buscar_s1210_unico` (leitura do ZIP em memória) continua serial porque o cache já está em RAM e o custo é baixo — não compensa serializar ZIP pra worker.
- Cada worker devolve: `(cpf, xml_assinado, evt_id, nr_recibo_usado)` ou erro estruturado.
- **Preserva 100%** dos campos atuais (etapa, erro, nr_recibo_usado, evt_id).

**Nota técnica:** em Windows, ProcessPool exige que a função esteja no topo do módulo (picklable). Vou criar `_worker_build_sign(args)` no módulo.

---

### 🟢 **O2 — Reduzir primeira espera do polling**

**Ganho estimado: −3 a −4s/batch**

Hoje:

```python
for attempt in range(15):
    __t.sleep(5)          # <-- sempre espera 5s antes da 1ª consulta
    cons = consultar_lote(...)
```

Mudança: **polling adaptativo com backoff progressivo**:

```python
waits = [1.0, 1.5, 2.0, 3.0, 4.0, 5.0, 5.0, 5.0, ...]  # até 20 tentativas
```

- Primeira consulta 1s após o envio (eSocial frequentemente responde em 2–4s).
- Se `cd=101` (processando) → dobra até 5s.
- Limite máximo total = 75s (atual = 75s também, mas cobrindo mais tentativas rápidas no início).
- **Preserva 100%**: mesmo campo `eventos_retorno`, mesma lógica de mapeamento.

---

### 🟢 **O3 — Bulk INSERT da marca "enviando"**

**Ganho estimado: −2 a −3s/batch**

Hoje: 50 `INSERT` separados (cada um round-trip com o Supabase pooler).  
Mudança: `execute_values` (psycopg2) → **1 único INSERT com 50 rows**.

Mesma tabela, mesmas colunas. Nada muda no schema nem no front.

---

### 🟢 **O4 — Bulk UPDATE/UPSERT na persistência final**

**Ganho estimado: −3 a −5s/batch**

Hoje: `_persistir_resultados_batch` roda 50 `UPDATE ... WHERE id = (SELECT id ... ORDER BY enviado_em DESC LIMIT 1)` — 50 sub-selects + 50 updates.  
Mudança: **1 UPDATE com `FROM VALUES`** (Postgres suporta nativo):

```sql
UPDATE s1210_cpf_envios u
   SET status = v.status,
       nr_recibo_novo = v.nr_recibo_novo,
       codigo_resposta = v.codigo_resposta,
       descricao_resposta = v.descricao_resposta,
       erro_descricao = v.erro_descricao,
       xml_resposta = v.xml_resposta,
       duracao_ms = v.duracao_ms
  FROM (VALUES (%s,%s,%s,...), ...) AS v(cpf, status, nr_recibo_novo, ...)
 WHERE u.cpf = v.cpf
   AND u.per_apur = %s
   AND u.lote_num = %s
   AND u.id = (SELECT id FROM s1210_cpf_envios
                WHERE cpf = u.cpf AND per_apur = u.per_apur AND lote_num = u.lote_num
                ORDER BY enviado_em DESC NULLS LAST LIMIT 1)
```

Preserva 100% dos campos gravados. Só muda o número de round-trips (de 50 para 1).

---

### 🟡 **O5 — Persistir HTTP session com keep-alive**

**Ganho estimado: −1 a −2s/batch**

`ESocialClient.enviar_lote` e `ESocialClient.consultar_lote` abrem um TCP/TLS novo a cada chamada.  
Mudança: usar `requests.Session()` reutilizável no escopo da request → reaproveita handshake TLS na consulta após o envio.

**Risco:** nenhum (session é thread-safe aqui).

---

### 🟡 **O6 — Cachear `_CACHE_XLSX` + `_load_cert_ativo` entre batches**

**Ganho estimado: −0,5 a −1s/batch (já parcialmente cacheado)**

Hoje `_CACHE_XLSX` é global por `per_apur`, mas há re-parsing defensivo.  
Mudança: verificar se está em RAM e pular revalidação quando batches consecutivos rodam em sequência.

---

### 🔴 **O7 — Paralelizar múltiplos lotes eSocial** (NÃO RECOMENDADO)

Poderia mandar 2 ou 3 `<envioLoteEventos>` concorrentes ao eSocial. **Mas voltaria o risco de 1089** (auto-concorrência) que acabamos de eliminar. **Descartado.**

---

## 3. Ganho projetado (soma)

| Fase                |     Hoje | Com O1+O2+O3+O4+O5 |            Ganho |
| ------------------- | -------: | -----------------: | ---------------: |
| Fase 1 (build+sign) |     120s |           **~20s** |            −100s |
| Fase 2 (send)       |       8s |                 7s |              −1s |
| Fase 3 (poll)       |      55s |           **~25s** |             −30s |
| Fase 4 (persist)    |       5s |            **~1s** |              −4s |
| Overhead            |       7s |                 5s |              −2s |
| **Total batch 50**  | **195s** |           **≈58s** | **−137s (−70%)** |

### Projeção para 2000 CPFs

- Hoje: 121 min
- Depois: **~39 min** (3,1× mais rápido)

### Projeção para 6.393 pendentes restantes

- Hoje: ~6h 30min
- Depois: **~2h 05min**

---

## 4. O que **não** muda

- ✅ Logs linha-a-linha no front (mesmo formato: `✓ cpf · nome · novo recibo` / `✗ cpf · etapa · descricao`).
- ✅ Contadores `OK/ok_idempotente/ERRO/retry` no resumo.
- ✅ Todas as colunas gravadas em `s1210_cpf_envios` (status, nr_recibo_novo, codigo_resposta, descricao_resposta, erro_descricao, xml_resposta, duracao_ms, ocorrencias).
- ✅ Mapeamento evt_id → CPF por seq.
- ✅ Tratamento de 543 (ok_idempotente), 1089 (erro_retry).
- ✅ Chain walk para evitar 459.
- ✅ Contagem do front: OK / erro / pendentes.
- ✅ Comportamento do botão Play / Pause.
- ✅ Erro isolado por CPF (um quebrar não derruba o batch).

---

## 5. Riscos e mitigação

| Risco                                                                    | Mitigação                                                                |
| ------------------------------------------------------------------------ | ------------------------------------------------------------------------ |
| ProcessPool no Windows precisa `if __name__ == "__main__":` guard        | Worker fica no topo do módulo, isolado, sem globals                      |
| Workers não herdarem cert em memória                                     | Cert é passado como argumento serializado (bytes + senha)                |
| Primeira consulta em 1s pode sempre dar `cd=101`                         | Backoff continua; pior caso é igual ao atual                             |
| Bulk UPDATE sql bugar em edge-case (CPF com múltiplas linhas 'enviando') | Subquery `ORDER BY enviado_em DESC LIMIT 1` garante a linha mais recente |
| Keep-alive TLS expirar                                                   | `requests.Session` refaz handshake transparente                          |

---

## 6. Plano de implementação (ordem)

1. **O3 + O4** (bulk INSERT/UPDATE) — ganho pequeno, risco mínimo, warm-up.
2. **O2** (polling adaptativo) — trivial, −3s imediato.
3. **O5** (Session keep-alive) — uma linha.
4. **O1** (ProcessPool build+sign) — o grande ganho; requer refactor com worker isolado.
5. Teste em 1 batch de 50 → comparar com 195s.
6. Teste em 2000 → comparar com 121 min.
7. Se métrica bater ≤ 65s/batch, rodar os 6.393 pendentes restantes.

---

## 7. Esforço

- Código: ~150 linhas no `s1210_repo_routes.py` + pequena função worker.
- Sem mudança no frontend.
- Sem mudança no schema do banco.
- Sem mudança no contrato HTTP (request/response iguais).
- Sem dependência nova.

---

**Aguardando confirmação visual (imagem) do usuário para iniciar a implementação.**
