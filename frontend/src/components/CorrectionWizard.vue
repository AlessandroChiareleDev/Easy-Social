<template>
  <div class="wizard-overlay" @click.self="$emit('close')">
    <div class="wizard-modal">
      <div class="wizard-header">
        <h3>🧭 Correção Guiada de Rubricas</h3>
        <button class="btn-close" @click="$emit('close')">✕</button>
      </div>

      <!-- Loading -->
      <div v-if="loading" class="wizard-loading">Carregando próxima rubrica...</div>

      <!-- Todas tratadas -->
      <div v-else-if="!rubrica" class="wizard-done">
        <div class="done-icon">🎉</div>
        <h4>Todas as divergências foram tratadas!</h4>
        <p>Não há mais rubricas pendentes para correção.</p>
        <button class="btn btn-fechar" @click="$emit('close')">Fechar</button>
      </div>

      <!-- Wizard Steps -->
      <div v-else class="wizard-content">
        <!-- Step Indicator -->
        <div class="step-indicator">
          <div
            v-for="s in steps"
            :key="s.num"
            :class="['step-dot', { active: step === s.num, done: step > s.num }]"
            :title="s.label"
          >
            {{ step > s.num ? '✓' : s.num }}
          </div>
        </div>

        <!-- Step 1: Dados da Rubrica -->
        <div v-if="step === 1" class="step-panel">
          <h4>📋 Etapa 1 — Dados da Rubrica</h4>
          <p class="step-desc">Identifique a rubrica divergente abaixo:</p>

          <div class="rubrica-card">
            <div class="rubrica-header">
              <span class="rubrica-code">Código: {{ rubrica.cod_rubrica }}</span>
              <span class="rubrica-desc">{{ rubrica.descricao }}</span>
            </div>

            <div class="compare-grid">
              <div class="compare-header">
                <span></span>
                <span class="col-label col-antes">Atual (D/E/F)</span>
                <span class="col-label">→</span>
                <span class="col-label col-correto">Correto (H/I/J)</span>
              </div>
              <div
                class="compare-row"
                :class="{ 'has-diff': rubrica.inss_antes !== rubrica.inss_correto }"
              >
                <span class="field-name">INSS</span>
                <span class="val-antes">{{ rubrica.inss_antes || '(vazio)' }}</span>
                <span class="arrow">→</span>
                <span class="val-correto">{{ rubrica.inss_correto || '(vazio)' }}</span>
              </div>
              <div
                class="compare-row"
                :class="{ 'has-diff': rubrica.irrf_antes !== rubrica.irrf_correto }"
              >
                <span class="field-name">IRRF</span>
                <span class="val-antes">{{ rubrica.irrf_antes || '(vazio)' }}</span>
                <span class="arrow">→</span>
                <span class="val-correto">{{ rubrica.irrf_correto || '(vazio)' }}</span>
              </div>
              <div
                class="compare-row"
                :class="{ 'has-diff': rubrica.fgts_antes !== rubrica.fgts_correto }"
              >
                <span class="field-name">FGTS</span>
                <span class="val-antes">{{ rubrica.fgts_antes || '(vazio)' }}</span>
                <span class="arrow">→</span>
                <span class="val-correto">{{ rubrica.fgts_correto || '(vazio)' }}</span>
              </div>
            </div>

            <div class="legal-basis" v-if="rubrica.col_h || rubrica.col_i || rubrica.col_j">
              <h5>📜 Base Legal (valores completos H/I/J):</h5>
              <p v-if="rubrica.col_h"><strong>INSS:</strong> {{ rubrica.col_h }}</p>
              <p v-if="rubrica.col_i"><strong>IRRF:</strong> {{ rubrica.col_i }}</p>
              <p v-if="rubrica.col_j"><strong>FGTS:</strong> {{ rubrica.col_j }}</p>
            </div>
          </div>

          <div class="step-actions">
            <button class="btn btn-next" @click="step = 2">Avançar → Buscar no eSocial</button>
          </div>
        </div>

        <!-- Step 2: Buscar no eSocial -->
        <div v-if="step === 2" class="step-panel">
          <h4>🔍 Etapa 2 — Buscar no eSocial (Print 1)</h4>
          <p class="step-desc">
            No sistema eSocial, acesse:
            <strong>Empregador/Contribuinte → Tabelas → Tabela de Rubricas</strong>
          </p>

          <div class="instruction-box">
            <div class="instruction-step">
              <span class="num">1</span>
              <span>No campo <strong>"Código da rubrica"</strong>, digite:</span>
            </div>
            <div class="copy-value" @click="copiarTexto(rubrica.cod_rubrica)">
              <span class="value">{{ rubrica.cod_rubrica }}</span>
              <span class="copy-icon">📋 Copiar</span>
            </div>
            <div class="instruction-step">
              <span class="num">2</span>
              <span>Clique em pesquisar</span>
            </div>
          </div>

          <div class="warning-box">
            ⚠️ <strong>Atenção — Busca Regex!</strong> A busca no eSocial não é exata. Ao buscar "{{
              rubrica.cod_rubrica
            }}", podem aparecer resultados como {{ rubrica.cod_rubrica }}0,
            {{ rubrica.cod_rubrica }}1, etc. <br /><br />
            Você deve selecionar o resultado que corresponda <strong>exatamente</strong> ao: <br />•
            Código: <strong>{{ rubrica.cod_rubrica }}</strong> <br />• Descrição:
            <strong>{{ rubrica.descricao }}</strong>
          </div>

          <div class="step-actions">
            <button class="btn btn-back" @click="step = 1">← Voltar</button>
            <button class="btn btn-next" @click="step = 3">Encontrei a rubrica → Avançar</button>
          </div>
        </div>

        <!-- Step 3: Editar no eSocial -->
        <div v-if="step === 3" class="step-panel">
          <h4>✏️ Etapa 3 — Aplicar Correção no eSocial (Prints 3→4)</h4>
          <p class="step-desc">
            Na tela de edição da rubrica, altere os campos de incidência tributária:
          </p>

          <div class="correction-guide">
            <div class="correction-field" v-if="rubrica.inss_antes !== rubrica.inss_correto">
              <span class="field-label">Incidência Tributária - Previdência Social (INSS):</span>
              <div class="correction-values">
                <span class="old-val">{{ rubrica.inss_antes || '(vazio)' }}</span>
                <span class="arrow-big">→</span>
                <span class="new-val" @click="copiarTexto(rubrica.inss_correto)">
                  {{ rubrica.inss_correto }} 📋
                </span>
              </div>
            </div>

            <div class="correction-field" v-if="rubrica.irrf_antes !== rubrica.irrf_correto">
              <span class="field-label">Incidência Tributária - IRRF:</span>
              <div class="correction-values">
                <span class="old-val">{{ rubrica.irrf_antes || '(vazio)' }}</span>
                <span class="arrow-big">→</span>
                <span class="new-val" @click="copiarTexto(rubrica.irrf_correto)">
                  {{ rubrica.irrf_correto }} 📋
                </span>
              </div>
            </div>

            <div class="correction-field" v-if="rubrica.fgts_antes !== rubrica.fgts_correto">
              <span class="field-label">Incidência Tributária - FGTS:</span>
              <div class="correction-values">
                <span class="old-val">{{ rubrica.fgts_antes || '(vazio)' }}</span>
                <span class="arrow-big">→</span>
                <span class="new-val" @click="copiarTexto(rubrica.fgts_correto)">
                  {{ rubrica.fgts_correto }} 📋
                </span>
              </div>
            </div>

            <div
              v-if="
                rubrica.inss_antes === rubrica.inss_correto &&
                rubrica.irrf_antes === rubrica.irrf_correto &&
                rubrica.fgts_antes === rubrica.fgts_correto
              "
              class="no-change"
            >
              Nenhuma alteração necessária para esta rubrica.
            </div>
          </div>

          <div class="instruction-box">
            <div class="instruction-step">
              <span class="num">1</span>
              <span>Altere os campos acima no formulário do eSocial</span>
            </div>
            <div class="instruction-step">
              <span class="num">2</span>
              <span>Clique em <strong>"Salvar"</strong> no eSocial</span>
            </div>
            <div class="instruction-step">
              <span class="num">3</span>
              <span>Verifique se os valores foram salvos corretamente</span>
            </div>
          </div>

          <div class="step-actions">
            <button class="btn btn-back" @click="step = 2">← Voltar</button>
            <button class="btn btn-next" @click="step = 4">Correção salva → Validar</button>
          </div>
        </div>

        <!-- Step 4: Validação Final -->
        <div v-if="step === 4" class="step-panel">
          <h4>✅ Etapa 4 — Validação Final</h4>
          <p class="step-desc">Confirme que os valores no eSocial agora correspondem a H/I/J:</p>

          <div class="validation-checklist">
            <div class="check-item" v-if="rubrica.inss_antes !== rubrica.inss_correto">
              <label>
                <input type="checkbox" v-model="checks.inss" />
                INSS = <strong>{{ rubrica.inss_correto }}</strong> no eSocial?
              </label>
            </div>
            <div class="check-item" v-if="rubrica.irrf_antes !== rubrica.irrf_correto">
              <label>
                <input type="checkbox" v-model="checks.irrf" />
                IRRF = <strong>{{ rubrica.irrf_correto }}</strong> no eSocial?
              </label>
            </div>
            <div class="check-item" v-if="rubrica.fgts_antes !== rubrica.fgts_correto">
              <label>
                <input type="checkbox" v-model="checks.fgts" />
                FGTS = <strong>{{ rubrica.fgts_correto }}</strong> no eSocial?
              </label>
            </div>
          </div>

          <div class="obs-field">
            <label>Observação (opcional):</label>
            <textarea
              v-model="observacao"
              placeholder="Ex: Corrigido em 25/03/2026"
              rows="2"
            ></textarea>
          </div>

          <div class="step-actions">
            <button class="btn btn-back" @click="step = 3">← Voltar (corrigir novamente)</button>
            <button class="btn btn-confirm" @click="confirmarCorrecao" :disabled="!allChecked">
              ✅ Confirmar e Avançar
            </button>
          </div>
        </div>
      </div>

      <!-- Footer com contador -->
      <div class="wizard-footer" v-if="rubrica">
        <span>Rubrica {{ currentIndex + 1 }} de {{ totalPendentes }}</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import axios from 'axios'

