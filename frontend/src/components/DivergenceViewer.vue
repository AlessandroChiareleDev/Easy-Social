<template>
  <div class="dv">
    <!-- Section Header -->
    <div class="dv-header">
      <div>
        <h2 class="dv-title">Validação de Rubricas</h2>
        <p class="dv-subtitle">Ponto 1 · Análise de divergências entre DIRF e eSocial</p>
      </div>
    </div>

    <!-- Resumo Cards -->
    <div class="resumo-cards" v-if="resumo">
      <div class="card card-total">
        <span class="card-number">{{ resumo.total_rubricas }}</span>
        <span class="card-label">Total Rubricas</span>
      </div>
      <div class="card card-divergente">
        <span class="card-number">{{ resumo.total_divergentes }}</span>
        <span class="card-label">Divergentes</span>
      </div>
      <div class="card card-pendente">
        <span class="card-number">{{ resumo.total_pendentes }}</span>
        <span class="card-label">Pendentes</span>
      </div>
      <div class="card card-corrigido">
        <span class="card-number">{{ resumo.total_corrigidas }}</span>
        <span class="card-label">Corrigidas</span>
      </div>
      <div class="card card-verificado">
        <span class="card-number">{{ resumo.total_verificadas }}</span>
        <span class="card-label">Verificadas</span>
      </div>
      <div class="card card-realizada">
        <span class="card-number">{{ resumo.total_realizadas }}</span>
        <span class="card-label">Realizadas</span>
      </div>
    </div>

    <!-- Ações -->
    <div class="actions-bar">
      <button class="btn btn-detectar" @click="executarDeteccao" :disabled="detecting">
        <svg
          class="btn-icon"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="2"
          stroke-linecap="round"
        >
          <path d="M21 12a9 9 0 1 1-6.22-8.56" />
          <polyline points="21 3 21 9 15 9" />
        </svg>
        {{ detecting ? 'Analisando...' : 'Detectar Divergências' }}
      </button>
      <button
        class="btn btn-wizard"
        @click="abrirWizard"
        :disabled="!resumo || resumo.total_pendentes === 0"
      >
        <svg
          class="btn-icon"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="2"
          stroke-linecap="round"
        >
          <circle cx="12" cy="12" r="10" />
          <polygon points="10 8 16 12 10 16 10 8" fill="currentColor" stroke="none" />
        </svg>
        Iniciar Correção Guiada
      </button>
    </div>

    <!-- Barra de Progresso -->
    <div class="progress-bar" v-if="resumo && resumo.total_divergentes > 0">
      <div class="progress-track">
        <div
          class="progress-fill progress-verificado"
          :style="{ width: progressVerificado + '%' }"
        ></div>
        <div
          class="progress-fill progress-corrigido"
          :style="{ width: progressCorrigido + '%', left: progressVerificado + '%' }"
        ></div>
      </div>
      <span class="progress-text">
        {{ resumo.total_corrigidas + resumo.total_verificadas + resumo.total_realizadas }} /
        {{ resumo.total_divergentes }} tratadas ({{
          Math.round(
            ((resumo.total_corrigidas + resumo.total_verificadas + resumo.total_realizadas) /
              resumo.total_divergentes) *
              100,
          )
        }}%)
      </span>
    </div>

    <!-- Filtro -->
    <div class="filter-bar" v-if="resumo && resumo.total_divergentes > 0">
      <button :class="['filter-btn', { active: filtroStatus === '' }]" @click="setFilter('')">
        Todas ({{ resumo.total_divergentes }})
      </button>
      <button
        :class="['filter-btn filter-pendente', { active: filtroStatus === 'pendente' }]"
        @click="setFilter('pendente')"
      >
        Pendentes ({{ resumo.total_pendentes }})
      </button>
      <button
        :class="['filter-btn filter-corrigido', { active: filtroStatus === 'corrigido' }]"
        @click="setFilter('corrigido')"
      >
        Corrigidas ({{ resumo.total_corrigidas }})
      </button>
      <button
        :class="['filter-btn filter-verificado', { active: filtroStatus === 'verificado' }]"
        @click="setFilter('verificado')"
      >
        Verificadas ({{ resumo.total_verificadas }})
      </button>
      <button
        :class="['filter-btn filter-realizada', { active: filtroStatus === 'realizada' }]"
        @click="setFilter('realizada')"
      >
        Realizadas ({{ resumo.total_realizadas }})
      </button>
    </div>

    <!-- Tabela de Divergências -->
    <div class="table-container" v-if="divergencias.length > 0">
      <table>
        <thead>
          <tr>
            <th>Cód. Rubrica</th>
            <th>Descrição</th>
            <th class="col-compare">INSS (D)</th>
            <th class="col-arrow">→</th>
            <th class="col-compare">INSS (H)</th>
            <th class="col-compare">IRRF (E)</th>
            <th class="col-arrow">→</th>
            <th class="col-compare">IRRF (I)</th>
            <th class="col-compare">FGTS (F)</th>
            <th class="col-arrow">→</th>
            <th class="col-compare">FGTS (J)</th>
            <th>Status</th>
            <th>Ações</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="div in divergencias" :key="div.id" :class="'row-' + div.status">
            <td class="col-code">{{ div.cod_rubrica }}</td>
            <td class="col-desc">{{ div.descricao }}</td>
            <td :class="{ divergent: div.inss_antes !== div.inss_correto }">
              {{ div.inss_antes || '-' }}
            </td>
            <td class="arrow">→</td>
            <td :class="{ corrected: div.inss_antes !== div.inss_correto }">
              {{ div.inss_correto || '-' }}
            </td>
            <td :class="{ divergent: div.irrf_antes !== div.irrf_correto }">
              {{ div.irrf_antes || '-' }}
            </td>
            <td class="arrow">→</td>
            <td :class="{ corrected: div.irrf_antes !== div.irrf_correto }">
              {{ div.irrf_correto || '-' }}
            </td>
            <td :class="{ divergent: div.fgts_antes !== div.fgts_correto }">
              {{ div.fgts_antes || '-' }}
            </td>
            <td class="arrow">→</td>
            <td :class="{ corrected: div.fgts_antes !== div.fgts_correto }">
              {{ div.fgts_correto || '-' }}
            </td>
            <td>
              <span :class="'badge badge-' + div.status">{{ statusLabel(div.status) }}</span>
            </td>
            <td class="col-actions">
              <button
                v-if="div.status === 'pendente' && confirmandoId !== div.id"
                class="btn-sm btn-corrigir"
                @click="marcarCorrigido(div.id)"
              >
                Corrigido
              </button>
              <button
                v-if="div.status === 'pendente' && confirmandoId !== div.id"
                class="btn-sm btn-realizada"
                @click="iniciarRealizada(div.id)"
              >
                Realizada
              </button>
              <button
                v-if="confirmandoId === div.id"
                class="btn-sm btn-salvar"
                @click="confirmarRealizada(div.id)"
              >
                Salvar
              </button>
              <button
                v-if="confirmandoId === div.id"
                class="btn-sm btn-resetar"
                @click="cancelarRealizada()"
              >
                Cancelar
              </button>
              <button
                v-if="div.status === 'corrigido'"
                class="btn-sm btn-verificar"
                @click="marcarVerificado(div.id)"
              >
                Verificar
              </button>
              <button
                v-if="div.status !== 'pendente' && confirmandoId !== div.id"
                class="btn-sm btn-resetar"
                @click="resetar(div.id)"
              >
                Resetar
              </button>
            </td>
          </tr>
        </tbody>
      </table>

      <!-- Paginação -->
      <div class="pagination">
        <button @click="prevPage" :disabled="currentPage === 1">Anterior</button>
        <span>Página {{ currentPage }} de {{ totalPages }}</span>
        <button @click="nextPage" :disabled="currentPage === totalPages">Próxima</button>
      </div>
    </div>

    <div
      v-if="!loading && resumo && resumo.total_divergentes === 0 && resumo.total_rubricas > 0"
      class="no-divergences"
    >
      <svg class="nd-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" />
        <polyline points="22 4 12 14.01 9 11.01" />
      </svg>
      Nenhuma divergência encontrada! Todas as rubricas estão corretas.
    </div>

    <div v-if="loading" class="loading">
      <div class="loading-spinner"></div>
      Carregando...
    </div>
    <div v-if="error" class="error-message">{{ error }}</div>

    <!-- Wizard Modal -->
    <CorrectionWizard v-if="showWizard" @close="fecharWizard" @updated="onWizardUpdate" />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import axios from 'axios'
