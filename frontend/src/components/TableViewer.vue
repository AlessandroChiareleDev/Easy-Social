<template>
  <div class="table-viewer" :class="{ 'is-fullscreen': isFullscreen }">
    <!-- ── Toolbar ── -->
    <div class="toolbar">
      <div class="toolbar-left">
        <div class="select-wrapper">
          <select v-model="selectedTable" @change="selectTab(selectedTable)" class="table-select">
            <option v-for="tab in tabs" :key="tab.key" :value="tab.key">{{ tab.label }}</option>
          </select>
          <svg
            class="select-chevron"
            width="12"
            height="12"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2.5"
            stroke-linecap="round"
            stroke-linejoin="round"
          >
            <polyline points="6 9 12 15 18 9" />
          </svg>
        </div>
        <span v-if="totalItems > 0" class="record-count">{{ totalItems }} registros</span>
        <button
          v-if="hasActiveFilters"
          class="btn-clear-filters"
          @click="clearAllFilters"
          title="Limpar todos os filtros"
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
            <line x1="18" y1="6" x2="6" y2="18" />
            <line x1="6" y1="6" x2="18" y2="18" />
          </svg>
          Limpar filtros
        </button>
      </div>
      <div class="toolbar-right">
        <button
          v-if="selectedTable && tableData.length > 0"
          class="btn-icon"
          @click="toggleFullscreen"
          :title="isFullscreen ? 'Sair do fullscreen' : 'Expandir'"
        >
          <svg
            v-if="!isFullscreen"
            width="16"
            height="16"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
            stroke-linecap="round"
            stroke-linejoin="round"
          >
            <polyline points="15 3 21 3 21 9" />
            <polyline points="9 21 3 21 3 15" />
            <line x1="21" y1="3" x2="14" y2="10" />
            <line x1="3" y1="21" x2="10" y2="14" />
          </svg>
          <svg
            v-else
            width="16"
            height="16"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
            stroke-linecap="round"
            stroke-linejoin="round"
          >
            <polyline points="4 14 10 14 10 20" />
            <polyline points="20 10 14 10 14 4" />
            <line x1="14" y1="10" x2="21" y2="3" />
            <line x1="3" y1="21" x2="10" y2="14" />
          </svg>
        </button>
        <button
          v-if="selectedTable && tableData.length > 0"
          class="btn-icon btn-icon-danger"
          @click="showDeleteModal = true"
          title="Excluir tabela"
        >
          <svg
            width="16"
            height="16"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
            stroke-linecap="round"
            stroke-linejoin="round"
          >
            <polyline points="3 6 5 6 21 6" />
            <path
              d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"
            />
          </svg>
        </button>
        <button
          v-if="selectedTable && tableData.length > 0"
          class="btn-download"
          @click="downloadXlsx"
          :disabled="downloading"
        >
          {{ downloading ? 'Baixando...' : '⬇ XLSX' }}
        </button>
      </div>
    </div>

    <!-- Fullscreen zoom controls -->
    <div v-if="isFullscreen" class="zoom-bar">
      <button @click="zoomOut" :disabled="zoomLevel <= 0.5">−</button>
      <span>{{ Math.round(zoomLevel * 100) }}%</span>
      <button @click="zoomIn" :disabled="zoomLevel >= 2">+</button>
      <button class="btn-zoom-reset" @click="zoomLevel = 1">Reset</button>
      <span class="zoom-hint">Arraste bordas das colunas para redimensionar</span>
    </div>

    <div v-if="loading" class="loading">
      <div class="loading-spinner"></div>
      <span>Carregando...</span>
    </div>

    <div v-if="!loading && tableData.length === 0 && !error" class="empty-state">
      <span class="empty-icon">📋</span>
      <p>Nenhum dado disponível nesta tabela</p>
    </div>

    <div v-if="tableData.length > 0" class="table-card" :class="{ 'fs-table': isFullscreen }">
      <div class="table-scroll">
        <table :style="isFullscreen ? { fontSize: 12 * zoomLevel + 'px' } : {}">
          <thead>
            <tr>
              <th
                v-for="(col, index) in columns"
                :key="index"
                :style="
                  colWidths[index]
                    ? { width: colWidths[index] + 'px', minWidth: colWidths[index] + 'px' }
                    : {}
                "
              >
                {{ col.name }}
                <div
                  v-if="isFullscreen"
                  class="col-resizer"
                  @mousedown.prevent="startResize($event, index)"
                ></div>
              </th>
            </tr>
            <tr class="filter-row">
              <th v-for="(col, index) in columns" :key="'f' + index" class="filter-cell">
                <div class="filter-input-wrapper">
                  <svg
                    class="filter-icon"
                    width="12"
                    height="12"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    stroke-width="2"
                    stroke-linecap="round"
                    stroke-linejoin="round"
                  >
                    <circle cx="11" cy="11" r="8" />
                    <line x1="21" y1="21" x2="16.65" y2="16.65" />
                  </svg>
                  <input
                    type="text"
                    class="filter-input"
                    :placeholder="'Filtrar...'"
                    :value="columnFilters[col.letter.toLowerCase()] || ''"
                    @input="
                      onFilterInput(
                        col.letter.toLowerCase(),
                        ($event.target as HTMLInputElement).value,
                      )
                    "
                  />
                  <button
                    v-if="columnFilters[col.letter.toLowerCase()]"
                    class="filter-clear"
                    @click="clearFilter(col.letter.toLowerCase())"
                  >
                    <svg
                      width="10"
                      height="10"
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                      stroke-width="3"
                      stroke-linecap="round"
                    >
                      <line x1="18" y1="6" x2="6" y2="18" />
                      <line x1="6" y1="6" x2="18" y2="18" />
                    </svg>
                  </button>
                </div>
              </th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(row, rowIndex) in tableData" :key="rowIndex">
              <td v-for="(col, colIndex) in columns" :key="colIndex">
                {{ row[`col_${col.letter.toLowerCase()}`] || '-' }}
              </td>
            </tr>
          </tbody>
        </table>
      </div>
      <div class="pagination">
        <button class="pg-btn" @click="prevPage" :disabled="currentPage === 1">
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
            <polyline points="15 18 9 12 15 6" />
          </svg>
        </button>
        <span class="pg-info">{{ currentPage }} / {{ totalPages }}</span>
        <button class="pg-btn" @click="nextPage" :disabled="currentPage === totalPages">
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
            <polyline points="9 18 15 12 9 6" />
          </svg>
        </button>
      </div>
    </div>

    <div v-if="error" class="error-message">❌ {{ error }}</div>

    <!-- Delete confirmation modal -->
    <Teleport to="body">
      <Transition name="modal-fade">
        <div v-if="showDeleteModal" class="modal-overlay" @click.self="showDeleteModal = false">
          <div class="modal-box">
            <h3>Excluir tabela</h3>
            <p>
              Tem certeza que deseja excluir todos os dados de
              <strong>{{ formatTableName(selectedTable) }}</strong
              >?
            </p>
            <p class="modal-warning">
              Esta ação não pode ser desfeita. Digite <code>delete</code> para confirmar.
            </p>
            <input
              v-model="deleteConfirmText"
              class="modal-input"
              placeholder="Digite delete"
              @keydown.enter="confirmDelete"
            />
            <div class="modal-actions">
              <button class="btn-cancel" @click="cancelDelete">Cancelar</button>
              <button
                class="btn-confirm-delete"
                :disabled="deleteConfirmText !== 'delete' || deleting"
                @click="confirmDelete"
              >
                {{ deleting ? 'Excluindo...' : 'Excluir' }}
              </button>
            </div>
          </div>
        </div>
      </Transition>
    </Teleport>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import axios from 'axios'
