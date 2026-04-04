<template>
  <div class="min-h-screen relative overflow-hidden admin-bg">
    <!-- Background shapes -->
    <div class="absolute inset-0 overflow-hidden">
      <div class="glass-shape shape-1"></div>
      <div class="glass-shape shape-2"></div>
      <div class="glass-shape shape-3"></div>
    </div>

    <!-- Top bar -->
    <div class="relative z-10 flex items-center justify-between px-8 pt-6">
      <div class="flex items-center gap-3">
        <button
          @click="router.push('/')"
          class="flex items-center gap-2 text-white/60 hover:text-white transition-colors"
        >
          <svg
            class="w-5 h-5"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
          >
            <path d="M19 12H5M12 19l-7-7 7-7" />
          </svg>
          Voltar
        </button>
      </div>
      <h1 class="text-white/90 font-semibold text-lg">
        Painel <span class="text-[#0066FF]">Admin</span>
      </h1>
      <div class="text-white/40 text-xs">{{ authStore.user?.username }}</div>
    </div>

    <!-- Content -->
    <div class="relative z-10 px-8 mt-6 pb-16 max-w-7xl mx-auto">
      <!-- Period filter -->
      <div class="glass-card p-4 mb-6 flex flex-wrap items-center gap-4">
        <label class="text-white/60 text-sm">Período:</label>
        <select v-model="periodoSelecionado" @change="loadData" class="glass-input text-sm">
          <option value="hoje">Hoje</option>
          <option value="7d">Últimos 7 dias</option>
          <option value="30d">Últimos 30 dias</option>
          <option value="todos">Todos</option>
        </select>
        <button @click="loadData" class="btn-primary text-sm">Atualizar</button>
        <div v-if="loading" class="text-[#0066FF] text-sm animate-pulse">Carregando...</div>
      </div>

      <!-- Summary cards -->
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        <div class="glass-card p-5 text-center">
          <div class="text-3xl font-bold text-white">{{ totalAcoes }}</div>
          <div class="text-white/50 text-sm mt-1">Total de Ações</div>
        </div>
        <div class="glass-card p-5 text-center">
          <div class="text-3xl font-bold text-[#0066FF]">{{ totalUsuarios }}</div>
          <div class="text-white/50 text-sm mt-1">Operadores Ativos</div>
        </div>
        <div class="glass-card p-5 text-center">
          <div class="text-3xl font-bold text-green-400">{{ totalErros }}</div>
          <div class="text-white/50 text-sm mt-1">Erros (4xx/5xx)</div>
        </div>
        <div class="glass-card p-5 text-center">
          <div class="text-3xl font-bold text-amber-400">{{ duracaoMedia }}ms</div>
          <div class="text-white/50 text-sm mt-1">Tempo Médio</div>
        </div>
      </div>

      <!-- Operator summary table -->
      <div class="glass-card p-5 mb-6">
        <h2 class="text-white/90 font-semibold mb-4 flex items-center gap-2">
          <svg
            class="w-5 h-5 text-[#0066FF]"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
          >
            <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2" />
            <circle cx="9" cy="7" r="4" />
            <path d="M23 21v-2a4 4 0 0 0-3-3.87M16 3.13a4 4 0 0 1 0 7.75" />
          </svg>
          Atividade por Operador
        </h2>
        <div class="overflow-x-auto">
          <table class="w-full text-sm">
            <thead>
              <tr class="text-white/50 border-b border-white/10">
                <th class="text-left py-2 px-3">Operador</th>
                <th class="text-right py-2 px-3">Total</th>
                <th class="text-right py-2 px-3">GETs</th>
                <th class="text-right py-2 px-3">POSTs</th>
                <th class="text-right py-2 px-3">Erros</th>
                <th class="text-right py-2 px-3">Tempo Médio</th>
                <th class="text-right py-2 px-3">Dias Ativos</th>
                <th class="text-left py-2 px-3">Último Acesso</th>
                <th class="text-left py-2 px-3">IPs</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="op in resumoOperadores"
                :key="op.usuario_id"
                class="text-white/80 border-b border-white/5 hover:bg-white/5 cursor-pointer transition-colors"
                @click="filtrarPorUsuario(op.usuario_id)"
              >
                <td class="py-2 px-3 font-medium">{{ op.username }}</td>
                <td class="py-2 px-3 text-right">{{ op.total_acoes }}</td>
                <td class="py-2 px-3 text-right text-blue-300">{{ op.gets }}</td>
                <td class="py-2 px-3 text-right text-green-300">{{ op.posts }}</td>
                <td
                  class="py-2 px-3 text-right"
                  :class="op.erros > 0 ? 'text-red-400' : 'text-white/40'"
                >
                  {{ op.erros }}
                </td>
                <td class="py-2 px-3 text-right">{{ op.duracao_media_ms }}ms</td>
                <td class="py-2 px-3 text-right">{{ op.dias_ativos }}</td>
                <td class="py-2 px-3 text-white/50">{{ formatDate(op.ultimo_acesso) }}</td>
                <td class="py-2 px-3 text-white/40 text-xs">{{ (op.ips || []).join(', ') }}</td>
              </tr>
              <tr v-if="resumoOperadores.length === 0">
                <td colspan="9" class="text-center py-8 text-white/30">
                  Nenhuma atividade registrada
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- Popular routes -->
      <div class="glass-card p-5 mb-6">
        <h2 class="text-white/90 font-semibold mb-4 flex items-center gap-2">
          <svg
            class="w-5 h-5 text-[#0066FF]"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
          >
            <path d="M22 12h-4l-3 9L9 3l-3 9H2" />
          </svg>
          Rotas Mais Acessadas
        </h2>
        <div class="overflow-x-auto">
          <table class="w-full text-sm">
            <thead>
              <tr class="text-white/50 border-b border-white/10">
                <th class="text-left py-2 px-3">Método</th>
                <th class="text-left py-2 px-3">Rota</th>
                <th class="text-right py-2 px-3">Total</th>
                <th class="text-right py-2 px-3">Tempo Médio</th>
                <th class="text-right py-2 px-3">Erros</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="(r, i) in rotasPopulares"
                :key="i"
                class="text-white/80 border-b border-white/5"
              >
                <td class="py-2 px-3">
                  <span
                    :class="methodClass(r.metodo)"
                    class="px-2 py-0.5 rounded text-xs font-mono"
                  >
                    {{ r.metodo }}
                  </span>
                </td>
                <td class="py-2 px-3 font-mono text-xs">{{ r.rota }}</td>
                <td class="py-2 px-3 text-right">{{ r.total }}</td>
                <td class="py-2 px-3 text-right">{{ r.duracao_media_ms }}ms</td>
                <td
                  class="py-2 px-3 text-right"
                  :class="r.erros > 0 ? 'text-red-400' : 'text-white/40'"
                >
                  {{ r.erros }}
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- Activity log (detailed) -->
      <div class="glass-card p-5">
        <div class="flex items-center justify-between mb-4">
          <h2 class="text-white/90 font-semibold flex items-center gap-2">
            <svg
              class="w-5 h-5 text-[#0066FF]"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="2"
            >
              <rect x="3" y="4" width="18" height="18" rx="2" ry="2" />
              <line x1="16" y1="2" x2="16" y2="6" />
              <line x1="8" y1="2" x2="8" y2="6" />
              <line x1="3" y1="10" x2="21" y2="10" />
            </svg>
            Log de Atividades
            <span
              v-if="filtroUsuario"
              class="text-xs bg-[#0066FF]/20 text-[#0066FF] px-2 py-0.5 rounded-full"
            >
              {{ filtroUsuarioNome }}
              <button @click="limparFiltroUsuario" class="ml-1 hover:text-white">✕</button>
            </span>
          </h2>
          <div class="text-white/40 text-xs">{{ totalAtividades }} registros</div>
        </div>

        <div class="overflow-x-auto">
          <table class="w-full text-sm">
            <thead>
              <tr class="text-white/50 border-b border-white/10">
                <th class="text-left py-2 px-3">Quando</th>
                <th class="text-left py-2 px-3">Operador</th>
                <th class="text-left py-2 px-3">Método</th>
                <th class="text-left py-2 px-3">Rota</th>
                <th class="text-right py-2 px-3">Status</th>
                <th class="text-right py-2 px-3">Tempo</th>
                <th class="text-left py-2 px-3">IP</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="a in atividades"
                :key="a.id"
                class="text-white/70 border-b border-white/5 hover:bg-white/5 transition-colors"
              >
                <td class="py-2 px-3 text-xs text-white/50">{{ formatDateTime(a.criado_em) }}</td>
                <td class="py-2 px-3 font-medium text-white/80">{{ a.username }}</td>
                <td class="py-2 px-3">
                  <span
                    :class="methodClass(a.metodo)"
                    class="px-2 py-0.5 rounded text-xs font-mono"
                  >
                    {{ a.metodo }}
                  </span>
                </td>
                <td class="py-2 px-3 font-mono text-xs max-w-xs truncate">{{ a.rota }}</td>
                <td class="py-2 px-3 text-right" :class="statusClass(a.status_code)">
                  {{ a.status_code }}
                </td>
                <td class="py-2 px-3 text-right">{{ a.duracao_ms }}ms</td>
                <td class="py-2 px-3 text-white/40 text-xs">{{ a.ip }}</td>
              </tr>
              <tr v-if="atividades.length === 0">
                <td colspan="7" class="text-center py-8 text-white/30">
                  Nenhuma atividade encontrada
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <!-- Pagination -->
        <div v-if="totalAtividades > pageSize" class="flex items-center justify-center gap-4 mt-4">
          <button
            @click="paginaAnterior"
            :disabled="currentPage === 0"
            class="btn-secondary text-sm"
            :class="{ 'opacity-30 cursor-not-allowed': currentPage === 0 }"
          >
            ← Anterior
          </button>
          <span class="text-white/50 text-sm">
            Página {{ currentPage + 1 }} de {{ totalPages }}
          </span>
          <button
            @click="proximaPagina"
            :disabled="currentPage >= totalPages - 1"
            class="btn-secondary text-sm"
            :class="{ 'opacity-30 cursor-not-allowed': currentPage >= totalPages - 1 }"
          >
            Próxima →
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import axios from 'axios'
import { API_URL } from '@/lib/api'

