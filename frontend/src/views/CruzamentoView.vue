<template>
  <div class="cruzamento-view">
    <!-- ═══════ TELA 1: Seletor de Cruzamentos ═══════ -->
    <div v-if="!activeModule" class="selector-screen">
      <!-- Glassmorphism shapes -->
      <div class="shapes-container">
        <div class="glass-shape shape-1"></div>
        <div class="glass-shape shape-2"></div>
        <div class="glass-shape shape-3"></div>
        <div class="glass-shape shape-4"></div>
      </div>

      <div class="selector-content">
        <div class="selector-header">
          <div class="selector-badge">
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
            Cruzamento de Tabelas
          </div>
          <h1>Selecione um cruzamento</h1>
          <p>Escolha o tipo de cruzamento que deseja realizar</p>
        </div>

        <!-- Cards grid -->
        <div class="cards-grid">
          <!-- Card: Eventos × FGTS INSS IRRF -->
          <div class="cruz-card" @click="openModule('eventos-impostos')">
            <div class="card-icon">
              <svg
                width="28"
                height="28"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                stroke-width="1.5"
                stroke-linecap="round"
                stroke-linejoin="round"
              >
                <line x1="18" y1="6" x2="6" y2="18" />
                <line x1="6" y1="6" x2="18" y2="18" />
              </svg>
            </div>
            <h3>Cruzar Eventos × FGTS INSS IRRF</h3>
            <p class="card-desc">
              Cruza a tabela de eventos/naturezas com os códigos de impostos (FGTS, INSS, IRRF)
            </p>
            <div class="card-footer">
              <span v-if="statusEventos.total > 0" class="card-status done">
                <svg
                  width="12"
                  height="12"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  stroke-width="3"
                >
                  <polyline points="20 6 9 17 4 12" />
                </svg>
                {{ statusEventos.total }} registros cruzados
              </span>
              <span v-else class="card-status pending">Não cruzado</span>
              <svg
                class="card-arrow"
                width="20"
                height="20"
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

    <!-- ═══════ TELA 2: Módulo Eventos × Impostos ═══════ -->
    <div v-else class="module-screen">
      <!-- Header com voltar -->
      <div class="module-top">
        <button class="btn-voltar" @click="activeModule = null">
          <svg
            width="16"
            height="16"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
            stroke-linecap="round"
          >
            <path d="M19 12H5M12 19l-7-7 7-7" />
          </svg>
          Voltar
        </button>
        <h1>Cruzar Eventos × FGTS INSS IRRF</h1>
        <button v-if="uploadInfo" class="btn-reset" :disabled="resetting" @click="resetCruzamento">
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
            <polyline points="3 6 5 6 21 6" />
            <path
              d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"
            />
          </svg>
          {{ resetting ? 'Limpando...' : 'Refazer do zero' }}
        </button>
      </div>

      <!-- Upload -->
      <div class="upload-area">
        <div
          class="drop-zone"
          :class="{ dragover: isDragging }"
          @dragover.prevent="isDragging = true"
          @dragleave="isDragging = false"
          @drop.prevent="onDrop"
          @click="openFilePicker"
        >
          <svg
            width="40"
            height="40"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="1.5"
            stroke-linecap="round"
            stroke-linejoin="round"
            class="upload-icon"
          >
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
            <polyline points="17 8 12 3 7 8" />
            <line x1="12" y1="3" x2="12" y2="15" />
          </svg>
          <span v-if="!uploading">
            {{
              uploadInfo
                ? 'Trocar arquivo'
                : 'Arraste o arquivo .xlsx aqui ou clique para selecionar'
            }}
          </span>
          <span v-else class="uploading-text">Processando... {{ uploadProgress }}</span>
        </div>
        <input ref="fileInput" type="file" accept=".xlsx,.xls" hidden @change="onFileSelected" />

        <div v-if="uploadInfo" class="upload-status">
          <span class="filename">{{ uploadInfo.originalName }}</span>
          <span class="sheet-info">
            {{ uploadInfo.sheetNames[0] }} ({{ uploadInfo.rowsA }} linhas) ×
            {{ uploadInfo.sheetNames[1] }} ({{ uploadInfo.rowsB }} linhas)
          </span>
        </div>
      </div>

      <!-- Tabelas lado a lado -->
      <div v-if="uploadInfo" class="tables-container">
        <div class="table-panel">
          <div class="panel-header">
            <h2>{{ uploadInfo.sheetNames[0] || 'Tabela A' }}</h2>
            <span class="row-count">{{ uploadInfo.rowsA }} linhas</span>
          </div>
          <div class="panel-body">
            <div v-if="loadingA" class="loading">Carregando...</div>
            <div v-else-if="dataA.length > 0" class="table-scroll">
              <table>
                <thead>
                  <tr>
                    <th v-for="col in colsA" :key="col.letter">
                      <span class="col-letter">{{ col.letter }}</span
                      ><span class="col-name">{{ col.name }}</span>
                    </th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="(row, i) in dataA" :key="i">
                    <td v-for="col in colsA" :key="col.letter">
                      {{ row[`col_${col.letter.toLowerCase()}`] || '-' }}
                    </td>
                  </tr>
                </tbody>
              </table>
              <div class="pagination">
                <button @click="pageA > 1 && loadTable('a', --pageA)" :disabled="pageA <= 1">
                  Anterior
                </button>
                <span>Pág {{ pageA }}/{{ totalPagesA }}</span>
                <button
                  @click="pageA < totalPagesA && loadTable('a', ++pageA)"
                  :disabled="pageA >= totalPagesA"
                >
                  Próxima
                </button>
              </div>
            </div>
            <div v-else class="empty-panel">Sem dados</div>
          </div>
        </div>

        <div class="table-panel">
          <div class="panel-header">
            <h2>{{ uploadInfo.sheetNames[1] || 'Tabela B' }}</h2>
            <span class="row-count">{{ uploadInfo.rowsB }} linhas</span>
          </div>
          <div class="panel-body">
            <div v-if="loadingB" class="loading">Carregando...</div>
            <div v-else-if="dataB.length > 0" class="table-scroll">
              <table>
                <thead>
                  <tr>
                    <th v-for="col in colsB" :key="col.letter">
                      <span class="col-letter">{{ col.letter }}</span
                      ><span class="col-name">{{ col.name }}</span>
                    </th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="(row, i) in dataB" :key="i">
                    <td v-for="col in colsB" :key="col.letter">
                      {{ row[`col_${col.letter.toLowerCase()}`] || '-' }}
                    </td>
                  </tr>
                </tbody>
              </table>
              <div class="pagination">
                <button @click="pageB > 1 && loadTable('b', --pageB)" :disabled="pageB <= 1">
                  Anterior
                </button>
                <span>Pág {{ pageB }}/{{ totalPagesB }}</span>
                <button
                  @click="pageB < totalPagesB && loadTable('b', ++pageB)"
                  :disabled="pageB >= totalPagesB"
                >
                  Próxima
                </button>
              </div>
            </div>
            <div v-else class="empty-panel">Sem dados</div>
          </div>
        </div>
      </div>

      <!-- Botão Cruzar -->
      <div v-if="uploadInfo && !resultData.length" class="cruzar-section">
        <button class="btn-cruzar" :disabled="cruzando" @click="executarCruzamento">
          <svg
            width="18"
            height="18"
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
          {{ cruzando ? 'Cruzando...' : 'Cruzar Tabelas' }}
        </button>
        <p class="cruzar-desc">
          Une as duas tabelas pelo código. Só entram códigos presentes na tabela de natureza.
        </p>
      </div>

      <!-- Tabela Resultado -->
      <div v-if="resultData.length > 0" class="resultado-section">
        <div class="resultado-header">
          <div class="resultado-title">
            <h2>Tabela Cruzada</h2>
            <span class="row-count">{{ resultTotal }} registros</span>
          </div>
          <button class="btn-recruzar" @click="executarCruzamento" :disabled="cruzando">
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
              <polyline points="23 4 23 10 17 10" />
              <path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10" />
            </svg>
            Recruzar
          </button>
        </div>
        <div class="resultado-table-scroll">
          <table class="resultado-table">
            <thead>
              <tr>
                <th>Código</th>
                <th>Nome Evento</th>
                <th>Natureza E-social</th>
                <th>Cód. INSS</th>
                <th>Cód. IRRF</th>
                <th>Cód. FGTS</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(row, i) in resultData" :key="i">
                <td class="col-codigo">{{ row.codigo }}</td>
                <td>{{ row.nome_evento || '-' }}</td>
                <td>{{ row.natureza_esocial || '-' }}</td>
                <td class="col-imposto">{{ row.cod_inss || '-' }}</td>
                <td class="col-imposto">{{ row.cod_irrf || '-' }}</td>
                <td class="col-imposto">{{ row.cod_fgts || '-' }}</td>
              </tr>
            </tbody>
          </table>
          <div class="pagination">
            <button @click="pageR > 1 && loadResultado(--pageR)" :disabled="pageR <= 1">
              Anterior
            </button>
            <span>Pág {{ pageR }}/{{ totalPagesR }}</span>
            <button
              @click="pageR < totalPagesR && loadResultado(++pageR)"
              :disabled="pageR >= totalPagesR"
            >
              Próxima
            </button>
          </div>
        </div>
        <div class="resultado-actions">
          <button class="btn-salvar-tabelas" :disabled="salvando" @click="salvarEmTabelas">
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
              <path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z" />
              <polyline points="17 21 17 13 7 13 7 21" />
              <polyline points="7 3 7 8 15 8" />
            </svg>
            {{ salvando ? 'Salvando...' : 'Salvar em Tabelas' }}
          </button>
        </div>
      </div>
    </div>

    <!-- Toast -->
    <Transition name="toast">
      <div v-if="toast" :class="['toast', toast.type]">{{ toast.msg }}</div>
    </Transition>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import axios from 'axios'