import CorrectionWizard from './CorrectionWizard.vue'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:3333/api'

interface Resumo {
  total_rubricas: number
  total_divergentes: number
  total_pendentes: number
  total_corrigidas: number
  total_verificadas: number
  total_realizadas: number
}

interface Divergencia {
  id: number
  tabela_eb_id: number
  cod_rubrica: string
  descricao: string
  inss_antes: string
  irrf_antes: string
  fgts_antes: string
  inss_correto: string
  irrf_correto: string
  fgts_correto: string
  status: string
  corrigido_em: string | null
  observacao: string | null
  col_h: string
  col_i: string
  col_j: string
}

const resumo = ref<Resumo | null>(null)
const divergencias = ref<Divergencia[]>([])
const loading = ref(false)
const detecting = ref(false)
const error = ref<string | null>(null)
const filtroStatus = ref('')
const showWizard = ref(false)
const confirmandoId = ref<number | null>(null)

const currentPage = ref(1)
const itemsPerPage = 50
const totalItems = ref(0)
const totalPages = computed(() => Math.max(1, Math.ceil(totalItems.value / itemsPerPage)))

const progressVerificado = computed(() => {
  if (!resumo.value || resumo.value.total_divergentes === 0) return 0
  return (resumo.value.total_verificadas / resumo.value.total_divergentes) * 100
})