const emit = defineEmits<{
  (e: 'close'): void
  (e: 'updated'): void
}>()

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:3333/api'

interface Rubrica {
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
  col_h: string
  col_i: string
  col_j: string
}

const rubrica = ref<Rubrica | null>(null)
const loading = ref(true)
const step = ref(1)
const observacao = ref('')
const currentIndex = ref(0)
const totalPendentes = ref(0)

const checks = ref({
  inss: false,
  irrf: false,
  fgts: false,
})

const steps = [
  { num: 1, label: 'Dados da Rubrica' },
  { num: 2, label: 'Buscar no eSocial' },
  { num: 3, label: 'Aplicar Correção' },
  { num: 4, label: 'Validação Final' },
]

const allChecked = computed(() => {
  const r = rubrica.value
  if (!r) return false
  if (r.inss_antes !== r.inss_correto && !checks.value.inss) return false
  if (r.irrf_antes !== r.irrf_correto && !checks.value.irrf) return false
  if (r.fgts_antes !== r.fgts_correto && !checks.value.fgts) return false
  return true
})

async function loadProxima() {
  loading.value = true
  try {
    // Load resumo for count
    const resumoRes = await axios.get(`${API_URL}/validacao/resumo`)
    totalPendentes.value = resumoRes.data.total_pendentes

    const res = await axios.get(`${API_URL}/validacao/proxima`)
    rubrica.value = res.data.data
    step.value = 1
    observacao.value = ''
    checks.value = { inss: false, irrf: false, fgts: false }
  } finally {
    loading.value = false
  }
}

