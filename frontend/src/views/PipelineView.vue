<template>
  <div class="pipeline-view">
    <!-- Header -->
    <div class="flex items-center justify-between mb-6">
      <div>
        <h1 class="text-2xl font-bold text-white flex items-center gap-3">
          <svg
            class="w-7 h-7 text-[#5ac8f5]"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
            stroke-linecap="round"
            stroke-linejoin="round"
          >
            <polyline points="22 12 18 12 15 21 9 3 6 12 2 12" />
          </svg>
          Pipeline 98-10-99
        </h1>
        <p class="text-sm text-slate-400 mt-1">
          Automação S-1298 → S-1210 retif → S-1299 — Acompanhamento por período
        </p>
      </div>
      <button
        v-if="selectedRun && selectedRun.status === 'rodando'"
        class="btn-refresh"
        @click="refreshProgress"
        :disabled="refreshing"
      >
        <svg
          :class="['w-4 h-4', { 'animate-spin': refreshing }]"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="2"
        >
          <polyline points="23 4 23 10 17 10" />
          <path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10" />
        </svg>
        Atualizar
      </button>
    </div>

    <!-- Period Filter -->
    <div class="filter-card">
      <div class="filter-grid">
        <div class="filter-group">
          <label class="filter-label">Período</label>
          <select class="filter-select" v-model="selectedPeriodo" @change="onPeriodoChange">
            <option value="">Todos os períodos</option>
            <option v-for="p in periodos" :key="p" :value="p">
              {{ formatPeriodo(p) }}
            </option>
          </select>
        </div>
      </div>
    </div>

    <!-- Runs List -->
    <div v-if="!selectedRun" class="runs-section">
      <div v-if="loadingRuns" class="loading-container">
        <div class="loading-spinner"></div>
        <p class="text-slate-400 text-sm mt-3">Carregando execuções...</p>
      </div>

      <div v-else-if="runs.length === 0" class="empty-state">
        <svg
          class="w-12 h-12 text-slate-600 mx-auto mb-3"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="1.5"
        >
          <polyline points="22 12 18 12 15 21 9 3 6 12 2 12" />
        </svg>
        <p class="text-slate-400">Nenhuma execução de pipeline encontrada.</p>
        <p class="text-xs text-slate-500 mt-2">
          Execute o pipeline_batch_set2025.py no servidor para iniciar.
        </p>
      </div>

      <div v-else class="runs-grid">
        <div
          v-for="run in runs"
          :key="run.id"
          class="run-card"
          :class="[`run-card--${run.status}`]"
          @click="selectRun(run)"
        >
          <div class="run-card-header">
            <span class="run-id">Run #{{ run.id }}</span>
            <span :class="['run-status-badge', `badge--${run.status}`]">{{ statusLabel(run.status) }}</span>
          </div>
          <div class="run-card-body">
            <div class="run-periodo">{{ formatPeriodo(run.per_apur) }}</div>
            <div class="run-stats">
              <div class="run-stat">
                <span class="run-stat-value">{{ run.total_cpfs }}</span>
                <span class="run-stat-label">Total</span>
              </div>
              <div class="run-stat run-stat--ok">
                <span class="run-stat-value">{{ run.cpfs_ok }}</span>
                <span class="run-stat-label">OK</span>
              </div>
              <div class="run-stat run-stat--erro">
                <span class="run-stat-value">{{ run.cpfs_erro }}</span>
                <span class="run-stat-label">Erros</span>
              </div>
            </div>
            <!-- Progress bar -->
            <div class="run-progress-bar">
              <div
                class="run-progress-fill"
                :style="{ width: runPct(run) + '%' }"
                :class="[run.cpfs_erro > 0 ? 'run-progress-fill--partial' : 'run-progress-fill--ok']"
              ></div>
            </div>
            <div class="run-meta">
              <span class="text-xs text-slate-500">
                <template v-if="run.s1298_done">S1298 ✓</template>
                <template v-else>S1298 ✗</template>
                &nbsp;·&nbsp;
                <template v-if="run.s1299_done">S1299 ✓</template>
                <template v-else>S1299 ✗</template>
              </span>
              <span class="text-xs text-slate-500">{{ formatDateTime(run.started_at) }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Selected Run Detail -->
    <div v-if="selectedRun" class="run-detail-section">
      <button class="btn-back" @click="selectedRun = null; cpfResult = null">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <polyline points="15 18 9 12 15 6" />
        </svg>
        Voltar à lista
      </button>

      <!-- Run summary stats -->
      <div class="stats-grid">
        <div class="stat-card">
          <div class="stat-icon stat-icon--blue">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2" />
              <circle cx="9" cy="7" r="4" />
            </svg>
          </div>
          <div>
            <div class="stat-value">{{ selectedRun.total_cpfs }}</div>
            <div class="stat-label">Total CPFs</div>
          </div>
        </div>
        <div class="stat-card">
          <div class="stat-icon stat-icon--green">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <polyline points="20 6 9 17 4 12" />
            </svg>
          </div>
          <div>
            <div class="stat-value">{{ selectedRun.cpfs_ok }}</div>
            <div class="stat-label">Retificados OK</div>
          </div>
        </div>
        <div class="stat-card">
          <div class="stat-icon stat-icon--red">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <circle cx="12" cy="12" r="10" />
              <line x1="15" y1="9" x2="9" y2="15" />
              <line x1="9" y1="9" x2="15" y2="15" />
            </svg>
          </div>
          <div>
            <div class="stat-value">{{ selectedRun.cpfs_erro }}</div>
            <div class="stat-label">Com Erro</div>
          </div>
        </div>
        <div class="stat-card">
          <div class="stat-icon stat-icon--cyan">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <polyline points="22 12 18 12 15 21 9 3 6 12 2 12" />
            </svg>
          </div>
          <div>
            <div class="stat-value">{{ progressPct }}%</div>
            <div class="stat-label">
              Lote {{ selectedRun.lote_atual }}/{{ selectedRun.total_lotes }}
            </div>
          </div>
        </div>
      </div>

      <!-- Progress bar -->
      <div class="progress-section">
        <div class="progress-bar-large">
          <div
            class="progress-fill-large"
            :style="{ width: progressPct + '%' }"
            :class="selectedRun.status === 'erro' ? 'progress-fill--error' : ''"
          ></div>
        </div>
        <div class="flex justify-between text-xs text-slate-500 mt-2">
          <span>
            <template v-if="selectedRun.s1298_done">✓ S-1298 (reabrir)</template>
            <template v-else>○ S-1298 (reabrir)</template>
          </span>
          <span :class="['run-status-badge', `badge--${selectedRun.status}`]">
            {{ statusLabel(selectedRun.status) }}
          </span>
          <span>
            <template v-if="selectedRun.s1299_done">✓ S-1299 (fechar)</template>
            <template v-else>○ S-1299 (fechar)</template>
          </span>
        </div>
        <div v-if="selectedRun.erro_fatal" class="erro-fatal-box">
          <strong>Erro Fatal:</strong> {{ selectedRun.erro_fatal }}
        </div>
      </div>

      <!-- CPF Filters -->
      <div class="filter-card">
        <div class="filter-grid filter-grid--cpfs">
          <div class="filter-group">
            <label class="filter-label">Buscar CPF</label>
            <input
              class="filter-input"
              v-model="cpfSearch"
              placeholder="Pesquisar por CPF..."
              @keydown.enter="buscarCpfs(1)"
            />
          </div>
          <div class="filter-group">
            <label class="filter-label">Status</label>
            <select class="filter-select" v-model="cpfStatusFilter" @change="buscarCpfs(1)">
              <option value="">Todos</option>
              <option value="ok">OK</option>
              <option value="erro">Com Erro</option>
              <option value="pendente">Pendente</option>
            </select>
          </div>
        </div>
        <div class="filter-actions">
          <button class="btn-clear" @click="cpfSearch = ''; cpfStatusFilter = ''; buscarCpfs(1)">Limpar</button>
          <button class="btn-search" @click="buscarCpfs(1)" :disabled="loadingCpfs">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <circle cx="11" cy="11" r="8" />
              <line x1="21" y1="21" x2="16.65" y2="16.65" />
            </svg>
            Buscar
          </button>
        </div>
      </div>

      <!-- Loading CPFs -->
      <div v-if="loadingCpfs" class="loading-container">
        <div class="loading-spinner"></div>
        <p class="text-slate-400 text-sm mt-3">Carregando CPFs...</p>
      </div>

      <!-- CPFs Table -->
      <div v-else-if="cpfResult" class="results-section">
        <div class="results-header">
          <span class="text-sm text-slate-400">
            {{ cpfResult.total }} CPF{{ cpfResult.total !== 1 ? 's' : '' }}
          </span>
        </div>

        <div class="results-table-wrapper" v-if="cpfResult.items.length">
          <table class="results-table">
            <thead>
              <tr>
                <th></th>
                <th>CPF</th>
                <th>Status</th>
                <th>Recibo Original</th>
                <th>Recibo Novo</th>
                <th>Lote</th>
                <th>Processado</th>
              </tr>
            </thead>
            <tbody>
              <template v-for="item in cpfResult.items" :key="item.id">
                <tr
                  class="result-row"
                  :class="{ 'result-row--expanded': expandedCpf === item.cpf }"
                  @click="toggleExpand(item)"
                >
                  <td>
                    <svg
                      :class="['expand-chevron', { 'expand-chevron--open': expandedCpf === item.cpf }]"
                      width="14" height="14" viewBox="0 0 24 24"
                      fill="none" stroke="currentColor" stroke-width="2"
                    >
                      <polyline points="9 18 15 12 9 6" />
                    </svg>
                  </td>
                  <td class="font-mono text-sm text-white">{{ formatCpf(item.cpf) }}</td>
                  <td>
                    <span :class="['status-badge', statusBadgeClass(item.status)]">
                      {{ statusLabel(item.status) }}
                    </span>
                  </td>
                  <td class="font-mono text-xs text-slate-400">{{ item.nr_recibo_original || '—' }}</td>
                  <td class="font-mono text-xs" :class="item.nr_recibo_novo ? 'text-emerald-400' : 'text-slate-500'">
                    {{ item.nr_recibo_novo || '—' }}
                  </td>
                  <td class="text-sm text-slate-400">{{ item.lote_num ?? '—' }}</td>
                  <td class="text-xs text-slate-500">{{ formatDateTime(item.processed_at) }}</td>
                </tr>

                <!-- Expanded detail row -->
                <tr v-if="expandedCpf === item.cpf" class="detail-row">
                  <td :colspan="7">
                    <div class="detail-content">
                      <!-- Error -->
                      <div v-if="item.erro_descricao" class="erro-box">
                        <strong class="text-red-400">Erro:</strong>
                        <span class="text-red-300 text-sm">{{ item.erro_descricao }}</span>
                      </div>

                      <!-- Pagamentos -->
                      <div v-if="item.pagamentos && item.pagamentos.length">
                        <h4 class="detail-section-title">Pagamentos ({{ item.pagamentos.length }})</h4>
                        <div v-for="(pgto, pi) in item.pagamentos" :key="pi" class="pgto-card">
                          <div class="detail-meta">
                            <div class="meta-item" v-if="pgto.dtPgto">
                              <span class="meta-label">Data Pgto</span>
                              <span class="meta-value">{{ pgto.dtPgto }}</span>
                            </div>
                            <div class="meta-item" v-if="pgto.tpPgto">
                              <span class="meta-label">Tipo Pgto</span>
                              <span class="meta-value">{{ pgto.tpPgto }}</span>
                            </div>
                            <div class="meta-item" v-if="pgto.indResBr">
                              <span class="meta-label">Resid. BR</span>
                              <span class="meta-value">{{ pgto.indResBr }}</span>
                            </div>
                          </div>
                          <!-- detPgtoFl items -->
                          <div v-if="pgto.detPgtoFl && pgto.detPgtoFl.length" class="det-pgto-list">
                            <div v-for="(det, di) in pgto.detPgtoFl" :key="di" class="det-pgto-item">
                              <span class="text-xs text-slate-400">perRef: {{ det.perRef || '—' }}</span>
                              <span class="text-xs text-slate-400">ideDmDev: {{ det.ideDmDev || '—' }}</span>
                              <span v-if="det.vrLiq" class="text-xs text-emerald-400">
                                R$ {{ Number(det.vrLiq).toLocaleString('pt-BR', { minimumFractionDigits: 2 }) }}
                              </span>
                            </div>
                          </div>
                          <!-- detPgtoBenPr items -->
                          <div v-if="pgto.detPgtoBenPr && pgto.detPgtoBenPr.length" class="det-pgto-list">
                            <div v-for="(det, di) in pgto.detPgtoBenPr" :key="'bp'+di" class="det-pgto-item">
                              <span class="text-xs text-slate-400">perRef: {{ det.perRef || '—' }}</span>
                              <span class="text-xs text-slate-400">ideDmDev: {{ det.ideDmDev || '—' }}</span>
                              <span v-if="det.vrLiq" class="text-xs text-emerald-400">
                                R$ {{ Number(det.vrLiq).toLocaleString('pt-BR', { minimumFractionDigits: 2 }) }}
                              </span>
                            </div>
                          </div>
                        </div>
                      </div>

                      <!-- InfoIRCR -->
                      <div v-if="item.info_ir_cr && item.info_ir_cr.length">
                        <h4 class="detail-section-title">InfoIR/CR ({{ item.info_ir_cr.length }})</h4>
                        <div class="info-ir-grid">
                          <div v-for="(ir, ii) in item.info_ir_cr" :key="ii" class="info-ir-item">
                            <span class="meta-label">tpCR {{ ir.tpCR }}</span>
                            <span class="meta-value">R$ {{ Number(ir.vrCR).toLocaleString('pt-BR', { minimumFractionDigits: 2 }) }}</span>
                          </div>
                        </div>
                      </div>

                      <!-- No detail -->
                      <div v-if="!item.pagamentos?.length && !item.info_ir_cr?.length && !item.erro_descricao">
                        <p class="text-xs text-slate-500">Sem dados detalhados disponíveis.</p>
                      </div>
                    </div>
                  </td>
                </tr>
              </template>
            </tbody>
          </table>
        </div>

        <!-- Empty state -->
        <div v-else class="empty-state">
          <p class="text-slate-400">Nenhum CPF encontrado com os filtros atuais.</p>
        </div>

        <!-- Pagination -->
        <div v-if="cpfResult.total_pages > 1" class="pagination">
          <button class="page-btn" :disabled="cpfResult.page <= 1" @click="buscarCpfs(cpfResult.page - 1)">‹</button>
          <button
            v-for="p in visiblePages"
            :key="p"
            :class="['page-btn', { 'page-btn--active': p === cpfResult.page }]"
            @click="buscarCpfs(p)"
          >
            {{ p }}
          </button>
          <button class="page-btn" :disabled="cpfResult.page >= cpfResult.total_pages" @click="buscarCpfs(cpfResult.page + 1)">›</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { PYTHON_API } from '../lib/api'

const API = `${PYTHON_API}/api/pipeline-batch`

// ── State ──
const periodos = ref<string[]>([])
const selectedPeriodo = ref('')
const runs = ref<any[]>([])
const loadingRuns = ref(false)
const selectedRun = ref<any>(null)
const refreshing = ref(false)

const cpfResult = ref<any>(null)
const loadingCpfs = ref(false)
const cpfSearch = ref('')
const cpfStatusFilter = ref('')
const expandedCpf = ref<string | null>(null)

let pollTimer: ReturnType<typeof setInterval> | null = null

// ── Lifecycle ──
onMounted(async () => {
  await loadPeriodos()
  await loadRuns()
})

onUnmounted(() => {
  if (pollTimer) clearInterval(pollTimer)
})

// ── API calls ──
async function loadPeriodos() {
  try {
    const res = await fetch(`${API}/periodos`)
    if (res.ok) periodos.value = await res.json()
  } catch (e) {
    console.error('Erro ao carregar períodos:', e)
  }
}

async function loadRuns() {
  loadingRuns.value = true
  try {
    const params = new URLSearchParams()
    if (selectedPeriodo.value) params.set('per_apur', selectedPeriodo.value)
    const res = await fetch(`${API}/runs?${params}`)
    if (res.ok) runs.value = await res.json()
  } catch (e) {
    console.error('Erro ao carregar runs:', e)
  } finally {
    loadingRuns.value = false
  }
}

async function selectRun(run: any) {
  selectedRun.value = run
  await buscarCpfs(1)
  startPolling(run.id)
}

async function buscarCpfs(page: number) {
  if (!selectedRun.value) return
  loadingCpfs.value = true
  expandedCpf.value = null
  try {
    const params = new URLSearchParams({ page: String(page), page_size: '50' })
    if (cpfSearch.value) params.set('search', cpfSearch.value.replace(/\D/g, ''))
    if (cpfStatusFilter.value) params.set('status', cpfStatusFilter.value)
    const res = await fetch(`${API}/runs/${selectedRun.value.id}/cpfs?${params}`)
    if (res.ok) cpfResult.value = await res.json()
  } catch (e) {
    console.error('Erro ao buscar CPFs:', e)
  } finally {
    loadingCpfs.value = false
  }
}

async function refreshProgress() {
  if (!selectedRun.value) return
  refreshing.value = true
  try {
    const res = await fetch(`${API}/runs/${selectedRun.value.id}/progresso`)
    if (res.ok) {
      const data = await res.json()
      Object.assign(selectedRun.value, data)
      // Stop polling if done
      if (!data.rodando && pollTimer) {
        clearInterval(pollTimer)
        pollTimer = null
      }
    }
  } catch (e) {
    console.error('Erro ao atualizar progresso:', e)
  } finally {
    refreshing.value = false
  }
}

function startPolling(runId: number) {
  if (pollTimer) clearInterval(pollTimer)
  if (selectedRun.value?.status === 'rodando') {
    pollTimer = setInterval(() => refreshProgress(), 5000)
  }
}

function toggleExpand(item: any) {
  if (expandedCpf.value === item.cpf) {
    expandedCpf.value = null
  } else {
    expandedCpf.value = item.cpf
  }
}

function onPeriodoChange() {
  selectedRun.value = null
  cpfResult.value = null
  loadRuns()
}

// ── Computed ──
const progressPct = computed(() => {
  if (!selectedRun.value || !selectedRun.value.total_cpfs) return 0
  const processados = selectedRun.value.cpfs_ok + selectedRun.value.cpfs_erro
  return Math.round((processados / selectedRun.value.total_cpfs) * 1000) / 10
})

const visiblePages = computed(() => {
  if (!cpfResult.value) return []
  const total = cpfResult.value.total_pages
  const current = cpfResult.value.page
  const pages: number[] = []
  const start = Math.max(1, current - 3)
  const end = Math.min(total, current + 3)
  for (let i = start; i <= end; i++) pages.push(i)
  return pages
})

// ── Helpers ──
function runPct(run: any): number {
  if (!run.total_cpfs) return 0
  return Math.round(((run.cpfs_ok + run.cpfs_erro) / run.total_cpfs) * 100)
}

function statusLabel(s: string): string {
  const map: Record<string, string> = {
    preparando: 'Preparando',
    rodando: 'Rodando',
    completo: 'Completo',
    parcial: 'Parcial',
    erro: 'Erro',
    ok: 'OK',
    pendente: 'Pendente',
  }
  return map[s] || s
}

function statusBadgeClass(s: string): string {
  const map: Record<string, string> = {
    ok: 'status-badge--done',
    erro: 'status-badge--error',
    pendente: 'status-badge--pending',
  }
  return map[s] || 'status-badge--pending'
}

function formatCpf(cpf: string): string {
  if (!cpf || cpf.length !== 11) return cpf ?? ''
  return `${cpf.slice(0, 3)}.${cpf.slice(3, 6)}.${cpf.slice(6, 9)}-${cpf.slice(9)}`
}

function formatPeriodo(p: string): string {
  if (!p) return ''
  const parts = p.split('-')
  const year = parts[0] ?? p
  const month = parts[1] ?? ''
  const months = [
    '', 'Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho',
    'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro',
  ]
  return `${months[parseInt(month)] || month}/${year}`
}

function formatDateTime(dt: string | null): string {
  if (!dt) return '—'
  try {
    const d = new Date(dt)
    return d.toLocaleDateString('pt-BR') + ' ' + d.toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' })
  } catch {
    return dt
  }
}
</script>

<style scoped>
.pipeline-view {
  --brain-blue: #5ac8f5;
  --brain-glow: rgba(90, 200, 245, 0.55);
  --brain-dim: rgba(90, 200, 245, 0.25);
  --brain-faint: rgba(90, 200, 245, 0.08);
  --glass-bg: rgba(8, 14, 36, 0.75);
  --glass-border: rgba(90, 200, 245, 0.12);
  --surface-dark: #0a1024;
  max-width: 1200px;
}

/* ── Stats Cards ──────────────────────────────────── */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin-bottom: 24px;
}
@media (max-width: 900px) {
  .stats-grid { grid-template-columns: repeat(2, 1fr); }
}

