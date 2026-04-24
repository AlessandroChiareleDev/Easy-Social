# Erros de Envio eSocial — APPA

> Log vivo de todos os erros de envio S-1210 (e eventos correlatos) da APPA.
> **Começa em 24/04/2026.** Atualizar a cada rodada de envio.
>
> Fonte canônica: `s1210_cpf_envios` (empresa_id=1).
> Lógica de status final por CPF: `DISTINCT ON (cpf) ORDER BY enviado_em DESC`.

---

## Snapshot geral — 24/04/2026

| Mês | Lote | Scope | OK | Erro | `nao_enviar_ana` | % fechado |
|---|---:|---:|---:|---:|---:|---:|
| 2025-02 | 1 | 9.471 | 8.599 | 872 | — | 90,8% |
| 2025-02 | 2 | 1.390 | 1.279 | 21 | — | 92,0% |
| 2025-02 | 3 | 737 | 730 | — | 7 | **100%** |
| 2025-02 | 4 | 2 | — | — | — | — |
| 2025-03 | 1 | 8.164 | 7.373 | 791 | — | 90,3% |
| 2025-03 | 2 | 1.395 | 1.275 | 13 | — | 91,4% |
| 2025-03 | 3 | 1.624 | 1.619 | 2 | 3 | **99,9%** |
| 2025-03 | 4 | 2 | — | — | — | — |
| 2025-04 | 1 | 7.142 | 6.221 | 921 | — | 87,1% |
| 2025-04 | 2 | 1.376 | 1.123 | 147 | — | 81,6% |
| 2025-04 | 3 | 1.498 | 1.482 | 1 | 15 | **99,9%** |
| 2025-05 | 1 | 8.724 | 8.583 | **1.438** | — | 85,6% |
| 2025-05 | 3 | 1.319 | 1.289 | 30 | — | 97,7% |
| 2025-06 | 1 | 6.827 | 6.781 | 46 | — | 99,3% |
| 2025-06 | 3 | 1.423 | — | — | — | ainda não enviado |
| 2025-07 | 1 | 6.559 | 6.516 | 43 | — | 99,3% |

---

## Incidentes (rodadas com erro em massa)

### INC-2026-04-23 — Maio/2025 Lote 1 — 1.438 erros código 8

- **Quem**: PC2 (NITRO).
- **Quando**: 23/04/2026 17:46 → 19:16 UTC (~1h30).
- **Endpoint**: `POST /api/s1210-repo/enviar-lote-cpfs`.
- **Causa raiz**: PC2 disparou retificação S-1210 em massa **sem popular `s1210_operadoras`** do Maio. Para os ~1.438 CPFs que tinham plano de saúde no evento original, o XML novo saiu sem o grupo `planSaude` → eSocial rejeitou com ocorrência código 8.
- **Código eSocial**: `401` + ocorrência tipo 1 código 8: *"Grupo 'Plano de saúde coletivo' deve ser preenchido."*
- **Impacto**: 1.438 CPFs em `status='erro'`. Status original no eSocial **não foi alterado** (evento rejeitado antes de gravar).
- **Ação corretiva pendente**:
  1. Popular `s1210_operadoras` Maio a partir do XLSX da Ana.
  2. Reenviar os 1.438 CPFs via `/enviar-lote-cpfs` (o endpoint puxa `plan_saude` do banco sozinho).

### INC-2026-04-24 — Scope L1 Maio/Junho deletado por bug em `ingest_lote3_*.py`

- **Quem**: PC2.
- **Quando**: 23/04/2026 (Maio) e 24/04/2026 (Junho).
- **Causa raiz**: `ingest_lote3_maio.py` e a cópia `ingest_lote3_junho.py` faziam `DELETE FROM s1210_cpf_scope WHERE empresa_id=%s AND per_apur=%s` **sem filtrar `lote_num`** antes de inserir o L3. Apagou L1/L2/L4 Maio e L1 Junho.
- **Estrago**: scope zerado para Maio L1/L2/L4 e Junho L1.
- **Status dos envios**: **intocado** (`s1210_cpf_envios` não foi alterado).
- **Recuperação**: PC2 reconstruiu scope a partir de `s1210_cpf_envios` via `INSERT ... SELECT DISTINCT cpf` com `ON CONFLICT DO NOTHING`.
  - Maio L1: 8.724 linhas recriadas.
  - Junho L1: 6.827 linhas recriadas.
  - Maio L2: **não recuperado** (nunca teve envio — precisa reingestar XLSX original se quiser restaurar).
