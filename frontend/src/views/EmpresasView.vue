<template>
  <div class="min-h-screen relative overflow-hidden emp-bg">
    <!-- Animated glassmorphism shapes -->
    <div class="absolute inset-0 overflow-hidden">
      <div class="glass-shape shape-1"></div>
      <div class="glass-shape shape-2"></div>
      <div class="glass-shape shape-3"></div>
      <div class="glass-shape shape-4"></div>
      <div class="glass-shape shape-5"></div>
      <div class="glass-shape shape-6"></div>
      <div class="glass-shape shape-7"></div>
      <div class="glass-shape shape-8"></div>
    </div>

    <!-- Top bar -->
    <div class="relative z-10 flex items-center justify-between px-8 pt-6">
      <div class="flex items-center gap-3">
        <BrandLogo :size="52" :speed="4" />
        <span class="text-white/80 font-semibold text-lg"
          >Easy <span class="text-[#0066FF]">e-Social</span></span
        >
      </div>

      <div class="flex items-center gap-3">
        <button
          v-if="authStore.isAdmin"
          @click="router.push('/admin')"
          class="flex items-center gap-2 px-4 py-2 bg-[#0066FF]/20 hover:bg-[#0066FF]/40 border border-[#0066FF]/30 text-blue-100 rounded-lg text-sm font-medium backdrop-blur-sm transition-all duration-200"
        >
          <svg
            class="w-4 h-4"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
            stroke-linecap="round"
          >
            <path d="M12 20V10M18 20V4M6 20v-4" />
          </svg>
          Admin
        </button>

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
            class="mt-8 flex items-center justify-center gap-2 text-white/50 text-xs font-medium"
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
            <p v-if="empresa.cnpj" class="text-white/60 text-xs font-mono mt-1">
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
import BrandLogo from '../components/BrandLogo.vue'

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

/* ── Animated background gradient ── */
.emp-bg {
  background: linear-gradient(135deg, #0a1024, #0d1530, #0066ff, #0d1530, #0a1024);
  background-size: 400% 400%;
  animation: bgShift 12s ease-in-out infinite;
}
@keyframes bgShift {
  0% {
    background-position: 0% 50%;
  }
  50% {
    background-position: 100% 50%;
  }
  100% {
    background-position: 0% 50%;
  }
}

/* ── Glass shape base ── */
.glass-shape {
  position: absolute;
  border: 1.5px solid rgba(0, 102, 255, 0.25);
  background: rgba(0, 102, 255, 0.06);
  box-shadow:
    0 0 15px rgba(0, 102, 255, 0.3),
    0 0 40px rgba(0, 102, 255, 0.18),
    0 0 80px rgba(0, 102, 255, 0.08),
    inset 0 0 20px rgba(0, 102, 255, 0.04);
  will-change: transform;
}

/* ── Shape 1 — large circle ── */
.shape-1 {
  width: 300px;
  height: 300px;
  border-radius: 50%;
  filter: blur(2px);
  animation: drift1 26s ease-in-out infinite;
}
@keyframes drift1 {
  0% {
    transform: translate(-10%, -15%) rotate(0deg);
  }
  50% {
    transform: translate(40%, 60%) rotate(30deg);
  }
  100% {
    transform: translate(-10%, -15%) rotate(0deg);
  }
}

/* ── Shape 2 — rotated rounded square ── */
.shape-2 {
  width: 220px;
  height: 220px;
  border-radius: 36px;
  filter: blur(1.5px);
  right: -30px;
  animation: drift2 30s ease-in-out infinite;
}
@keyframes drift2 {
  0% {
    transform: translate(10%, -20%) rotate(45deg);
  }
  50% {
    transform: translate(-50%, 70%) rotate(90deg);
  }
  100% {
    transform: translate(10%, -20%) rotate(45deg);
  }
}

/* ── Shape 3 — medium circle ── */
.shape-3 {
  width: 170px;
  height: 170px;
  border-radius: 50%;
  filter: blur(3px);
  left: 60%;
  animation: drift3 22s ease-in-out infinite;
  animation-delay: -8s;
}
@keyframes drift3 {
  0% {
    transform: translate(0, -30%) rotate(0deg);
  }
  50% {
    transform: translate(-30%, 85%) rotate(-20deg);
  }
  100% {
    transform: translate(0, -30%) rotate(0deg);
  }
}

/* ── Shape 4 — small rounded square ── */
.shape-4 {
  width: 110px;
  height: 110px;
  border-radius: 22px;
  filter: blur(1px);
  left: 35%;
  animation: drift4 18s ease-in-out infinite;
  animation-delay: -4s;
}
@keyframes drift4 {
  0% {
    transform: translate(0, -10%) rotate(12deg);
  }
  50% {
    transform: translate(20%, 95%) rotate(60deg);
  }
  100% {
    transform: translate(0, -10%) rotate(12deg);
  }
}

/* ── Shape 5 — large rounded rect ── */
.shape-5 {
  width: 250px;
  height: 190px;
  border-radius: 44px;
  filter: blur(2.5px);
  left: 12%;
  bottom: 0;
  animation: drift5 34s ease-in-out infinite;
  animation-delay: -12s;
}
@keyframes drift5 {
  0% {
    transform: translate(-5%, 20%) rotate(-8deg);
  }
  50% {
    transform: translate(30%, -75%) rotate(15deg);
  }
  100% {
    transform: translate(-5%, 20%) rotate(-8deg);
  }
}

/* ── Shape 6 — small circle, bright neon ── */
.shape-6 {
  width: 85px;
  height: 85px;
  border-radius: 50%;
  filter: blur(1px);
  left: 75%;
  top: 55%;
  border-color: rgba(0, 102, 255, 0.4);
  box-shadow:
    0 0 20px rgba(0, 102, 255, 0.4),
    0 0 50px rgba(0, 102, 255, 0.2),
    0 0 80px rgba(0, 102, 255, 0.1);
  animation: drift6 15s ease-in-out infinite;
  animation-delay: -6s;
}
@keyframes drift6 {
  0% {
    transform: translate(0, 0) rotate(0deg);
  }
  50% {
    transform: translate(-40%, -110%) rotate(45deg);
  }
  100% {
    transform: translate(0, 0) rotate(0deg);
  }
}

/* ── Shape 7 — medium rounded square ── */
.shape-7 {
  width: 150px;
  height: 150px;
  border-radius: 30px;
  filter: blur(2px);
  right: 12%;
  top: 18%;
  animation: drift7 24s ease-in-out infinite;
  animation-delay: -10s;
}
@keyframes drift7 {
  0% {
    transform: translate(10%, -5%) rotate(-12deg);
  }
  50% {
    transform: translate(-20%, 70%) rotate(25deg);
  }
  100% {
    transform: translate(10%, -5%) rotate(-12deg);
  }
}

/* ── Shape 8 — tiny circle, fast bright ── */
.shape-8 {
  width: 65px;
  height: 65px;
  border-radius: 50%;
  filter: blur(0.5px);
  left: 22%;
  top: 42%;
  border-color: rgba(0, 102, 255, 0.45);
  box-shadow:
    0 0 18px rgba(0, 102, 255, 0.45),
    0 0 45px rgba(0, 102, 255, 0.22),
    0 0 70px rgba(0, 102, 255, 0.1);
  animation: drift8 13s ease-in-out infinite;
  animation-delay: -3s;
}
@keyframes drift8 {
  0% {
    transform: translate(0, 0) rotate(0deg);
  }
  50% {
    transform: translate(50%, 100%) rotate(-30deg);
  }
  100% {
    transform: translate(0, 0) rotate(0deg);
  }
}
</style>
