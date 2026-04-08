<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { RouterLink, RouterView, useRouter, useRoute } from 'vue-router'
import { useAuthStore } from './stores/auth'
import BrandLogo from './components/BrandLogo.vue'

const authStore = useAuthStore()
const router = useRouter()
const route = useRoute()

const sidebarCollapsed = ref(false)
const userMenuOpen = ref(false)

const navGroups = [
  {
    id: 'arquivos',
    label: 'Arquivos, Folhas e Tabelas',
    items: [
      { to: '/tabelas', label: 'Tabelas', icon: 'table' },
      { to: '/cruzamento', label: 'Cruzamento', icon: 'cruzamento' },
      { to: '/depara', label: 'De-Para', icon: 'depara' },
    ],
  },
  {
    id: 'rubricas',
    label: 'Rubricas',
    items: [
      { to: '/validador', label: 'Validador', icon: 'check' },
      { to: '/confirmar', label: 'Confirmar', icon: 'confirm' },
      { to: '/eb-cruzamento', label: 'EB Skills Cruzamentos', icon: 'cruzamento' },
    ],
  },
  {
    id: 'automacao',
    label: 'Automação eSocial',
    items: [
      { to: '/bot', label: 'Robô eSocial', icon: 'bot' },
      { to: '/esocial', label: 'eSocial S-1010', icon: 'esocial' },
      { to: '/explorador', label: 'Explorador', icon: 'explorador' },
    ],
  },
  {
    id: 'logs',
    label: 'Logs de Sistema',
    items: [{ to: '/logs', label: 'Logs de Sistema', icon: 'check' }],
  },
]

const allNavItems = navGroups.flatMap((g) => g.items)

const currentPageTitle = computed(() => {
  return allNavItems.find((n) => n.to === route.path)?.label ?? 'Painel'
})

const userInitial = computed(() => {
  return authStore.user?.nome?.charAt(0)?.toUpperCase() ?? 'U'
})

const showLayout = computed(() => {
  return (
    authStore.isLoggedIn &&
    !!authStore.empresaSelecionada &&
    route.path !== '/login' &&
    route.path !== '/empresas' &&
    route.path !== '/'
  )
})

function trocarEmpresa() {
  router.push('/empresas')
}

function handleLogout() {
  userMenuOpen.value = false
  authStore.logout()
  router.push('/login')
}

function onClickOutside(e: MouseEvent) {
  if (!(e.target as HTMLElement).closest('.user-menu-container')) {
    userMenuOpen.value = false
  }
}

function checkWidth() {
  sidebarCollapsed.value = window.innerWidth < 1280
}

onMounted(() => {
  document.addEventListener('click', onClickOutside)
  checkWidth()
  window.addEventListener('resize', checkWidth)
})

onUnmounted(() => {
  document.removeEventListener('click', onClickOutside)
  window.removeEventListener('resize', checkWidth)
})
</script>

