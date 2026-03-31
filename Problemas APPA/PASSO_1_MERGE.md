# PASSO 1 — Merge da Branch Supabase no Main

> **Objetivo**: Trazer TODO o trabalho de `feature/supabase-migration` para `main`, mantendo o sistema funcionando com banco LOCAL.
> **Regra**: Após o merge, o sistema roda LOCAL exatamente como hoje. Supabase fica "desligado" via .env.

---

## 1. ESTADO ATUAL DAS BRANCHES

### Branch `main` (3 commits + 39 arquivos não commitados)

```
dc7214d  fix: tunnel URLs atualizadas + .env corrigido para local DB
e31948b  1
9764a3f  feat: Easy Social - sistema completo
```

**+ 39 arquivos modificados/novos NÃO COMMITADOS** (branding, api.ts, CORS, nr_recibo, etc.)

### Branch `feature/supabase-migration` (7 commits extras)

```
43cb7a9  fix: _load_cert_ativo usa LOCAL_DB_CONFIG + tunnel URLs
36c461d  feat(supabase): FASE 5+6 — Python API migrated
f9b796e  feat(supabase): FASE 4 — backend Node.js migrated
fc44b86  feat(supabase): FASE 2+3 — schema deployed + data migrated
83a1a78  feat(supabase): FASE 1.5 — gabarito, validação e status
c100896  feat(supabase): FASE 1 — schema migration + export scripts
67e8cdd  chore: iniciar migração para Supabase
```

### Ponto de divergência (fork)

```
e31948b  — "1" — é o último commit em comum
```

---

## 2. PRÉ-MERGE — Commitar trabalho pendente no main

**OBRIGATÓRIO fazer ANTES do merge.** Se não commitar, o merge pode sobrescrever as alterações não commitadas.

### Commit 1: "feat: branding Easy e-Social + centralized api.ts + CORS regex"

Arquivos (~30):

- Branding rename (26+ arquivos): frontend, backend, Python, docs
- `frontend/src/lib/api.ts` (NOVO) — centralized API URLs
- `frontend/.env.tunnel` (NOVO) — template de URLs de tunnel
- 10 views/components atualizados para usar `api.ts`
- `python-scripts/bot_api.py` — `allow_origin_regex` para CORS
- `frontend/index.html`, `App.vue`, `base.css`, `BrandLogo.vue`

### Commit 2: "feat: nr_recibo + XPath fix para consulta S-1010"

Arquivos (~2):

- `python-scripts/esocial/esocial_routes.py` — coluna nr_recibo, lógica de extração, endpoint de reconsulta batch
- `python-scripts/esocial/esocial_client.py` — XPath fix (`recibo/nrRecibo` ao invés de `processamento/nrRecibo`), retorno de `xml_resposta`

### Commit 3: "docs: pesquisas e análises APPA" (opcional, pode pular se preferir)

- `Problemas APPA/*.md` — documentação de pesquisa
- Recibos S-1010 em `recibos_s1010/`

---

## 3. CONFLITOS ESPERADOS NO MERGE

### Apenas 3 arquivos com conflito — TODOS triviais (só URLs de tunnel)

| Arquivo                              | O que `main` mudou                  | O que `supabase` mudou               | Resolução                                                                         |
| ------------------------------------ | ----------------------------------- | ------------------------------------ | --------------------------------------------------------------------------------- |
| `frontend/src/stores/auth.ts`        | URL tunnel: `article-latest-...`    | URL tunnel: `breath-conferences-...` | **DESCARTAR AMBOS** — vai usar `api.ts` centralizado (que elimina URLs hardcoded) |
| `frontend/src/views/ESocialView.vue` | URL tunnel: `remaining-instead-...` | URL tunnel: `landing-turning-...`    | **DESCARTAR AMBOS** — vai usar `api.ts` centralizado                              |
| `python-scripts/bot_api.py`          | URL tunnel: `premises-emotions-...` | URL tunnel: `distributor-timing-...` | **DESCARTAR AMBOS** — já temos `allow_origin_regex` que cobre qualquer tunnel     |

**Resumo: Os 3 conflitos são sobre URLs de tunnel que JÁ ESTÃO RESOLVIDOS de outra forma (api.ts centralizado + CORS regex). Basta descartar os dois lados e manter a versão nova.**

---

## 4. O QUE CADA BRANCH TEM QUE A OUTRA NÃO TEM

### Features que SÓ existem no `main` (não commitadas):

| Feature                  | Arquivos                               | Criticidade                                    |
| ------------------------ | -------------------------------------- | ---------------------------------------------- |
| Branding "Easy e-Social" | ~26 arquivos                           | Cosmético                                      |
| Centralized `api.ts`     | `frontend/src/lib/api.ts` + 10 imports | IMPORTANTE — elimina URLs hardcoded            |
| CORS regex               | `bot_api.py`                           | IMPORTANTE — tunnels funcionam sem editar URLs |
| `nr_recibo` column       | `esocial_routes.py`                    | CRÍTICO — coluna nova em esocial_envios        |
| XPath fix consulta       | `esocial_client.py`                    | CRÍTICO — sem isso recibos não são extraídos   |
| `xml_resposta` return    | `esocial_client.py`                    | IMPORTANTE — salva XML bruto do retorno        |
| Pesquisas APPA           | 5 MDs + recibos                        | Documentação                                   |

