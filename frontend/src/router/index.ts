import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/login',
      name: 'login',
      component: () => import('../views/LoginView.vue'),
      meta: { public: true },
    },
    {
      path: '/empresas',
      name: 'empresas',
      component: () => import('../views/EmpresasView.vue'),
    },
    {
      path: '/',
      name: 'painel',
      component: () => import('../views/PainelView.vue'),
      meta: { requireEmpresa: true },
    },
    {
      path: '/tabelas',
      name: 'tabelas',
      component: () => import('../views/TabelasView.vue'),
      meta: { requireEmpresa: true },
    },
    {
      path: '/bot',
      name: 'bot',
      component: () => import('../views/BotView.vue'),
      meta: { requireEmpresa: true },
    },
    {
      path: '/validador',
      name: 'validador',
      component: () => import('../views/ValidadorView.vue'),
      meta: { requireEmpresa: true },
    },
    {
      path: '/confirmar',
      name: 'confirmar',
      component: () => import('../views/ConfirmarAlteracoesView.vue'),
      meta: { requireEmpresa: true },
    },
    {
      path: '/cruzamento',
      name: 'cruzamento',
      component: () => import('../views/CruzamentoView.vue'),
      meta: { requireEmpresa: true },
    },
    {
      path: '/depara',
      name: 'depara',
      component: () => import('../views/DeParaView.vue'),
      meta: { requireEmpresa: true },
    },
    {
      path: '/esocial',
      name: 'esocial',
      component: () => import('../views/ESocialView.vue'),
      meta: { requireEmpresa: true },
    },
    {
      path: '/s1210-missao',
      name: 's1210-missao',
      component: () => import('../views/S1210MissaoView.vue'),
      meta: { requireEmpresa: true },
    },
    {
      path: '/repositorio-s1210',
      name: 'repositorio-s1210',
      component: () => import('../views/RepositorioS1210View.vue'),
      meta: { requireEmpresa: true },
    },
    {
      path: '/repositorio-s1210/por-lote',
      name: 'repositorio-s1210-por-lote',
      component: () => import('../views/RepositorioS1210PorLoteView.vue'),
      meta: { requireEmpresa: true },
    },
    {
      path: '/repositorio-s1210/por-lote/:lote/:mes',
      name: 'repositorio-s1210-compartimento',
      component: () => import('../views/RepositorioS1210CompartimentoView.vue'),
      meta: { requireEmpresa: true },
    },
    {
      path: '/s1210-anual',
      name: 's1210-anual',
      component: () => import('../views/S1210AnualView.vue'),
      meta: { requireEmpresa: true },
    },
    {
      path: '/eb-cruzamento',
      name: 'eb-cruzamento',
      component: () => import('../views/EBSkillsCruzamentoView.vue'),
      meta: { requireEmpresa: true },
    },
    {
      path: '/explorador',
      name: 'explorador',
      component: () => import('../views/ExploradorView.vue'),
      meta: { requireEmpresa: true },
    },
    {
      path: '/pipeline',
      name: 'pipeline',
      component: () => import('../views/PipelineView.vue'),
      meta: { requireEmpresa: true },
    },
    {
      path: '/logs',
      name: 'logs',
      component: () => import('../views/LogsSistemaView.vue'),
      meta: { requireEmpresa: true },
    },
    {
      path: '/pipeline-audit',
      redirect: '/logs',
    },
    {
      path: '/prova',
      redirect: '/logs',
    },
    {
      path: '/problemas',
      name: 'problemas',
      component: () => import('../views/ProblemasView.vue'),
      meta: { requireEmpresa: true },
    },
    {
      path: '/admin',
      name: 'admin',
      component: () => import('../views/AdminPanelView.vue'),
    },
  ],
})

let authChecked = false

router.beforeEach(async (to) => {
  const authStore = useAuthStore()

  // First load: verify stored token
  if (!authChecked) {
    authChecked = true
    if (authStore.token) {
      await authStore.checkAuth()
    }
  }

  // Public pages (login)
  if (to.meta.public) {
    if (authStore.isLoggedIn) return '/empresas'
    return true
  }

  // Not logged in → login
  if (!authStore.isLoggedIn) {
    return '/login'
  }

  // Pages requiring empresa selection
  if (to.meta.requireEmpresa && !authStore.empresaSelecionada) {
    return '/empresas'
  }

  return true
})

export default router
