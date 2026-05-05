# Easy e-Social

---

## � PENDÊNCIA — SYNC RECIBOS jun/2025 L2 plansaude (2026-05-05)

**163 retificações S-1210 plansaude jun/2025 L2 enviadas em PROD (todas cod=201 aceito).**

- Marcadas `status='ok'` no DB com flag `RECIBO_PENDENTE_SYNC|jun L2 plansaude` em `descricao_resposta`
- `nr_recibo_novo` está NULL — não foi consultado para não esgotar cota diária do eSocial
- Após fechamento do mês, rodar para popular recibos:
  ```sql
  SELECT cpf, protocolo FROM s1210_cpf_envios
  WHERE descricao_resposta LIKE 'RECIBO_PENDENTE_SYNC%' AND nr_recibo_novo IS NULL;
  ```
- Loop: para cada protocolo, GET `/api/esocial/consultar/{proto}?ambiente=1` e UPDATE `nr_recibo_novo`
- Arquivos: `python-scripts/saida_plansaude_jun_l2.json` (envios), `_marca_ok_jun_l2.py`, `_flag_recibo_pendente.py`

### 🟠 42 CPFs restantes em ERRO no jun/2025 L2 (cod 401/459)

**Erro idêntico nos 42:** `"Não foi localizado um evento para o recibo de entrega informado ou o mesmo foi excluído/retificado"`

- Causa: o `nr_recibo_usado` na retificação aponta para um evento **já excluído/retificado** no eSocial — o recibo no DB está desatualizado
- Solução: consultar identificadores ATIVOS no eSocial (`WsConsultarIdentificadoresEventos`) para descobrir o recibo vigente de cada CPF e re-retificar com ele
- ⚠️ **Precisa autorização explícita** — gasta cota diária (limite 10/dia Download Cirúrgico)
- Diagnóstico: `python-scripts/_erros_jun_l2.py`

---

## �🚨🔴 ALERTA CRÍTICO — XMLs DE RETORNO PERDIDOS (2026-04-25)

**LEIA ANTES DE RODAR QUALQUER ENVIO:** [ALERTA_CRITICO_XMLS_RETORNO_PERDIDOS.md](ALERTA_CRITICO_XMLS_RETORNO_PERDIDOS.md)

Resumo: todos os envios S-1210 até hoje (Fev–Out/2025) foram processados, mas o backend NÃO salvou os XMLs de retorno em disco — só os campos parseados no banco. **Ana precisa dos XMLs.** A partir do **L1 Novembro/2025** todo envio DEVE capturar os XMLs em `ARQUIVOS_RETORNO/<YYYY-MM>/`. Detalhes, plano de recuperação e patches no arquivo acima.

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
