<template>
  <div class="flex min-h-screen">
    <!-- Left Brand Panel (60%) -->
    <div
      class="hidden lg:flex w-3/5 relative overflow-hidden items-center justify-center brand-panel"
    >
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

      <div class="relative z-10 text-center px-16 max-w-lg">
        <!-- Logo mark -->
        <div class="mx-auto mb-8">
          <BrandLogo :size="120" :speed="4" />
        </div>
        <h1 class="text-4xl font-bold text-white mb-3 tracking-tight leading-tight">
          Easy<br /><span class="text-[#0066FF]">e-Social</span>
        </h1>
        <p class="text-lg text-white/60">Gestão eSocial simplificada</p>
      </div>
    </div>

    <!-- Right Form Panel (40%) -->
    <div class="flex-1 flex items-center justify-center px-8" style="background: #0d1530">
      <div class="w-full max-w-sm">
        <!-- Mobile logo -->
        <div class="lg:hidden text-center mb-8 flex flex-col items-center gap-2">
          <BrandLogo :size="72" :speed="4" />
          <h1 class="text-2xl font-bold text-[#0066FF]">Easy<br />e-Social</h1>
        </div>

        <h2 class="text-2xl font-bold text-white">Entrar</h2>
        <p class="text-sm text-slate-400 mt-1 mb-8">Acesse sua conta Easy e-Social</p>

        <!-- Error banner -->
        <div
          v-if="error"
          class="mb-6 flex items-center gap-2 p-3 bg-red-50 border border-red-200 rounded-lg text-red-600 text-sm"
        >
          <svg
            class="w-4 h-4 shrink-0"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
          >
            <circle cx="12" cy="12" r="10" />
            <line x1="15" y1="9" x2="9" y2="15" />
            <line x1="9" y1="9" x2="15" y2="15" />
          </svg>
          {{ error }}
        </div>

        <form @submit.prevent="handleLogin" class="space-y-5">
          <!-- Usuário -->
          <div>
            <label for="usuario" class="block text-sm font-medium text-slate-300 mb-1.5"
              >Usuário</label
            >
            <div class="relative">
              <span class="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-500">
                <svg
                  class="w-5 h-5"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  stroke-width="2"
                >
                  <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
                  <circle cx="12" cy="7" r="4" />
                </svg>
              </span>
              <input
                id="usuario"
                v-model="usuario"
                type="text"
                required
                autocomplete="username"
                placeholder="Seu usuário"
                class="w-full h-11 pl-11 pr-4 text-sm border border-slate-600 rounded-lg bg-[#111b3a] text-white placeholder-slate-500 outline-none focus:border-[#0066FF] focus:ring-2 focus:ring-[#0066FF]/20 transition-all duration-150"
              />
            </div>
          </div>

          <!-- Password -->
          <div>
            <label for="senha" class="block text-sm font-medium text-slate-300 mb-1.5">Senha</label>
            <div class="relative">
              <input
                id="senha"
                v-model="senha"
                :type="showPassword ? 'text' : 'password'"
                required
                autocomplete="current-password"
                placeholder="••••••••"
                class="w-full h-11 pl-4 pr-11 text-sm border border-slate-600 rounded-lg bg-[#111b3a] text-white placeholder-slate-500 outline-none focus:border-[#0066FF] focus:ring-2 focus:ring-[#0066FF]/20 transition-all duration-150"
              />
              <button
                type="button"
                @click="showPassword = !showPassword"
                class="absolute right-3 top-1/2 -translate-y-1/2 text-slate-500 hover:text-slate-300 transition-colors"
              >
                <svg
                  v-if="!showPassword"
                  class="w-5 h-5"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  stroke-width="2"
                >
                  <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z" />
                  <circle cx="12" cy="12" r="3" />
                </svg>
                <svg
                  v-else
                  class="w-5 h-5"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  stroke-width="2"
                >
                  <path
                    d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"
                  />
                  <line x1="1" y1="1" x2="23" y2="23" />
                </svg>
              </button>
            </div>
          </div>

          <!-- Submit -->
          <button
            type="submit"
            :disabled="loading"
            class="w-full h-12 bg-[#0066FF] hover:bg-[#0055dd] active:bg-[#0055dd] text-white font-semibold rounded-lg transition-colors duration-150 disabled:opacity-60 disabled:cursor-not-allowed flex items-center justify-center"
          >
            <svg v-if="loading" class="w-5 h-5 animate-spin" viewBox="0 0 24 24" fill="none">
              <circle
                cx="12"
                cy="12"
                r="10"
                stroke="currentColor"
                stroke-width="3"
                class="opacity-25"
              />
              <path
                d="M4 12a8 8 0 0 1 8-8"
                stroke="currentColor"
                stroke-width="3"
                stroke-linecap="round"
                class="opacity-75"
              />
            </svg>
            <span v-else>Entrar</span>
          </button>
        </form>

        <!-- Footer -->
        <p class="text-center text-xs text-slate-600 mt-10">
          Easy e-Social v1.0 · By Alessandro Chiarele Filho
        </p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import BrandLogo from '../components/BrandLogo.vue'