import { API_URL } from '@/lib/api'

// Módulo ativo (null = tela de seleção)
const activeModule = ref<string | null>(null)
const statusEventos = ref<{ total: number }>({ total: 0 })

interface UploadInfo {
  id: number
  originalName: string
  sheetNames: string[]
  rowsA: number
  rowsB: number
}

const uploadInfo = ref<UploadInfo | null>(null)
const isDragging = ref(false)
const uploading = ref(false)
const uploadProgress = ref('')
const fileInput = ref<HTMLInputElement | null>(null)
const toast = ref<{ msg: string; type: 'ok' | 'err' } | null>(null)

// Tabela A
const dataA = ref<any[]>([])
const colsA = ref<{ letter: string; name: string }[]>([])
const loadingA = ref(false)
const pageA = ref(1)
const totalPagesA = ref(1)

// Tabela B
const dataB = ref<any[]>([])
const colsB = ref<{ letter: string; name: string }[]>([])
const loadingB = ref(false)
const pageB = ref(1)
const totalPagesB = ref(1)

// Resultado do cruzamento
const resultData = ref<any[]>([])
const resultTotal = ref(0)
const pageR = ref(1)
const totalPagesR = ref(1)
const cruzando = ref(false)
const salvando = ref(false)
const resetting = ref(false)

