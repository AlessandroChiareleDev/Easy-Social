# Incidente PC2 — 24/04/2026 — Scope L1 Maio/Junho deletado por bug em ingest_lote3_*.py

> **Para PC1 revisar.** PC2 cometeu erro destrutivo em `s1210_cpf_scope`. Tudo foi
> reconstruído a partir de `s1210_cpf_envios`. Status de envios no eSocial **NÃO**
> foi tocado em momento algum.

---

## TL;DR

- **Bug:** `ingest_lote3_maio.py` (e cópia `ingest_lote3_junho.py`) faziam
  `DELETE FROM s1210_cpf_scope WHERE empresa_id=%s AND per_apur=%s` **SEM**
  filtrar `lote_num` antes de inserir o L3.
- **Estrago:** apagou L1/L2/L4 de Maio (ontem 23/04) e L1 de Junho (hoje 24/04).
- **Reconstrução:** `INSERT … FROM (SELECT DISTINCT cpf FROM s1210_cpf_envios …)`
  recriou o scope a partir dos envios reais.
- **Bug corrigido nos 2 scripts:** DELETE agora filtra `AND lote_num=%s`.
- **Resultado pós-fix:** todos CPFs com envio têm scope (cobertura 100%).

---

## Linha do tempo

| Data        | O que aconteceu |
|-------------|-----------------|
| 23/04/2026  | PC2 rodou `ingest_lote3_maio.py` → apagou scope L1/L2/L4 Maio, deixou só 1319 L3 |
| 24/04/2026  | PC2 copiou script pra `ingest_lote3_junho.py` → mesmo bug → apagou 6827 L1 Junho |
| 24/04/2026  | User pegou: *"VC APAGOU LOTE 1 ?????"* |
| 24/04/2026  | PC2 reconstruiu Maio L1 (8724) e Junho L1 (6827) via `s1210_cpf_envios` |
| 24/04/2026  | PC2 corrigiu bug nos 2 scripts |

---

## Estado FINAL `s1210_cpf_scope` (empresa_id=1)

```
('2025-02', 1, 9471)
('2025-02', 2, 1390)
('2025-02', 3, 737)
('2025-02', 4, 2)
('2025-03', 1, 8164)
('2025-03', 2, 1395)
('2025-03', 3, 1624)
('2025-03', 4, 2)
('2025-04', 1, 7142)
('2025-04', 2, 1376)
('2025-04', 3, 1498)
('2025-05', 1, 8724)   ← reconstruído (era 0 após bug)
('2025-05', 3, 1319)   ← intacto (foi o que o ingest popou)
('2025-06', 1, 6827)   ← reconstruído (era 0 após bug)
('2025-06', 3, 1423)   ← novo (popado hoje)
('2025-07', 1, 6559)
```

---

## Validação — cobertura 100%

Query: `SELECT COUNT(DISTINCT e.cpf) FROM s1210_cpf_envios e WHERE NOT EXISTS
(SELECT 1 FROM s1210_cpf_scope s WHERE s.cpf=e.cpf AND mesmo per_apur)`

| Período  | Lote | CPFs em envios sem scope |
|----------|------|--------------------------|
| 2025-05  | 1    | **0** |
| 2025-05  | 3    | **0** |
| 2025-06  | 1    | **0** |
| 2025-06  | 3    | **0** |

Todos CPFs que tiveram envio têm linha em scope.

---

## Status de envios eSocial — INALTERADO

Confirmado: as colunas `status`, `nr_recibo_novo`, `xml_resposta`, etc. de
`s1210_cpf_envios` **não foram tocadas em nenhum momento**.

```
('2025-05', 1, 'erro', 1438)
('2025-05', 1, 'ok',   8583)
('2025-05', 3, 'erro', 2306)
('2025-05', 3, 'ok',   2578)
('2025-06', 1, 'erro',   46)
('2025-06', 1, 'ok',   6781)
```

---

## Discrepância de números — L1 Maio: 8724 scope vs 10021 envios distintos

A diferença (1297 CPFs) é **esperada** e não é perda de dado:

- O constraint UNIQUE em `s1210_cpf_scope` é `(empresa_id, per_apur, cpf)` —
  um CPF só pode estar em **um** lote por mês.
- 1319 CPFs estão em scope como L3 Maio.
- Desses, ~1297 também tiveram envio como L1 historicamente (situação anterior
  ao split em lotes diferentes).
