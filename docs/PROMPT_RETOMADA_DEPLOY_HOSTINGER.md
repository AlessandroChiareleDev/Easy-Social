# Prompt para retomar chat de deploy na Hostinger

Cole isso no chat antigo que cuidava do deploy na Hostinger:

---

Fala, faz tempo que não falamos. Desde aquela época do deploy a gente evoluiu muito o sistema. Vou te atualizar com o estado atual de tudo e depois a gente retoma o deploy — quero usar uma VPS da Hostinger.

## O que é o sistema

Easy e-Social — sistema web pra corrigir rubricas de folha de pagamento no eSocial. Cliente é a APPA (porto de Paranaguá), ~20 mil funcionários. O sistema importa planilhas DIRF, cruza com tabelas do eSocial, detecta divergências nas naturezas/incidências das rubricas e manda correções direto pro eSocial via webservice SOAP com certificado digital A1.

## Stack atual (3 serviços + banco)

### 1. Frontend — Vue 3 + Vite (porta 5173)

- Vue 3.5, Vue Router 5, Pinia 3, Tailwind CSS 4, TypeScript
- 16 telas: Login, Dashboard, Upload de DIRF, Cruzamento de tabelas, Validador de naturezas, De-Para de campos, Bot eSocial, Explorador de eventos, Pipeline de correção, Audit trail, etc.
- Componentes: BrainNav (navegação inteligente), CorrectionWizard, DivergenceViewer
- Node >=20.19.0 || >=22.12.0
- Build: `npm run build` (vue-tsc + vite build)

### 2. Backend Node — Express 5 + TypeScript (porta 3333)

- Express 5.2.1, PostgreSQL (pg), Socket.IO, JWT auth, Multer (upload), xlsx parser
- Responsável por: autenticação multi-tenant, upload de planilhas, parsing DIRF, validação de rubricas, consulta de tabelas
- Build: `npm run build` (tsc) → `npm start` (node dist/app.js)
- Multi-user: admin/admin123, Ana/123321, Lobo/180306

### 3. API Python — FastAPI + Uvicorn (porta 8000)

- FastAPI 0.135.2, SQLAlchemy 2.0, psycopg2, Selenium, Pandas, lxml
- O coração do eSocial — faz tudo de comunicação com o governo:
  - Gerenciamento de certificado digital A1 (upload, leitura, assinatura XML)
  - Geração de XML dos eventos: S-1010, S-1200, S-1210, S-1298, S-1299, S-3000
  - Assinatura XML com xmlsec1
  - Construção SOAP e envio ao webservice eSocial
  - Pipeline de correção em 8 passos (reabre folha → retifica → fecha)
  - Pipeline de recovery multi-período
  - Parser de payloads XML (S-1200/S-1210)
  - Audit trail com snapshots pré/pós correção
- O módulo esocial/ tem 21 arquivos Python
- Dependencies: requirements.txt (fastapi, uvicorn, psycopg2-binary, sqlalchemy, selenium, pandas, anthropic, openai, python-dotenv, etc.)

### 4. Banco de dados — PostgreSQL 16

- **Produção (Supabase cloud):** banco principal com todas as tabelas de rubricas, análises, cruzamentos, etc.
- **Local:** usado apenas pra certificados A1
- Configuração via .env: DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD, DB_SSL
- Tabelas principais: analise_natureza (455 rows), tabela_eventos_gl (1145), tabela_eb (1224), dinamica (276), correcoes_staging, auditoria_naturezas

## Estrutura do repositório

```
Easy-Social/
├── frontend/          # Vue 3 + Vite + Tailwind
│   ├── src/views/     # 16 páginas
│   ├── src/components/
│   ├── src/stores/    # Pinia
│   └── public/
├── backend/           # Node + Express 5 + TypeScript
│   └── src/
│       ├── controllers/
│       ├── routes/
│       ├── services/
│       └── config/
├── python-scripts/    # FastAPI + módulo eSocial
│   ├── bot_api.py     # Entry point FastAPI
│   ├── db_config.py   # Config banco (Supabase + local)
│   ├── esocial/       # 21 arquivos (XML, SOAP, pipeline, etc.)
│   ├── certificados/  # Certificados A1
│   └── requirements.txt
├── supabase/          # Scripts de migração e export
└── docs/              # Documentação
```

## Estado atual da produção

- 11 rubricas S-1010 já corrigidas no eSocial de produção
- 1 CPF piloto (081.325.889-83) passou pelo pipeline completo de 8 passos — OK
- ~150 rubricas S-1010 ainda pendentes de correção
- ~20.000 CPFs para processar depois que o piloto for validado
- Estamos pausados esperando dia 8 de abril pra baixar o S-5002 (totalizador IRRF) e confirmar que a correção do piloto funcionou

## O que preciso de você agora

Vamos retomar o deploy. Quero usar uma **VPS da Hostinger** (não hosting compartilhado). Preciso rodar os 3 serviços (frontend porta 5173, backend Node porta 3333, API Python porta 8000) + o banco PostgreSQL local (pra certificados, o principal fica no Supabase cloud).

O frontend em produção precisa de build estático servido por Nginx ou similar. O backend Node e a API Python rodam como processos (PM2 ou systemd). Preciso de HTTPS com domínio.

Me ajuda a configurar essa VPS do zero?

---
