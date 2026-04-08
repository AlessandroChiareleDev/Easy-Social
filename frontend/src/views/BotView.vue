<template>
  <div class="bot-view">
    <!-- Glass shapes -->
    <div class="glass-shapes">
      <div class="glass-shape shape-1"></div>
      <div class="glass-shape shape-2"></div>
      <div class="glass-shape shape-3"></div>
    </div>

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
import { PYTHON_API } from '../lib/api'

const BOT_API = PYTHON_API

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
  position: relative;
  overflow: hidden;
  padding: 20px;
  max-width: 1000px;
  margin: 0 auto;
  color: #e2e8f0;
}

h1 {
  margin-bottom: 20px;
  color: #ffffff;
}

h3 {
  color: #ffffff;
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
  background: rgba(16, 185, 129, 0.15);
  color: #34d399;
}
.status-badge.stopped {
  background: rgba(255, 255, 255, 0.06);
  color: #94a3b8;
}
.status-badge.error {
  background: rgba(239, 68, 68, 0.15);
  color: #f87171;
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
  background: #0066ff;
  color: white;
}
.btn-stop {
  background: rgba(239, 68, 68, 0.8);
  color: white;
}
.btn-screenshot {
  background: rgba(17, 27, 58, 0.7);
  backdrop-filter: blur(12px);
  color: #cbd5e1;
  border: 1px solid rgba(0, 102, 255, 0.15);
}

.calibration-section {
  padding: 16px;
  border-radius: 8px;
  margin-bottom: 24px;
  border-left: 4px solid #f59e0b;
  background: rgba(245, 158, 11, 0.08);
  backdrop-filter: blur(12px);
}

.calibration-section.calibrated {
  border-left-color: #0066ff;
  background: rgba(0, 102, 255, 0.08);
}

.calibration-ok {
  color: #34d399;
}

.calibration-missing {
  color: #fbbf24;
}

.calibration-missing code {
  display: block;
  background: #0a1024;
  color: #d4d4d4;
  padding: 10px;
  border-radius: 4px;
  margin: 8px 0;
  font-size: 13px;
  word-break: break-all;
  border: 1px solid rgba(0, 102, 255, 0.12);
}

.cal-steps {
  margin-top: 8px;
  font-size: 0.9rem;
  line-height: 1.6;
  color: #cbd5e1;
}

.progress-section {
  margin-bottom: 24px;
}

.progress-bar {
  width: 100%;
  height: 28px;
  background: rgba(17, 27, 58, 0.7);
  backdrop-filter: blur(12px);
  border-radius: 14px;
  overflow: hidden;
  margin-top: 8px;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #0066ff, #3388ff);
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
  color: #64748b;
  font-size: 0.9rem;
}
.error-count {
  color: #f87171;
}

.current-rubrica {
  margin-bottom: 24px;
}

.rubrica-card {
  background: rgba(13, 21, 48, 0.7);
  backdrop-filter: blur(16px);
  border-left: 4px solid #0066ff;
  padding: 16px;
  border-radius: 6px;
  border: 1px solid rgba(0, 102, 255, 0.15);
  box-shadow:
    0 0 20px rgba(0, 102, 255, 0.04),
    0 8px 32px rgba(0, 0, 0, 0.3);
}

.rubrica-card p {
  margin: 4px 0;
  color: #cbd5e1;
}

.screenshot-section {
  margin-bottom: 24px;
}

.screenshot-img {
  max-width: 100%;
  border: 1px solid rgba(0, 102, 255, 0.15);
  border-radius: 6px;
  margin-top: 8px;
}

.log-section {
  margin-bottom: 24px;
}

.log-container {
  background: rgba(10, 16, 36, 0.8);
  backdrop-filter: blur(16px);
  color: #d4d4d4;
  border-radius: 6px;
  padding: 12px;
  max-height: 400px;
  overflow-y: auto;
  font-family: 'Consolas', 'Courier New', monospace;
  font-size: 13px;
  border: 1px solid rgba(0, 102, 255, 0.15);
  box-shadow:
    0 0 20px rgba(0, 102, 255, 0.04),
    0 8px 32px rgba(0, 0, 0, 0.3);
}

.log-entry {
  padding: 2px 0;
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
}

.log-entry.error {
  color: #f87171;
}
.log-entry.warning {
  color: #fbbf24;
}
.log-entry.success {
  color: #34d399;
}

.log-time {
  color: #64748b;
  margin-right: 8px;
}

.log-empty {
  color: #475569;
  text-align: center;
  padding: 20px;
}

.error-message {
  color: #f87171;
  padding: 10px;
  background-color: rgba(239, 68, 68, 0.1);
  border: 1px solid rgba(239, 68, 68, 0.2);
  border-radius: 4px;
  margin-top: 10px;
}

/* ── Glass Shapes ── */
.glass-shapes {
  position: absolute;
  inset: 0;
  pointer-events: none;
  overflow: hidden;
}
.glass-shape {
  position: absolute;
  border-radius: 50%;
  border: 1px solid rgba(0, 102, 255, 0.15);
  background: rgba(0, 102, 255, 0.04);
  box-shadow:
    0 0 15px rgba(0, 102, 255, 0.2),
    0 0 40px rgba(0, 102, 255, 0.1);
}
.shape-1 {
  width: 280px;
  height: 280px;
  top: -60px;
  right: -60px;
  filter: blur(2px);
  animation: drift1 26s ease-in-out infinite;
}
.shape-2 {
  width: 200px;
  height: 200px;
  bottom: 10%;
  left: -40px;
  border-radius: 36px;
  filter: blur(1.5px);
  animation: drift2 30s ease-in-out infinite;
}
.shape-3 {
  width: 150px;
  height: 150px;
  top: 40%;
  left: 55%;
  filter: blur(3px);
  animation: drift3 22s ease-in-out infinite;
  animation-delay: -8s;
}
@keyframes drift1 {
  0%,
  100% {
    transform: translate(-10%, -15%) rotate(0deg);
  }
  50% {
    transform: translate(30%, 50%) rotate(25deg);
  }
}
@keyframes drift2 {
  0%,
  100% {
    transform: translate(10%, -20%) rotate(45deg);
  }
  50% {
    transform: translate(-40%, 60%) rotate(90deg);
  }
}
@keyframes drift3 {
  0%,
  100% {
    transform: translate(0, -20%) rotate(0deg);
  }
  50% {
    transform: translate(-25%, 70%) rotate(-20deg);
  }
}
</style>
