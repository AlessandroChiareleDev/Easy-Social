<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { RouterLink, RouterView, useRouter, useRoute } from 'vue-router'
import { useAuthStore } from './stores/auth'

const authStore = useAuthStore()
const router = useRouter()
const route = useRoute()

const sidebarCollapsed = ref(false)
const userMenuOpen = ref(false)

const navItems = [
  { to: '/', label: 'Painel', icon: 'dashboard' },
  { to: '/tabelas', label: 'Tabelas', icon: 'table' },
  { to: '/validador', label: 'Validador', icon: 'check' },
  { to: '/bot', label: 'Robô eSocial', icon: 'bot' },
]

const currentPageTitle = computed(() => {
  return navItems.find((n) => n.to === route.path)?.label ?? ''
})

const userInitial = computed(() => {
  return authStore.user?.nome?.charAt(0)?.toUpperCase() ?? 'U'
})

const showLayout = computed(() => {
  return (
    authStore.isLoggedIn &&
    !!authStore.empresaSelecionada &&
    route.path !== '/login' &&
    route.path !== '/empresas'
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
  <div v-else class="flex h-screen bg-gray-50">
    <!-- Sidebar -->
    <aside
      :class="sidebarCollapsed ? 'w-16' : 'w-60'"
      class="bg-white border-r border-gray-200 flex flex-col shrink-0 transition-all duration-300 overflow-hidden"
    >
      <!-- Sidebar header -->
      <div
        class="h-16 flex items-center border-b border-gray-200"
        :class="sidebarCollapsed ? 'justify-center px-2' : 'px-5'"
      >
        <span v-if="!sidebarCollapsed" class="text-lg font-bold text-gray-900 whitespace-nowrap">
          Easy Social
        </span>
        <span v-else class="text-lg font-bold text-primary-600">ES</span>
      </div>

      <!-- Navigation -->
      <nav class="flex-1 py-4" :class="sidebarCollapsed ? 'px-2' : 'px-3'">
        <RouterLink
          v-for="item in navItems"
          :key="item.to"
          :to="item.to"
          :class="[
            route.path === item.to
              ? 'bg-primary-50 text-primary-700'
              : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900',
            sidebarCollapsed ? 'justify-center' : '',
          ]"
          class="flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors duration-150 mb-1 relative"
          :title="sidebarCollapsed ? item.label : undefined"
        >
          <!-- Active indicator bar -->
          <div
            v-if="route.path === item.to"
            class="absolute left-0 top-1/2 -translate-y-1/2 w-[3px] h-5 bg-primary-500 rounded-r-full"
          ></div>

          <!-- Icons -->
          <svg
            v-if="item.icon === 'dashboard'"
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
          <svg
            v-else-if="item.icon === 'table'"
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

          <span v-if="!sidebarCollapsed" class="whitespace-nowrap">{{ item.label }}</span>
        </RouterLink>
      </nav>
    </aside>

    <!-- Main content area -->
    <div class="flex-1 flex flex-col min-w-0">
      <!-- Top bar -->
      <header
        class="h-16 bg-white border-b border-gray-200 flex items-center justify-between px-6 shrink-0"
      >
        <div class="flex items-center gap-3">
          <!-- Toggle sidebar -->
          <button
            @click="sidebarCollapsed = !sidebarCollapsed"
            class="p-1.5 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
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
          <h1 class="text-lg font-semibold text-gray-900">{{ currentPageTitle }}</h1>
        </div>

        <div class="flex items-center gap-4">
          <!-- Company chip -->
          <button
            @click="trocarEmpresa"
            class="flex items-center gap-2 px-3 py-1.5 bg-gray-100 hover:bg-gray-200 rounded-lg text-sm font-medium text-gray-700 transition-colors"
          >
            <svg
              class="w-4 h-4 text-gray-500"
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
              class="w-3.5 h-3.5 text-gray-400"
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
              class="w-8 h-8 rounded-full bg-primary-600 text-white text-sm font-semibold flex items-center justify-center hover:bg-primary-700 transition-colors"
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
                class="absolute right-0 mt-2 w-56 bg-white border border-gray-200 rounded-xl shadow-xl py-2 z-50"
              >
                <div class="px-4 py-2 border-b border-gray-100">
                  <p class="text-sm font-medium text-gray-900">{{ authStore.user?.nome }}</p>
                  <p class="text-xs text-gray-500 mt-0.5">{{ authStore.user?.email }}</p>
                </div>
                <button
                  @click="handleLogout"
                  class="w-full flex items-center gap-2 px-4 py-2 text-sm text-red-600 hover:bg-red-50 transition-colors mt-1"
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
      <main class="flex-1 overflow-auto p-6">
        <div class="max-w-[1400px] mx-auto">
          <RouterView />
        </div>
      </main>
    </div>
  </div>
</template>