const progressCorrigido = computed(() => {
  if (!resumo.value || resumo.value.total_divergentes === 0) return 0
  return (resumo.value.total_corrigidas / resumo.value.total_divergentes) * 100
})

function statusLabel(status: string): string {
  const labels: Record<string, string> = {
    pendente: 'Pendente',
    corrigido: 'Corrigido',
    verificado: 'Verificado',
    realizada: 'Realizada',
  }
  return labels[status] || status
}

function setFilter(status: string) {
  filtroStatus.value = status
  loadDivergencias()
}

async function loadResumo() {
  try {
    const res = await axios.get(`${API_URL}/validacao/resumo`)
    resumo.value = res.data
  } catch (err: any) {
    error.value = err.response?.data?.error || 'Erro ao carregar resumo'
  }
}

async function loadDivergencias() {
  loading.value = true
  error.value = null
  try {
    const offset = (currentPage.value - 1) * itemsPerPage
    let url = `${API_URL}/validacao/divergencias?limit=${itemsPerPage}&offset=${offset}`
    if (filtroStatus.value) {
      url += `&status=${filtroStatus.value}`
    }
    const res = await axios.get(url)
    divergencias.value = res.data.data
    totalItems.value = res.data.total
  } catch (err: any) {
    error.value = err.response?.data?.error || 'Erro ao carregar divergências'
  } finally {
    loading.value = false
  }
}

async function executarDeteccao() {
  detecting.value = true
  error.value = null
  try {
    await axios.post(`${API_URL}/validacao/detectar`)
    await loadResumo()
    currentPage.value = 1
    await loadDivergencias()
  } catch (err: any) {
    error.value = err.response?.data?.error || 'Erro ao executar detecção'
  } finally {
    detecting.value = false
  }
}

async function marcarCorrigido(id: number) {
  try {
    await axios.patch(`${API_URL}/validacao/${id}/corrigir`)
    await loadResumo()
    await loadDivergencias()
  } catch (err: any) {
    error.value = err.response?.data?.error || 'Erro ao marcar como corrigido'
  }
}

async function marcarVerificado(id: number) {
  try {
    await axios.patch(`${API_URL}/validacao/${id}/verificar`)
    await loadResumo()
    await loadDivergencias()
  } catch (err: any) {
    error.value = err.response?.data?.error || 'Erro ao verificar'
  }
}

function iniciarRealizada(id: number) {
  confirmandoId.value = id
}

function cancelarRealizada() {
  confirmandoId.value = null
}