import * as XLSX from 'xlsx'
import { API_URL } from '@/lib/api'

const allTabs = [
  { key: 'analise_natureza', label: 'Análise Natureza' },
  { key: 'analise_natureza_certo', label: 'Análise Natureza (Certa)' },
  { key: 'dinamica', label: 'Dinâmica' },
  { key: 'tabela_eventos_gl', label: 'Tabela Eventos GI' },
  { key: 'tabela_eb', label: 'Tabela EB' },
  { key: 'tabela_cruzamento', label: 'Tabela Cruzamento' },
  { key: 'tabela3_esocial_oficial', label: 'Tabela 3 E-Social Oficial' },
]

const tabs = ref([...allTabs])
const selectedTable = ref(allTabs[0]!.key)
const tableData = ref<any[]>([])
const columns = ref<{ letter: string; name: string }[]>([])
const loading = ref(false)
const error = ref<string | null>(null)

const currentPage = ref(1)
const itemsPerPage = 100
const totalItems = ref(0)
const totalPages = ref(1)
const downloading = ref(false)

// Column filters
const columnFilters = ref<Record<string, string>>({})
let filterDebounceTimer: ReturnType<typeof setTimeout> | null = null

const hasActiveFilters = computed(() => {
  return Object.values(columnFilters.value).some((v) => v.trim() !== '')
})

