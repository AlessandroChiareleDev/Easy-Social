<template>
  <div class="painel-view">
    <h1>Painel Easy Social</h1>

    <div class="stats-grid" v-if="resumo">
      <div class="stat-card">
        <span class="stat-number">{{ resumo.total_rubricas }}</span>
        <span class="stat-label">Total Rubricas</span>
      </div>
      <div class="stat-card divergente">
        <span class="stat-number">{{ resumo.total_divergentes }}</span>
        <span class="stat-label">Divergentes</span>
      </div>
      <div class="stat-card pendente">
        <span class="stat-number">{{ resumo.total_pendentes }}</span>
        <span class="stat-label">Pendentes</span>
      </div>
      <div class="stat-card corrigida">
        <span class="stat-number">{{ resumo.total_corrigidas }}</span>
        <span class="stat-label">Corrigidas</span>
      </div>
      <div class="stat-card verificada">
        <span class="stat-number">{{ resumo.total_verificadas }}</span>
        <span class="stat-label">Verificadas</span>
      </div>
    </div>

    <div v-if="resumo && resumo.total_divergentes > 0" class="progress-section">
      <h3>Progresso das Correções</h3>
      <div class="progress-bar">
        <div class="progress-fill" :style="{ width: progressPercent + '%' }">
          {{ progressPercent }}%
        </div>
      </div>
      <p class="progress-text">
        {{ resumo.total_corrigidas + resumo.total_verificadas }} de
        {{ resumo.total_divergentes }} corrigidas
      </p>
    </div>

    <div v-if="!resumo && !loading" class="empty-state">
      <p>Nenhum dado encontrado. Verifique se o banco de dados está populado.</p>
    </div>

    <div v-if="loading" class="loading">Carregando resumo...</div>
    <div v-if="error" class="error-message">❌ {{ error }}</div>

    <DivergenceViewer />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import axios from 'axios'
import DivergenceViewer from '../components/DivergenceViewer.vue'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:3333/api'

const resumo = ref<any>(null)
const loading = ref(false)
const error = ref<string | null>(null)

const progressPercent = computed(() => {
  if (!resumo.value || resumo.value.total_divergentes === 0) return 0
  const done = resumo.value.total_corrigidas + resumo.value.total_verificadas
  return Math.round((done / resumo.value.total_divergentes) * 100)
})

const fetchResumo = async () => {
  loading.value = true
  error.value = null
  try {
    const resp = await axios.get(`${API_URL}/validacao/resumo`)
    resumo.value = resp.data
  } catch (err: any) {
    error.value = err.response?.data?.error || 'Erro ao carregar resumo'
  } finally {
    loading.value = false
  }
}

onMounted(fetchResumo)
</script>

<style scoped>
.painel-view {
  padding: 20px;
  max-width: 1200px;
  margin: 0 auto;
  color: #333;
}

h1 {
  margin-bottom: 24px;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 16px;
  margin-bottom: 30px;
}

.stat-card {
  background: #f8f9fa;
  border-radius: 8px;
  padding: 20px;
  text-align: center;
  border-left: 4px solid #6c757d;
}

.stat-card.divergente {
  border-left-color: #dc3545;
}
.stat-card.pendente {
  border-left-color: #ffc107;
}
.stat-card.corrigida {
  border-left-color: #28a745;
}
.stat-card.verificada {
  border-left-color: #007bff;
}

.stat-number {
  display: block;
  font-size: 2rem;
  font-weight: bold;
}

.stat-label {
  display: block;
  font-size: 0.85rem;
  color: #666;
  margin-top: 4px;
}

.progress-section {
  margin-bottom: 30px;
}

.progress-bar {
  width: 100%;
  height: 28px;
  background: #e9ecef;
  border-radius: 14px;
  overflow: hidden;
  margin-top: 8px;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #28a745, #20c997);
  color: white;
  font-size: 13px;
  font-weight: bold;
  display: flex;
  align-items: center;
  justify-content: center;
  min-width: 40px;
  transition: width 0.5s;
}

.progress-text {
  margin-top: 6px;
  color: #666;
  font-size: 0.9rem;
}

.empty-state {
  text-align: center;
  padding: 40px;
  color: #999;
}

.loading {
  text-align: center;
  padding: 20px;
  color: #666;
}

.error-message {
  color: #dc3545;
  padding: 10px;
  background-color: #f8d7da;
  border-radius: 4px;
  margin-top: 10px;
}
</style>
