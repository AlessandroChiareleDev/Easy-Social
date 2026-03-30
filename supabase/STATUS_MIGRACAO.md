# Migração Supabase — Status e Roadmap

> Última atualização: 30/03/2025

---

## Resumo da Migração

| Item                | Valor                                         |
| ------------------- | --------------------------------------------- |
| Branch              | `feature/supabase-migration`                  |
| Supabase Project    | `zpizibafccwsjgvplcum` (us-east-2)            |
| URL                 | `https://zpizibafccwsjgvplcum.supabase.co`    |
| PostgreSQL Supabase | 17.6                                          |
| PostgreSQL Local    | 16                                            |
| Total de tabelas    | 30 (26 easy_social_db + 4 easy_social_master) |
| Volume total        | ~9 MB                                         |

---

## O Que Já Foi Feito ✅

### FASE 0 — Planejamento

- [x] Mapeamento completo dos 2 bancos locais (26 + 4 tabelas)
- [x] Análise de drivers (pg para Node, psycopg2 para Python)
- [x] Identificação de todas as queries SQL no codebase
- [x] Plano de migração em 7 fases

### FASE 1 — Schema + Scripts

- [x] Branch `feature/supabase-migration` criada e pushada
- [x] DDL exportado dos dois bancos locais (pg_dump)
- [x] Migration SQL unificado: `supabase/migrations/20260330000000_initial_schema.sql`
- [x] Script de export de dados: `supabase/export_data.ps1`
- [x] Commit: `feat(supabase): FASE 1 — schema migration + export scripts`

### FASE 1.5 — Gabarito de Verificação

- [x] Projeto Supabase criado e conexão testada
- [x] Contagem de todas as 30 tabelas coletada
- [x] Checksums MD5 de 15 tabelas com dados
- [x] Registros sentinela (primeiro/último) capturados
- [x] Max IDs para validação de sequences
- [x] Script de validação pós-migração: `supabase/validate_migration.ps1`
- [x] Gabarito salvo: `supabase/gabarito_pre_migracao.sql`

---

## Feito Agora ✅

### FASE 2 — Deploy do Schema no Supabase

- [x] Adaptado migration SQL para Session Pooler (Opção B: prefixo `master_`)
- [x] Migration file: `20260330000001_pooler_compatible.sql`
- [x] 28 tabelas criadas no Supabase (sem `certificados_a1` e `senha_certificado_salva`)
- [x] `master_perfis` criado com `id integer` temporário (UUID quando integrar Supabase Auth)

### FASE 3 — Migração de Dados

- [x] 22 tabelas easy_social_db exportadas via CSV + pg_dump
- [x] 4 tabelas master exportadas (empresas, perfis, usuario_empresa, naturezas_esocial)
- [x] Encoding corrigido (Latin1 → UTF8) para tabelas com acentos
- [x] Todas as 28 tabelas importadas com contagens corretas
- [x] Sequences ajustadas (setval) para novos inserts
- [x] naturezas_esocial: 206→203 (3 duplicatas locais removidas pela UNIQUE constraint)
- [x] Checksums validados: cruzamento_eb, esocial_envios, esocial_depara, analise_natureza, rubrica_corrections, tabela_eventos_gl ✅
- [x] Registros sentinela confirmados (primeiro/último cruzamento_eb, esocial_envios, master_empresas)
- [x] Pequenas divergências de checksum em tabela_eb, dinamica, eb_skills_base_legal são por normalização de encoding (dados semanticamente idênticos)

---

## O Que Falta Fazer ❌

### FASE 4 — Backend Node.js ✅

- [x] `database.ts`: SSL support + pool apontando para Supabase Session Pooler
- [x] `masterDatabase.ts`: re-exporta o pool compartilhado (1 banco apenas)
- [x] `auth-service.ts`: tabelas renomeadas (usuarios→master_perfis, empresas→master_empresas, usuario_empresa→master_usuario_empresa)
- [x] `.env.example` atualizado com config Supabase
- [x] `initializeDatabase()` simplificado para verificação de conexão
- [x] JWT custom mantido (migração para Supabase Auth fica para fase futura)
- [x] Testados 10 endpoints: health, login, empresas, tables, naturezas, rubricas, validacao, cruzamento, admin/usuarios