function onFilterInput(colLetter: string, value: string) {
  columnFilters.value = { ...columnFilters.value, [colLetter]: value }
  if (filterDebounceTimer) clearTimeout(filterDebounceTimer)
  filterDebounceTimer = setTimeout(() => {
    currentPage.value = 1
    loadTableData()
  }, 400)
}

function clearFilter(colLetter: string) {
  const newFilters = { ...columnFilters.value }
  delete newFilters[colLetter]
  columnFilters.value = newFilters
  currentPage.value = 1
  loadTableData()
}

function clearAllFilters() {
  columnFilters.value = {}
  currentPage.value = 1
  loadTableData()
}

// Delete modal
const showDeleteModal = ref(false)
const deleteConfirmText = ref('')
const deleting = ref(false)

function cancelDelete() {
  showDeleteModal.value = false
  deleteConfirmText.value = ''
}

// Fullscreen
const isFullscreen = ref(false)
const zoomLevel = ref(0.8)
const colWidths = ref<Record<number, number>>({})

// Column resize state
let resizingCol = -1
let resizeStartX = 0
let resizeStartW = 0

const selectTab = (key: string) => {
  selectedTable.value = key
  currentPage.value = 1
  colWidths.value = {}
  columnFilters.value = {}
  loadTableData()
}

const loadTableData = async () => {
  if (!selectedTable.value) return

  loading.value = true
  error.value = null

  try {
    if (currentPage.value === 1) {
      const colRes = await axios.get(`${API_URL}/tables/${selectedTable.value}/columns`)
      columns.value = colRes.data.columns
    }

    const offset = (currentPage.value - 1) * itemsPerPage
    const params: Record<string, string | number> = {
      limit: itemsPerPage,
      offset,
    }

    // Add column filters to query params
    for (const [letter, value] of Object.entries(columnFilters.value)) {
      if (value.trim()) {
        params[`filter_col_${letter}`] = value.trim()
      }
    }

    const response = await axios.get(`${API_URL}/tables/${selectedTable.value}`, { params })
    tableData.value = response.data.data
    totalItems.value = response.data.total
    totalPages.value = Math.ceil(totalItems.value / itemsPerPage)
  } catch (err: any) {
    error.value = err.response?.data?.error || 'Erro ao carregar tabela'
  } finally {
    loading.value = false
  }
}

const formatTableName = (key: string) => {
  return allTabs.find((t) => t.key === key)?.label || key
}

const nextPage = () => {
  if (currentPage.value < totalPages.value) {
    currentPage.value++
    loadTableData()
  }
}

const prevPage = () => {
  if (currentPage.value > 1) {
    currentPage.value--
    loadTableData()
  }
}

const downloadXlsx = async () => {
  if (!selectedTable.value) return

  downloading.value = true
  try {
    const response = await axios.get(`${API_URL}/tables/${selectedTable.value}/export`)
    const { data, columns: cols } = response.data

    // Montar dados com nomes reais das colunas
    const rows = data.map((row: any) => {
      const obj: any = {}
      for (const col of cols) {
        obj[col.name] = row[`col_${col.letter.toLowerCase()}`] || ''
      }
      return obj
    })

    const ws = XLSX.utils.json_to_sheet(rows)
    const wb = XLSX.utils.book_new()
    XLSX.utils.book_append_sheet(wb, ws, formatTableName(selectedTable.value))
    XLSX.writeFile(wb, `${formatTableName(selectedTable.value)}.xlsx`)
  } catch (err: any) {
    error.value = err.response?.data?.error || 'Erro ao exportar tabela'
  } finally {
    downloading.value = false
  }
}

