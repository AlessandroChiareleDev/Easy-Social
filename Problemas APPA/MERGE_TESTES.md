# MERGE_TESTES.md — Testes Pós-Merge (Antes de Configurar Supabase)

> **Objetivo**: Verificar que TUDO funciona com banco LOCAL após o merge.
> **Contexto**: O merge traz código do branch Supabase. Precisamos confirmar que o sistema não quebrou rodando no banco local.
> **REGRA**: Esses testes são executados com `.env` apontando para PostgreSQL LOCAL.

---

## CHECKLIST PRÉ-TESTE

- [ ] Merge completado sem erros
- [ ] `.env` do backend aponta para `localhost` / `easy_social_db`
- [ ] `.env` do Python (se existir) aponta para `localhost`
- [ ] PostgreSQL local rodando (`easy_social_db` + `easy_social_master`)
- [ ] `npm install` no backend (caso package.json tenha mudado)
- [ ] `pip install` no Python (caso requirements.txt tenha mudado)

---

## BLOCO 1 — Backend Node.js Inicia

### Teste 1.1: Backend starta sem erro

```bash
cd backend
npm run dev
```

**Esperado**:

- Sem erros no console
- "Server running on port 3333" (ou similar)
- Conexão com banco OK

**O QUE PODE QUEBRAR**:

- `database.ts` mudou para leitura de SSL. Se o .env não tiver `DB_SSL=false`, pode tentar SSL no localhost e falhar.
- `masterDatabase.ts` agora re-exporta o pool principal. Se `database.ts` falhar, tudo falha.

### Teste 1.2: Backend conecta no banco

- Abrir `http://localhost:3333/api/health` (se existir)
- Ou verificar no console que não tem erro de conexão

**O QUE PODE QUEBRAR**:

- Se as tabelas foram renomeadas para `master_*` mas o banco local ainda tem os nomes antigos (e o código já usa `master_*`).

---

## BLOCO 2 — Login e Autenticação

### Teste 2.1: Login funciona

- Abrir `http://localhost:5173`
- Fazer login com usuário existente
- Verificar que entra no dashboard

**O QUE PODE QUEBRAR**:

- `auth-service.ts` agora faz queries em `master_perfis` ao invés de `usuarios`. Se a tabela local ainda se chama `usuarios`, vai dar `relation "master_perfis" does not exist`.
- **SOLUÇÃO**: Renomear tabelas locais OU adaptar auth-service.ts com fallback.

### Teste 2.2: Dados do usuário carregam

- Verificar que nome, email, role aparecem corretamente
- Verificar que lista de empresas aparece

**O QUE PODE QUEBRAR**:

- Query em `master_empresas` ao invés de `empresas`
- Query em `master_usuario_empresa` ao invés de `usuario_empresa`

---

## BLOCO 3 — Python API Inicia

### Teste 3.1: Python API starta sem erro

```bash
cd python-scripts
.\venv\Scripts\python.exe bot_api.py
```

**Esperado**:

- "Uvicorn running on http://0.0.0.0:8000"
- Sem ImportError

**O QUE PODE QUEBRAR**:

- `db_config.py` é um arquivo NOVO do branch Supabase. Se ele lê variáveis de ambiente para Supabase que não existem no .env, pode dar erro.
- Imports em `esocial_routes.py`, `depara_routes.py`, `cruzamento_eb_routes.py` mudaram de hardcoded pra `from db_config import DB_CONFIG`. Se `db_config.py` falhar, TODOS falham.

### Teste 3.2: Health check da Python API

- `GET http://localhost:8000/` — deve retornar status OK

---

## BLOCO 4 — Features Críticas do eSocial

### Teste 4.1: Carregar rubricas (De-Para)

- Navegar para tela De-Para
- Verificar que lista de rubricas carrega

**O QUE PODE QUEBRAR**:

- `depara_routes.py` usa `DB_CONFIG` do `db_config.py`. Se DB_CONFIG aponta pra Supabase mas queremos local, vai falhar.

### Teste 4.2: Carregar cruzamento EB

- Navegar para tela EB Skills Cruzamento
- Verificar que 448 rubricas carregam

**O QUE PODE QUEBRAR**:

- `cruzamento_eb_routes.py` usa `DB_CONFIG` — mesmo problema.

### Teste 4.3: Carregar envios eSocial

