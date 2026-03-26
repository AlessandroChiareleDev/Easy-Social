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