### Features que SÓ existem no `feature/supabase-migration`:

| Feature                      | Arquivos                                         | Criticidade                         |
| ---------------------------- | ------------------------------------------------ | ----------------------------------- |
| `db_config.py` (dual config) | `python-scripts/db_config.py` (NOVO)             | ESSENCIAL — config Supabase + Local |
| database.ts simplificado     | `backend/src/config/database.ts`                 | ESSENCIAL — Pool com SSL            |
| masterDatabase.ts unificado  | `backend/src/config/masterDatabase.ts`           | ESSENCIAL — re-export do pool       |
| auth-service.ts renomeado    | `backend/src/services/auth-service.ts`           | ESSENCIAL — tabelas master\_\*      |
| certificate_routes.py LOCAL  | `python-scripts/esocial/certificate_routes.py`   | ESSENCIAL — certs A1 local          |
| esocial_routes.py dual DB    | `python-scripts/esocial/esocial_routes.py`       | ESSENCIAL — Supabase + Local        |
| depara_routes.py             | `python-scripts/esocial/depara_routes.py`        | ESSENCIAL — usa DB_CONFIG           |
| cruzamento_eb_routes.py      | `python-scripts/esocial/cruzamento_eb_routes.py` | ESSENCIAL — usa DB_CONFIG           |
| bot_esocial.py               | `python-scripts/bot_esocial.py`                  | ESSENCIAL — usa DB_CONFIG           |
| Schema SQL Supabase          | `supabase/migrations/*.sql`                      | Referência                          |
| Scripts validação/export     | `supabase/*.ps1`                                 | Utilitário                          |
| .env.example atualizado      | `backend/.env.example`                           | Referência                          |
| .gitignore atualizado        | `.gitignore`                                     | Infra                               |

---

## 5. PLANO DE EXECUÇÃO DO MERGE

```
PASSO 1: Commitar todo trabalho pendente no main (2-3 commits)
         └── git add + git commit (organizados por feature)

PASSO 2: Merge feature/supabase-migration → main
         └── git merge feature/supabase-migration
         └── Resolver 3 conflitos triviais (URLs de tunnel)

PASSO 3: Pós-merge — adaptar código para funcionar nos 2 modos
         └── database.ts: ler DB_SSL do .env, se false → local, se true → Supabase
         └── Python db_config.py: já faz isso (DB_CONFIG vs LOCAL_DB_CONFIG)
         └── auth-service.ts: precisa lidar com nomes de tabela (master_* vs sem prefixo)
         └── OU: renomear tabelas locais para usar master_* também (mais limpo)

PASSO 4: Verificar que sistema funciona LOCAL com .env apontando pra local
         └── Ver MERGE_TESTES.md
```

---

## 6. QUESTÃO CRÍTICA — NOMES DE TABELA

O branch supabase renomeou tabelas:

```
LOCAL (main):              SUPABASE (branch):
usuarios           →      master_perfis
empresas           →      master_empresas
usuario_empresa    →      master_usuario_empresa
naturezas_esocial  →      master_naturezas_esocial (no schema master)
```

### Opção A: Renomear tabelas locais para master\_\* (RECOMENDADO)

- Executar ALTER TABLE RENAME no PostgreSQL local
- Prós: código unificado, sem IF/ELSE
- Contras: execução única, irreversível (mas trivial de reverter)

### Opção B: IF/ELSE no código baseado em variável de ambiente

- Prós: não mexe no banco local
- Contras: código bifurcado, manutenção dobrada, propenso a bug

### Opção C: Criar VIEWs no banco local com nomes master\_\*

- Prós: tabelas originais intactas, código unificado
- Contras: um pouco mais complexo que Opção A

**Recomendação: Opção A** — renomear as 4 tabelas locais. São 4 comandos SQL e pronto.

---

## 7. ESTIMATIVA DE TEMPO

| Etapa                              | Tempo estimado |
| ---------------------------------- | -------------- |
| Commitar trabalho pendente         | 15 min         |
| Merge + resolver conflitos         | 10 min         |
| Adaptar database.ts para dual mode | 30 min         |
| Renomear tabelas locais (Opção A)  | 10 min         |
| Adaptar auth-service.ts            | 15 min         |
| Testar sistema local               | 30 min         |
| **TOTAL**                          | **~2 horas**   |

---

## 8. RISCOS

| Risco                                      | Probabilidade              | Impacto | Mitigação                          |
| ------------------------------------------ | -------------------------- | ------- | ---------------------------------- |
| Conflito de merge inesperado               | Baixa                      | Baixo   | São só 3 conflitos triviais de URL |
| Trabalho não commitado perdido             | ALTA se não commitar antes | ALTO    | **OBRIGATÓRIO commitar antes**     |
| auth-service.ts quebra com nomes de tabela | Média                      | Alto    | Testar login imediatamente         |
| database.ts não conecta local              | Baixa                      | Alto    | Manter .env local como fallback    |
| esocial_routes.py conflito nr_recibo       | Média                      | Médio   | Merge manual cuidadoso             |

---

_Documento de planejamento — nenhum arquivo de código alterado._
