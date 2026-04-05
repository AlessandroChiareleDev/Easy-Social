<template>
  <div class="ebc-root">
    <!-- Header -->
    <div class="ebc-header">
      <div>
        <h1 class="ebc-title">EB Skills Cruzamentos</h1>
        <p class="ebc-subtitle">
          Tabela de cruzamento com incidências corretas e base legal (EB Skills / Datamace)
        </p>
      </div>
    </div>

    <!-- Cards resumo -->
    <div class="ebc-cards" v-if="resumo">
      <div class="ebc-card ebc-card-total">
        <div class="ebc-card-icon">📋</div>
        <div class="ebc-card-body">
          <span class="ebc-card-value">{{ resumo.total }}</span>
          <span class="ebc-card-label">Rubricas</span>
        </div>
      </div>
      <div class="ebc-card ebc-card-ok">
        <div class="ebc-card-icon">✅</div>
        <div class="ebc-card-body">
          <span class="ebc-card-value">{{ resumo.regulares }}</span>
          <span class="ebc-card-label">Regulares</span>
        </div>
      </div>
      <div class="ebc-card ebc-card-warn">
        <div class="ebc-card-icon">⚠️</div>
        <div class="ebc-card-body">
          <span class="ebc-card-value">{{ resumo.inconsistentes }}</span>
          <span class="ebc-card-label">Inconsistências</span>
        </div>
      </div>
      <div class="ebc-card ebc-card-done">
        <div class="ebc-card-icon">🔧</div>
        <div class="ebc-card-body">
          <span class="ebc-card-value">{{ resumo.corrigidos ?? 0 }}</span>
          <span class="ebc-card-label">Corrigidos</span>
        </div>
      </div>
    </div>

    <!-- Filtros -->
    <div class="ebc-toolbar">
      <div class="ebc-search">
        <svg class="ebc-search-icon" viewBox="0 0 24 24" width="18" height="18">
          <circle cx="11" cy="11" r="7" fill="none" stroke="currentColor" stroke-width="2" />
          <line x1="16.5" y1="16.5" x2="21" y2="21" stroke="currentColor" stroke-width="2" />
        </svg>
        <input
          v-model="searchQuery"
          type="text"
          placeholder="Buscar por código ou descrição..."
          class="ebc-search-input"
          @input="debouncedSearch"
        />
      </div>
      <div class="ebc-filter-tabs">
        <button
          :class="['ebc-filter-btn', { active: filtro === 'todas' }]"
          @click="setFiltro('todas')"
        >
          Todas
        </button>
        <button
          :class="['ebc-filter-btn ebc-filter-warn', { active: filtro === 'inconsistentes' }]"
          @click="setFiltro('inconsistentes')"
        >
          ⚠️ Inconsistentes
        </button>
        <button
          :class="['ebc-filter-btn ebc-filter-pending', { active: filtro === 'pendentes' }]"
          @click="setFiltro('pendentes')"
        >
          🔴 Pendentes
        </button>
        <button
          :class="['ebc-filter-btn ebc-filter-done', { active: filtro === 'corrigidos' }]"
          @click="setFiltro('corrigidos')"
        >
          🔧 Corrigidos
        </button>
        <button
          :class="['ebc-filter-btn ebc-filter-ok', { active: filtro === 'regulares' }]"
          @click="setFiltro('regulares')"
        >
          ✅ Regulares
        </button>
      </div>
    </div>

    <!-- Tabela -->
    <div class="ebc-table-wrap" v-if="!loading">
      <table class="ebc-table">
        <thead>
          <tr>
            <th class="ebc-th-action">Ação</th>
            <th class="ebc-th-status"></th>
            <th class="ebc-th-id">ID</th>
            <th class="ebc-th-rubrica">Rubrica</th>
            <th class="ebc-th-natureza">Cód. Natureza</th>
            <th class="ebc-th-code">INSS</th>
            <th class="ebc-th-code">IRRF</th>
            <th class="ebc-th-code">FGTS</th>
            <th class="ebc-th-legal">Incid./Base Legal INSS</th>
            <th class="ebc-th-legal">Incid./Base Legal IRRF</th>
            <th class="ebc-th-legal">Incid./Base Legal FGTS</th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="r in rubricas"
            :key="r.id"
            :class="[
              'ebc-row',
              r.corrigido ? 'ebc-row-done' : isInconsistente(r) ? 'ebc-row-warn' : 'ebc-row-ok',
            ]"
          >
            <td class="ebc-td-action">
              <button
                v-if="isInconsistente(r) && !r.corrigido"
                class="ebc-btn-done"
                :disabled="markingId === r.cod_rubrica"
                @click="toggleCorrigido(r)"
                title="Marcar como corrigido"
              >
                <svg
                  width="14"
                  height="14"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  stroke-width="2.5"
                  stroke-linecap="round"
                  stroke-linejoin="round"
                >
                  <polyline points="20 6 9 17 4 12" />
                </svg>
                {{ markingId === r.cod_rubrica ? '...' : 'Feito' }}
              </button>
              <button
                v-else-if="r.corrigido"
                class="ebc-btn-undo"
                :disabled="markingId === r.cod_rubrica"
                @click="toggleCorrigido(r)"
                title="Desmarcar correção"
              >
                <svg
                  width="14"
                  height="14"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  stroke-width="2"
                  stroke-linecap="round"
                  stroke-linejoin="round"
                >
                  <polyline points="1 4 1 10 7 10" />
                  <path d="M3.51 15a9 9 0 1 0 2.13-9.36L1 10" />
                </svg>
                {{ markingId === r.cod_rubrica ? '...' : 'Desfazer' }}
              </button>
            </td>
            <td class="ebc-td-status">
              <span v-if="r.corrigido" class="ebc-badge-done" title="Corrigido">🔧</span>
              <span
                v-else-if="isInconsistente(r)"
                class="ebc-badge-warn"
                title="Inconsistência encontrada"
                >⚠️</span
              >
              <span v-else class="ebc-badge-ok" title="Regular">✅</span>
            </td>
            <td class="ebc-td-id">{{ r.cod_rubrica }}</td>
            <td class="ebc-td-rubrica">{{ r.descricao }}</td>
            <td class="ebc-td-natureza">{{ r.cod_natureza }}</td>
            <td :class="['ebc-td-code', inssChanged(r) && !r.corrigido ? 'ebc-changed' : '']">
              {{ r.incid_inss }}
            </td>
            <td :class="['ebc-td-code', irrfChanged(r) && !r.corrigido ? 'ebc-changed' : '']">
              {{ r.incid_irrf }}
            </td>
            <td :class="['ebc-td-code', fgtsChanged(r) && !r.corrigido ? 'ebc-changed' : '']">
              {{ r.incid_fgts }}
            </td>
            <td
              :class="['ebc-td-legal', inssChanged(r) && !r.corrigido ? 'ebc-legal-highlight' : '']"
            >
              {{ r.incid_base_legal_inss }}
            </td>
            <td
              :class="['ebc-td-legal', irrfChanged(r) && !r.corrigido ? 'ebc-legal-highlight' : '']"
            >
              {{ r.incid_base_legal_irrf }}
            </td>
            <td
              :class="['ebc-td-legal', fgtsChanged(r) && !r.corrigido ? 'ebc-legal-highlight' : '']"
            >
              {{ r.incid_base_legal_fgts }}
            </td>
          </tr>
          <tr v-if="rubricas.length === 0">
            <td colspan="11" class="ebc-empty">Nenhuma rubrica encontrada</td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="ebc-loading">
      <div class="ebc-spinner"></div>
      <span>Carregando rubricas...</span>
    </div>

    <!-- Paginação -->
    <div class="ebc-pagination" v-if="totalPages > 1">
      <button class="ebc-page-btn" :disabled="page === 1" @click="goPage(1)" aria-label="Primeira página">«</button>
      <button class="ebc-page-btn" :disabled="page === 1" @click="goPage(page - 1)" aria-label="Página anterior">‹</button>
      <span class="ebc-page-info"
        >Página {{ page }} de {{ totalPages }} ({{ total }} rubricas)</span
      >
      <button class="ebc-page-btn" :disabled="page === totalPages" @click="goPage(page + 1)" aria-label="Próxima página">
        ›
      </button>
      <button class="ebc-page-btn" :disabled="page === totalPages" @click="goPage(totalPages)" aria-label="Última página">
        »
      </button>
    </div>

    <!-- Toast -->
    <Transition name="toast">
      <div v-if="toast" :class="['ebc-toast', toast.type]">{{ toast.msg }}</div>
    </Transition>

    <!-- Erro -->
    <div v-if="error" class="ebc-error">{{ error }}</div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import axios from 'axios'