async function confirmarCorrecao() {
  if (!rubrica.value) return
  try {
    await axios.patch(`${API_URL}/validacao/${rubrica.value.id}/corrigir`, {
      observacao: observacao.value || undefined,
    })
    currentIndex.value++
    emit('updated')
    await loadProxima()
  } catch (err) {
    console.error('Erro ao confirmar correção:', err)
  }
}

function copiarTexto(texto: string) {
  navigator.clipboard.writeText(texto)
}

onMounted(() => {
  loadProxima()
})
</script>

<style scoped>
.wizard-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.6);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.wizard-modal {
  background: white;
  border-radius: 12px;
  width: 90%;
  max-width: 700px;
  max-height: 90vh;
  overflow-y: auto;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
}

.wizard-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 24px;
  border-bottom: 1px solid #e0e0e0;
  background: #37474f;
  color: white;
  border-radius: 12px 12px 0 0;
}

.wizard-header h3 {
  margin: 0;
}

.btn-close {
  background: none;
  border: none;
  color: white;
  font-size: 20px;
  cursor: pointer;
}

.wizard-content {
  padding: 24px;
}

.wizard-loading,
.wizard-done {
  padding: 60px 24px;
  text-align: center;
}

.done-icon {
  font-size: 64px;
  margin-bottom: 16px;
}