const PER_PAGE = 100

function openFilePicker() {
  fileInput.value?.click()
}

function onFileSelected(e: Event) {
  const file = (e.target as HTMLInputElement).files?.[0]
  if (file) uploadFile(file)
}

function onDrop(e: DragEvent) {
  isDragging.value = false
  const file = e.dataTransfer?.files?.[0]
  if (file) uploadFile(file)
}

async function uploadFile(file: File) {
  uploading.value = true
  uploadProgress.value = 'Enviando...'
  try {
    const formData = new FormData()
    formData.append('file', file)

    const res = await axios.post(`${API_URL}/cruzamento/upload`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      onUploadProgress: (p) => {
        if (p.total) {
          const pct = Math.round((p.loaded / p.total) * 100)
          uploadProgress.value = `${pct}%`
        }
      },
    })

    if (res.data.success) {
      showToast(res.data.message, 'ok')
      await checkStatus()
    }
  } catch (err: any) {
    showToast(err.response?.data?.error || 'Erro no upload', 'err')
  } finally {
    uploading.value = false
    if (fileInput.value) fileInput.value.value = ''
  }
}

async function checkStatus() {
  try {
    const res = await axios.get(`${API_URL}/cruzamento/status`)
    if (res.data.hasData) {
      uploadInfo.value = res.data.upload
      await Promise.all([loadColumns('a'), loadColumns('b')])
      await Promise.all([loadTable('a', 1), loadTable('b', 1)])
      // Check if there's already a cruzamento result
      await loadResultado(1)
    }
  } catch {
    // silently fail
  }
}