- Navegar para tela eSocial
- Verificar que lista de envios aparece
- Verificar que `nr_recibo` aparece nos envios que têm

**O QUE PODE QUEBRAR**:

- `esocial_routes.py` usa `DB_CONFIG` + `LOCAL_DB_CONFIG`
- Se a coluna `nr_recibo` não existir no banco local, a query de listar envios pode falhar (depende de se o ALTER TABLE dinâmico roda)

### Teste 4.4: Certificado A1 carrega

- Navegar para tela eSocial
- Verificar que certificado A1 aparece como "ativo"
- Verificar data de validade

**O QUE PODE QUEBRAR**:

- `certificate_routes.py` usa `LOCAL_DB_CONFIG`. Se `db_config.py` não conseguir ler config local, certs não carregam.
- **ESTE É O TESTE MAIS IMPORTANTE** — se certs não funcionam, não envia nada pro eSocial.

---

## BLOCO 5 — Frontend Geral

### Teste 5.1: Frontend starta sem erro

```bash
cd frontend
npm run dev
```

**Esperado**: Vite inicia em `http://localhost:5173`

### Teste 5.2: Navegação entre telas

- Dashboard ✓
- Painel ✓
- De-Para ✓
- EB Skills Cruzamento ✓
- eSocial ✓
- Cruzamento ✓
- Empresas ✓
- Login/Logout ✓

### Teste 5.3: Branding "Easy e-Social"

- Verificar que logo/título mostra "Easy e-Social" (não "Easy Social")
- Verificar em: header, login, dashboard, título do browser

### Teste 5.4: API centralizada funciona

- Verificar que `frontend/src/lib/api.ts` existe e é importado
- Verificar que requests vão para o endereço correto (localhost em dev)
- DevTools → Network → verificar que APIs batem em `localhost:3333` e `localhost:8000`

---

## BLOCO 6 — Upload e Cruzamento

### Teste 6.1: Upload de planilha

- Fazer upload de uma planilha de teste
- Verificar que dados aparecem em TableViewer

### Teste 6.2: Cruzamento funciona

- Executar cruzamento com dados existentes
- Verificar que resultados aparecem

---

## BLOCO 7 — Testes de Banco de Dados

### Teste 7.1: Tabelas existem

```sql
-- Executar no psql conectado em easy_social_db
\dt
```

**Esperado**: Todas as tabelas existem (com ou sem prefixo master\_ dependendo se renomeamos)

### Teste 7.2: Coluna nr_recibo existe

```sql
SELECT column_name FROM information_schema.columns
WHERE table_name='esocial_envios' AND column_name='nr_recibo';
```

**Esperado**: Retorna 1 linha. Se não retornar, o ALTER TABLE dinâmico precisa rodar.

### Teste 7.3: Dados intactos

```sql
SELECT count(*) FROM esocial_envios;       -- Esperado: >= 18
SELECT count(*) FROM esocial_depara;       -- Esperado: >= 2381
SELECT count(*) FROM cruzamento_eb;         -- Esperado: >= 448
SELECT count(*) FROM certificados_a1;       -- Esperado: >= 1
```

---

## RESUMO — ORDEM DOS TESTES

```
1. Backend Node.js starta          → Se falhar: problema em database.ts ou .env
2. Login funciona                   → Se falhar: tabelas renomeadas sem banco atualizado
3. Python API starta                → Se falhar: db_config.py com config errada
4. Certificado A1 carrega           → Se falhar: LOCAL_DB_CONFIG errado
5. Rubricas/De-Para carregam        → Se falhar: DB_CONFIG apontando pra Supabase
6. Envios eSocial + nr_recibo       → Se falhar: coluna nr_recibo faltando
7. Frontend navegação completa      → Se falhar: imports quebrados pós-merge
8. Upload + cruzamento              → Se falhar: queries incompatíveis
```

---

## CENÁRIO "DEU MERDA" — ROLLBACK

Se algo **realmente** quebrar e não conseguir resolver rápido:

```bash
# Desfazer o merge (se ainda não commitou o merge)
git merge --abort

# Se já commitou o merge
git reset --hard dc7214d
# Isso volta pro estado anterior (commit atual do main)
```

⚠️ **IMPORTANTE**: O `git reset --hard` descarta tudo. Por isso é OBRIGATÓRIO commitar o trabalho pendente ANTES do merge.

---

_Documento de planejamento — nenhum arquivo de código alterado._