- Quando o INSERT de reconstrução do L1 rodou com `ON CONFLICT DO NOTHING`,
  esses 1297 foram bloqueados pelo constraint porque já estavam como L3.
- **Os envios L1 deles continuam em `s1210_cpf_envios` intactos** — só o
  cadastro de scope ficou apenas como L3.

Se PC1 considerar que esses 1297 deveriam aparecer como L1 (e não como L3) no
scope, é só rodar:

```sql
-- decisão de design: priorizar L1 pra esses CPFs
UPDATE s1210_cpf_scope
   SET lote_num = 1
 WHERE empresa_id=1 AND per_apur='2025-05' AND lote_num=3
   AND cpf IN (
     SELECT DISTINCT cpf FROM s1210_cpf_envios
     WHERE empresa_id=1 AND per_apur='2025-05' AND lote_num=1
   );
```
**(NÃO RODADO — aguardando decisão.)**

---

## L2 Maio — não foi possível restaurar

`s1210_cpf_envios` tem 0 envios L2 Maio → não há de onde reconstruir o scope.
Antes do bug, o scope tinha L2 Maio? Não sei — não tenho backup. Provavelmente
nunca teve (pelo padrão dos outros meses Fev/Mar/Abr não teve envio L2 também,
só scope cadastrado por XLSX). **Se PC1 souber qual era o XLSX original do L2
Maio, basta reingestar.**

---

## Bug e correção (diff conceitual)

**ANTES (bugado):**
```python
cur.execute(
    "DELETE FROM s1210_cpf_scope WHERE empresa_id=%s AND per_apur=%s",
    (EMPRESA_ID, PER_APUR),
)
```

**DEPOIS (corrigido):**
```python
cur.execute(
    "DELETE FROM s1210_cpf_scope WHERE empresa_id=%s AND per_apur=%s AND lote_num=%s",
    (EMPRESA_ID, PER_APUR, LOTE_ALVO),
)
```

Aplicado em:
- `python-scripts/ingest_lote3_maio.py`
- `python-scripts/ingest_lote3_junho.py`

---

## Comandos SQL executados na reconstrução (auditoria completa)

### Maio L1
```sql
INSERT INTO s1210_cpf_scope (xlsx_id, empresa_id, per_apur, cpf, lote_num, row_number, raw_row)
SELECT (SELECT MIN(id) FROM s1210_xlsx WHERE empresa_id=1 AND per_apur='2025-05'),
       1, '2025-05', cpf, 1, ROW_NUMBER() OVER (ORDER BY cpf), '{}'::jsonb
  FROM (SELECT DISTINCT cpf FROM s1210_cpf_envios
         WHERE empresa_id=1 AND per_apur='2025-05' AND lote_num=1) s
ON CONFLICT DO NOTHING;
-- Resultado: 8724 linhas inseridas
```

### Maio L2 e L4
Mesmo INSERT trocando `lote_num=2` e `lote_num=4` → 0 linhas (não havia envios).

### Junho L1
```sql
INSERT INTO s1210_cpf_scope (xlsx_id, empresa_id, per_apur, cpf, lote_num, row_number, raw_row)
SELECT 6, 1, '2025-06', cpf, 1, ROW_NUMBER() OVER (ORDER BY cpf), '{}'::jsonb
  FROM (SELECT DISTINCT cpf FROM s1210_cpf_envios
         WHERE empresa_id=1 AND per_apur='2025-06' AND lote_num=1) s
ON CONFLICT DO NOTHING;
-- Resultado: 6827 linhas inseridas
```

---

## O que PC1 precisa decidir

1. **L2 Maio:** reingestar XLSX original ou ignorar?
2. **1297 CPFs L1/L3 Maio:** deixar como L3 (estado atual) ou mover pra L1
   via UPDATE acima?
3. **Pode prosseguir Junho L3?** Scope = 1423 CPFs prontos, plan_saude do
   XLSX Ana confirmado, recibos S-1200 disponíveis (6781 OK).

---

## Aprendizados

- **NUNCA** fazer DELETE em scope sem filtro `lote_num`.
- **SEMPRE** validar antes/depois com `COUNT FROM scope GROUP BY lote_num`.
- Quando copiar script pra novo mês, **revisar TODAS as queries de mutação**,
  não só constantes/paths.