// ── Delete table ──
const confirmDelete = async () => {
  if (deleteConfirmText.value !== 'delete') return
  deleting.value = true
  try {
    await axios.delete(`${API_URL}/tables/${selectedTable.value}`, {
      data: { confirmation: 'delete' },
    })
    const deletedKey = selectedTable.value
    showDeleteModal.value = false
    deleteConfirmText.value = ''
    tableData.value = []
    columns.value = []
    totalItems.value = 0
    totalPages.value = 1
    currentPage.value = 1
    // Remove the tab and switch to first remaining
    tabs.value = tabs.value.filter((t) => t.key !== deletedKey)
    selectedTable.value = tabs.value[0]?.key || ''
    if (selectedTable.value) await loadTableData()
  } catch (err: any) {
    error.value = err.response?.data?.error || 'Erro ao excluir tabela'
  } finally {
    deleting.value = false
  }
}

// ── Fullscreen ──
const toggleFullscreen = () => {
  isFullscreen.value = !isFullscreen.value
  if (!isFullscreen.value) {
    colWidths.value = {}
    zoomLevel.value = 0.8
  }
}

const zoomIn = () => {
  zoomLevel.value = Math.min(2, +(zoomLevel.value + 0.1).toFixed(1))
}
const zoomOut = () => {
  zoomLevel.value = Math.max(0.5, +(zoomLevel.value - 0.1).toFixed(1))
}

// ── Column resize (Excel-like) ──
const startResize = (e: MouseEvent, colIndex: number) => {
  resizingCol = colIndex
  resizeStartX = e.clientX
  const th = (e.target as HTMLElement).parentElement!
  resizeStartW = th.offsetWidth
  document.addEventListener('mousemove', onResizeMove)
  document.addEventListener('mouseup', onResizeEnd)
}

const onResizeMove = (e: MouseEvent) => {
  if (resizingCol < 0) return
  const diff = e.clientX - resizeStartX
  const newW = Math.max(40, resizeStartW + diff)
  colWidths.value = { ...colWidths.value, [resizingCol]: newW }
}

const onResizeEnd = () => {
  resizingCol = -1
  document.removeEventListener('mousemove', onResizeMove)
  document.removeEventListener('mouseup', onResizeEnd)
}

// Esc to exit fullscreen
const onKeydown = (e: KeyboardEvent) => {
  if (e.key === 'Escape' && isFullscreen.value) {
    isFullscreen.value = false
    colWidths.value = {}
    zoomLevel.value = 0.8
  }
}

onMounted(async () => {
  document.addEventListener('keydown', onKeydown)
  // Only show tabs for tables that have data
  const available: typeof allTabs = []
  for (const tab of allTabs) {
    try {
      const res = await axios.get(`${API_URL}/tables/${tab.key}?limit=1&offset=0`)
      if (res.data.total > 0) available.push(tab)
    } catch {
      // skip
    }
  }
  if (available.length > 0) {
    tabs.value = available
    selectedTable.value = available[0]!.key
  }
  await loadTableData()
})

onBeforeUnmount(() => {
  document.removeEventListener('keydown', onKeydown)
  document.removeEventListener('mousemove', onResizeMove)
  document.removeEventListener('mouseup', onResizeEnd)
})
</script>

<style scoped>
.table-viewer {
  color: #e2e8f0;
}

/* ── Fullscreen overlay ── */
.table-viewer.is-fullscreen {
  position: fixed;
  inset: 0;
  z-index: 9999;
  background: #0a1024;
  padding: 0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}
.is-fullscreen .toolbar {
  padding: 10px 16px;
  border-radius: 0;
  margin-bottom: 0;
  flex-shrink: 0;
}
.is-fullscreen .table-card {
  flex: 1;
  margin-top: 0;
  border-radius: 0;
  border: none;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}
