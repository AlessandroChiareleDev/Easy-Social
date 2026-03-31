# ESTADO PÓS-MERGE — O que acontece com o sistema

> **Pergunta**: Após o merge, o sistema funciona? Qual versão de banco usa?

---

## RESPOSTA CURTA

**Após o merge, o sistema NÃO funciona automaticamente.** Precisa de ~30 min de ajuste fino no `.env` e possivelmente renomear 4 tabelas no banco local.

---

## ESTADO DETALHADO

### Situação imediata pós-merge (antes de qualquer ajuste):

```
┌─────────────────────────────────────────────────────────┐
│                    PÓS-MERGE                            │
│                                                         │
│  Backend (Node.js):                                     │
│  ├── database.ts     → Versão SUPABASE (lê DB_SSL)     │
│  ├── masterDatabase.ts → Re-export do pool              │
│  └── auth-service.ts → Queries com master_*             │
│       ⚠️ QUEBRA se banco local não tem tabelas master_* │
│                                                         │
│  Python:                                                │
│  ├── db_config.py    → NOVO (lê env, dual config)      │
│  ├── esocial_routes  → Importa de db_config             │
│  ├── depara_routes   → Importa de db_config             │
│  ├── cruzamento_eb   → Importa de db_config             │
│  └── bot_esocial     → Importa de db_config             │
│       ⚠️ QUEBRA se DB_HOST env aponta pra Supabase      │
│          mas quer usar local                             │
│                                                         │
│  Frontend:                                              │
│  ├── api.ts centralizado ✅ (funciona)                  │
│  ├── Branding "Easy e-Social" ✅ (funciona)             │
│  └── CORS regex ✅ (funciona)                           │
│                                                         │
│  Banco de dados:                                        │
│  ├── PostgreSQL LOCAL → Rodando ✅                      │
│  │   └── Tabelas: usuarios, empresas, etc. (nomes      │
│  │       ANTIGOS — auth-service espera master_*)        │
│  └── Supabase CLOUD → Dados desatualizados ⚠️          │
└─────────────────────────────────────────────────────────┘
```

### O que precisa ser ajustado para funcionar LOCAL:

| Item                              | Ação                                          | Tempo  |
| --------------------------------- | --------------------------------------------- | ------ |
| `.env` backend                    | Garantir `DB_HOST=localhost`, `DB_SSL=false`  | 2 min  |
| `.env` Python (ou `db_config.py`) | Garantir que `DB_CONFIG` aponta pra localhost | 5 min  |
| Tabelas no banco local            | Renomear 4 tabelas (ver abaixo)               | 10 min |
| Coluna `nr_recibo`                | Verificar se ALTER TABLE dinâmico roda        | 2 min  |

### Renomeação de tabelas necessária:

```sql
-- No banco easy_social_master (ou easy_social_db dependendo da unificação):
ALTER TABLE usuarios RENAME TO master_perfis;
ALTER TABLE empresas RENAME TO master_empresas;
ALTER TABLE usuario_empresa RENAME TO master_usuario_empresa;

-- Se naturezas_esocial existir no master, também:
ALTER TABLE naturezas_esocial RENAME TO master_naturezas_esocial;
-- (mas naturezas_esocial também existe em easy_social_db, esse NÃO renomeia)
```

---

## QUAL BANCO O SISTEMA USA APÓS O MERGE?

### Cenário A: Sem ajuste nenhum

```
Backend Node.js → TENTA conectar segundo .env
                   Se .env tem localhost → LOCAL ✅
                   Se .env tem supabase → CLOUD (dados velhos) ⚠️

Python API     → TENTA ler db_config.py
                   DB_CONFIG → Depende das env vars
                   LOCAL_DB_CONFIG → Sempre local ✅

Certificados A1 → SEMPRE LOCAL ✅ (hardcoded em certificate_routes.py)
```

### Cenário B: Configurado corretamente para LOCAL (o que queremos)

```
┌──────────────────────────────────────────────┐
│  SISTEMA FUNCIONANDO LOCAL (pós-ajuste)      │
│                                              │
│  Backend Node.js ──→ PostgreSQL LOCAL        │
│    └── easy_social_db (porta 5432)           │
│    └── Tabelas: master_perfis,               │
│        master_empresas, etc. (renomeadas)    │
│                                              │
│  Python API ──→ PostgreSQL LOCAL             │
│    └── easy_social_db (porta 5432)           │
│    └── Mesmas tabelas                        │
│                                              │
│  Certificados A1 ──→ PostgreSQL LOCAL        │
│    └── easy_social_db (porta 5432)           │
│    └── certificados_a1, senha_cert_salva     │
│                                              │
│  Supabase ──→ NÃO USADO (desligado via env) │
│                                              │
│  Frontend ──→ localhost:5173                  │
│    └── API: localhost:3333                    │
│    └── Python: localhost:8000                 │
└──────────────────────────────────────────────┘
```

### Cenário C: Configurado para SUPABASE (futuro)