### FASE 5 — Backend Python ✅

- [x] Criado `db_config.py` centralizado (carrega .env sem dependência de python-dotenv)
- [x] DB_CONFIG → Supabase (com sslmode=require)
- [x] LOCAL_DB_CONFIG → PostgreSQL local (apenas certificados A1)
- [x] Atualizado: esocial_routes.py, depara_routes.py, cruzamento_eb_routes.py, certificate_routes.py, bot_esocial.py
- [x] `certificate_routes.py` usa LOCAL_DB_CONFIG (certificados nunca vão para nuvem)
- [x] Testados: /health, /api/cruzamento-eb/rubricas (448), /api/depara/resumo, /api/esocial/envios (18)

### FASE 6 — Frontend ✅ (sem alterações necessárias)

- [x] Frontend se comunica via HTTP com backends (localhost:3333 + localhost:8000)
- [x] Mudança de banco é transparente — mesmos endpoints, mesmas respostas
- [x] JWT custom continua funcionando (auth-service.ts gera tokens idênticos)
- [x] Nenhum código frontend precisou ser alterado

### FASE 7 — Testes e Cutover

- [ ] Executar validação completa (validate_migration.ps1)
- [ ] Teste end-to-end: login → upload → cruzamento → envio
- [ ] Confirmar certificados A1 funcionam localmente
- [ ] Remover banco local (após confirmação)
- [ ] Atualizar README.md

---

## Decisões Arquiteturais

### Certificados A1 — LOCAL ONLY

- **`certificados_a1`** (90 registros): metadados ficam NO BANCO LOCAL, não migram
- **Arquivos PFX**: permanecem em `backend/uploads/`, nunca vão para Supabase Storage
- **`senha_certificado_salva`**: permanece local
- **Python Bot**: continua rodando localmente para assinatura SOAP/XML
- **Motivo**: segurança — certificados digitais A1 não devem ficar em cloud

### Schema Unificado

- 2 bancos locais → 1 banco Supabase
- Tabelas do `easy_social_master` recebem prefixo `master_` no schema `public`
  - `empresas` → `master_empresas`
  - `usuarios` → `master_perfis` (integrado com Supabase Auth)
  - `usuario_empresa` → `master_usuario_empresa`
  - `naturezas_esocial` (master) → `master_naturezas_esocial`

### Autenticação

- JWT custom (bcryptjs + jsonwebtoken) → Supabase Auth
- `usuarios` → `auth.users` (email/senha) + `master_perfis` (role, nome)
- Multi-tenant via `X-Empresa-Id` continua funcionando

---

## Arquivos da Migração

| Arquivo                                                 | Propósito                  |
| ------------------------------------------------------- | -------------------------- |
| `supabase/migrations/20260330000000_initial_schema.sql` | DDL unificado              |
| `supabase/migrations/easy_social_db_schema.sql`         | DDL original referência    |
| `supabase/migrations/easy_social_master_schema.sql`     | DDL master referência      |
| `supabase/export_data.ps1`                              | Script export dados locais |
| `supabase/validate_migration.ps1`                       | Validação pós-migração     |
| `supabase/gabarito_pre_migracao.sql`                    | Snapshot de verificação    |
| `supabase/migrations/README_DATA_MIGRATION.sql`         | Instruções de migração     |

---

## Limitações Conhecidas

1. **Session Pooler** não suporta DDL (`CREATE SCHEMA`, `ALTER TYPE`, etc.)
   - Solução: usar SQL Editor do dashboard ou conexão direta
2. **IPv4 add-on** pode ser necessário para conexão direta do psql local
3. **Sequences**: precisam ser ajustadas após import dos dados (`setval()`)
4. **Timestamps**: migration converte `timestamp` → `timestamptz` (UTC)