const router = useRouter()
const authStore = useAuthStore()

const loading = ref(false)
const periodoSelecionado = ref('7d')

// Data
const resumoOperadores = ref<any[]>([])
const rotasPopulares = ref<any[]>([])
const atividades = ref<any[]>([])
const totalAtividades = ref(0)

// Filters
const filtroUsuario = ref<number | null>(null)
const filtroUsuarioNome = ref('')
const currentPage = ref(0)
const pageSize = 50

const totalAcoes = computed(() =>
  resumoOperadores.value.reduce((sum, op) => sum + parseInt(op.total_acoes || 0), 0),
)
const totalUsuarios = computed(() => resumoOperadores.value.length)
const totalErros = computed(() =>
  resumoOperadores.value.reduce((sum, op) => sum + parseInt(op.erros || 0), 0),
)
const duracaoMedia = computed(() => {
  if (resumoOperadores.value.length === 0) return 0
  const total = resumoOperadores.value.reduce(
    (sum, op) => sum + parseInt(op.duracao_media_ms || 0),
    0,
  )
  return Math.round(total / resumoOperadores.value.length)
})
const totalPages = computed(() => Math.ceil(totalAtividades.value / pageSize))

function getPeriodDates() {
  const now = new Date()
  let desde: string | undefined
  switch (periodoSelecionado.value) {
    case 'hoje':
      desde = new Date(now.getFullYear(), now.getMonth(), now.getDate()).toISOString()
      break
    case '7d':
      desde = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000).toISOString()
      break
    case '30d':
      desde = new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000).toISOString()
      break
    default:
      desde = undefined
  }
  return { desde }
}

