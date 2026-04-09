<template>
  <div class="dados-func-view">
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
            <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2" />
            <circle cx="9" cy="7" r="4" />
            <path d="M23 21v-2a4 4 0 0 0-3-3.87" />
            <path d="M16 3.13a4 4 0 0 1 0 7.75" />
          </svg>
          Dados Funcionários
        </h1>
        <p class="text-sm text-slate-400 mt-1">
          Visão por CPF — S-1200 (Remuneração) e S-1210 (Pagamentos)
        </p>
      </div>
    </div>

    <!-- Stats Cards -->
    <div class="stats-grid" v-if="stats">
      <div class="stat-card">
        <div class="stat-icon stat-icon--blue">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2" />
            <circle cx="9" cy="7" r="4" />
          </svg>
        </div>
        <div>
          <div class="stat-value">{{ stats.total_cpfs ?? 0 }}</div>
          <div class="stat-label">CPFs Encontrados</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon stat-icon--cyan">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <rect x="2" y="3" width="20" height="14" rx="2" ry="2" />
            <line x1="8" y1="21" x2="16" y2="21" />
            <line x1="12" y1="17" x2="12" y2="21" />
          </svg>
        </div>
        <div>
          <div class="stat-value">{{ stats.total_s1200 ?? 0 }}</div>
          <div class="stat-label">Eventos S-1200 ({{ stats.cpfs_com_s1200 ?? 0 }} CPFs)</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon stat-icon--green">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <line x1="12" y1="1" x2="12" y2="23" />
            <path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6" />
          </svg>
        </div>
        <div>
          <div class="stat-value">{{ stats.total_s1210 ?? 0 }}</div>
          <div class="stat-label">Eventos S-1210 ({{ stats.cpfs_com_s1210 ?? 0 }} CPFs)</div>
        </div>
      </div>
      <div class="stat-card" :class="{ 'stat-card--success': (stats.cpfs_retificados ?? 0) > 0 }">
        <div
          class="stat-icon"
          :class="(stats.cpfs_retificados ?? 0) > 0 ? 'stat-icon--green' : 'stat-icon--red'"
        >
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polyline points="20 6 9 17 4 12" />
          </svg>
        </div>
        <div>
          <div class="stat-value">{{ stats.cpfs_retificados ?? 0 }}</div>
          <div class="stat-label">CPFs Retificados</div>
        </div>
      </div>
    </div>

    <!-- Filters -->
    <div class="filter-card">
      <div class="filter-grid">
        <div class="filter-group">
          <label class="filter-label">Período</label>
          <select class="filter-select" v-model="filters.per_apur" @change="onPeriodoChange()">
            <option value="">Todos os períodos</option>
            <option v-for="p in stats?.periodos ?? []" :key="p" :value="p">
              {{ formatPeriodo(p) }}
            </option>
          </select>
        </div>
        <div class="filter-group">
          <label class="filter-label">Buscar CPF</label>
          <input
            class="filter-input"
            v-model="filters.cpf"
            placeholder="Pesquisar por CPF..."
            @keydown.enter="buscar(1)"
          />
        </div>
        <div class="filter-group">
          <label class="filter-label">Status</label>
          <select class="filter-select" v-model="filters.status" @change="buscar(1)">
            <option value="">Todos</option>
            <option value="retificado">Retificado</option>
            <option value="pendente">Pendente</option>
          </select>
        </div>
      </div>
      <div class="filter-actions">
        <button class="btn-clear" @click="limparFiltros">Limpar</button>
        <button class="btn-search" @click="buscar(1)" :disabled="loading">
          <svg
            width="16"
            height="16"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
          >
            <circle cx="11" cy="11" r="8" />
            <line x1="21" y1="21" x2="16.65" y2="16.65" />
          </svg>
          Buscar
        </button>
      </div>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="loading-container">
      <div class="loading-spinner"></div>
      <p class="text-slate-400 text-sm mt-3">Carregando dados dos funcionários...</p>
    </div>

    <!-- Results -->
    <div v-else-if="result" class="results-section">
      <div class="results-header">
        <span class="text-sm text-slate-400">
          {{ result.total }} CPF{{ result.total !== 1 ? 's' : '' }} encontrado{{
            result.total !== 1 ? 's' : ''
          }}
          <span v-if="filters.per_apur"> em {{ formatPeriodo(filters.per_apur) }}</span>
        </span>
      </div>

      <!-- Table -->
      <div class="results-table-wrapper" v-if="result.items.length">
        <table class="results-table">
          <thead>
            <tr>
              <th></th>
              <th>CPF</th>
              <th>Matrícula</th>
              <th>Categoria</th>
              <th>S-1200</th>
              <th>S-1210</th>
              <th>Valor Líq.</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            <template v-for="item in result.items" :key="item.cpf">
              <tr
                class="result-row"
                :class="{ 'result-row--expanded': expandedCpf === item.cpf }"
                @click="toggleExpand(item.cpf)"
              >
                <td>
                  <svg
                    :class="[
                      'expand-chevron',
                      { 'expand-chevron--open': expandedCpf === item.cpf },
                    ]"
                    width="14"
                    height="14"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    stroke-width="2"
                  >
                    <polyline points="9 18 15 12 9 6" />
                  </svg>
                </td>
                <td class="font-mono text-sm text-white">{{ formatCpf(item.cpf) }}</td>
                <td class="text-sm text-slate-300">{{ item.matricula || '—' }}</td>
                <td class="text-sm text-slate-400">{{ item.cod_categ || '—' }}</td>
                <td>
                  <span class="event-badge badge--blue">{{ item.qtd_s1200 }}</span>
                </td>
                <td>
                  <span class="event-badge badge--cyan">{{ item.qtd_s1210 }}</span>
                </td>
                <td class="text-sm text-slate-300">
                  {{
                    item.vr_liq
                      ? `R$ ${Number(item.vr_liq).toLocaleString('pt-BR', { minimumFractionDigits: 2 })}`
                      : '—'
                  }}
                </td>
                <td>
                  <span
                    :class="[
                      'status-badge',
                      item.retificado ? 'status-badge--done' : 'status-badge--pending',
                    ]"
                  >
                    {{ item.retificado ? 'Retificado' : 'Pendente' }}
                  </span>
                </td>
              </tr>

              <!-- Expanded detail row -->
              <tr v-if="expandedCpf === item.cpf" class="detail-row">
                <td :colspan="8">
                  <div class="detail-content">
                    <!-- Summary -->
                    <div class="detail-meta">
                      <div class="meta-item">
                        <span class="meta-label">DmDev S-1200</span>
                        <span class="meta-value">{{ item.ide_dm_dev_s1200 || '—' }}</span>
                      </div>
                      <div class="meta-item">
                        <span class="meta-label">Data Pagamento</span>
                        <span class="meta-value">{{ item.dt_pgto || '—' }}</span>
                      </div>
                      <div class="meta-item">
                        <span class="meta-label">Tipo CR</span>
                        <span class="meta-value">{{ item.tp_cr || '—' }}</span>
                      </div>
                      <div class="meta-item">
                        <span class="meta-label">Recibo S-1210</span>
                        <span class="meta-value font-mono text-xs">{{
                          item.nr_recibo_s1210 || '—'
                        }}</span>
                      </div>
                      <div class="meta-item">
                        <span class="meta-label">Último Processamento</span>
                        <span class="meta-value">{{
                          formatDateTime(item.ultimo_processamento)
                        }}</span>
                      </div>
                      <div class="meta-item" v-if="item.periodos">
                        <span class="meta-label">Períodos</span>
                        <span class="meta-value">{{
                          (item.periodos || []).map(formatPeriodo).join(', ')
                        }}</span>
                      </div>
                    </div>

                    <!-- Detailed events (lazy-loaded) -->
                    <div v-if="detailLoading" class="text-center py-4">
                      <div class="loading-spinner" style="width: 24px; height: 24px"></div>
                    </div>
                    <div v-else-if="detailEvents.length">
                      <h4
                        class="text-xs font-semibold text-[rgba(90,200,245,0.6)] uppercase tracking-wider mb-3 border-t border-[rgba(90,200,245,0.08)] pt-3"
                      >
                        Eventos Detalhados
                      </h4>
                      <div v-for="evt in detailEvents" :key="evt.id" class="detail-event-card">
                        <div class="detail-event-header">
                          <span :class="['event-badge', eventBadgeClass(evt.tipo_evento)]">{{
                            evt.tipo_evento
                          }}</span>
                          <span class="text-xs text-slate-400">{{ evt.arquivo_origem }}</span>
                          <span v-if="evt.nr_recibo" class="text-xs font-mono text-slate-500">{{
                            evt.nr_recibo
                          }}</span>
                        </div>
                        <div class="detail-event-fields">
                          <template v-for="(val, key) in flatDados(evt.dados_json)" :key="key">
                            <div class="meta-item" v-if="val">
                              <span class="meta-label">{{ key }}</span>
                              <span class="meta-value text-xs">{{ val }}</span>
                            </div>
                          </template>
                        </div>
                        <!-- Rubricas sub-table -->
                        <div v-if="evt.rubricas && evt.rubricas.length" class="rubricas-detail">
                          <table class="rubricas-table">
                            <thead>
                              <tr>
                                <th>CodRubr</th>
                                <th>TabRubr</th>
                                <th>NatRubr</th>
                                <th>IncIRRF</th>
                                <th>Valor</th>
                              </tr>
                            </thead>
                            <tbody>
                              <tr v-for="r in evt.rubricas" :key="r.id">
                                <td class="font-mono">{{ r.cod_rubr }}</td>
                                <td>{{ r.ide_tab_rubr || '—' }}</td>
                                <td>{{ r.nat_rubr || '—' }}</td>
                                <td>
                                  <span
                                    v-if="r.cod_inc_irrf === '11'"
                                    class="text-red-400 font-bold"
                                    >{{ r.cod_inc_irrf }}</span
                                  >
                                  <span v-else>{{ r.cod_inc_irrf || '—' }}</span>
                                </td>
                                <td class="text-right">
                                  {{
                                    r.vr_rubr
                                      ? Number(r.vr_rubr).toLocaleString('pt-BR', {
                                          minimumFractionDigits: 2,
                                        })
                                      : '—'
                                  }}
                                </td>
                              </tr>
                            </tbody>
                          </table>
                        </div>
                      </div>
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
        <p class="text-slate-400">Nenhum funcionário encontrado com os filtros atuais.</p>
        <p class="text-xs text-slate-500 mt-2">
          Importe XMLs na aba "Explorador de Eventos" para popular os dados.
        </p>
      </div>

      <!-- Pagination -->
      <div v-if="result.total_pages > 1" class="pagination">
        <button class="page-btn" :disabled="result.page <= 1" @click="buscar(result.page - 1)">
          ‹
        </button>
        <button
          v-for="p in visiblePages"
          :key="p"
          :class="['page-btn', { 'page-btn--active': p === result.page }]"
          @click="buscar(p)"
        >
          {{ p }}
        </button>
        <button
          class="page-btn"
          :disabled="result.page >= result.total_pages"
          @click="buscar(result.page + 1)"
        >
          ›
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { PYTHON_API } from '../lib/api'