/* Step Indicator */
.step-indicator {
  display: flex;
  justify-content: center;
  gap: 8px;
  margin-bottom: 24px;
}

.step-dot {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 13px;
  font-weight: bold;
  background: #e0e0e0;
  color: #666;
}

.step-dot.active {
  background: #1976d2;
  color: white;
}
.step-dot.done {
  background: #4caf50;
  color: white;
}

/* Step Panel */
.step-panel h4 {
  margin: 0 0 8px 0;
  color: #37474f;
}
.step-desc {
  color: #666;
  margin-bottom: 16px;
}

/* Rubrica Card */
.rubrica-card {
  background: #f5f5f5;
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 16px;
}

.rubrica-header {
  margin-bottom: 12px;
}

.rubrica-code {
  display: block;
  font-size: 18px;
  font-weight: bold;
  color: #1976d2;
}

.rubrica-desc {
  display: block;
  color: #555;
  margin-top: 4px;
}

/* Compare Grid */
.compare-grid {
  background: white;
  border-radius: 6px;
  overflow: hidden;
  border: 1px solid #e0e0e0;
}

.compare-header,
.compare-row {
  display: grid;
  grid-template-columns: 60px 1fr 30px 1fr;
  align-items: center;
  padding: 8px 12px;
}

.compare-header {
  background: #37474f;
  color: white;
  font-size: 12px;
  font-weight: 600;
}

.compare-row {
  border-top: 1px solid #e0e0e0;
}

.compare-row.has-diff {
  background: #fff8e1;
}

.field-name {
  font-weight: 600;
  color: #37474f;
}
.val-antes {
  color: #c62828;
  font-weight: bold;
  text-align: center;
}
.val-correto {
  color: #2e7d32;
  font-weight: bold;
  text-align: center;
}
.arrow {
  text-align: center;
  color: #999;
}
.col-label {
  text-align: center;
  font-size: 11px;
}
.col-antes {
  color: #ffcdd2;
}
.col-correto {
  color: #c8e6c9;
}

/* Legal Basis */
.legal-basis {
  margin-top: 12px;
  padding: 12px;
  background: #e3f2fd;
  border-radius: 6px;
  font-size: 12px;
}

.legal-basis h5 {
  margin: 0 0 8px 0;
}
.legal-basis p {
  margin: 4px 0;
  word-break: break-word;
}