async function loadColumns(side: 'a' | 'b') {
  try {
    const res = await axios.get(`${API_URL}/cruzamento/colunas/${side}`)
    if (side === 'a') colsA.value = res.data.columns
    else colsB.value = res.data.columns
  } catch {
    // ignore
  }
}

async function loadTable(side: 'a' | 'b', page: number) {
  const loading = side === 'a' ? loadingA : loadingB
  loading.value = true

  try {
    const offset = (page - 1) * PER_PAGE
    const res = await axios.get(
      `${API_URL}/cruzamento/tabela/${side}?limit=${PER_PAGE}&offset=${offset}`,
    )
    const total = res.data.total
    const pages = Math.ceil(total / PER_PAGE)

    if (side === 'a') {
      dataA.value = res.data.data
      pageA.value = page
      totalPagesA.value = pages
    } else {
      dataB.value = res.data.data
      pageB.value = page
      totalPagesB.value = pages
    }
  } catch {
    showToast(`Erro ao carregar tabela ${side.toUpperCase()}`, 'err')
  } finally {
    loading.value = false
  }
}

async function executarCruzamento() {
  cruzando.value = true
  try {
    const res = await axios.post(`${API_URL}/cruzamento/cruzar`)
    if (res.data.success) {
      showToast(res.data.message, 'ok')
      await loadResultado(1)
    }
  } catch (err: any) {
    showToast(err.response?.data?.error || 'Erro ao cruzar tabelas', 'err')
  } finally {
    cruzando.value = false
  }
}

async function loadResultado(page: number) {
  try {
    const offset = (page - 1) * PER_PAGE
    const res = await axios.get(
      `${API_URL}/cruzamento/resultado?limit=${PER_PAGE}&offset=${offset}`,
    )
    if (res.data.hasData === false) return
    resultData.value = res.data.data
    resultTotal.value = res.data.total
    pageR.value = page
    totalPagesR.value = Math.ceil(res.data.total / PER_PAGE)
  } catch {
    // ignore
  }
}

async function salvarEmTabelas() {
  salvando.value = true
  try {
    const res = await axios.post(`${API_URL}/cruzamento/salvar-em-tabelas`)
    if (res.data.success) {
      showToast(res.data.message, 'ok')
    }
  } catch (err: any) {
    showToast(err.response?.data?.error || 'Erro ao salvar', 'err')
  } finally {
    salvando.value = false
  }
}

async function resetCruzamento() {
  resetting.value = true
  try {
    const res = await axios.post(`${API_URL}/cruzamento/reset`)
    if (res.data.success) {
      showToast(res.data.message, 'ok')
      uploadInfo.value = null
      dataA.value = []
      dataB.value = []
      colsA.value = []
      colsB.value = []
      resultData.value = []
      resultTotal.value = 0
      pageA.value = 1
      pageB.value = 1
      pageR.value = 1
    }
  } catch (err: any) {
    showToast(err.response?.data?.error || 'Erro ao resetar', 'err')
  } finally {
    resetting.value = false
  }
}

function showToast(msg: string, type: 'ok' | 'err') {
  toast.value = { msg, type }
  setTimeout(() => (toast.value = null), 4000)
}

