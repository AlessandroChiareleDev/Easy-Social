<template>
  <div class="flex min-h-screen">
    <!-- Left Brand Panel (60%) -->
    <div
      class="hidden lg:flex w-3/5 bg-gradient-to-br from-primary-600 via-primary-700 to-primary-900 relative overflow-hidden items-center justify-center"
    >
      <!-- Abstract geometric decorations -->
      <div class="absolute inset-0 opacity-[0.07]">
        <div class="absolute top-20 left-20 w-64 h-64 border-2 border-white rounded-full"></div>
        <div
          class="absolute bottom-32 right-16 w-48 h-48 border-2 border-white rounded-2xl rotate-45"
        ></div>
        <div class="absolute top-1/2 left-1/3 w-32 h-32 border-2 border-white rounded-full"></div>
        <div
          class="absolute bottom-20 left-40 w-24 h-24 border-2 border-white rounded-lg rotate-12"
        ></div>
        <div
          class="absolute top-32 right-32 w-40 h-40 border-2 border-white rounded-2xl -rotate-12"
        ></div>
      </div>

      <div class="relative z-10 text-center px-16 max-w-lg">
        <!-- Logo mark -->
        <div
          class="w-20 h-20 mx-auto mb-8 bg-white/10 rounded-2xl flex items-center justify-center backdrop-blur-sm border border-white/10"
        >
          <svg
            viewBox="0 0 40 40"
            class="w-10 h-10 text-white"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
          >
            <circle cx="20" cy="20" r="18" />
            <path d="M12 28c0-4.4 3.6-8 8-8s8 3.6 8 8" stroke-linecap="round" />
            <circle cx="20" cy="14" r="4" fill="currentColor" stroke="none" />
          </svg>
        </div>
        <h1 class="text-4xl font-bold text-white mb-3 tracking-tight">Easy Social</h1>
        <p class="text-lg text-white/60">Gestão eSocial simplificada</p>
      </div>
    </div>

    <!-- Right Form Panel (40%) -->
    <div class="flex-1 flex items-center justify-center bg-gray-50 px-8">
      <div class="w-full max-w-sm">
        <!-- Mobile logo -->
        <div class="lg:hidden text-center mb-8">
          <h1 class="text-2xl font-bold text-primary-600">Easy Social</h1>
        </div>

        <h2 class="text-2xl font-bold text-gray-900">Entrar</h2>
        <p class="text-sm text-gray-500 mt-1 mb-8">Acesse sua conta Easy Social</p>

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
            <label for="usuario" class="block text-sm font-medium text-gray-700 mb-1.5"
              >Usuário</label
            >
            <div class="relative">
              <span class="absolute left-3.5 top-1/2 -translate-y-1/2 text-gray-400">
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
                class="w-full h-11 pl-11 pr-4 text-sm border border-gray-300 rounded-lg bg-white text-gray-900 placeholder-gray-400 outline-none focus:border-primary-600 focus:ring-2 focus:ring-primary-500/20 transition-all duration-150"
              />
            </div>
          </div>

          <!-- Password -->
          <div>
            <label for="senha" class="block text-sm font-medium text-gray-700 mb-1.5">Senha</label>
            <div class="relative">
              <input
                id="senha"
                v-model="senha"
                :type="showPassword ? 'text' : 'password'"
                required
                autocomplete="current-password"
                placeholder="••••••••"
                class="w-full h-11 pl-4 pr-11 text-sm border border-gray-300 rounded-lg bg-white text-gray-900 placeholder-gray-400 outline-none focus:border-primary-600 focus:ring-2 focus:ring-primary-500/20 transition-all duration-150"
              />
              <button
                type="button"
                @click="showPassword = !showPassword"
                class="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600 transition-colors"
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
            class="w-full h-12 bg-primary-600 hover:bg-primary-700 active:bg-primary-700 text-white font-semibold rounded-lg transition-colors duration-150 disabled:opacity-60 disabled:cursor-not-allowed flex items-center justify-center"
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
        <p class="text-center text-xs text-gray-400 mt-10">Easy Social v1.0 · By Xandao</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'

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
    } else {
      error.value = 'Usuário ou senha incorretos'
    }
  } catch {
    error.value = 'Erro de conexão com o servidor'
  } finally {
    loading.value = false
  }
}
</script>
