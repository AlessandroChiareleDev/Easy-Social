# Deploy — commit 84dcf14

Pushado pra `main`. Precisa redeploy na VPS.

## O que mudou

**Backend Node** (rebuild necessário):
- `backend/src/middleware/activityLogger.ts` — novo
- `backend/src/routes/adminRoutes.ts` — novo
- `backend/src/app.ts` — alterado
- `backend/src/services/auth-service.ts` — alterado

**Frontend Vue** (rebuild necessário):
- `frontend/src/views/AdminPanelView.vue` — novo
- `frontend/src/views/PainelView.vue` — alterado
- `frontend/src/views/EmpresasView.vue` — alterado
- `frontend/src/router/index.ts` — alterado

## Banco

Nada manual. A tabela `master_atividades` é criada automaticamente na primeira request.