function openModule(module: string) {
  activeModule.value = module
  checkStatus()
}

async function loadStatusCards() {
  try {
    const res = await axios.get(`${API_URL}/cruzamento/resultado?limit=1&offset=0`)
    if (res.data.hasData !== false) {
      statusEventos.value = { total: res.data.total }
    }
  } catch {
    // ignore
  }
}

onMounted(loadStatusCards)

watch(activeModule, (val) => {
  if (val === null) loadStatusCards()
})
</script>

<style scoped>
/* ═══════ Root ═══════ */
.cruzamento-view {
  color: #e2e8f0;
  min-height: 100vh;
}

/* ═══════ TELA 1: Selector Screen ═══════ */
.selector-screen {
  min-height: 100vh;
  position: relative;
  overflow: hidden;
  background: linear-gradient(135deg, #0a1024, #0d1530, #0066ff, #0d1530, #0a1024);
  background-size: 400% 400%;
  animation: bgShift 12s ease-in-out infinite;
  display: flex;
  align-items: center;
  justify-content: center;
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

/* ── Glass shapes ── */
.shapes-container {
  position: absolute;
  inset: 0;
  overflow: hidden;
  pointer-events: none;
}
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

/* ── Selector content ── */
.selector-content {
  position: relative;
  z-index: 1;
  max-width: 700px;
  width: 100%;
  padding: 40px 24px;
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
.selector-header {
  text-align: center;
  margin-bottom: 36px;
}
.selector-badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 5px 14px;
  background: rgba(255, 255, 255, 0.08);
  border: 1px solid rgba(255, 255, 255, 0.15);
  border-radius: 20px;
  color: rgba(255, 255, 255, 0.7);
  font-size: 0.75rem;
  font-weight: 500;
  margin-bottom: 16px;
}
.selector-header h1 {
  font-size: 1.8rem;
  font-weight: 800;
  color: #fff;
  margin: 0 0 8px;
}
.selector-header p {
  color: rgba(255, 255, 255, 0.5);
  font-size: 0.9rem;
  margin: 0;
}

/* ── Cards grid ── */
.cards-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 16px;
}
.cruz-card {
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 16px;
  padding: 24px;
  cursor: pointer;
  transition: all 0.3s;
}
.cruz-card:hover {
  background: rgba(255, 255, 255, 0.18);
  border-color: rgba(255, 255, 255, 0.3);
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.15);
  transform: translateY(-2px);
}
.card-icon {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.12);
  border: 1px solid rgba(255, 255, 255, 0.1);
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  margin-bottom: 14px;
  transition: background 0.2s;
}
.cruz-card:hover .card-icon {
  background: rgba(255, 255, 255, 0.22);
}
.cruz-card h3 {
  font-size: 1.05rem;
  font-weight: 700;
  color: #fff;
  margin: 0 0 6px;
}
.card-desc {
  color: rgba(255, 255, 255, 0.45);
  font-size: 0.82rem;
  margin: 0 0 16px;
  line-height: 1.5;
}
.card-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.card-status {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 3px 10px;
  border-radius: 12px;
  font-size: 0.72rem;
  font-weight: 600;
}
.card-status.done {
  background: rgba(52, 211, 153, 0.15);
  border: 1px solid rgba(52, 211, 153, 0.25);
  color: #34d399;
}
.card-status.pending {
  background: rgba(255, 255, 255, 0.08);
  border: 1px solid rgba(255, 255, 255, 0.12);
  color: rgba(255, 255, 255, 0.45);
}
.card-arrow {
  color: rgba(255, 255, 255, 0.2);
  transition: all 0.2s;
}
.cruz-card:hover .card-arrow {
  color: rgba(255, 255, 255, 0.6);
  transform: translateX(3px);
}