const API = `${PYTHON_API}/api/explorador`

// ── State ──
const stats = ref<any>(null)
const result = ref<any>(null)
const loading = ref(false)
const expandedCpf = ref<string | null>(null)
const detailEvents = ref<any[]>([])
const detailLoading = ref(false)

const filters = ref({
  per_apur: '',
  cpf: '',
  status: '',
})

// ── Lifecycle ──
onMounted(async () => {
  await loadStats()
  await buscar(1)
})

// ── API calls ──
async function loadStats() {
  try {
    const params = new URLSearchParams()
    if (filters.value.per_apur) params.set('per_apur', filters.value.per_apur)
    const res = await fetch(`${API}/dados-funcionarios/estatisticas?${params}`)
    if (res.ok) stats.value = await res.json()
  } catch (e) {
    console.error('Erro ao carregar estatísticas:', e)
  }
}

async function buscar(page: number) {
  loading.value = true
  expandedCpf.value = null
  try {
    const params = new URLSearchParams({ page: String(page), page_size: '50' })
    if (filters.value.per_apur) params.set('per_apur', filters.value.per_apur)
    if (filters.value.cpf) params.set('cpf', filters.value.cpf.replace(/\D/g, ''))
    if (filters.value.status) params.set('status', filters.value.status)
    const res = await fetch(`${API}/dados-funcionarios?${params}`)
    if (res.ok) {
      result.value = await res.json()
    }
  } catch (e) {
    console.error('Erro ao buscar dados funcionários:', e)
  } finally {
    loading.value = false
  }
}

