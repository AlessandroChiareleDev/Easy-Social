# Easy e-Social

### Developed By Xandao

Sistema focado em eSocial e suas tabelas. Recebe o arquivo **Relatório DIRF.xlsx** (bíblia do sistema), divide em 6 tabelas normalizadas e disponibiliza para processamento, validação e integração com o portal eSocial.

## Stack

| Camada   | Tecnologia                               |
| -------- | ---------------------------------------- |
| Frontend | Vue 3 + TypeScript + Tailwind CSS (Vite) |
| Backend  | Node.js + Express + TypeScript           |
| Scripts  | Python + FastAPI + Pandas                |
| Banco    | PostgreSQL 16                            |

## Estrutura

```
easy-esocial/
├── backend/       → API Node.js/TS (porta 3000)
├── frontend/      → Vue 3 SPA (porta 5173)
├── python-scripts/ → FastAPI + processamento DIRF (porta 8000)
└── .env           → Variáveis de ambiente
```

## 6 Tabelas do DIRF

1. ANALISE NATUREZA
2. Dinamica
3. Base Ficha Financeira 2025
4. Planilha 1
5. Tabela Eventos Gl
6. Tabela EB

## Início Rápido

```bash
# Backend
cd backend && npm install && npm run dev

# Frontend
cd frontend && npm install && npm run dev

# Python
cd python-scripts && .\venv\Scripts\Activate.ps1 && pip install -r requirements.txt
python src/main.py
```