.stat-card {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 18px 20px;
  background: var(--glass-bg);
  backdrop-filter: blur(16px);
  border-radius: 14px;
  border: 1px solid var(--glass-border);
  transition: all 0.3s ease;
}
.stat-card:hover {
  border-color: rgba(90, 200, 245, 0.22);
  box-shadow: 0 0 20px rgba(90, 200, 245, 0.06);
}
.stat-icon {
  width: 44px; height: 44px;
  border-radius: 12px;
  display: flex; align-items: center; justify-content: center;
  flex-shrink: 0;
}
.stat-icon svg { width: 22px; height: 22px; }
.stat-icon--blue { background: rgba(0, 102, 255, 0.12); color: #4d9fff; }
.stat-icon--cyan { background: rgba(90, 200, 245, 0.1); color: #5ac8f5; }
.stat-icon--green { background: rgba(16, 185, 129, 0.1); color: #34d399; }
.stat-icon--red { background: rgba(239, 68, 68, 0.1); color: #f87171; }
.stat-value { font-size: 1.5rem; font-weight: 700; color: #fff; line-height: 1.2; }
.stat-label { font-size: 0.75rem; color: #64748b; margin-top: 2px; }

/* ── Filter Card ──────────────────────────────────── */
.filter-card {
  background: var(--glass-bg);
  backdrop-filter: blur(16px);
  border-radius: 16px;
  padding: 20px 24px;
  border: 1px solid var(--glass-border);
  margin-bottom: 24px;
  box-shadow: 0 0 20px rgba(90, 200, 245, 0.04), 0 8px 32px rgba(0, 0, 0, 0.3);
}
.filter-grid {
  display: grid;
  grid-template-columns: 1fr 2fr;
  gap: 14px;
  margin-bottom: 0;
}
.filter-grid--cpfs {
  grid-template-columns: 2fr 1fr;
  margin-bottom: 16px;
}
.filter-group { display: flex; flex-direction: column; gap: 5px; }
.filter-label {
  font-size: 0.6875rem; font-weight: 600;
  color: rgba(90, 200, 245, 0.6);
  text-transform: uppercase; letter-spacing: 0.05em;
}
.filter-input, .filter-select {
  width: 100%; padding: 8px 12px;
  background: var(--surface-dark);
  border: 1px solid var(--glass-border);
  border-radius: 8px; color: #fff; font-size: 0.8125rem;
  outline: none; transition: border-color 0.25s ease, box-shadow 0.25s ease;
}
.filter-input:focus, .filter-select:focus {
  border-color: var(--brain-blue);
  box-shadow: 0 0 12px rgba(90, 200, 245, 0.15);
}
.filter-select {
  appearance: none;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 24 24' fill='none' stroke='%2364748b' stroke-width='2'%3E%3Cpath d='M6 9l6 6 6-6'/%3E%3C/svg%3E");
  background-repeat: no-repeat; background-position: right 10px center; padding-right: 30px;
}
.filter-select option { background: #0a1024; color: #fff; }
.filter-actions {
  display: flex; gap: 10px; justify-content: flex-end;
  padding-top: 14px; border-top: 1px solid rgba(90, 200, 245, 0.08);
}
.btn-search {
  display: flex; align-items: center; gap: 8px;
  padding: 8px 22px;
  background: rgba(90, 200, 245, 0.15);
  border: 1px solid rgba(90, 200, 245, 0.3);
  border-radius: 10px; color: var(--brain-blue);
  font-size: 0.875rem; font-weight: 600; cursor: pointer;
  transition: all 0.25s ease;
}
.btn-search:hover { background: rgba(90, 200, 245, 0.25); box-shadow: 0 0 18px rgba(90, 200, 245, 0.2); }
.btn-search:disabled { opacity: 0.4; cursor: not-allowed; }
.btn-clear {
  padding: 8px 18px; background: transparent;
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 10px; color: #64748b; font-size: 0.8125rem;
  cursor: pointer; transition: all 0.25s ease;
}
.btn-clear:hover { color: #94a3b8; border-color: rgba(255, 255, 255, 0.2); }

/* ── Runs Grid ────────────────────────────────────── */
.runs-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 16px;
}
.run-card {
  background: var(--glass-bg);
  backdrop-filter: blur(16px);
  border-radius: 14px;
  border: 1px solid var(--glass-border);
  padding: 0;
  cursor: pointer;
  transition: all 0.3s ease;
  overflow: hidden;
}
.run-card:hover {
  border-color: rgba(90, 200, 245, 0.25);
  box-shadow: 0 0 24px rgba(90, 200, 245, 0.08);
  transform: translateY(-2px);
}
.run-card--rodando { border-color: rgba(59, 130, 246, 0.3); }
.run-card--completo { border-color: rgba(16, 185, 129, 0.2); }
.run-card--erro { border-color: rgba(239, 68, 68, 0.25); }
.run-card--parcial { border-color: rgba(245, 158, 11, 0.25); }
.run-card-header {
  display: flex; align-items: center; justify-content: space-between;
  padding: 14px 18px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
}
.run-id { font-size: 0.875rem; font-weight: 700; color: #fff; }
.run-card-body { padding: 16px 18px; }
.run-periodo { font-size: 1.1rem; font-weight: 600; color: #cbd5e1; margin-bottom: 12px; }
.run-stats { display: flex; gap: 20px; margin-bottom: 12px; }
.run-stat { display: flex; flex-direction: column; align-items: center; }
.run-stat-value { font-size: 1.25rem; font-weight: 700; color: #fff; }
.run-stat-label { font-size: 0.625rem; color: #64748b; text-transform: uppercase; letter-spacing: 0.05em; }
.run-stat--ok .run-stat-value { color: #34d399; }
.run-stat--erro .run-stat-value { color: #f87171; }
.run-meta { display: flex; justify-content: space-between; margin-top: 8px; }
.run-progress-bar {
  height: 4px; border-radius: 2px;
  background: rgba(255, 255, 255, 0.06);
  overflow: hidden;
}
.run-progress-fill {
  height: 100%; border-radius: 2px;
  transition: width 0.5s ease;
}
.run-progress-fill--ok { background: linear-gradient(90deg, #34d399, #5ac8f5); }
.run-progress-fill--partial { background: linear-gradient(90deg, #fbbf24, #f97316); }

/* ── Run Status Badge ─────────────────────────────── */
.run-status-badge {
  display: inline-block; padding: 3px 10px;
  border-radius: 20px; font-size: 0.6875rem;
  font-weight: 600; letter-spacing: 0.02em;
}
.badge--preparando { background: rgba(100, 116, 139, 0.12); color: #94a3b8; border: 1px solid rgba(100, 116, 139, 0.2); }
.badge--rodando { background: rgba(59, 130, 246, 0.12); color: #60a5fa; border: 1px solid rgba(59, 130, 246, 0.25); animation: pulse-glow 2s ease-in-out infinite; }
.badge--completo { background: rgba(16, 185, 129, 0.12); color: #34d399; border: 1px solid rgba(16, 185, 129, 0.25); }
.badge--parcial { background: rgba(245, 158, 11, 0.12); color: #fbbf24; border: 1px solid rgba(245, 158, 11, 0.2); }
.badge--erro { background: rgba(239, 68, 68, 0.12); color: #f87171; border: 1px solid rgba(239, 68, 68, 0.25); }

@keyframes pulse-glow {
  0%, 100% { box-shadow: 0 0 4px rgba(59, 130, 246, 0.2); }
  50% { box-shadow: 0 0 12px rgba(59, 130, 246, 0.4); }
}

/* ── Progress Section ─────────────────────────────── */
.progress-section { margin-bottom: 24px; }
.progress-bar-large {
  height: 8px; border-radius: 4px;
  background: rgba(255, 255, 255, 0.06);
  overflow: hidden;
}
.progress-fill-large {
  height: 100%; border-radius: 4px;
  background: linear-gradient(90deg, #0066FF, #5ac8f5);
  transition: width 0.5s ease;
}
.progress-fill--error {
  background: linear-gradient(90deg, #ef4444, #f97316);
}
.erro-fatal-box {
  margin-top: 12px; padding: 12px 16px;
  background: rgba(239, 68, 68, 0.08);
  border: 1px solid rgba(239, 68, 68, 0.2);
  border-radius: 10px; color: #fca5a5; font-size: 0.8125rem;
}

/* ── Back Button ──────────────────────────────────── */
.btn-back {
  display: inline-flex; align-items: center; gap: 6px;
  padding: 8px 16px; margin-bottom: 20px;
  background: transparent; border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 10px; color: #94a3b8; font-size: 0.8125rem;
  cursor: pointer; transition: all 0.25s ease;
}
.btn-back:hover { color: #fff; border-color: rgba(90, 200, 245, 0.2); }

/* ── Refresh Button ───────────────────────────────── */
.btn-refresh {
  display: flex; align-items: center; gap: 8px;
  padding: 8px 18px;
  background: rgba(59, 130, 246, 0.12);
  border: 1px solid rgba(59, 130, 246, 0.25);
  border-radius: 10px; color: #60a5fa;
  font-size: 0.8125rem; font-weight: 600;
  cursor: pointer; transition: all 0.25s ease;
}
.btn-refresh:hover { background: rgba(59, 130, 246, 0.2); }
.btn-refresh:disabled { opacity: 0.5; cursor: not-allowed; }

/* ── Loading ──────────────────────────────────────── */
.loading-container { text-align: center; padding: 48px 0; }
.loading-spinner {
  width: 36px; height: 36px;
  border: 3px solid rgba(90, 200, 245, 0.15);
  border-top-color: var(--brain-blue);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
  margin: 0 auto;
}
@keyframes spin { to { transform: rotate(360deg); } }

/* ── Results Table ────────────────────────────────── */
.results-section { margin-bottom: 32px; }
.results-header { margin-bottom: 12px; }
.results-table-wrapper {
  background: var(--glass-bg);
  backdrop-filter: blur(16px);
  border-radius: 14px;
  border: 1px solid var(--glass-border);
  overflow: hidden;
  box-shadow: 0 0 20px rgba(90, 200, 245, 0.04), 0 8px 32px rgba(0, 0, 0, 0.3);
}
.results-table { width: 100%; border-collapse: separate; border-spacing: 0; }
.results-table thead tr { border-bottom: 1px solid rgba(90, 200, 245, 0.1); }
.results-table th {
  padding: 12px 14px; text-align: left;
  font-size: 0.6875rem; font-weight: 600;
  color: rgba(90, 200, 245, 0.6);
  text-transform: uppercase; letter-spacing: 0.05em;
  border-bottom: 1px solid rgba(90, 200, 245, 0.1);
}
.results-table td { padding: 10px 14px; border-bottom: 1px solid rgba(255, 255, 255, 0.04); }
.result-row { cursor: pointer; transition: background 0.2s ease; }
.result-row:hover { background: rgba(90, 200, 245, 0.03); }
.result-row--expanded { background: rgba(90, 200, 245, 0.05) !important; }

.expand-chevron { transition: transform 0.2s ease; color: #64748b; }
.expand-chevron--open { transform: rotate(90deg); color: var(--brain-blue); }

/* ── Status badges ────────────────────────────────── */
.status-badge {
  display: inline-block; padding: 3px 10px;
  border-radius: 20px; font-size: 0.6875rem;
  font-weight: 600; letter-spacing: 0.02em;
}
.status-badge--done { background: rgba(16, 185, 129, 0.12); color: #34d399; border: 1px solid rgba(16, 185, 129, 0.25); }
.status-badge--error { background: rgba(239, 68, 68, 0.12); color: #f87171; border: 1px solid rgba(239, 68, 68, 0.25); }
.status-badge--pending { background: rgba(245, 158, 11, 0.12); color: #fbbf24; border: 1px solid rgba(245, 158, 11, 0.2); }

/* ── Detail row ───────────────────────────────────── */
.detail-row td {
  padding: 0 !important;
  border-bottom: 1px solid rgba(90, 200, 245, 0.08) !important;
}
.detail-content { padding: 16px 20px; background: rgba(90, 200, 245, 0.02); }
.detail-section-title {
  font-size: 0.6875rem; font-weight: 600;
  color: rgba(90, 200, 245, 0.6);
  text-transform: uppercase; letter-spacing: 0.05em;
  margin-bottom: 10px; margin-top: 12px;
  border-top: 1px solid rgba(90, 200, 245, 0.08);
  padding-top: 10px;
}
.detail-meta {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
  gap: 8px;
}
.meta-item { display: flex; flex-direction: column; gap: 2px; }
.meta-label {
  font-size: 0.625rem; font-weight: 600;
  color: rgba(90, 200, 245, 0.5);
  text-transform: uppercase; letter-spacing: 0.05em;
}
.meta-value { color: #cbd5e1; word-break: break-all; }

.erro-box {
  padding: 10px 14px; margin-bottom: 10px;
  background: rgba(239, 68, 68, 0.06);
  border: 1px solid rgba(239, 68, 68, 0.15);
  border-radius: 8px;
  display: flex; gap: 8px; align-items: flex-start;
}
.pgto-card {
  background: rgba(0, 0, 0, 0.2);
  border: 1px solid rgba(90, 200, 245, 0.08);
  border-radius: 10px; padding: 12px 16px; margin-bottom: 8px;
}
.det-pgto-list {
  margin-top: 8px;
  border-top: 1px solid rgba(90, 200, 245, 0.06);
  padding-top: 8px;
}
.det-pgto-item { display: flex; gap: 16px; padding: 3px 0; }
.info-ir-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
  gap: 8px;
}
.info-ir-item {
  display: flex; flex-direction: column; gap: 2px;
  padding: 8px 12px;
  background: rgba(0, 0, 0, 0.15);
  border-radius: 6px;
}

/* ── Empty state ──────────────────────────────────── */
.empty-state { text-align: center; padding: 48px 0; }

/* ── Pagination ───────────────────────────────────── */
.pagination {
  display: flex; align-items: center; justify-content: center;
  gap: 4px; margin-top: 16px;
}
.page-btn {
  display: flex; align-items: center; justify-content: center;
  min-width: 36px; height: 36px; padding: 0 8px;
  border-radius: 8px; font-size: 0.8125rem; font-weight: 500;
  color: #94a3b8; border: 1px solid rgba(255, 255, 255, 0.08);
  background: transparent; cursor: pointer; transition: all 0.2s ease;
}
.page-btn:hover:not(:disabled) { color: #fff; border-color: rgba(90, 200, 245, 0.2); }
.page-btn:disabled { opacity: 0.3; cursor: not-allowed; }
.page-btn--active {
  color: var(--brain-blue);
  border-color: rgba(90, 200, 245, 0.3);
  background: rgba(90, 200, 245, 0.1);
}
</style>