async function loadDetail(cpf: string) {
  detailLoading.value = true
  detailEvents.value = []
  try {
    const params = new URLSearchParams()
    if (filters.value.per_apur) params.set('per_apur', filters.value.per_apur)
    const res = await fetch(`${API}/dados-funcionarios/${cpf}?${params}`)
    if (res.ok) {
      detailEvents.value = await res.json()
    }
  } catch (e) {
    console.error('Erro ao carregar detalhe:', e)
  } finally {
    detailLoading.value = false
  }
}

function toggleExpand(cpf: string) {
  if (expandedCpf.value === cpf) {
    expandedCpf.value = null
    detailEvents.value = []
  } else {
    expandedCpf.value = cpf
    loadDetail(cpf)
  }
}

function onPeriodoChange() {
  loadStats()
  buscar(1)
}

function limparFiltros() {
  filters.value = { per_apur: '', cpf: '', status: '' }
  loadStats()
  buscar(1)
}

// ── Pagination ──
const visiblePages = computed(() => {
  if (!result.value) return []
  const total = result.value.total_pages
  const current = result.value.page
  const pages: number[] = []
  const start = Math.max(1, current - 3)
  const end = Math.min(total, current + 3)
  for (let i = start; i <= end; i++) pages.push(i)
  return pages
})