import { PYTHON_API } from '@/lib/api'

// State
const resumo = ref<any>(null)
const rubricas = ref<any[]>([])
const loading = ref(false)
const error = ref('')
const page = ref(1)
const perPage = 50
const total = ref(0)
const totalPages = ref(0)
const searchQuery = ref('')
const filtro = ref('todas')
const markingId = ref<string | null>(null)
const toast = ref<{ msg: string; type: 'ok' | 'err' } | null>(null)

let debounceTimer: ReturnType<typeof setTimeout> | null = null

// ── Helpers ──
function extractCode(baseLegal: string): string {
  if (!baseLegal) return ''
  return (baseLegal.split(' - ')[0] ?? '').trim()
}

function isInconsistente(r: any): boolean {
  return inssChanged(r) || irrfChanged(r) || fgtsChanged(r)
}

function inssChanged(r: any): boolean {
  return r.incid_inss !== extractCode(r.incid_base_legal_inss)
}

function irrfChanged(r: any): boolean {
  return r.incid_irrf !== extractCode(r.incid_base_legal_irrf)
}

function fgtsChanged(r: any): boolean {
  return r.incid_fgts !== extractCode(r.incid_base_legal_fgts)
}

function showToast(msg: string, type: 'ok' | 'err') {
  toast.value = { msg, type }
  setTimeout(() => (toast.value = null), 3000)
}

