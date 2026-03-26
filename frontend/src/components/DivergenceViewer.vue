<template>
  <div class="divergence-viewer">
    <h2>🔍 Validação de Rubricas — Ponto 1</h2>

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
    </div>

    <!-- Ações -->
    <div class="actions-bar">
      <button class="btn btn-detectar" @click="executarDeteccao" :disabled="detecting">
        {{ detecting ? 'Analisando...' : '🔄 Detectar Divergências' }}
      </button>
      <button
        class="btn btn-wizard"
        @click="abrirWizard"
        :disabled="!resumo || resumo.total_pendentes === 0"
      >
        🧭 Iniciar Correção Guiada
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
        {{ resumo.total_corrigidas + resumo.total_verificadas }} /
        {{ resumo.total_divergentes }} tratadas ({{
          Math.round(
            ((resumo.total_corrigidas + resumo.total_verificadas) / resumo.total_divergentes) * 100,
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
                v-if="div.status === 'pendente'"
                class="btn-sm btn-corrigir"
                @click="marcarCorrigido(div.id)"
              >
                ✅ Corrigido
              </button>
              <button
                v-if="div.status === 'corrigido'"
                class="btn-sm btn-verificar"
                @click="marcarVerificado(div.id)"
              >
                🔍 Verificar
              </button>
              <button
                v-if="div.status !== 'pendente'"
                class="btn-sm btn-resetar"
                @click="resetar(div.id)"
              >
                ↩ Resetar
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
      ✅ Nenhuma divergência encontrada! Todas as rubricas estão corretas.
    </div>

    <div v-if="loading" class="loading">Carregando...</div>
    <div v-if="error" class="error-message">❌ {{ error }}</div>

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
.divergence-viewer {
  padding: 20px;
  color: #333;
}

/* Cards de Resumo */
.resumo-cards {
  display: flex;
  gap: 12px;
  margin: 20px 0;
  flex-wrap: wrap;
}

.card {
  flex: 1;
  min-width: 140px;
  padding: 16px;
  border-radius: 8px;
  text-align: center;
  color: white;
}

.card-number {
  display: block;
  font-size: 28px;
  font-weight: bold;
}

.card-label {
  display: block;
  font-size: 12px;
  margin-top: 4px;
  opacity: 0.9;
}

.card-total {
  background: #607d8b;
}
.card-divergente {
  background: #e53935;
}
.card-pendente {
  background: #ff9800;
}
.card-corrigido {
  background: #2196f3;
}
.card-verificado {
  background: #4caf50;
}

/* Actions Bar */
.actions-bar {
  display: flex;
  gap: 10px;
  margin: 16px 0;
}

.btn {
  padding: 10px 20px;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 600;
}

.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-detectar {
  background: #1976d2;
  color: white;
}
.btn-detectar:hover:not(:disabled) {
  background: #1565c0;
}
.btn-wizard {
  background: #7b1fa2;
  color: white;
}
.btn-wizard:hover:not(:disabled) {
  background: #6a1b9a;
}

/* Progress Bar */
.progress-bar {
  margin: 16px 0;
}

.progress-track {
  height: 20px;
  background: #e0e0e0;
  border-radius: 10px;
  position: relative;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  position: absolute;
  top: 0;
  transition: width 0.5s ease;
}

.progress-verificado {
  background: #4caf50;
  left: 0;
}
.progress-corrigido {
  background: #2196f3;
}

.progress-text {
  font-size: 13px;
  color: #666;
  margin-top: 4px;
  display: block;
}

/* Filtros */
.filter-bar {
  display: flex;
  gap: 8px;
  margin: 16px 0;
  flex-wrap: wrap;
}

.filter-btn {
  padding: 6px 14px;
  border: 2px solid #ccc;
  border-radius: 20px;
  background: white;
  cursor: pointer;
  font-size: 13px;
}

.filter-btn.active {
  border-color: #1976d2;
  background: #e3f2fd;
  color: #1976d2;
  font-weight: 600;
}

.filter-pendente.active {
  border-color: #ff9800;
  background: #fff3e0;
  color: #e65100;
}
.filter-corrigido.active {
  border-color: #2196f3;
  background: #e3f2fd;
  color: #1565c0;
}
.filter-verificado.active {
  border-color: #4caf50;
  background: #e8f5e9;
  color: #2e7d32;
}

/* Tabela */
.table-container {
  overflow-x: auto;
  margin-top: 16px;
}

table {
  width: 100%;
  border-collapse: collapse;
  background: white;
  font-size: 13px;
}

th,
td {
  border: 1px solid #e0e0e0;
  padding: 8px 10px;
  text-align: center;
}

th {
  background: #37474f;
  color: white;
  font-weight: 600;
  font-size: 12px;
  white-space: nowrap;
}

.col-code {
  font-weight: bold;
  font-size: 14px;
}
.col-desc {
  text-align: left;
  max-width: 250px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.col-arrow {
  width: 20px;
}
.col-compare {
  min-width: 50px;
}
.col-actions {
  min-width: 120px;
}
.arrow {
  color: #999;
  font-weight: bold;
}

td.divergent {
  background: #ffebee;
  color: #c62828;
  font-weight: bold;
}

td.corrected {
  background: #e8f5e9;
  color: #2e7d32;
  font-weight: bold;
}

/* Status Badges */
.badge {
  padding: 3px 10px;
  border-radius: 12px;
  font-size: 11px;
  font-weight: 600;
  white-space: nowrap;
}

.badge-pendente {
  background: #fff3e0;
  color: #e65100;
}
.badge-corrigido {
  background: #e3f2fd;
  color: #1565c0;
}
.badge-verificado {
  background: #e8f5e9;
  color: #2e7d32;
}

/* Row states */
.row-corrigido {
  background: #f5f9ff;
}
.row-verificado {
  background: #f0faf0;
}

/* Action Buttons */
.btn-sm {
  padding: 4px 8px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 11px;
  margin: 1px;
}

.btn-corrigir {
  background: #2196f3;
  color: white;
}
.btn-corrigir:hover {
  background: #1976d2;
}
.btn-verificar {
  background: #4caf50;
  color: white;
}
.btn-verificar:hover {
  background: #388e3c;
}
.btn-resetar {
  background: #e0e0e0;
  color: #333;
}
.btn-resetar:hover {
  background: #bdbdbd;
}

.no-divergences {
  text-align: center;
  padding: 40px;
  font-size: 18px;
  color: #4caf50;
  background: #e8f5e9;
  border-radius: 8px;
  margin-top: 20px;
}

.loading {
  text-align: center;
  padding: 20px;
  color: #666;
}

.error-message {
  color: #dc3545;
  padding: 10px;
  background: #f8d7da;
  border-radius: 4px;
  margin-top: 10px;
}

/* Pagination */
.pagination {
  margin-top: 16px;
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 10px;
}

.pagination button {
  background: #37474f;
  color: white;
  padding: 8px 15px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

.pagination button:disabled {
  background: #ccc;
  cursor: not-allowed;
}
</style>