// ── Formatting helpers ──
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
    '',
    'Janeiro',
    'Fevereiro',
    'Março',
    'Abril',
    'Maio',
    'Junho',
    'Julho',
    'Agosto',
    'Setembro',
    'Outubro',
    'Novembro',
    'Dezembro',
  ]
  return `${months[parseInt(month)] || month}/${year}`
}

function formatDateTime(dt: string | null): string {
  if (!dt) return '—'
  try {
    const d = new Date(dt)
    return (
      d.toLocaleDateString('pt-BR') +
      ' ' +
      d.toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' })
    )
  } catch {
    return dt
  }
}

function eventBadgeClass(tipo: string): string {
  const map: Record<string, string> = {
    'S-1200': 'badge--blue',
    'S-1210': 'badge--cyan',
  }
  return map[tipo] ?? 'badge--slate'
}

function flatDados(dados: any): Record<string, string> {
  if (!dados) return {}
  const flat: Record<string, string> = {}
  for (const [key, val] of Object.entries(dados)) {
    if (typeof val === 'string' || typeof val === 'number') {
      flat[key] = String(val)
    }
  }
  return flat
}
</script>

<style scoped>
.dados-func-view {
  --brain-blue: #5ac8f5;
  --brain-glow: rgba(90, 200, 245, 0.55);
  --brain-dim: rgba(90, 200, 245, 0.25);
  --brain-faint: rgba(90, 200, 245, 0.08);
  --glass-bg: rgba(8, 14, 36, 0.75);
  --glass-border: rgba(90, 200, 245, 0.12);
  --surface-dark: #0a1024;
  max-width: 1200px;
}

/* ── Stats Cards ─────────────────────────────────── */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin-bottom: 24px;
}