const router = useRouter()
const authStore = useAuthStore()

const usuario = ref('')
const senha = ref('')
const error = ref('')
const loading = ref(false)
const showPassword = ref(false)

async function handleLogin() {
  error.value = ''
  loading.value = true

  try {
    const ok = await authStore.login(usuario.value, senha.value)
    if (ok) {
      router.push('/empresas')
    }
  } catch (err: any) {
    error.value = err.message || 'Erro de conexão com o servidor'
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
/* ── Animated background gradient ── */
.brand-panel {
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
  width: 280px;
  height: 280px;
  border-radius: 50%;
  filter: blur(2px);
  animation: drift1 26s ease-in-out infinite;
}
@keyframes drift1 {
  0% {
    transform: translate(-10%, -15%) rotate(0deg);
  }
  50% {
    transform: translate(40%, 70%) rotate(30deg);
  }
  100% {
    transform: translate(-10%, -15%) rotate(0deg);
  }
}

/* ── Shape 2 — rotated rounded square ── */
.shape-2 {
  width: 200px;
  height: 200px;
  border-radius: 32px;
  filter: blur(1.5px);
  right: -40px;
  animation: drift2 30s ease-in-out infinite;
}
@keyframes drift2 {
  0% {
    transform: translate(10%, -20%) rotate(45deg);
  }
  50% {
    transform: translate(-50%, 80%) rotate(90deg);
  }
  100% {
    transform: translate(10%, -20%) rotate(45deg);
  }
}

/* ── Shape 3 — medium circle ── */
.shape-3 {
  width: 160px;
  height: 160px;
  border-radius: 50%;
  filter: blur(3px);
  left: 55%;
  animation: drift3 22s ease-in-out infinite;
  animation-delay: -8s;
}
@keyframes drift3 {
  0% {
    transform: translate(0, -30%) rotate(0deg);
  }
  50% {
    transform: translate(-30%, 90%) rotate(-20deg);
  }
  100% {
    transform: translate(0, -30%) rotate(0deg);
  }
}

/* ── Shape 4 — small rounded square ── */
.shape-4 {
  width: 100px;
  height: 100px;
  border-radius: 20px;
  filter: blur(1px);
  left: 30%;
  animation: drift4 18s ease-in-out infinite;
  animation-delay: -4s;
}
@keyframes drift4 {
  0% {
    transform: translate(0, -10%) rotate(12deg);
  }
  50% {
    transform: translate(20%, 100%) rotate(60deg);
  }
  100% {
    transform: translate(0, -10%) rotate(12deg);
  }
}

/* ── Shape 5 — large rounded rect ── */
.shape-5 {
  width: 240px;
  height: 180px;
  border-radius: 40px;
  filter: blur(2.5px);
  left: 10%;
  bottom: 0;
  animation: drift5 34s ease-in-out infinite;
  animation-delay: -12s;
}
@keyframes drift5 {
  0% {
    transform: translate(-5%, 20%) rotate(-8deg);
  }
  50% {
    transform: translate(30%, -80%) rotate(15deg);
  }
  100% {
    transform: translate(-5%, 20%) rotate(-8deg);
  }
}

/* ── Shape 6 — small circle, faster ── */
.shape-6 {
  width: 80px;
  height: 80px;
  border-radius: 50%;
  filter: blur(1px);
  left: 70%;
  top: 60%;
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
    transform: translate(-40%, -120%) rotate(45deg);
  }
  100% {
    transform: translate(0, 0) rotate(0deg);
  }
}

/* ── Shape 7 — medium rounded square ── */
.shape-7 {
  width: 140px;
  height: 140px;
  border-radius: 28px;
  filter: blur(2px);
  right: 15%;
  top: 20%;
  animation: drift7 24s ease-in-out infinite;
  animation-delay: -10s;
}
@keyframes drift7 {
  0% {
    transform: translate(10%, -5%) rotate(-12deg);
  }
  50% {
    transform: translate(-20%, 75%) rotate(25deg);
  }
  100% {
    transform: translate(10%, -5%) rotate(-12deg);
  }
}

/* ── Shape 8 — tiny circle, fast ── */
.shape-8 {
  width: 60px;
  height: 60px;
  border-radius: 50%;
  filter: blur(0.5px);
  left: 20%;
  top: 40%;
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
    transform: translate(50%, 110%) rotate(-30deg);
  }
  100% {
    transform: translate(0, 0) rotate(0deg);
  }
}
</style>
