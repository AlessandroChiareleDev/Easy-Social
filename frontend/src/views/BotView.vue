<template>
  <div class="bot-view">
    <h1>Robô eSocial</h1>

    <div class="bot-controls">
      <div class="status-badge" :class="statusClass">
        {{ statusLabel }}
      </div>

      <div class="btn-group">
        <button class="btn btn-start" @click="startBot" :disabled="botRunning">
          ▶ Iniciar Robô
        </button>
        <button class="btn btn-stop" @click="stopBot" :disabled="!botRunning">⏹ Parar Robô</button>
        <button class="btn btn-screenshot" @click="takeScreenshot">📸 Capturar Tela</button>
      </div>
    </div>

    <div class="calibration-section" :class="{ calibrated: isCalibrated }">
      <div v-if="isCalibrated" class="calibration-ok">
        <strong>✅ Calibrado</strong> em {{ calibratedAt }}
      </div>
      <div v-else class="calibration-missing">
        <strong>⚠️ Bot não calibrado!</strong>
        <p>Execute no terminal do Python:</p>
        <code
          >cd python-scripts && .\venv\Scripts\activate && python bot_esocial.py --calibrate</code
        >
        <p class="cal-steps">
          1. Esteja logado no eSocial na Tabela de Rubricas<br />
          2. Pesquise qualquer rubrica<br />
          3. Posicione o mouse sobre cada elemento e pressione F2
        </p>
      </div>
    </div>

    <div v-if="resumo" class="progress-section">
      <h3>Progresso</h3>
      <div class="progress-bar">
        <div class="progress-fill" :style="{ width: progressPercent + '%' }">
          {{ progressPercent }}%
        </div>
      </div>
      <p class="progress-text">
        {{ resumo.corrigidas }} de {{ resumo.total }} rubricas processadas
        <span v-if="resumo.erros > 0" class="error-count">({{ resumo.erros }} erros)</span>
      </p>
    </div>

    <div v-if="currentRubrica" class="current-rubrica">
      <h3>Rubrica Atual</h3>
      <div class="rubrica-card">
        <p><strong>Código:</strong> {{ currentRubrica.codigo }}</p>
        <p><strong>Nome:</strong> {{ currentRubrica.nome }}</p>
        <p v-if="currentRubrica.inss_esperado">
          <strong>INSS:</strong> {{ currentRubrica.inss_atual }} →
          {{ currentRubrica.inss_esperado }}
        </p>
        <p v-if="currentRubrica.irrf_esperado">
          <strong>IRRF:</strong> {{ currentRubrica.irrf_atual }} →
          {{ currentRubrica.irrf_esperado }}
        </p>
        <p v-if="currentRubrica.fgts_esperado">
          <strong>FGTS:</strong> {{ currentRubrica.fgts_atual }} →
          {{ currentRubrica.fgts_esperado }}
        </p>
      </div>
    </div>

    <div v-if="screenshotUrl" class="screenshot-section">
      <h3>Última Captura</h3>
      <img :src="screenshotUrl" alt="Screenshot" class="screenshot-img" />
    </div>

    <div class="log-section">
      <h3>Log do Robô</h3>
      <div class="log-container" ref="logContainer">
        <div v-for="(entry, i) in logEntries" :key="i" class="log-entry" :class="entry.level">
          <span class="log-time">{{ entry.time }}</span>
          <span class="log-msg">{{ entry.message }}</span>
        </div>
        <div v-if="logEntries.length === 0" class="log-empty">
          Nenhum log ainda. Inicie o robô para ver a atividade.
        </div>
      </div>
    </div>

    <div v-if="error" class="error-message">❌ {{ error }}</div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue'
import axios from 'axios'

const BOT_API = 'http://localhost:8000'

const botStatus = ref('parado')
const resumo = ref<any>(null)
const currentRubrica = ref<any>(null)
const screenshotUrl = ref<string | null>(null)
const logEntries = ref<{ time: string; message: string; level: string }[]>([])
const error = ref<string | null>(null)
const logContainer = ref<HTMLElement | null>(null)
const isCalibrated = ref(false)
const calibratedAt = ref('')
let pollInterval: number | null = null

const botRunning = computed(() => botStatus.value === 'running')

const statusClass = computed(() => {
  if (botStatus.value === 'running') return 'running'
  if (botStatus.value === 'error') return 'error'
  return 'stopped'
})

const statusLabel = computed(() => {
  const labels: Record<string, string> = {
    idle: '⏹ Parado',
    stopped: '⏹ Parado',
    running: '▶ Rodando',
    paused: '⏸ Pausado',
    error: '❌ Erro',
  }
  return labels[botStatus.value] || botStatus.value
})

const progressPercent = computed(() => {
  if (!resumo.value || resumo.value.total === 0) return 0
  return Math.round((resumo.value.corrigidas / resumo.value.total) * 100)
})