```
┌──────────────────────────────────────────────┐
│  SISTEMA FUNCIONANDO SUPABASE (futuro)       │
│                                              │
│  Backend Node.js ──→ Supabase CLOUD          │
│    └── aws-1-us-east-2.pooler.supabase.com   │
│    └── DB: postgres, SSL: true               │
│    └── Tabelas: master_*, públicas           │
│                                              │
│  Python API ──→ Supabase CLOUD               │
│    └── Mesma conexão                         │
│                                              │
│  Certificados A1 ──→ PostgreSQL LOCAL ⬅️     │
│    └── SEMPRE LOCAL, não muda nunca          │
│    └── PostgreSQL local TEM que continuar    │
│        rodando (só pra certs)                │
│                                              │
│  Frontend ──→ localhost:5173 ou tunnel        │
│    └── API: localhost:3333 ou tunnel          │
│    └── Python: localhost:8000 ou tunnel       │
└──────────────────────────────────────────────┘
```

---

## PROBLEMA DO "2 BANCOS DE DADOS"

**Mesmo no modo Supabase, o PostgreSQL local não pode ser desligado:**

```
Supabase (cloud)          PostgreSQL Local
├── master_perfis         ├── certificados_a1  ← OBRIGATÓRIO
├── master_empresas       └── senha_certificado_salva
├── esocial_envios
├── esocial_depara
├── cruzamento_eb
├── ... (28 tabelas)
└── uploads
```

O sistema precisa manter **2 conexões**:

1. `DB_CONFIG` → Supabase (dados do sistema)
2. `LOCAL_DB_CONFIG` → PostgreSQL local (apenas certificados A1)

Isso já está implementado no branch supabase via `db_config.py`.

---

## RESUMO VISUAL — SWITCH DE MODO

```
.env do backend:
┌────────────────────────────────────┐
│ # MODO LOCAL (default pós-merge)   │
│ DB_HOST=localhost                   │
│ DB_PORT=5432                       │
│ DB_NAME=easy_social_db             │
│ DB_USER=easy_social_user           │
│ DB_PASSWORD=sua_senha_segura       │
│ DB_SSL=false                       │
│                                    │
│ # MODO SUPABASE (trocar para):    │
│ # DB_HOST=aws-1-us-east-2.pooler  │
│ #         .supabase.com            │
│ # DB_PORT=5432                     │
│ # DB_NAME=postgres                 │
│ # DB_USER=postgres.zpizibafccwsjg  │
│ #         vplcum                   │
│ # DB_PASSWORD=6.18.13.1.8Supa     │
│ # DB_SSL=true                      │
└────────────────────────────────────┘

Trocar de LOCAL → SUPABASE = descomentar 6 linhas.
Trocar de SUPABASE → LOCAL = comentar de volta.
Restart backend + Python. Pronto.
```

---

## FUNCIONALIDADES — O QUE FUNCIONA E O QUE NÃO

### Logo após o merge (modo LOCAL, com ajustes):

| Funcionalidade           | Status | Nota                                  |
| ------------------------ | ------ | ------------------------------------- |
| Login/Auth               | ✅     | Após renomear tabelas para master\_\* |
| Upload planilhas         | ✅     | Sem alteração                         |
| Análise naturezas        | ✅     | Sem alteração                         |
| Cruzamento               | ✅     | Sem alteração                         |
| De-Para eSocial          | ✅     | Após ajustar db_config.py para local  |
| EB Skills Cruzamento     | ✅     | Após ajustar db_config.py para local  |
| Envio S-1010             | ✅     | Após ajustar db_config.py para local  |
| Consulta recibos         | ✅     | nr_recibo + XPath fix mantidos        |
| Certificado A1           | ✅     | Sem alteração (sempre local)          |
| Branding "Easy e-Social" | ✅     | Sem alteração                         |
| API centralizada         | ✅     | Sem alteração                         |
| CORS tunnels             | ✅     | Sem alteração (regex)                 |

### Logo após o merge (modo SUPABASE, SEM RE-MIGRAÇÃO):

| Funcionalidade   | Status | Nota                                                        |
| ---------------- | ------ | ----------------------------------------------------------- |
| Login/Auth       | ⚠️     | Funciona mas dados podem estar velhos                       |
| Upload planilhas | ⚠️     | Upload novo vai pro Supabase OK, dados antigos não estão lá |
| Envio S-1010     | ❌     | Dados de envio no Supabase estão OLD, sem nr_recibo         |
| Consulta recibos | ❌     | Coluna nr_recibo não existe no Supabase                     |
| Certificado A1   | ✅     | Sempre local                                                |
| De-Para          | ⚠️     | Dados desatualizados no Supabase                            |

**Conclusão: Para usar modo Supabase, PRECISA re-migrar dados. Isso é PASSO 2 (depois do merge funcionar local).**

---

## TIMELINE COMPLETA

```
HOJE À NOITE:
  1. Commitar trabalho pendente no main         (15 min)
  2. Merge da branch supabase                    (10 min)
  3. Ajustar .env para local                     (5 min)
  4. Renomear 4 tabelas no banco local           (10 min)
  5. Testar sistema local (MERGE_TESTES.md)      (30 min)

  → Sistema funciona LOCAL. Supabase desligado.
  → Pronto para continuar desenvolvendo features.

DEPOIS (quando decidir ir pro Supabase):
  6. Re-exportar dados do local                  (30 min)
  7. Re-importar no Supabase + add nr_recibo     (1 hora)
  8. Trocar .env → Supabase                      (2 min)
  9. Testar end-to-end com Supabase              (2-4 horas)
  10. Cutover definitivo                         (5 min)
```

---

_Documento de planejamento — nenhum arquivo de código alterado._
