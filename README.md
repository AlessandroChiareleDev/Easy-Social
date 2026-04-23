# Easy e-Social

---

## ⛔ AGENTE / DESENVOLVEDOR: MISSÃO ATIVA S-1210 APPA

**ANTES DE QUALQUER AÇÃO relacionada a S-1210, lotes, APPA, envio em massa dos 3 meses (fev/mar/abr 2025):**

👉 **LEIA:** [docs/MISSAO_S1210_APPA_21-04-2026/LEIA_PRIMEIRO.md](docs/MISSAO_S1210_APPA_21-04-2026/LEIA_PRIMEIRO.md)

Pasta contém:

- `LEIA_PRIMEIRO.md` — 7 regras inegociáveis
- `NORTE_S1210.md` — norte aprovado pelo usuário
- `RESOLUCAO_S1200_3_MESES.md` — bíblia (12 porcarias, missão real, transcrição da call, parser rules)
- `TAREFAS.md` — checklist da execução corrente

**Regra nº 1:** NUNCA usar `explorador_eventos` como fonte de escopo. Escopo vem do XLSX da Ana.

---

## Backup Operacional (Lote 1 Pre-envio)

Existe um backup operacional de estado 0 (pre-envio) separado por mes para o Lote 1.

- Documentacao do backup: [docs/backup_preenvio_lote1/README.md](docs/backup_preenvio_lote1/README.md)
- Pasta dos artefatos versionados: [docs/backup_preenvio_lote1](docs/backup_preenvio_lote1)

Esse backup serve para auditoria, rastreabilidade e rollback operacional antes de qualquer envio.

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