const fetchStatus = async () => {
  try {
    const resp = await axios.get(`${BOT_API}/bot/status`)
    const data = resp.data
    botStatus.value = data.bot_status || 'parado'
    isCalibrated.value = !!data.calibrated
    calibratedAt.value = data.calibrated_at
      ? new Date(data.calibrated_at).toLocaleString('pt-BR')
      : ''
    if (data.total !== undefined) {
      resumo.value = {
        total: data.total,
        corrigidas: data.total_corrigidas || 0,
        erros: data.total_erros || 0,
        pendentes: data.total_pendentes || 0,
      }
    }
    if (data.current_rubrica) {
      currentRubrica.value = {
        codigo: data.current_rubrica.cod_rubrica,
        nome: data.current_rubrica.descricao,
        inss_atual: data.current_rubrica.inss_antes,
        inss_esperado: data.current_rubrica.inss_correto,
        irrf_atual: data.current_rubrica.irrf_antes,
        irrf_esperado: data.current_rubrica.irrf_correto,
        fgts_atual: data.current_rubrica.fgts_antes,
        fgts_esperado: data.current_rubrica.fgts_correto,
      }
    } else {
      currentRubrica.value = null
    }
    if (data.log && data.log.length > 0) {
      logEntries.value = data.log.map((entry: any) => {
        if (typeof entry === 'string') {
          const match = entry.match(/^\[(.+?)\]\s*(.*)$/)
          return {
            time: match ? match[1] : '',
            message: match ? match[2] : entry,
            level: entry.includes('❌')
              ? 'error'
              : entry.includes('⚠')
                ? 'warning'
                : entry.includes('✅')
                  ? 'success'
                  : '',
          }
        }
        return entry
      })
      await nextTick()
      if (logContainer.value) {
        logContainer.value.scrollTop = logContainer.value.scrollHeight
      }
    }
  } catch {
    // API offline
  }
}

const startBot = async () => {
  error.value = null
  try {
    await axios.post(`${BOT_API}/bot/start`)
    botStatus.value = 'rodando'
  } catch (err: any) {
    error.value = err.response?.data?.detail || 'Erro ao iniciar o robô'
  }
}

const stopBot = async () => {
  try {
    await axios.post(`${BOT_API}/bot/stop`)
    botStatus.value = 'parado'
  } catch (err: any) {
    error.value = err.response?.data?.detail || 'Erro ao parar o robô'
  }
}

const takeScreenshot = async () => {
  try {
    const resp = await axios.post(`${BOT_API}/bot/screenshot`)
    if (resp.data.path) {
      screenshotUrl.value = `${BOT_API}/bot/screenshot/view?t=${Date.now()}`
    }
  } catch (err: any) {
    error.value = err.response?.data?.detail || 'Erro ao capturar tela'
  }
}

onMounted(() => {
  fetchStatus()
  pollInterval = window.setInterval(fetchStatus, 2000)
})

onUnmounted(() => {
  if (pollInterval) clearInterval(pollInterval)
})
</script>

<style scoped>
.bot-view {
  padding: 20px;
  max-width: 1000px;
  margin: 0 auto;
  color: #333;
}

h1 {
  margin-bottom: 20px;
}

.bot-controls {
  display: flex;
  align-items: center;
  gap: 20px;
  margin-bottom: 24px;
  flex-wrap: wrap;
}

.status-badge {
  padding: 8px 20px;
  border-radius: 20px;
  font-weight: bold;
  font-size: 0.95rem;
}

.status-badge.running {
  background: #d4edda;
  color: #155724;
}
.status-badge.stopped {
  background: #e2e3e5;
  color: #383d41;
}
.status-badge.error {
  background: #f8d7da;
  color: #721c24;
}

.btn-group {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.btn {
  padding: 10px 18px;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 0.9rem;
  font-weight: 600;
  transition: opacity 0.2s;
}

.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
.btn-start {
  background: #28a745;
  color: white;
}
.btn-stop {
  background: #dc3545;
  color: white;
}
.btn-screenshot {
  background: #17a2b8;
  color: white;
}

.calibration-section {
  padding: 16px;
  border-radius: 8px;
  margin-bottom: 24px;
  border-left: 4px solid #ffc107;
  background: #fff3cd;
}

.calibration-section.calibrated {
  border-left-color: #28a745;
  background: #d4edda;
}

.calibration-ok {
  color: #155724;
}

.calibration-missing {
  color: #856404;
}

.calibration-missing code {
  display: block;
  background: #1e1e1e;
  color: #d4d4d4;
  padding: 10px;
  border-radius: 4px;
  margin: 8px 0;
  font-size: 13px;
  word-break: break-all;
}

.cal-steps {
  margin-top: 8px;
  font-size: 0.9rem;
  line-height: 1.6;
}

.progress-section {
  margin-bottom: 24px;
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
.error-count {
  color: #dc3545;
}

.current-rubrica {
  margin-bottom: 24px;
}

.rubrica-card {
  background: #f8f9fa;
  border-left: 4px solid #007bff;
  padding: 16px;
  border-radius: 6px;
}

.rubrica-card p {
  margin: 4px 0;
}

.screenshot-section {
  margin-bottom: 24px;
}

.screenshot-img {
  max-width: 100%;
  border: 1px solid #ddd;
  border-radius: 6px;
  margin-top: 8px;
}

.log-section {
  margin-bottom: 24px;
}

.log-container {
  background: #1e1e1e;
  color: #d4d4d4;
  border-radius: 6px;
  padding: 12px;
  max-height: 400px;
  overflow-y: auto;
  font-family: 'Consolas', 'Courier New', monospace;
  font-size: 13px;
}

.log-entry {
  padding: 2px 0;
  border-bottom: 1px solid #333;
}

.log-entry.error {
  color: #f44;
}
.log-entry.warning {
  color: #fa0;
}
.log-entry.success {
  color: #4f4;
}

.log-time {
  color: #888;
  margin-right: 8px;
}

.log-empty {
  color: #666;
  text-align: center;
  padding: 20px;
}

.error-message {
  color: #dc3545;
  padding: 10px;
  background-color: #f8d7da;
  border-radius: 4px;
  margin-top: 10px;
}
</style>