/* ═══════ TELA 2: Module Screen ═══════ */
.module-screen {
  padding: 28px 32px;
  min-height: 100vh;
  animation: fadeIn 300ms ease;
}
.module-top {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 24px;
}
.module-top h1 {
  font-size: 1.35rem;
  font-weight: 700;
  color: #fff;
  margin: 0;
}
.btn-voltar {
  display: flex;
  align-items: center;
  gap: 6px;
  background: rgba(0, 102, 255, 0.1);
  border: 1px solid rgba(0, 102, 255, 0.2);
  color: #0066ff;
  padding: 7px 14px;
  border-radius: 8px;
  font-size: 0.8rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}
.btn-voltar:hover {
  background: rgba(0, 102, 255, 0.18);
}
.btn-reset {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-left: auto;
  background: rgba(248, 113, 113, 0.1);
  border: 1px solid rgba(248, 113, 113, 0.25);
  color: #f87171;
  padding: 7px 14px;
  border-radius: 8px;
  font-size: 0.8rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}
.btn-reset:hover:not(:disabled) {
  background: rgba(248, 113, 113, 0.2);
  border-color: rgba(248, 113, 113, 0.4);
}
.btn-reset:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

/* ═══════ Upload area ═══════ */
.upload-area {
  margin: 20px 0;
}
.drop-zone {
  border: 2px dashed rgba(0, 102, 255, 0.3);
  border-radius: 12px;
  padding: 32px;
  text-align: center;
  cursor: pointer;
  transition: all 0.2s;
  color: #8892b0;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
}
.drop-zone:hover,
.drop-zone.dragover {
  border-color: #0066ff;
  background: rgba(0, 102, 255, 0.05);
  color: #0066ff;
}
.upload-icon {
  color: #0066ff;
  opacity: 0.6;
}
.uploading-text {
  color: #0066ff;
  font-weight: 600;
}
.upload-status {
  margin-top: 12px;
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 10px 16px;
  background: rgba(0, 102, 255, 0.08);
  border-radius: 8px;
  border: 1px solid rgba(0, 102, 255, 0.15);
}
.filename {
  font-weight: 600;
  color: #fff;
  font-size: 0.9rem;
}
.sheet-info {
  color: #8892b0;
  font-size: 0.82rem;
}

/* ═══════ Side by side tables ═══════ */
.tables-container {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
  margin-top: 20px;
}
.table-panel {
  background: rgba(13, 21, 48, 0.6);
  border: 1px solid rgba(0, 102, 255, 0.12);
  border-radius: 10px;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}
.panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  background: rgba(0, 102, 255, 0.06);
  border-bottom: 1px solid rgba(0, 102, 255, 0.12);
}
.panel-header h2 {
  font-size: 0.95rem;
  font-weight: 600;
  color: #fff;
}
.row-count {
  font-size: 0.78rem;
  color: #0066ff;
  background: rgba(0, 102, 255, 0.12);
  padding: 2px 10px;
  border-radius: 12px;
}
.panel-body {
  flex: 1;
  overflow: hidden;
}
.table-scroll {
  overflow-x: auto;
  max-height: 60vh;
  overflow-y: auto;
}
table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.78rem;
}
thead {
  position: sticky;
  top: 0;
  z-index: 2;
}
th {
  background: #111b3a;
  padding: 8px 10px;
  text-align: left;
  white-space: nowrap;
  border-bottom: 1px solid rgba(0, 102, 255, 0.15);
}
.col-letter {
  color: #0066ff;
  font-weight: 700;
  font-size: 0.7rem;
  margin-right: 4px;
}
.col-name {
  color: #8892b0;
  font-weight: 400;
  font-size: 0.72rem;
}
td {
  padding: 6px 10px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.04);
  white-space: nowrap;
  max-width: 200px;
  overflow: hidden;
  text-overflow: ellipsis;
  color: #c8d0e0;
}
tr:hover td {
  background: rgba(0, 102, 255, 0.04);
}

/* ═══════ Pagination ═══════ */
.pagination {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  padding: 10px;
  border-top: 1px solid rgba(0, 102, 255, 0.1);
  font-size: 0.78rem;
  color: #8892b0;
}
.pagination button {
  background: rgba(0, 102, 255, 0.1);
  border: 1px solid rgba(0, 102, 255, 0.2);
  color: #0066ff;
  padding: 4px 12px;
  border-radius: 6px;
  cursor: pointer;
  font-size: 0.75rem;
}
.pagination button:disabled {
  opacity: 0.3;
  cursor: not-allowed;
}
.loading,
.empty-panel {
  padding: 40px;
  text-align: center;
  color: #8892b0;
}