/* Instruction Box */
.instruction-box {
  background: #f5f5f5;
  border-radius: 8px;
  padding: 16px;
  margin: 16px 0;
}

.instruction-step {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px 0;
}

.instruction-step .num {
  width: 28px;
  height: 28px;
  background: #1976d2;
  color: white;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: bold;
  font-size: 13px;
  flex-shrink: 0;
}

.copy-value {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: white;
  border: 2px dashed #1976d2;
  border-radius: 6px;
  padding: 12px 16px;
  margin: 8px 0 8px 40px;
  cursor: pointer;
}

.copy-value:hover {
  background: #e3f2fd;
}

.copy-value .value {
  font-size: 24px;
  font-weight: bold;
  color: #1976d2;
}

.copy-value .copy-icon {
  color: #1976d2;
  font-size: 13px;
}

/* Warning Box */
.warning-box {
  background: #fff3e0;
  border: 1px solid #ffcc80;
  border-radius: 8px;
  padding: 16px;
  margin: 16px 0;
  font-size: 13px;
  color: #e65100;
  line-height: 1.6;
}

/* Correction Guide */
.correction-guide {
  margin: 16px 0;
}

.correction-field {
  background: #f5f5f5;
  border-radius: 8px;
  padding: 12px 16px;
  margin-bottom: 8px;
}

.field-label {
  display: block;
  font-size: 13px;
  color: #666;
  margin-bottom: 8px;
}

.correction-values {
  display: flex;
  align-items: center;
  gap: 12px;
}

.old-val {
  padding: 6px 12px;
  background: #ffebee;
  color: #c62828;
  border-radius: 4px;
  font-weight: bold;
  font-size: 18px;
}

.arrow-big {
  font-size: 24px;
  color: #999;
}

.new-val {
  padding: 6px 12px;
  background: #e8f5e9;
  color: #2e7d32;
  border-radius: 4px;
  font-weight: bold;
  font-size: 18px;
  cursor: pointer;
}

.new-val:hover {
  background: #c8e6c9;
}

/* Validation Checklist */
.validation-checklist {
  margin: 16px 0;
}

.check-item {
  padding: 12px;
  background: #f5f5f5;
  border-radius: 6px;
  margin-bottom: 8px;
}

.check-item label {
  display: flex;
  align-items: center;
  gap: 10px;
  cursor: pointer;
  font-size: 14px;
}

.check-item input[type='checkbox'] {
  width: 20px;
  height: 20px;
  cursor: pointer;
}

.obs-field {
  margin: 16px 0;
}

.obs-field label {
  display: block;
  font-size: 13px;
  color: #666;
  margin-bottom: 4px;
}

.obs-field textarea {
  width: 100%;
  padding: 8px;
  border: 1px solid #ccc;
  border-radius: 4px;
  resize: vertical;
  font-family: inherit;
}

/* Step Actions */
.step-actions {
  display: flex;
  justify-content: space-between;
  gap: 10px;
  margin-top: 20px;
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

.btn-next {
  background: #1976d2;
  color: white;
  margin-left: auto;
}
.btn-next:hover:not(:disabled) {
  background: #1565c0;
}
.btn-back {
  background: #e0e0e0;
  color: #333;
}
.btn-back:hover {
  background: #bdbdbd;
}
.btn-confirm {
  background: #4caf50;
  color: white;
  margin-left: auto;
}
.btn-confirm:hover:not(:disabled) {
  background: #388e3c;
}
.btn-fechar {
  background: #37474f;
  color: white;
  margin-top: 16px;
}

/* Wizard Footer */
.wizard-footer {
  padding: 12px 24px;
  border-top: 1px solid #e0e0e0;
  text-align: center;
  font-size: 13px;
  color: #666;
  background: #fafafa;
  border-radius: 0 0 12px 12px;
}

.no-change {
  text-align: center;
  padding: 20px;
  color: #4caf50;
  font-weight: 600;
}
</style>