// ── API ──
async function fetchResumo() {
  try {
    const { data } = await axios.get(`${PYTHON_API}/api/cruzamento-eb/resumo`)
    resumo.value = data
  } catch (e: any) {
    error.value = 'Erro ao carregar resumo: ' + (e.response?.data?.detail || e.message)
  }
}

async function fetchRubricas() {
  loading.value = true
  error.value = ''
  try {
    const { data } = await axios.get(`${PYTHON_API}/api/cruzamento-eb/rubricas`, {
      params: {
        page: page.value,
        per_page: perPage,
        search: searchQuery.value,
        filtro: filtro.value,
      },
    })
    rubricas.value = data.rubricas
    total.value = data.total
    totalPages.value = data.pages
  } catch (e: any) {
    error.value = 'Erro ao carregar rubricas: ' + (e.response?.data?.detail || e.message)
  } finally {
    loading.value = false
  }
}

async function toggleCorrigido(r: any) {
  markingId.value = r.cod_rubrica
  try {
    const endpoint = r.corrigido ? 'desmarcar-corrigido' : 'marcar-corrigido'
    const { data } = await axios.post(
      `${PYTHON_API}/api/cruzamento-eb/${endpoint}/${r.cod_rubrica}`,
    )
    if (data.success) {
      showToast(data.message, 'ok')
      await Promise.all([fetchResumo(), fetchRubricas()])
    } else {
      showToast(data.message, 'err')
    }
  } catch (e: any) {
    showToast('Erro: ' + (e.response?.data?.detail || e.message), 'err')
  } finally {
    markingId.value = null
  }
}

function setFiltro(f: string) {
  filtro.value = f
  page.value = 1
  fetchRubricas()
}

function goPage(p: number) {
  page.value = p
  fetchRubricas()
}