/* ═══════ Toast ═══════ */
.toast {
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
.toast.ok {
  background: rgba(52, 211, 153, 0.15);
  border: 1px solid rgba(52, 211, 153, 0.3);
  color: #34d399;
}
.toast.err {
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

/* ═══════ Cruzar button ═══════ */
.cruzar-section {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
  margin: 28px 0;
}
.btn-cruzar {
  display: flex;
  align-items: center;
  gap: 8px;
  background: linear-gradient(135deg, #0066ff 0%, #0044cc 100%);
  color: #fff;
  border: none;
  padding: 12px 32px;
  border-radius: 10px;
  font-size: 0.95rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
  box-shadow: 0 4px 16px rgba(0, 102, 255, 0.3);
}
.btn-cruzar:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 6px 24px rgba(0, 102, 255, 0.4);
}
.btn-cruzar:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
.cruzar-desc {
  color: #8892b0;
  font-size: 0.78rem;
}

/* ═══════ Resultado section ═══════ */
.resultado-section {
  margin-top: 28px;
  background: rgba(13, 21, 48, 0.6);
  border: 1px solid rgba(0, 102, 255, 0.15);
  border-radius: 10px;
  overflow: hidden;
}
.resultado-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 20px;
  background: rgba(0, 102, 255, 0.08);
  border-bottom: 1px solid rgba(0, 102, 255, 0.12);
}
.resultado-title {
  display: flex;
  align-items: center;
  gap: 12px;
}
.resultado-title h2 {
  font-size: 1.05rem;
  font-weight: 700;
  color: #fff;
}
.btn-recruzar {
  display: flex;
  align-items: center;
  gap: 6px;
  background: rgba(0, 102, 255, 0.12);
  border: 1px solid rgba(0, 102, 255, 0.25);
  color: #0066ff;
  padding: 6px 14px;
  border-radius: 7px;
  font-size: 0.78rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}
.btn-recruzar:hover:not(:disabled) {
  background: rgba(0, 102, 255, 0.2);
}
.btn-recruzar:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}
.resultado-table-scroll {
  overflow-x: auto;
  max-height: 65vh;
  overflow-y: auto;
}
.resultado-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.8rem;
}
.resultado-table thead {
  position: sticky;
  top: 0;
  z-index: 2;
}
.resultado-table th {
  background: #111b3a;
  padding: 10px 14px;
  text-align: left;
  white-space: nowrap;
  border-bottom: 1px solid rgba(0, 102, 255, 0.15);
  color: #0066ff;
  font-weight: 600;
  font-size: 0.78rem;
}
.resultado-table td {
  padding: 8px 14px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.04);
  color: #c8d0e0;
  white-space: nowrap;
}
.resultado-table tr:hover td {
  background: rgba(0, 102, 255, 0.04);
}
.col-codigo {
  font-weight: 700;
  color: #0066ff;
}
.col-imposto {
  font-weight: 600;
  color: #e2e8f0;
  text-align: center;
}

/* ═══════ Salvar em Tabelas ═══════ */
.resultado-actions {
  display: flex;
  justify-content: flex-end;
  padding: 14px 20px;
  border-top: 1px solid rgba(0, 102, 255, 0.1);
}
.btn-salvar-tabelas {
  display: flex;
  align-items: center;
  gap: 8px;
  background: linear-gradient(135deg, #059669 0%, #047857 100%);
  color: #fff;
  border: none;
  padding: 10px 22px;
  border-radius: 8px;
  font-size: 0.85rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
  box-shadow: 0 4px 14px rgba(5, 150, 105, 0.3);
}
.btn-salvar-tabelas:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 6px 20px rgba(5, 150, 105, 0.4);
}
.btn-salvar-tabelas:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
</style>