async function confirmarRealizada(id: number) {
  try {
    await axios.patch(`${API_URL}/validacao/${id}/realizada`)
    confirmandoId.value = null
    await loadResumo()
    await loadDivergencias()
  } catch (err: any) {
    error.value = err.response?.data?.error || 'Erro ao marcar como realizada'
  }
}

async function resetar(id: number) {
  try {
    await axios.patch(`${API_URL}/validacao/${id}/resetar`)
    await loadResumo()
    await loadDivergencias()
  } catch (err: any) {
    error.value = err.response?.data?.error || 'Erro ao resetar'
  }
}

function abrirWizard() {
  showWizard.value = true
}

function fecharWizard() {
  showWizard.value = false
}

async function onWizardUpdate() {
  await loadResumo()
  await loadDivergencias()
}

function nextPage() {
  if (currentPage.value < totalPages.value) {
    currentPage.value++
    loadDivergencias()
  }
}

function prevPage() {
  if (currentPage.value > 1) {
    currentPage.value--
    loadDivergencias()
  }
}

onMounted(async () => {
  await loadResumo()
  if (resumo.value && resumo.value.total_divergentes > 0) {
    await loadDivergencias()
  }
})
</script>

<style scoped>
/* ═══════════════════════════════════════════════
   DivergenceViewer — Orbit Navy + Electric Blue
   ═══════════════════════════════════════════════ */

.dv {
  color: #e2e8f0;
}

/* ── Header ── */
.dv-header {
  margin-bottom: 28px;
}
.dv-title {
  font-size: 1.5rem;
  font-weight: 800;
  color: #ffffff;
  letter-spacing: -0.02em;
}
.dv-subtitle {
  font-size: 0.85rem;
  color: #64748b;
  margin-top: 4px;
}

/* ── Stat Cards ── */
.resumo-cards {
  display: grid;
  grid-template-columns: repeat(6, 1fr);
  gap: 14px;
  margin-bottom: 28px;
}

.card {
  background: #0d1530;
  border-radius: 14px;
  padding: 22px 16px;
  text-align: center;
  color: #e2e8f0;
  border: 1px solid rgba(0, 102, 255, 0.12);
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.2);
  position: relative;
  overflow: hidden;
  transition:
    transform 0.2s,
    box-shadow 0.2s;
}
.card:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(0, 102, 255, 0.15);
}
.card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
}