async function loadData() {
  loading.value = true
  try {
    const { desde } = getPeriodDates()
    const params: any = {}
    if (desde) params.desde = desde

    const [resumoRes, rotasRes] = await Promise.all([
      axios.get(`${API_URL}/admin/atividades/resumo`, { params }),
      axios.get(`${API_URL}/admin/atividades/rotas-populares`, { params }),
    ])

    resumoOperadores.value = resumoRes.data.resumo || []
    rotasPopulares.value = rotasRes.data.rotas || []

    await loadAtividades()
  } catch (err: any) {
    console.error('Erro ao carregar dados admin:', err)
  } finally {
    loading.value = false
  }
}

async function loadAtividades() {
  const { desde } = getPeriodDates()
  const params: any = {
    limit: pageSize,
    offset: currentPage.value * pageSize,
  }
  if (desde) params.desde = desde
  if (filtroUsuario.value) params.usuario_id = filtroUsuario.value

  const res = await axios.get(`${API_URL}/admin/atividades`, { params })
  atividades.value = res.data.atividades || []
  totalAtividades.value = res.data.total || 0
}

function filtrarPorUsuario(id: number) {
  const op = resumoOperadores.value.find((o) => o.usuario_id === id)
  filtroUsuario.value = id
  filtroUsuarioNome.value = op?.username || `#${id}`
  currentPage.value = 0
  loadAtividades()
}

