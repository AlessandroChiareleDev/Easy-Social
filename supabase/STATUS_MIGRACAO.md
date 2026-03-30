# Migração Supabase — Status e Roadmap

> Última atualização: 30/03/2025

---

## Resumo da Migração

| Item | Valor |
|------|-------|
| Branch | `feature/supabase-migration` |
| Supabase Project | `zpizibafccwsjgvplcum` (us-east-2) |
| URL | `https://zpizibafccwsjgvplcum.supabase.co` |
| PostgreSQL Supabase | 17.6 |
| PostgreSQL Local | 16 |
| Total de tabelas | 30 (26 easy_social_db + 4 easy_social_master) |
| Volume total | ~9 MB |

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

## O Que Falta Fazer ❌

### FASE 2 — Deploy do Schema no Supabase
- [ ] **Adaptar migration SQL para Session Pooler** — O pooler não suporta `CREATE SCHEMA` nem `REFERENCES auth.users`. Opções:
  - **Opção A**: Rodar via SQL Editor no dashboard Supabase (recomendado)
  - **Opção B**: Usar prefixo `master_` no schema public ao invés de schema separado
- [ ] Criar tabelas no Supabase
- [ ] Configurar RLS (Row Level Security) básico

### FASE 3 — Migração de Dados
- [ ] Executar `export_data.ps1` para gerar CSVs/SQL
- [ ] Importar dados no Supabase (via `\copy` ou SQL Editor)
- [ ] Rodar `validate_migration.ps1` para confirmar integridade
- [ ] Validar checksums MD5 contra gabarito

### FASE 4 — Backend Node.js
- [ ] Instalar `@supabase/supabase-js` no backend
- [ ] Substituir `database.ts` → conexão Supabase
- [ ] Eliminar `masterDatabase.ts` (tudo em 1 banco agora)
- [ ] Migrar `auth-service.ts` → Supabase Auth
- [ ] Migrar `auth.ts` middleware → validação JWT Supabase
- [ ] Atualizar queries que referenciam schema master

### FASE 5 — Backend Python
- [ ] Atualizar `DB_CONFIG` em todos os 10+ scripts Python
- [ ] Instalar `supabase` Python SDK (ou manter psycopg2 com nova connection string)
- [ ] Testar bot_esocial.py com novo banco
- [ ] Testar bot_api.py endpoints

### FASE 6 — Frontend
- [ ] Instalar `@supabase/supabase-js` no frontend
- [ ] Migrar `stores/auth.ts` → Supabase Auth
- [ ] Atualizar env variables no Vite
- [ ] Remover JWT custom do frontend

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

| Arquivo | Propósito |
|---------|-----------|
| `supabase/migrations/20260330000000_initial_schema.sql` | DDL unificado |
| `supabase/migrations/easy_social_db_schema.sql` | DDL original referência |
| `supabase/migrations/easy_social_master_schema.sql` | DDL master referência |
| `supabase/export_data.ps1` | Script export dados locais |
| `supabase/validate_migration.ps1` | Validação pós-migração |
| `supabase/gabarito_pre_migracao.sql` | Snapshot de verificação |
| `supabase/migrations/README_DATA_MIGRATION.sql` | Instruções de migração |

---

## Limitações Conhecidas

1. **Session Pooler** não suporta DDL (`CREATE SCHEMA`, `ALTER TYPE`, etc.)
   - Solução: usar SQL Editor do dashboard ou conexão direta
2. **IPv4 add-on** pode ser necessário para conexão direta do psql local
3. **Sequences**: precisam ser ajustadas após import dos dados (`setval()`)
4. **Timestamps**: migration converte `timestamp` → `timestamptz` (UTC)