.card-total::before {
  background: linear-gradient(90deg, #0066ff, #3388ff);
}
.card-divergente::before {
  background: linear-gradient(90deg, #ef4444, #f87171);
}
.card-pendente::before {
  background: linear-gradient(90deg, #f59e0b, #fbbf24);
}
.card-corrigido::before {
  background: linear-gradient(90deg, #0066ff, #3388ff);
}
.card-verificado::before {
  background: linear-gradient(90deg, #10b981, #34d399);
}
.card-realizada::before {
  background: linear-gradient(90deg, #8b5cf6, #a78bfa);
}

.card-number {
  display: block;
  font-size: 2rem;
  font-weight: 800;
  color: #ffffff;
  line-height: 1;
}

.card-label {
  display: block;
  font-size: 0.7rem;
  color: #64748b;
  margin-top: 8px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.06em;
}

/* ── Actions Bar ── */
.actions-bar {
  display: flex;
  gap: 12px;
  margin-bottom: 24px;
}

.btn {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 10px 20px;
  border: none;
  border-radius: 10px;
  cursor: pointer;
  font-size: 0.85rem;
  font-weight: 600;
  transition: all 0.15s;
}
.btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}
.btn-icon {
  width: 16px;
  height: 16px;
}

.btn-detectar {
  background: #0066ff;
  color: white;
  box-shadow: 0 2px 8px rgba(0, 102, 255, 0.3);
}
.btn-detectar:hover:not(:disabled) {
  background: #0055dd;
  box-shadow: 0 4px 16px rgba(0, 102, 255, 0.4);
}

.btn-wizard {
  background: linear-gradient(135deg, #0066ff, #0044bb);
  color: white;
  box-shadow: 0 2px 8px rgba(0, 102, 255, 0.3);
}
.btn-wizard:hover:not(:disabled) {
  box-shadow: 0 4px 16px rgba(0, 102, 255, 0.4);
}

/* ── Progress ── */
.progress-bar {
  margin-bottom: 24px;
}

.progress-track {
  height: 8px;
  background: #111b3a;
  border-radius: 100px;
  position: relative;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  position: absolute;
  top: 0;
  border-radius: 100px;
  transition: width 0.6s cubic-bezier(0.4, 0, 0.2, 1);
}

.progress-verificado {
  background: linear-gradient(90deg, #10b981, #34d399);
  left: 0;
}
.progress-corrigido {
  background: linear-gradient(90deg, #0066ff, #3388ff);
}

.progress-text {
  font-size: 0.8rem;
  color: #64748b;
  margin-top: 8px;
  display: block;
  font-weight: 500;
}

/* ── Filters ── */
.filter-bar {
  display: flex;
  gap: 8px;
  margin-bottom: 20px;
  flex-wrap: wrap;
}

.filter-btn {
  padding: 7px 16px;
  border: 1.5px solid rgba(255, 255, 255, 0.1);
  border-radius: 100px;
  background: #0d1530;
  cursor: pointer;
  font-size: 0.8rem;
  font-weight: 500;
  color: #94a3b8;
  transition: all 0.15s;
}
.filter-btn:hover {
  border-color: rgba(0, 102, 255, 0.3);
  background: #111b3a;
}

.filter-btn.active {
  border-color: #0066ff;
  background: rgba(0, 102, 255, 0.15);
  color: #0066ff;
  font-weight: 600;
}
.filter-pendente.active {
  border-color: #f59e0b;
  background: rgba(245, 158, 11, 0.1);
  color: #fbbf24;
}
.filter-corrigido.active {
  border-color: #0066ff;
  background: rgba(0, 102, 255, 0.15);
  color: #3388ff;
}
.filter-verificado.active {
  border-color: #10b981;
  background: rgba(16, 185, 129, 0.1);
  color: #34d399;
}
.filter-realizada.active {
  border-color: #8b5cf6;
  background: rgba(139, 92, 246, 0.1);
  color: #a78bfa;
}

/* ── Table ── */
.table-container {
  background: #0d1530;
  border-radius: 14px;
  border: 1px solid rgba(0, 102, 255, 0.12);
  overflow: hidden;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.2);
}

table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.82rem;
}

th {
  background: #111b3a;
  color: #64748b;
  font-weight: 600;
  font-size: 0.7rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  padding: 12px 12px;
  text-align: center;
  white-space: nowrap;
  border-bottom: 1px solid rgba(0, 102, 255, 0.1);
}

td {
  padding: 10px 12px;
  text-align: center;
  border-bottom: 1px solid rgba(255, 255, 255, 0.04);
  color: #cbd5e1;
}

tr:last-child td {
  border-bottom: none;
}

tr:hover td {
  background: rgba(0, 102, 255, 0.05);
}

.col-code {
  font-weight: 700;
  color: #ffffff;
  font-size: 0.85rem;
}
.col-desc {
  text-align: left;
  max-width: 260px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  color: #cbd5e1;
}
.col-arrow {
  width: 24px;
}
.col-compare {
  min-width: 48px;
}
.col-actions {
  min-width: 180px;
}

.arrow {
  color: #475569;
  font-weight: 600;
}

td.divergent {
  background: rgba(239, 68, 68, 0.1);
  color: #f87171;
  font-weight: 700;
  font-size: 0.85rem;
}
td.corrected {
  background: rgba(16, 185, 129, 0.1);
  color: #34d399;
  font-weight: 700;
  font-size: 0.85rem;
}

/* ── Badges ── */
.badge {
  display: inline-block;
  padding: 4px 12px;
  border-radius: 100px;
  font-size: 0.7rem;
  font-weight: 600;
  white-space: nowrap;
  letter-spacing: 0.02em;
}

.badge-pendente {
  background: rgba(245, 158, 11, 0.15);
  color: #fbbf24;
}
.badge-corrigido {
  background: rgba(0, 102, 255, 0.15);
  color: #3388ff;
}
.badge-verificado {
  background: rgba(16, 185, 129, 0.12);
  color: #34d399;
}
.badge-realizada {
  background: rgba(139, 92, 246, 0.15);
  color: #a78bfa;
}

/* ── Row States ── */
.row-corrigido td {
  background: rgba(0, 102, 255, 0.04);
}
.row-corrigido:hover td {
  background: rgba(0, 102, 255, 0.08);
}
.row-verificado td {
  background: rgba(16, 185, 129, 0.04);
}
.row-verificado:hover td {
  background: rgba(16, 185, 129, 0.08);
}
.row-realizada td {
  background: rgba(139, 92, 246, 0.04);
}
.row-realizada:hover td {
  background: rgba(139, 92, 246, 0.08);
}

/* ── Small Action Buttons ── */
.btn-sm {
  padding: 5px 12px;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 0.72rem;
  font-weight: 600;
  margin: 2px;
  transition: all 0.15s;
}

.btn-corrigir {
  background: #0066ff;
  color: white;
}
.btn-corrigir:hover {
  background: #0055dd;
}
.btn-verificar {
  background: #10b981;
  color: white;
}
.btn-verificar:hover {
  background: #059669;
}
.btn-resetar {
  background: rgba(255, 255, 255, 0.06);
  color: #94a3b8;
}
.btn-resetar:hover {
  background: rgba(255, 255, 255, 0.1);
  color: #e2e8f0;
}
.btn-realizada {
  background: #8b5cf6;
  color: white;
}
.btn-realizada:hover {
  background: #7c3aed;
}
.btn-salvar {
  background: #10b981;
  color: white;
  animation: pulse-save 1s ease-in-out infinite;
}
.btn-salvar:hover {
  background: #059669;
}
@keyframes pulse-save {
  0%,
  100% {
    box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.4);
  }
  50% {
    box-shadow: 0 0 0 4px rgba(16, 185, 129, 0);
  }
}

/* ── States ── */
.no-divergences {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  text-align: center;
  padding: 40px;
  font-size: 1rem;
  font-weight: 600;
  color: #34d399;
  background: rgba(16, 185, 129, 0.08);
  border: 1px solid rgba(16, 185, 129, 0.2);
  border-radius: 14px;
  margin-top: 20px;
}
.nd-icon {
  width: 28px;
  height: 28px;
  color: #34d399;
}

.loading {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  text-align: center;
  padding: 40px;
  color: #64748b;
  font-weight: 500;
}
.loading-spinner {
  width: 20px;
  height: 20px;
  border: 2.5px solid rgba(255, 255, 255, 0.1);
  border-top-color: #0066ff;
  border-radius: 50%;
  animation: spin 0.7s linear infinite;
}
@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.error-message {
  color: #f87171;
  padding: 14px 18px;
  background: rgba(239, 68, 68, 0.1);
  border: 1px solid rgba(239, 68, 68, 0.2);
  border-radius: 10px;
  margin-top: 12px;
  font-size: 0.85rem;
  font-weight: 500;
}

/* ── Pagination ── */
.pagination {
  margin-top: 20px;
  padding-top: 16px;
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 12px;
}

.pagination button {
  background: #0d1530;
  color: #cbd5e1;
  padding: 8px 18px;
  border: 1.5px solid rgba(0, 102, 255, 0.15);
  border-radius: 8px;
  cursor: pointer;
  font-size: 0.82rem;
  font-weight: 600;
  transition: all 0.15s;
}
.pagination button:hover:not(:disabled) {
  border-color: #0066ff;
  color: #0066ff;
  background: rgba(0, 102, 255, 0.1);
}
.pagination button:disabled {
  background: #0a1024;
  color: #334155;
  border-color: rgba(255, 255, 255, 0.05);
  cursor: not-allowed;
}

.pagination span {
  font-size: 0.82rem;
  color: #64748b;
  font-weight: 500;
}

/* ── Responsive ── */
@media (max-width: 900px) {
  .resumo-cards {
    grid-template-columns: repeat(3, 1fr);
  }
}
@media (max-width: 600px) {
  .resumo-cards {
    grid-template-columns: repeat(2, 1fr);
  }
}
</style>