.is-fullscreen .table-scroll {
  flex: 1;
  overflow: auto;
}
.is-fullscreen .fs-table {
  max-height: none;
}

/* ── Toolbar ── */
.toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: #111b3a;
  border: 1px solid rgba(0, 102, 255, 0.12);
  border-radius: 10px;
  padding: 10px 16px;
  margin-bottom: 12px;
  gap: 12px;
}
.toolbar-left {
  display: flex;
  align-items: center;
  gap: 14px;
  min-width: 0;
}
.toolbar-right {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
}

/* ── Select dropdown ── */
.select-wrapper {
  position: relative;
  display: inline-flex;
  align-items: center;
}
.table-select {
  appearance: none;
  -webkit-appearance: none;
  background: rgba(0, 102, 255, 0.08);
  border: 1px solid rgba(0, 102, 255, 0.2);
  color: #e2e8f0;
  padding: 8px 36px 8px 14px;
  border-radius: 8px;
  font-size: 0.85rem;
  font-weight: 600;
  cursor: pointer;
  outline: none;
  transition: all 0.2s;
  min-width: 200px;
}
.table-select:hover {
  border-color: rgba(0, 102, 255, 0.4);
  background: rgba(0, 102, 255, 0.12);
}
.table-select:focus {
  border-color: #0066ff;
  box-shadow: 0 0 0 2px rgba(0, 102, 255, 0.15);
}
.table-select option {
  background: #111b3a;
  color: #e2e8f0;
  padding: 8px;
}
.select-chevron {
  position: absolute;
  right: 12px;
  color: #64748b;
  pointer-events: none;
}

.record-count {
  font-size: 0.78rem;
  color: #64748b;
  background: rgba(0, 102, 255, 0.06);
  padding: 4px 10px;
  border-radius: 12px;
  white-space: nowrap;
}

/* ── Icon buttons ── */
.btn-icon {
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.08);
  color: #64748b;
  width: 34px;
  height: 34px;
  border-radius: 8px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
}
.btn-icon:hover {
  color: #e2e8f0;
  background: rgba(0, 102, 255, 0.12);
  border-color: rgba(0, 102, 255, 0.25);
}
.btn-icon-danger:hover {
  color: #f87171;
  border-color: rgba(248, 113, 113, 0.3);
  background: rgba(248, 113, 113, 0.08);
}

.btn-download {
  background: #0066ff;
  color: white;
  padding: 7px 14px;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-size: 0.78rem;
  font-weight: 600;
  white-space: nowrap;
  transition: all 0.2s;
}
.btn-download:hover {
  background: #0055dd;
}
.btn-download:disabled {
  background: #1e293b;
  color: #475569;
  cursor: not-allowed;
}

/* ── Zoom bar ── */
.zoom-bar {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 16px;
  background: rgba(0, 102, 255, 0.04);
  border-bottom: 1px solid rgba(0, 102, 255, 0.1);
  flex-shrink: 0;
  font-size: 0.78rem;
  color: #8892b0;
}
.zoom-bar button {
  background: rgba(0, 102, 255, 0.1);
  border: 1px solid rgba(0, 102, 255, 0.18);
  color: #0066ff;
  width: 28px;
  height: 28px;
  border-radius: 6px;
  font-size: 1rem;
  font-weight: 700;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
}
.zoom-bar button:disabled {
  opacity: 0.3;
  cursor: not-allowed;
}
.btn-zoom-reset {
  width: auto !important;
  padding: 0 10px !important;
  font-size: 0.72rem !important;
  font-weight: 500 !important;
}
.zoom-hint {
  margin-left: auto;
  color: #475569;
  font-size: 0.72rem;
}