function debouncedSearch() {
  if (debounceTimer) clearTimeout(debounceTimer)
  debounceTimer = setTimeout(() => {
    page.value = 1
    fetchRubricas()
  }, 350)
}

onMounted(() => {
  fetchResumo()
  fetchRubricas()
})
</script>

<style scoped>
/* ═══════ Root ═══════ */
.ebc-root {
  padding: 28px 32px;
  max-width: 100%;
  overflow-x: auto;
  color: #e2e8f0;
  animation: fadeIn 300ms ease;
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

/* ═══════ Header ═══════ */
.ebc-header {
  margin-bottom: 24px;
}

.ebc-title {
  font-size: 1.5rem;
  font-weight: 700;
  color: #fff;
  margin: 0;
}

.ebc-subtitle {
  color: #8892b0;
  margin: 6px 0 0;
  font-size: 0.85rem;
}

/* ═══════ Summary Cards ═══════ */
.ebc-cards {
  display: flex;
  gap: 16px;
  margin-bottom: 24px;
  flex-wrap: wrap;
}

.ebc-card {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 18px 22px;
  border-radius: 12px;
  min-width: 180px;
  flex: 1;
  transition:
    transform 0.2s,
    box-shadow 0.2s;
}

.ebc-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
}

.ebc-card-total {
  background: rgba(0, 102, 255, 0.08);
  border: 1px solid rgba(0, 102, 255, 0.2);
}

.ebc-card-ok {
  background: rgba(52, 211, 153, 0.08);
  border: 1px solid rgba(52, 211, 153, 0.2);
}

.ebc-card-warn {
  background: rgba(251, 191, 36, 0.08);
  border: 1px solid rgba(251, 191, 36, 0.2);
}

.ebc-card-done {
  background: rgba(168, 85, 247, 0.08);
  border: 1px solid rgba(168, 85, 247, 0.2);
}

.ebc-card-done .ebc-card-value {
  color: #a855f7;
}

.ebc-card-icon {
  font-size: 1.8rem;
}

.ebc-card-value {
  display: block;
  font-size: 1.6rem;
  font-weight: 700;
  color: #fff;
}

.ebc-card-total .ebc-card-value {
  color: #60a5fa;
}

.ebc-card-ok .ebc-card-value {
  color: #34d399;
}

.ebc-card-warn .ebc-card-value {
  color: #fbbf24;
}

.ebc-card-label {
  display: block;
  font-size: 0.75rem;
  color: #8892b0;
  text-transform: uppercase;
  letter-spacing: 0.6px;
  font-weight: 500;
}

/* ═══════ Toolbar ═══════ */
.ebc-toolbar {
  display: flex;
  gap: 16px;
  margin-bottom: 20px;
  flex-wrap: wrap;
  align-items: center;
}

.ebc-search {
  position: relative;
  flex: 1;
  min-width: 250px;
}

.ebc-search-icon {
  position: absolute;
  left: 14px;
  top: 50%;
  transform: translateY(-50%);
  color: #8892b0;
}

.ebc-search-input {
  width: 100%;
  padding: 10px 14px 10px 40px;
  border: 1px solid rgba(0, 102, 255, 0.2);
  border-radius: 8px;
  font-size: 0.88rem;
  outline: none;
  background: #111b3a;
  color: #e2e8f0;
  transition: all 0.2s;
}

.ebc-search-input::placeholder {
  color: #5a6580;
}

.ebc-search-input:focus {
  border-color: #0066ff;
  box-shadow: 0 0 0 3px rgba(0, 102, 255, 0.15);
}

.ebc-filter-tabs {
  display: flex;
  gap: 6px;
}

.ebc-filter-btn {
  padding: 8px 16px;
  border: 1px solid rgba(0, 102, 255, 0.2);
  border-radius: 8px;
  background: rgba(0, 102, 255, 0.06);
  color: #8892b0;
  cursor: pointer;
  font-size: 0.84rem;
  font-weight: 500;
  transition: all 0.2s;
}