- **Bug corrigido nos 2 scripts** (DELETE agora filtra `AND lote_num=%s`).
- **Relatório completo**: [docs/INCIDENTE_PC2_24-04-2026_SCOPE_DELETADO.md](docs/INCIDENTE_PC2_24-04-2026_SCOPE_DELETADO.md).
- **Discrepância conhecida**: L1 Maio tem 8.724 no scope vs 10.021 CPFs distintos em envios. Os 1.297 de diferença estão cadastrados como L3 no scope (constraint UNIQUE `(empresa_id, per_apur, cpf)` bloqueou o ON CONFLICT). Decisão pendente: mover pra L1 via UPDATE ou manter como L3.

---

## Catálogo de erros recorrentes

### Código 8 (tipo 1) — *"Grupo 'Plano de saúde coletivo' deve ser preenchido"*

- **Quando acontece**: retificação sem `planSaude` enquanto o evento original TINHA.
- **Correção**: popular `s1210_operadoras` (CNPJ operadora + regANS + valor titular + dependentes) e reenviar.
- **Ocorrências conhecidas**:
  - Maio L1 23/04/2026: **1.438 CPFs** (INC-2026-04-23).
  - Junho L1 24/04/2026: **46 CPFs** (sobra do mesmo problema).

### Código 401 + ocorrência `459` (recibo stale)

- **Quando acontece**: `nrReciboEvtAnterior` passado no XML não é mais o ativo no eSocial (retificação em cima de retificação sem o recibo mais novo).
- **Correção padrão**: `recibo_override_por_cpf` com valor da planilha da Ana.
- **Ocorrências**: histórico Fev/Mar/Abr Lote 3 (já resolvido via XLSX Ana).

### Código 401 + ocorrência `861` (rescisão vs competência)

- **Quando acontece**: CPF já desligado em competência anterior; o S-1210 tenta reportar pagamento em mês posterior à data de desligamento.
- **Correção**: não tem correção automática. Decidir com Ana se remove do scope ou se envia S-2299 pendente.
- **Ocorrência crônica**: Mar/2025 L3 CPF `36785342520` (mesmo recibo da Ana é stale, desligado).

### `buscar_recibo | Nenhum S-1210 com nrRecibo encontrado no ZIP`

- **Quando acontece**: chain walk do backend não acha o recibo ativo no ZIP local do mês.
- **Correção**: pedir XLSX da Ana com recibo ativo para esses CPFs → `recibo_override_por_cpf`.
- **Ocorrências conhecidas** (Maio L3, 24/04/2026): 22 CPFs, incluindo `86831908548`, `44979840873`, `36796398803`, `01658185573` etc.

### `nao_enviar_ana`

- **O que é**: não é erro do eSocial. É marcador manual (`UPDATE codigo_resposta='NAO_ENVIAR', status='nao_enviar_ana'`) para CPFs que a Ana instruiu a não enviar (sem S-1210 no ZIP original, fora de escopo, etc).
- **Quantidade**: 7 (Fev L3) + 3 (Mar L3) + 15 (Abr L3) = 25 CPFs.

---

## Pendências abertas

- [ ] **Maio L1** — reenviar 1.438 CPFs após popular `s1210_operadoras` (INC-2026-04-23).
- [ ] **Maio L3** — 30 CPFs com erro: 8 rejeição 401 + 22 sem recibo no ZIP. Pedir planilha Ana.
- [ ] **Junho L1** — reenviar 46 CPFs residuais código 8.
- [ ] **Junho L3** — scope 1.423 pronto, ainda não enviado.
- [ ] **Maio L2** — scope zerado; reingestar XLSX original se necessário.
- [ ] **Mar L3 CPF `36785342520`** — aguarda decisão Ana (desligado).
- [ ] **Abr L3 CPF `82472718500`** — aguarda recibo ativo Ana.
- [ ] **Mar L3 CPF `04171765897`** — fluxo de inclusão S-1210 (separado).
- [ ] **Decisão 1.297 CPFs Maio** (L1 vs L3) — ver INC-2026-04-24.
- [ ] **Lotes 1 e 2 dos meses Fev/Mar/Abr/Jul** — reprocessar ~3.800 erros residuais (maioria também código 8 provavelmente).

---

## Como consultar o estado

Sempre rodar com `DISTINCT ON (cpf) ORDER BY enviado_em DESC` — `COUNT(*)` inflado por retries não serve.

```python
# python-scripts/_check_estado_pos_incidente.py
# ou
# python-scripts/_check_lote3_distinct.py
```

## Regras de ouro

1. **NUNCA** rodar `/enviar-lote-cpfs` sem antes checar `s1210_operadoras` do mês.
2. **NUNCA** `DELETE FROM s1210_cpf_scope` sem filtrar `lote_num`.
3. Sempre que aparecer código 8 em massa, a hipótese #1 é operadoras vazias.
4. Qualquer novo incidente entra neste arquivo com ID `INC-YYYY-MM-DD-<slug>`.