/* ── Loading ── */
.loading {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  padding: 48px 20px;
  color: #64748b;
  font-size: 0.85rem;
}
.loading-spinner {
  width: 18px;
  height: 18px;
  border: 2px solid rgba(0, 102, 255, 0.15);
  border-top-color: #0066ff;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}
@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

/* ── Empty state ── */
.empty-state {
  text-align: center;
  padding: 48px 20px;
  color: #475569;
}
.empty-icon {
  font-size: 2rem;
  display: block;
  margin-bottom: 8px;
  opacity: 0.5;
}
.empty-state p {
  margin: 0;
  font-size: 0.85rem;
}

/* ── Table card ── */
.table-card {
  background: #0d1530;
  border: 1px solid rgba(0, 102, 255, 0.1);
  border-radius: 10px;
  overflow: hidden;
}
.table-scroll {
  overflow-x: auto;
}

table {
  width: 100%;
  border-collapse: collapse;
}

th {
  background: #111b3a;
  color: #94a3b8;
  font-weight: 600;
  font-size: 0.78rem;
  text-transform: uppercase;
  letter-spacing: 0.03em;
  padding: 10px 14px;
  text-align: left;
  white-space: nowrap;
  border-bottom: 2px solid rgba(0, 102, 255, 0.12);
  position: relative;
  user-select: none;
}

/* ── Filter row ── */
.filter-row th {
  padding: 4px 6px;
  border-bottom: 1px solid rgba(0, 102, 255, 0.15);
  background: rgba(0, 102, 255, 0.03);
}
.filter-cell {
  text-transform: none !important;
  letter-spacing: 0 !important;
}
.filter-input-wrapper {
  position: relative;
  display: flex;
  align-items: center;
}
.filter-icon {
  position: absolute;
  left: 6px;
  color: #475569;
  pointer-events: none;
  flex-shrink: 0;
}
.filter-input {
  width: 100%;
  background: rgba(0, 0, 0, 0.25);
  border: 1px solid rgba(255, 255, 255, 0.06);
  color: #e2e8f0;
  padding: 5px 24px 5px 24px;
  border-radius: 5px;
  font-size: 0.75rem;
  outline: none;
  transition: all 0.2s;
  min-width: 60px;
}
.filter-input::placeholder {
  color: #3e4a63;
  font-style: italic;
}
.filter-input:focus {
  border-color: rgba(0, 102, 255, 0.4);
  background: rgba(0, 0, 0, 0.35);
  box-shadow: 0 0 0 2px rgba(0, 102, 255, 0.1);
}
.filter-clear {
  position: absolute;
  right: 4px;
  background: none;
  border: none;
  color: #64748b;
  cursor: pointer;
  padding: 2px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 3px;
  transition: all 0.15s;
}
.filter-clear:hover {
  color: #f87171;
  background: rgba(248, 113, 113, 0.1);
}

/* ── Clear filters button ── */
.btn-clear-filters {
  display: flex;
  align-items: center;
  gap: 4px;
  background: rgba(248, 113, 113, 0.08);
  border: 1px solid rgba(248, 113, 113, 0.2);
  color: #f87171;
  padding: 4px 10px;
  border-radius: 6px;
  font-size: 0.72rem;
  font-weight: 500;
  cursor: pointer;
  white-space: nowrap;
  transition: all 0.2s;
}
.btn-clear-filters:hover {
  background: rgba(248, 113, 113, 0.15);
  border-color: rgba(248, 113, 113, 0.3);
}

td {
  padding: 9px 14px;
  text-align: left;
  white-space: nowrap;
  font-size: 0.82rem;
  color: #cbd5e1;
  border-bottom: 1px solid rgba(255, 255, 255, 0.04);
}

tbody tr {
  transition: background 0.15s;
}
tbody tr:hover {
  background: rgba(0, 102, 255, 0.06);
}
tbody tr:nth-child(even) {
  background: rgba(0, 102, 255, 0.02);
}
tbody tr:nth-child(even):hover {
  background: rgba(0, 102, 255, 0.06);
}

/* ── Column resizer handle ── */
.col-resizer {
  position: absolute;
  top: 0;
  right: 0;
  width: 5px;
  height: 100%;
  cursor: col-resize;
  background: transparent;
  z-index: 3;
}
.col-resizer:hover {
  background: rgba(0, 102, 255, 0.4);
}

/* ── Pagination ── */
.pagination {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 8px;
  padding: 10px 16px;
  border-top: 1px solid rgba(255, 255, 255, 0.04);
  background: rgba(0, 0, 0, 0.15);
}
.pg-btn {
  background: rgba(0, 102, 255, 0.08);
  border: 1px solid rgba(0, 102, 255, 0.15);
  color: #94a3b8;
  width: 32px;
  height: 32px;
  border-radius: 6px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
}
.pg-btn:hover:not(:disabled) {
  background: rgba(0, 102, 255, 0.15);
  color: #e2e8f0;
  border-color: rgba(0, 102, 255, 0.3);
}
.pg-btn:disabled {
  opacity: 0.3;
  cursor: not-allowed;
}
.pg-info {
  font-size: 0.78rem;
  color: #64748b;
  min-width: 60px;
  text-align: center;
}

/* ── Error ── */
.error-message {
  color: #f87171;
  padding: 10px 14px;
  background: rgba(239, 68, 68, 0.08);
  border: 1px solid rgba(239, 68, 68, 0.15);
  border-radius: 8px;
  font-size: 0.85rem;
  margin-top: 12px;
}

/* ── Delete modal ── */
.modal-overlay {
  position: fixed;
  inset: 0;
  z-index: 10000;
  background: rgba(0, 0, 0, 0.6);
  backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  justify-content: center;
}
.modal-box {
  background: #111b3a;
  border: 1px solid rgba(248, 113, 113, 0.25);
  border-radius: 14px;
  padding: 28px 32px;
  width: 440px;
  max-width: 90vw;
  box-shadow: 0 8px 40px rgba(0, 0, 0, 0.5);
}
.modal-box h3 {
  color: #f87171;
  font-size: 1.1rem;
  font-weight: 700;
  margin: 0 0 10px;
}
.modal-box p {
  color: #94a3b8;
  font-size: 0.85rem;
  margin: 0 0 8px;
  line-height: 1.5;
}
.modal-warning {
  color: #f87171 !important;
  font-size: 0.8rem !important;
}
.modal-warning code {
  background: rgba(248, 113, 113, 0.15);
  padding: 1px 6px;
  border-radius: 4px;
  font-weight: 700;
  color: #fca5a5;
}
.modal-input {
  width: 100%;
  padding: 10px 14px;
  background: rgba(0, 0, 0, 0.3);
  border: 1px solid rgba(248, 113, 113, 0.2);
  border-radius: 8px;
  color: #e2e8f0;
  font-size: 0.9rem;
  margin: 12px 0 16px;
  outline: none;
  transition: border-color 0.2s;
  box-sizing: border-box;
}
.modal-input:focus {
  border-color: #f87171;
}
.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}
.btn-cancel {
  background: rgba(255, 255, 255, 0.06);
  border: 1px solid rgba(255, 255, 255, 0.12);
  color: #94a3b8;
  padding: 8px 18px;
  border-radius: 8px;
  cursor: pointer;
  font-size: 0.82rem;
  transition: all 0.2s;
}
.btn-cancel:hover {
  background: rgba(255, 255, 255, 0.12);
  color: #e2e8f0;
}
.btn-confirm-delete {
  background: linear-gradient(135deg, #dc2626, #b91c1c);
  border: none;
  color: #fff;
  padding: 8px 20px;
  border-radius: 8px;
  cursor: pointer;
  font-size: 0.82rem;
  font-weight: 600;
  transition: all 0.2s;
  box-shadow: 0 2px 10px rgba(220, 38, 38, 0.3);
}
.btn-confirm-delete:hover:not(:disabled) {
  box-shadow: 0 4px 16px rgba(220, 38, 38, 0.4);
}
.btn-confirm-delete:disabled {
  opacity: 0.35;
  cursor: not-allowed;
}

/* ── Modal transition ── */
.modal-fade-enter-active,
.modal-fade-leave-active {
  transition: all 0.25s;
}
.modal-fade-enter-from,
.modal-fade-leave-to {
  opacity: 0;
}
.modal-fade-enter-from .modal-box,
.modal-fade-leave-to .modal-box {
  transform: scale(0.95);
}
</style>