.ebc-filter-btn:hover {
  background: rgba(0, 102, 255, 0.12);
  color: #e2e8f0;
}

.ebc-filter-btn.active {
  background: linear-gradient(135deg, #0066ff 0%, #0044cc 100%);
  color: #fff;
  border-color: #0066ff;
  box-shadow: 0 2px 10px rgba(0, 102, 255, 0.3);
}

.ebc-filter-warn.active {
  background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
  border-color: #f59e0b;
  box-shadow: 0 2px 10px rgba(245, 158, 11, 0.3);
}

.ebc-filter-ok.active {
  background: linear-gradient(135deg, #34d399 0%, #059669 100%);
  border-color: #34d399;
  box-shadow: 0 2px 10px rgba(52, 211, 153, 0.3);
}

.ebc-filter-done.active {
  background: linear-gradient(135deg, #a855f7 0%, #7c3aed 100%);
  border-color: #a855f7;
  box-shadow: 0 2px 10px rgba(168, 85, 247, 0.3);
}

.ebc-filter-pending.active {
  background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
  border-color: #ef4444;
  box-shadow: 0 2px 10px rgba(239, 68, 68, 0.3);
}

/* ═══════ Table ═══════ */
.ebc-table-wrap {
  overflow-x: auto;
  background: rgba(13, 21, 48, 0.6);
  border: 1px solid rgba(0, 102, 255, 0.12);
  border-radius: 10px;
}

.ebc-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.82rem;
}

.ebc-table thead {
  position: sticky;
  top: 0;
  z-index: 1;
}

.ebc-table th {
  padding: 10px 12px;
  text-align: left;
  font-weight: 600;
  color: #8892b0;
  background: #111b3a;
  border-bottom: 1px solid rgba(0, 102, 255, 0.15);
  white-space: nowrap;
  font-size: 0.78rem;
  text-transform: uppercase;
  letter-spacing: 0.3px;
}

.ebc-th-status {
  width: 36px;
  text-align: center;
}

.ebc-th-id {
  width: 60px;
}

.ebc-th-rubrica {
  min-width: 180px;
}

.ebc-th-natureza {
  min-width: 200px;
}

.ebc-th-code {
  width: 60px;
  text-align: center;
}

.ebc-th-legal {
  min-width: 250px;
}

.ebc-th-action {
  width: 90px;
  text-align: center;
  position: sticky;
  left: 0;
  z-index: 3;
  background: #111b3a;
}

.ebc-table td {
  padding: 9px 12px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.04);
  vertical-align: top;
}

.ebc-td-status {
  text-align: center;
  font-size: 1.1rem;
}

.ebc-td-id {
  font-weight: 600;
  color: #0066ff;
}

.ebc-td-rubrica {
  color: #e2e8f0;
  font-weight: 500;
}

.ebc-td-natureza {
  color: #8892b0;
  font-size: 0.78rem;
}

.ebc-td-code {
  text-align: center;
  font-weight: 600;
  font-family: 'Consolas', 'Monaco', monospace;
  color: #c8d0e0;
}

.ebc-td-legal {
  font-size: 0.78rem;
  color: #8892b0;
}

/* ═══════ Row states ═══════ */
.ebc-row-ok:hover td {
  background: rgba(0, 102, 255, 0.04);
}

.ebc-row-warn {
  background: rgba(251, 191, 36, 0.04);
}

.ebc-row-warn:hover td {
  background: rgba(251, 191, 36, 0.08);
}

.ebc-row-done {
  background: rgba(168, 85, 247, 0.04);
  opacity: 0.7;
}

.ebc-row-done:hover {
  opacity: 1;
}

.ebc-row-done:hover td {
  background: rgba(168, 85, 247, 0.08);
}

.ebc-row-done .ebc-td-rubrica,
.ebc-row-done .ebc-td-id {
  text-decoration: line-through;
  text-decoration-color: rgba(168, 85, 247, 0.5);
}

/* ═══════ Changed cell highlights ═══════ */
.ebc-changed {
  color: #f87171 !important;
  background: rgba(248, 113, 113, 0.1);
  font-weight: 700;
}

.ebc-legal-highlight {
  background: rgba(52, 211, 153, 0.1);
  color: #34d399 !important;
  font-weight: 600;
}

/* ═══════ Pagination ═══════ */
.ebc-pagination {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  margin-top: 16px;
  padding: 12px;
}

.ebc-page-btn {
  padding: 6px 12px;
  border: 1px solid rgba(0, 102, 255, 0.2);
  border-radius: 6px;
  background: rgba(0, 102, 255, 0.1);
  color: #0066ff;
  cursor: pointer;
  font-size: 0.85rem;
  font-weight: 500;
  transition: all 0.2s;
}

.ebc-page-btn:hover:not(:disabled) {
  background: rgba(0, 102, 255, 0.2);
}

.ebc-page-btn:disabled {
  opacity: 0.3;
  cursor: default;
}

.ebc-page-info {
  color: #8892b0;
  font-size: 0.82rem;
  padding: 0 8px;
}

/* ═══════ Empty & Loading ═══════ */
.ebc-empty {
  text-align: center;
  padding: 40px !important;
  color: #8892b0;
  font-size: 0.95rem;
}

.ebc-loading {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  padding: 60px;
  color: #8892b0;
}

.ebc-spinner {
  width: 24px;
  height: 24px;
  border: 3px solid rgba(0, 102, 255, 0.2);
  border-top-color: #0066ff;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.ebc-error {
  margin-top: 16px;
  padding: 12px 16px;
  background: rgba(248, 113, 113, 0.1);
  border: 1px solid rgba(248, 113, 113, 0.25);
  border-radius: 8px;
  color: #f87171;
  font-size: 0.88rem;
}

/* ═══════ Action buttons ═══════ */
.ebc-td-action {
  text-align: center;
  white-space: nowrap;
  position: sticky;
  left: 0;
  z-index: 2;
  background: #0d1530;
}

.ebc-row-warn .ebc-td-action {
  background: rgba(13, 21, 48, 0.97);
}

.ebc-row-done .ebc-td-action {
  background: rgba(13, 21, 48, 0.97);
}

.ebc-btn-done {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 5px 12px;
  border-radius: 6px;
  border: 1px solid rgba(52, 211, 153, 0.3);
  background: rgba(52, 211, 153, 0.1);
  color: #34d399;
  font-size: 0.75rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.ebc-btn-done:hover:not(:disabled) {
  background: rgba(52, 211, 153, 0.2);
  border-color: rgba(52, 211, 153, 0.5);
  box-shadow: 0 2px 8px rgba(52, 211, 153, 0.2);
}

.ebc-btn-done:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.ebc-btn-undo {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 5px 12px;
  border-radius: 6px;
  border: 1px solid rgba(168, 85, 247, 0.3);
  background: rgba(168, 85, 247, 0.1);
  color: #a855f7;
  font-size: 0.75rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.ebc-btn-undo:hover:not(:disabled) {
  background: rgba(168, 85, 247, 0.2);
  border-color: rgba(168, 85, 247, 0.5);
}

.ebc-btn-undo:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* ═══════ Toast ═══════ */
.ebc-toast {
  position: fixed;
  bottom: 24px;
  right: 24px;
  padding: 12px 24px;
  border-radius: 8px;
  font-size: 0.85rem;
  font-weight: 500;
  z-index: 1000;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.4);
}

.ebc-toast.ok {
  background: rgba(52, 211, 153, 0.15);
  border: 1px solid rgba(52, 211, 153, 0.3);
  color: #34d399;
}

.ebc-toast.err {
  background: rgba(248, 113, 113, 0.15);
  border: 1px solid rgba(248, 113, 113, 0.3);
  color: #f87171;
}

.toast-enter-active,
.toast-leave-active {
  transition: all 0.3s;
}

.toast-enter-from,
.toast-leave-to {
  opacity: 0;
  transform: translateY(20px);
}
</style>