@media (max-width: 900px) {
  .stats-grid {
    grid-template-columns: repeat(2, 1fr);
  }
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
.stat-card--success {
  border-color: rgba(16, 185, 129, 0.25) !important;
}
.stat-card--success:hover {
  box-shadow: 0 0 20px rgba(16, 185, 129, 0.1);
}

.stat-icon {
  width: 44px;
  height: 44px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.stat-icon svg {
  width: 22px;
  height: 22px;
}
.stat-icon--blue {
  background: rgba(0, 102, 255, 0.12);
  color: #4d9fff;
}
.stat-icon--cyan {
  background: rgba(90, 200, 245, 0.1);
  color: #5ac8f5;
}
.stat-icon--green {
  background: rgba(16, 185, 129, 0.1);
  color: #34d399;
}
.stat-icon--red {
  background: rgba(239, 68, 68, 0.1);
  color: #f87171;
}

.stat-value {
  font-size: 1.5rem;
  font-weight: 700;
  color: #fff;
  line-height: 1.2;
}
.stat-label {
  font-size: 0.75rem;
  color: #64748b;
  margin-top: 2px;
}

/* ── Filter Card ─────────────────────────────────── */
.filter-card {
  background: var(--glass-bg);
  backdrop-filter: blur(16px);
  border-radius: 16px;
  padding: 20px 24px;
  border: 1px solid var(--glass-border);
  margin-bottom: 24px;
  box-shadow:
    0 0 20px rgba(90, 200, 245, 0.04),
    0 8px 32px rgba(0, 0, 0, 0.3);
}

.filter-grid {
  display: grid;
  grid-template-columns: 1fr 2fr 1fr;
  gap: 14px;
  margin-bottom: 16px;
}
@media (max-width: 768px) {
  .filter-grid {
    grid-template-columns: 1fr;
  }
}

.filter-group {
  display: flex;
  flex-direction: column;
  gap: 5px;
}
.filter-label {
  font-size: 0.6875rem;
  font-weight: 600;
  color: rgba(90, 200, 245, 0.6);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.filter-input,
.filter-select {
  width: 100%;
  padding: 8px 12px;
  background: var(--surface-dark);
  border: 1px solid var(--glass-border);
  border-radius: 8px;
  color: #fff;
  font-size: 0.8125rem;
  outline: none;
  transition:
    border-color 0.25s ease,
    box-shadow 0.25s ease;
}
.filter-input:focus,
.filter-select:focus {
  border-color: var(--brain-blue);
  box-shadow: 0 0 12px rgba(90, 200, 245, 0.15);
}
.filter-select {
  appearance: none;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 24 24' fill='none' stroke='%2364748b' stroke-width='2'%3E%3Cpath d='M6 9l6 6 6-6'/%3E%3C/svg%3E");
  background-repeat: no-repeat;
  background-position: right 10px center;
  padding-right: 30px;
}
.filter-select option {
  background: #0a1024;
  color: #fff;
}

.filter-actions {
  display: flex;
  gap: 10px;
  justify-content: flex-end;
  padding-top: 14px;
  border-top: 1px solid rgba(90, 200, 245, 0.08);
}

.btn-search {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 22px;
  background: rgba(90, 200, 245, 0.15);
  border: 1px solid rgba(90, 200, 245, 0.3);
  border-radius: 10px;
  color: var(--brain-blue);
  font-size: 0.875rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.25s ease;
}
.btn-search:hover {
  background: rgba(90, 200, 245, 0.25);
  box-shadow: 0 0 18px rgba(90, 200, 245, 0.2);
}
.btn-search:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.btn-clear {
  padding: 8px 18px;
  background: transparent;
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 10px;
  color: #64748b;
  font-size: 0.8125rem;
  cursor: pointer;
  transition: all 0.25s ease;
}
.btn-clear:hover {
  color: #94a3b8;
  border-color: rgba(255, 255, 255, 0.2);
}

/* ── Loading ─────────────────────────────────────── */
.loading-container {
  text-align: center;
  padding: 48px 0;
}
.loading-spinner {
  width: 36px;
  height: 36px;
  border: 3px solid rgba(90, 200, 245, 0.15);
  border-top-color: var(--brain-blue);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
  margin: 0 auto;
}
@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

/* ── Results ─────────────────────────────────────── */
.results-section {
  margin-bottom: 32px;
}
.results-header {
  margin-bottom: 12px;
}

.results-table-wrapper {
  background: var(--glass-bg);
  backdrop-filter: blur(16px);
  border-radius: 14px;
  border: 1px solid var(--glass-border);
  overflow: hidden;
  box-shadow:
    0 0 20px rgba(90, 200, 245, 0.04),
    0 8px 32px rgba(0, 0, 0, 0.3);
}
.results-table {
  width: 100%;
  border-collapse: separate;
  border-spacing: 0;
}
.results-table thead tr {
  border-bottom: 1px solid rgba(90, 200, 245, 0.1);
}
.results-table th {
  padding: 12px 14px;
  text-align: left;
  font-size: 0.6875rem;
  font-weight: 600;
  color: rgba(90, 200, 245, 0.6);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  border-bottom: 1px solid rgba(90, 200, 245, 0.1);
}
.results-table td {
  padding: 10px 14px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.04);
}
.result-row {
  cursor: pointer;
  transition: background 0.2s ease;
}
.result-row:hover {
  background: rgba(90, 200, 245, 0.03);
}
.result-row--expanded {
  background: rgba(90, 200, 245, 0.05) !important;
}

/* ── Expand chevron ──────────────────────────────── */
.expand-chevron {
  transition: transform 0.2s ease;
  color: #64748b;
}
.expand-chevron--open {
  transform: rotate(90deg);
  color: var(--brain-blue);
}

/* ── Event badges ────────────────────────────────── */
.event-badge {
  display: inline-block;
  padding: 3px 8px;
  border-radius: 6px;
  font-size: 0.6875rem;
  font-weight: 700;
  font-family: monospace;
  letter-spacing: 0.02em;
}
.badge--blue {
  background: rgba(59, 130, 246, 0.15);
  color: #60a5fa;
  border: 1px solid rgba(59, 130, 246, 0.25);
}
.badge--cyan {
  background: rgba(90, 200, 245, 0.12);
  color: #5ac8f5;
  border: 1px solid rgba(90, 200, 245, 0.2);
}
.badge--slate {
  background: rgba(100, 116, 139, 0.12);
  color: #94a3b8;
  border: 1px solid rgba(100, 116, 139, 0.2);
}

/* ── Status badge ────────────────────────────────── */
.status-badge {
  display: inline-block;
  padding: 3px 10px;
  border-radius: 20px;
  font-size: 0.6875rem;
  font-weight: 600;
  letter-spacing: 0.02em;
}
.status-badge--done {
  background: rgba(16, 185, 129, 0.12);
  color: #34d399;
  border: 1px solid rgba(16, 185, 129, 0.25);
}
.status-badge--pending {
  background: rgba(245, 158, 11, 0.12);
  color: #fbbf24;
  border: 1px solid rgba(245, 158, 11, 0.2);
}

/* ── Detail row ──────────────────────────────────── */
.detail-row td {
  padding: 0 !important;
  border-bottom: 1px solid rgba(90, 200, 245, 0.08) !important;
}
.detail-content {
  padding: 16px 20px;
  background: rgba(90, 200, 245, 0.02);
}
.detail-meta {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 10px;
  margin-bottom: 16px;
}
.meta-item {
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.meta-label {
  font-size: 0.625rem;
  font-weight: 600;
  color: rgba(90, 200, 245, 0.5);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}
.meta-value {
  color: #cbd5e1;
  word-break: break-all;
}

/* ── Detail event cards ──────────────────────────── */
.detail-event-card {
  background: rgba(0, 0, 0, 0.2);
  border: 1px solid rgba(90, 200, 245, 0.08);
  border-radius: 10px;
  padding: 12px 16px;
  margin-bottom: 10px;
}
.detail-event-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 8px;
  flex-wrap: wrap;
}
.detail-event-fields {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
  gap: 8px;
  margin-bottom: 8px;
}

/* ── Rubricas detail ─────────────────────────────── */
.rubricas-detail {
  border-top: 1px solid rgba(90, 200, 245, 0.08);
  padding-top: 10px;
  margin-top: 8px;
}
.rubricas-table {
  width: 100%;
  border-collapse: separate;
  border-spacing: 0;
}
.rubricas-table th {
  padding: 6px 10px;
  font-size: 0.625rem;
  font-weight: 600;
  color: rgba(90, 200, 245, 0.5);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  text-align: left;
  border-bottom: 1px solid rgba(90, 200, 245, 0.08);
}
.rubricas-table td {
  padding: 6px 10px;
  font-size: 0.75rem;
  border-bottom: 1px solid rgba(255, 255, 255, 0.03);
}

/* ── Empty state ─────────────────────────────────── */
.empty-state {
  text-align: center;
  padding: 48px 0;
}

/* ── Pagination ──────────────────────────────────── */
.pagination {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
  margin-top: 16px;
}
.page-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  min-width: 36px;
  height: 36px;
  padding: 0 8px;
  border-radius: 8px;
  font-size: 0.8125rem;
  font-weight: 500;
  color: #94a3b8;
  border: 1px solid rgba(255, 255, 255, 0.08);
  background: transparent;
  cursor: pointer;
  transition: all 0.2s ease;
}
.page-btn:hover:not(:disabled) {
  color: #fff;
  border-color: rgba(90, 200, 245, 0.2);
}
.page-btn:disabled {
  opacity: 0.3;
  cursor: not-allowed;
}
.page-btn--active {
  color: var(--brain-blue);
  border-color: rgba(90, 200, 245, 0.3);
  background: rgba(90, 200, 245, 0.1);
}
</style>
