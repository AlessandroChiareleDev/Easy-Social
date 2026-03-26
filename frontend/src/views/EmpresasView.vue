<template>
  <div
    class="min-h-screen bg-gradient-to-br from-primary-600 via-primary-700 to-primary-900 relative overflow-hidden"
  >
    <!-- Background decorations -->
    <div class="absolute inset-0 opacity-[0.06]">
      <div class="absolute top-16 left-24 w-72 h-72 border-2 border-white rounded-full"></div>
      <div
        class="absolute bottom-20 right-20 w-56 h-56 border-2 border-white rounded-2xl rotate-45"
      ></div>
      <div class="absolute top-1/3 right-1/3 w-40 h-40 border-2 border-white rounded-full"></div>
    </div>

    <!-- Top bar -->
    <div class="relative z-10 flex items-center justify-between px-8 pt-6">
      <div class="flex items-center gap-3">
        <div
          class="w-10 h-10 bg-white/10 rounded-xl flex items-center justify-center backdrop-blur-sm border border-white/10"
        >
          <svg
            viewBox="0 0 40 40"
            class="w-5 h-5 text-white"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
          >
            <circle cx="20" cy="20" r="18" />
            <path d="M12 28c0-4.4 3.6-8 8-8s8 3.6 8 8" stroke-linecap="round" />
            <circle cx="20" cy="14" r="4" fill="currentColor" stroke="none" />
          </svg>
        </div>
        <span class="text-white/80 font-semibold text-lg">Easy Social</span>
      </div>

      <button
        @click="handleLogout"
        class="flex items-center gap-2 px-4 py-2 bg-red-500/20 hover:bg-red-500/40 border border-red-400/30 text-red-100 rounded-lg text-sm font-medium backdrop-blur-sm transition-all duration-200"
      >
        <svg
          class="w-4 h-4"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="2"
          stroke-linecap="round"
        >
          <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" />
          <polyline points="16 17 21 12 16 7" />
          <line x1="21" y1="12" x2="9" y2="12" />
        </svg>
        Sair
      </button>
    </div>

    <!-- Content -->
    <div class="relative z-10 flex items-center justify-center px-8 mt-12 pb-16">
      <div class="w-full max-w-2xl animate-fade-in">
        <!-- Glass header -->
        <div class="text-center mb-10">
          <div
            class="inline-flex items-center gap-2 px-4 py-1.5 bg-white/10 backdrop-blur-sm rounded-full border border-white/15 text-white/70 text-xs font-medium mb-5"
          >
            <svg
              class="w-3.5 h-3.5"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="2"
            >
              <path
                d="M3 21h18M9 8h1M9 12h1M9 16h1M14 8h1M14 12h1M14 16h1M5 21V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2v16"
              />
            </svg>
            Olá, {{ authStore.user?.nome }}
          </div>
          <h1 class="text-3xl font-bold text-white mb-2">Selecione uma empresa</h1>
          <p class="text-white/50 text-sm">Escolha a empresa que deseja acessar</p>
        </div>

        <!-- Empty state -->
        <div
          v-if="authStore.empresas.length === 0"
          class="bg-white/10 backdrop-blur-md border border-white/20 rounded-2xl p-12 text-center"
        >
          <div
            class="w-20 h-20 mx-auto mb-6 bg-white/10 rounded-2xl flex items-center justify-center border border-white/10"
          >
            <svg
              class="w-10 h-10 text-white/40"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="1.5"
            >
              <path
                d="M3 21h18M9 8h1M9 12h1M9 16h1M14 8h1M14 12h1M14 16h1M5 21V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2v16"
              />
            </svg>
          </div>
          <h3 class="text-xl font-semibold text-white mb-2">Nenhuma empresa vinculada</h3>
          <p class="text-white/50 text-sm max-w-sm mx-auto leading-relaxed">
            Sua conta ainda não possui acesso a nenhuma empresa. Entre em contato com um
            <span class="text-white/80 font-medium">administrador</span> para que ele adicione uma
            empresa à sua conta.
          </p>
          <div
            class="mt-8 flex items-center justify-center gap-2 text-white/30 text-xs font-medium"
          >
            <svg
              class="w-4 h-4"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="2"
            >
              <circle cx="12" cy="12" r="10" />
              <path d="M12 16v-4M12 8h.01" />
            </svg>
            Aguardando liberação de acesso
          </div>
        </div>

        <!-- Company cards grid -->
        <div v-else :class="gridClass">
          <div
            v-for="empresa in authStore.empresas"
            :key="empresa.id"
            class="group cursor-pointer bg-white/10 backdrop-blur-md border border-white/20 rounded-2xl p-6 hover:bg-white/20 hover:border-white/30 hover:shadow-2xl hover:shadow-black/10 hover:-translate-y-1 transition-all duration-300"
            @click="selectEmpresa(empresa)"
          >
            <!-- Initials avatar -->
            <div
              class="w-14 h-14 rounded-xl bg-white/15 text-white flex items-center justify-center font-bold text-lg mb-4 group-hover:bg-white/25 transition-colors border border-white/10"
            >
              {{ getInitials(empresa.nome) }}
            </div>

            <!-- Company name -->
            <h3
              class="font-semibold text-white text-base leading-snug mb-1 group-hover:text-white transition-colors"
            >
              {{ empresa.nome }}
            </h3>

            <!-- CNPJ -->
            <p v-if="empresa.cnpj" class="text-white/40 text-xs font-mono mt-1">
              {{ formatCNPJ(empresa.cnpj) }}
            </p>

            <!-- Role badge + arrow -->
            <div class="flex items-center justify-between mt-4">
              <span
                :class="
                  empresa.role_emp === 'admin'
                    ? 'bg-amber-400/20 text-amber-200 border-amber-400/20'
                    : 'bg-white/10 text-white/60 border-white/10'
                "
                class="inline-block px-2.5 py-0.5 text-xs font-semibold rounded-full border"
              >
                {{ empresa.role_emp === 'admin' ? 'Admin' : 'Operador' }}
              </span>
              <svg
                class="w-5 h-5 text-white/20 group-hover:text-white/60 group-hover:translate-x-1 transition-all duration-200"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                stroke-width="2"
                stroke-linecap="round"
              >
                <path d="M5 12h14M12 5l7 7-7 7" />
              </svg>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore, type Empresa } from '../stores/auth'

const router = useRouter()
const authStore = useAuthStore()

const gridClass = computed(() => {
  const count = authStore.empresas.length
  if (count <= 4) return 'grid grid-cols-1 sm:grid-cols-2 gap-5'
  if (count <= 12) return 'grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5'
  return 'grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-5'
})

function getInitials(nome: string): string {
  return nome
    .split(' ')
    .map((w) => w[0])
    .filter(Boolean)
    .slice(0, 2)
    .join('')
    .toUpperCase()
}

function formatCNPJ(cnpj: string): string {
  const digits = cnpj.replace(/\D/g, '')
  if (digits.length !== 14) return cnpj
  return digits.replace(/(\d{2})(\d{3})(\d{3})(\d{4})(\d{2})/, '$1.$2.$3/$4-$5')
}

function selectEmpresa(empresa: Empresa) {
  authStore.selecionarEmpresa(empresa)
  router.push('/')
}

function handleLogout() {
  authStore.logout()
  router.push('/login')
}

// Always show the empresa selector — let the user choose manually
</script>

<style scoped>
.animate-fade-in {
  animation: fadeIn 400ms ease;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(12px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
</style>