<template>
  <!-- Auth pages (login, empresas) — no layout wrapper -->
  <RouterView v-if="!showLayout" />

  <!-- Main app with sidebar + topbar -->
  <div v-else class="flex h-screen" style="background: #0a1024">
    <!-- Sidebar -->
    <aside
      :class="sidebarCollapsed ? 'w-16' : 'w-60'"
      class="flex flex-col shrink-0 transition-all duration-300 overflow-hidden"
      style="background: #0d1530; border-right: 1px solid rgba(0, 102, 255, 0.12)"
    >
      <!-- Sidebar header -->
      <div
        class="h-16 flex items-center gap-2"
        style="border-bottom: 1px solid rgba(0, 102, 255, 0.12)"
        :class="sidebarCollapsed ? 'justify-center px-2' : 'px-5'"
      >
        <template v-if="!sidebarCollapsed">
          <BrandLogo :size="40" :animate="false" />
          <span class="text-lg font-bold text-white whitespace-nowrap"
            >Easy <span class="text-[#0066FF]">e-Social</span></span
          >
        </template>
        <BrandLogo v-else :size="34" :animate="false" />
      </div>

      <!-- Navigation -->
      <nav class="flex-1 py-4 overflow-y-auto" :class="sidebarCollapsed ? 'px-2' : 'px-3'">
        <!-- Painel link -->
        <RouterLink
          to="/"
          :class="[
            route.path === '/'
              ? 'bg-[#0066FF]/15 text-[#0066FF]'
              : 'text-slate-400 hover:bg-white/5 hover:text-white',
            sidebarCollapsed ? 'justify-center' : '',
          ]"
          class="flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors duration-150 mb-3 relative"
          :title="sidebarCollapsed ? 'Painel' : undefined"
        >
          <div
            v-if="route.path === '/'"
            class="absolute left-0 top-1/2 -translate-y-1/2 w-[3px] h-5 bg-[#0066FF] rounded-r-full"
          ></div>
          <svg
            class="w-5 h-5 shrink-0"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
            stroke-linecap="round"
            stroke-linejoin="round"
          >
            <rect x="3" y="3" width="7" height="7" rx="1" />
            <rect x="14" y="3" width="7" height="7" rx="1" />
            <rect x="3" y="14" width="7" height="7" rx="1" />
            <rect x="14" y="14" width="7" height="7" rx="1" />
          </svg>
          <span v-if="!sidebarCollapsed" class="whitespace-nowrap">Painel</span>
        </RouterLink>

        <!-- Grouped nav items -->
        <div v-for="(group, gi) in navGroups" :key="group.id" :class="gi > 0 ? 'mt-2' : ''">
          <!-- Group header -->
          <div
            v-if="!sidebarCollapsed"
            class="px-3 pt-3 pb-1.5 text-[10px] font-semibold uppercase tracking-wider text-slate-500"
            style="border-top: 1px solid rgba(255, 255, 255, 0.06)"
          >
            {{ group.label }}
          </div>
          <div v-else class="my-2" style="border-top: 1px solid rgba(255, 255, 255, 0.06)"></div>

          <RouterLink
            v-for="item in group.items"
            :key="item.to"
            :to="item.to"
            :class="[
              route.path === item.to
                ? 'bg-[#0066FF]/15 text-[#0066FF]'
                : 'text-slate-400 hover:bg-white/5 hover:text-white',
              sidebarCollapsed ? 'justify-center' : '',
            ]"
            class="flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors duration-150 mb-1 relative"
            :title="sidebarCollapsed ? item.label : undefined"
          >
            <!-- Active indicator bar -->
            <div
              v-if="route.path === item.to"
              class="absolute left-0 top-1/2 -translate-y-1/2 w-[3px] h-5 bg-[#0066FF] rounded-r-full"
            ></div>

            <!-- Icons -->
            <svg
              v-if="item.icon === 'table'"
              class="w-5 h-5 shrink-0"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="2"
              stroke-linecap="round"
              stroke-linejoin="round"
            >
              <rect x="3" y="3" width="18" height="18" rx="2" />
              <line x1="3" y1="9" x2="21" y2="9" />
              <line x1="3" y1="15" x2="21" y2="15" />
              <line x1="9" y1="3" x2="9" y2="21" />
            </svg>
            <svg
              v-else-if="item.icon === 'check'"
              class="w-5 h-5 shrink-0"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="2"
              stroke-linecap="round"
              stroke-linejoin="round"
            >
              <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" />
              <polyline points="22 4 12 14.01 9 11.01" />
            </svg>
            <svg
              v-else-if="item.icon === 'confirm'"
              class="w-5 h-5 shrink-0"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="2"
              stroke-linecap="round"
              stroke-linejoin="round"
            >
              <path d="M9 11l3 3L22 4" />
              <path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11" />
            </svg>
            <svg
              v-else-if="item.icon === 'cruzamento'"
              class="w-5 h-5 shrink-0"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="2"
              stroke-linecap="round"
              stroke-linejoin="round"
            >
              <path d="M16 3h5v5" />
              <path d="M8 3H3v5" />
              <path d="M21 3l-7 7" />
              <path d="M3 3l7 7" />
              <path d="M16 21h5v-5" />
              <path d="M8 21H3v-5" />
              <path d="M21 21l-7-7" />
              <path d="M3 21l7-7" />
            </svg>
            <svg
              v-else-if="item.icon === 'bot'"
              class="w-5 h-5 shrink-0"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="2"
              stroke-linecap="round"
              stroke-linejoin="round"
            >
              <rect x="3" y="11" width="18" height="10" rx="2" />
              <circle cx="12" cy="5" r="2" />
              <path d="M12 7v4" />
              <circle cx="8.5" cy="16" r="1.5" fill="currentColor" stroke="none" />
              <circle cx="15.5" cy="16" r="1.5" fill="currentColor" stroke="none" />
            </svg>
            <svg
              v-else-if="item.icon === 'esocial'"
              class="w-5 h-5 shrink-0"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="2"
              stroke-linecap="round"
              stroke-linejoin="round"
            >
              <path d="M12 2L2 7l10 5 10-5-10-5z" />
              <path d="M2 17l10 5 10-5" />
              <path d="M2 12l10 5 10-5" />
            </svg>
            <svg
              v-else-if="item.icon === 'depara'"
              class="w-5 h-5 shrink-0"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="2"
              stroke-linecap="round"
              stroke-linejoin="round"
            >
              <path d="M8 3H5a2 2 0 0 0-2 2v3" />
              <path d="M21 8V5a2 2 0 0 0-2-2h-3" />
              <path d="M3 16v3a2 2 0 0 0 2 2h3" />
              <path d="M16 21h3a2 2 0 0 0 2-2v-3" />
              <path d="M7 12h10" />
              <path d="M14 9l3 3-3 3" />
            </svg>
            <svg
              v-else-if="item.icon === 'explorador'"
              class="w-5 h-5 shrink-0"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="2"
              stroke-linecap="round"
              stroke-linejoin="round"
            >
              <circle cx="11" cy="11" r="8" />
              <line x1="21" y1="21" x2="16.65" y2="16.65" />
              <line x1="11" y1="8" x2="11" y2="14" />
              <line x1="8" y1="11" x2="14" y2="11" />
            </svg>

            <span v-if="!sidebarCollapsed" class="whitespace-nowrap">{{ item.label }}</span>
          </RouterLink>
        </div>
      </nav>
    </aside>

    <!-- Main content area -->
    <div class="flex-1 flex flex-col min-w-0">
      <!-- Top bar -->
      <header
        class="h-16 flex items-center justify-between px-6 shrink-0"
        style="background: #0d1530; border-bottom: 1px solid rgba(0, 102, 255, 0.12)"
      >
        <div class="flex items-center gap-3">
          <!-- Toggle sidebar -->
          <button
            @click="sidebarCollapsed = !sidebarCollapsed"
            class="p-1.5 text-slate-400 hover:text-white hover:bg-white/10 rounded-lg transition-colors"
          >
            <svg
              class="w-5 h-5"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="2"
              stroke-linecap="round"
            >
              <line x1="3" y1="6" x2="21" y2="6" />
              <line x1="3" y1="12" x2="21" y2="12" />
              <line x1="3" y1="18" x2="21" y2="18" />
            </svg>
          </button>
          <h1 class="text-lg font-semibold text-white">{{ currentPageTitle }}</h1>
        </div>

        <div class="flex items-center gap-4">
          <!-- Company chip -->
          <button
            @click="trocarEmpresa"
            class="flex items-center gap-2 px-3 py-1.5 bg-white/5 hover:bg-white/10 rounded-lg text-sm font-medium text-slate-300 transition-colors border border-white/10"
          >
            <svg
              class="w-4 h-4 text-slate-500"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="2"
            >
              <path
                d="M3 21h18M9 8h1M9 12h1M9 16h1M14 8h1M14 12h1M14 16h1M5 21V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2v16"
              />
            </svg>
            {{ authStore.empresaSelecionada?.nome }}
            <svg
              class="w-3.5 h-3.5 text-slate-500"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="2"
            >
              <path d="M6 9l6 6 6-6" />
            </svg>
          </button>

          <!-- User menu -->
          <div class="relative user-menu-container">
            <button
              @click.stop="userMenuOpen = !userMenuOpen"
              class="w-8 h-8 rounded-full bg-[#0066FF] text-white text-sm font-semibold flex items-center justify-center hover:bg-[#0055dd] transition-colors"
            >
              {{ userInitial }}
            </button>

            <!-- Dropdown -->
            <Transition
              enter-active-class="transition duration-150 ease-out"
              enter-from-class="opacity-0 scale-95 -translate-y-1"
              enter-to-class="opacity-100 scale-100 translate-y-0"
              leave-active-class="transition duration-100 ease-in"
              leave-from-class="opacity-100 scale-100 translate-y-0"
              leave-to-class="opacity-0 scale-95 -translate-y-1"
            >
              <div
                v-if="userMenuOpen"
                class="absolute right-0 mt-2 w-56 rounded-xl shadow-xl py-2 z-50"
                style="background: #111b3a; border: 1px solid rgba(0, 102, 255, 0.15)"
              >
                <div class="px-4 py-2" style="border-bottom: 1px solid rgba(255, 255, 255, 0.08)">
                  <p class="text-sm font-medium text-white">{{ authStore.user?.nome }}</p>
                  <p class="text-xs text-slate-400 mt-0.5">{{ authStore.user?.email }}</p>
                </div>
                <button
                  @click="handleLogout"
                  class="w-full flex items-center gap-2 px-4 py-2 text-sm text-red-400 hover:bg-red-500/10 transition-colors mt-1"
                >
                  <svg
                    class="w-4 h-4"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    stroke-width="2"
                  >
                    <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4M16 17l5-5-5-5M21 12H9" />
                  </svg>
                  Sair
                </button>
              </div>
            </Transition>
          </div>
        </div>
      </header>

      <!-- Page content -->
      <main class="flex-1 overflow-auto p-6" style="background: #0a1024">
        <div class="max-w-[1400px] mx-auto">
          <RouterView />
        </div>
      </main>
    </div>
  </div>
</template>