function limparFiltroUsuario() {
  filtroUsuario.value = null
  filtroUsuarioNome.value = ''
  currentPage.value = 0
  loadAtividades()
}

function paginaAnterior() {
  if (currentPage.value > 0) {
    currentPage.value--
    loadAtividades()
  }
}

function proximaPagina() {
  if (currentPage.value < totalPages.value - 1) {
    currentPage.value++
    loadAtividades()
  }
}

function methodClass(method: string) {
  switch (method) {
    case 'GET':
      return 'bg-blue-500/20 text-blue-300'
    case 'POST':
      return 'bg-green-500/20 text-green-300'
    case 'PUT':
      return 'bg-amber-500/20 text-amber-300'
    case 'DELETE':
      return 'bg-red-500/20 text-red-300'
    default:
      return 'bg-white/10 text-white/60'
  }
}

function statusClass(code: number) {
  if (code >= 500) return 'text-red-400 font-bold'
  if (code >= 400) return 'text-amber-400'
  if (code >= 200 && code < 300) return 'text-green-400'
  return 'text-white/60'
}

function formatDate(d: string) {
  if (!d) return '-'
  return new Date(d).toLocaleDateString('pt-BR', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
  })
}

function formatDateTime(d: string) {
  if (!d) return '-'
  return new Date(d).toLocaleString('pt-BR', {
    day: '2-digit',
    month: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  })
}

onMounted(() => {
  if (!authStore.isAdmin) {
    router.push('/')
    return
  }
  loadData()
})
</script>

<style scoped>
.admin-bg {
  background: linear-gradient(135deg, #0a1024 0%, #0d1530 40%, #111b3d 100%);
  min-height: 100vh;
}

.glass-card {
  background: rgba(255, 255, 255, 0.04);
  backdrop-filter: blur(12px);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 12px;
}

.glass-input {
  background: rgba(255, 255, 255, 0.08);
  border: 1px solid rgba(255, 255, 255, 0.12);
  border-radius: 8px;
  color: white;
  padding: 6px 12px;
  outline: none;
}
.glass-input:focus {
  border-color: #0066ff;
}
.glass-input option {
  background: #1a2340;
  color: white;
}

.btn-primary {
  background: #0066ff;
  color: white;
  padding: 6px 16px;
  border-radius: 8px;
  font-weight: 500;
  transition: all 0.2s;
}
.btn-primary:hover {
  background: #0055dd;
}

.btn-secondary {
  background: rgba(255, 255, 255, 0.08);
  border: 1px solid rgba(255, 255, 255, 0.12);
  color: white;
  padding: 6px 16px;
  border-radius: 8px;
  transition: all 0.2s;
}
.btn-secondary:hover {
  background: rgba(255, 255, 255, 0.15);
}

.glass-shape {
  position: absolute;
  border-radius: 50%;
  background: radial-gradient(circle, rgba(0, 102, 255, 0.08) 0%, transparent 70%);
  animation: float 20s ease-in-out infinite;
}
.shape-1 {
  width: 400px;
  height: 400px;
  top: -100px;
  right: -100px;
  animation-delay: 0s;
}
.shape-2 {
  width: 300px;
  height: 300px;
  bottom: 10%;
  left: -50px;
  animation-delay: -7s;
}
.shape-3 {
  width: 250px;
  height: 250px;
  top: 50%;
  right: 20%;
  animation-delay: -14s;
}

@keyframes float {
  0%,
  100% {
    transform: translate(0, 0) scale(1);
  }
  33% {
    transform: translate(30px, -20px) scale(1.05);
  }
  66% {
    transform: translate(-20px, 15px) scale(0.95);
  }
}
</style>
