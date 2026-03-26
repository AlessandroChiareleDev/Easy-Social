<template>
  <div class="v-root">
    <!-- ═══════════ MODO LISTA ═══════════ -->
    <template v-if="modo === 'lista'">
      <!-- Header -->
      <div class="v-header">
        <h1 class="v-title">Validador de Naturezas</h1>
        <div class="v-stats" v-if="progresso">
          <span class="v-stat">
            <span class="v-stat-n total">{{ progresso.total_verificar }}</span> total
          </span>
          <span class="v-stat">
            <span class="v-stat-n pending">{{ progresso.total_pendentes }}</span> pendentes
          </span>
          <span class="v-stat">
            <span class="v-stat-n done">{{ progresso.total_corrigidas }}</span> corrigidas
          </span>
        </div>
      </div>

      <!-- Progress bar -->
      <div class="v-progress" v-if="progresso">
        <div class="v-progress-fill" :style="{ width: progresso.percentual + '%' }">
          {{ progresso.percentual }}%
        </div>
      </div>

      <!-- Error -->
      <div v-if="error" class="v-error">{{ error }}</div>

      <!-- Staging banner -->
      <div v-if="progresso && progresso.total_corrigidas > 0" class="v-staging">
        <div class="v-staging-left">
          <span>📋</span>
          <span
            ><strong>{{ progresso.total_corrigidas }}</strong> correções no staging</span
          >
        </div>
        <button
          v-if="authStore.isAdmin"
          class="v-btn v-btn-apply"
          @click="aplicarCorrecoes"
          :disabled="aplicando"
        >
          {{ aplicando ? 'Aplicando...' : '🚀 Aplicar Todas' }}
        </button>
        <span v-else class="v-staging-hint">Somente admin pode aplicar</span>
      </div>

      <!-- Filtro -->
      <div class="v-filter">
        <label class="v-checkbox">
          <input type="checkbox" v-model="apenaPendentes" @change="fetchRubricas" />
          Apenas pendentes
        </label>
        <button
          v-if="progresso && progresso.total_corrigidas > 0"
          class="v-btn v-btn-ghost"
          @click="toggleRelatorio"
        >
          {{ showRelatorio ? 'Fechar Relatório' : '📄 Relatório' }}
        </button>
      </div>

      <!-- Relatório inline -->
      <div v-if="showRelatorio && relatorio.length > 0" class="v-relatorio">
        <table>
          <thead>
            <tr>
              <th>Código</th>
              <th>Evento</th>
              <th>Anterior</th>
              <th>Nova</th>
              <th>Data</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="r in relatorio" :key="r.id">
              <td>{{ r.codigoevento }}</td>
              <td>{{ r.nome_evento }}</td>
              <td>{{ r.natureza_anterior }}</td>
              <td>{{ r.natureza_nova }}</td>
              <td>{{ formatDate(r.data_correcao) }}</td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Loading -->
      <div v-if="loading" class="v-loading">Carregando...</div>

      <!-- Lista de rubricas compacta -->
      <div v-if="rubricas.length > 0 && !loading" class="v-list">
        <div
          v-for="(rubrica, idx) in rubricas"
          :key="rubrica.id"
          class="v-item"
          :class="{ done: rubrica.natureza_nova }"
          @click="abrirCorrecao(rubrica)"
        >
          <div class="v-item-num">{{ idx + 1 }}</div>
          <div class="v-item-body">
            <div class="v-item-top">
              <span class="v-item-code">{{ rubrica.codigoevento }}</span>
              <span class="v-item-name">{{ rubrica.nome_evento }}</span>
            </div>
            <div class="v-item-sub">{{ rubrica.natureza_atual }}</div>
          </div>
          <div class="v-item-badge" :class="rubrica.natureza_nova ? 'ok' : 'pend'">
            {{ rubrica.natureza_nova ? '✓' : '●' }}
          </div>
        </div>
      </div>

      <div v-if="rubricas.length === 0 && !loading" class="v-empty">
        Nenhuma rubrica pendente encontrada.
      </div>
    </template>

    <!-- ═══════════ MODO CORREÇÃO ═══════════ -->
    <template v-if="modo === 'correcao' && rubricaSelecionada">
      <!-- Top bar -->
      <div class="c-topbar">
        <button class="v-btn v-btn-back" @click="voltarLista">← Voltar à lista</button>
        <div class="c-counter" v-if="progresso">{{ rubricaIndex + 1 }} / {{ totalPendentes }}</div>
        <div class="c-nav">
          <button class="v-btn v-btn-sm" :disabled="!temAnterior" @click="navegar(-1)">
            ‹ Anterior
          </button>
          <button class="v-btn v-btn-sm" :disabled="!temProxima" @click="navegar(1)">
            Próxima ›
          </button>
        </div>
      </div>

      <!-- Layout duas colunas -->
      <div class="c-layout">
        <!-- Coluna esquerda: info da rubrica -->
        <div class="c-info">
          <div class="c-rubrica-card">
            <div class="c-rubrica-code">{{ rubricaSelecionada.codigoevento }}</div>
            <div class="c-rubrica-name">{{ rubricaSelecionada.nome_evento }}</div>
            <div class="c-rubrica-nat">
              <span class="c-label">Natureza atual:</span>
              {{ rubricaSelecionada.natureza_atual }}
            </div>
            <div
              v-if="rubricaSelecionada.observacao && rubricaSelecionada.observacao !== '-'"
              class="c-rubrica-obs"
            >
              <span class="c-label">Obs:</span> {{ rubricaSelecionada.observacao }}
            </div>
            <div
              v-if="rubricaSelecionada.sugestao_col_f && rubricaSelecionada.sugestao_col_f !== '-'"
              class="c-rubrica-hint"
            >
              💡 {{ rubricaSelecionada.sugestao_col_f }}
            </div>
          </div>

          <!-- Seleção atual + salvar (sticky na esquerda) -->
          <div v-if="naturezaEscolhida" class="c-save-box">
            <div class="c-chosen">
              <span class="c-chosen-code">{{ naturezaEscolhida.codigo }}</span>
              <span class="c-chosen-name">{{ naturezaEscolhida.nome }}</span>
            </div>
            <textarea
              v-model="motivo"
              placeholder="Motivo (opcional)"
              rows="2"
              class="c-motivo"
            ></textarea>
            <div class="c-save-actions">
              <button class="v-btn v-btn-save" @click="confirmarCorrecao" :disabled="salvando">
                {{ salvando ? 'Salvando...' : '✓ Salvar e Avançar' }}
              </button>
              <button class="v-btn v-btn-ghost" @click="cancelarSelecao">Cancelar</button>
            </div>
          </div>

          <!-- Desfazer -->
          <div v-if="rubricaSelecionada.natureza_nova" class="c-undo">
            <span class="c-undo-text">Corrigida: {{ rubricaSelecionada.natureza_nova }}</span>
            <button class="v-btn v-btn-danger-sm" @click="desfazerCorrecao">Desfazer</button>
          </div>

          <!-- Busca manual -->
          <div class="c-search">
            <input
              v-model="buscaManual"
              placeholder="Buscar natureza manualmente..."
              @keyup.enter="buscarManual"
              class="c-search-input"
            />
            <button class="v-btn v-btn-sm" @click="buscarManual" :disabled="!buscaManual.trim()">
              Buscar
            </button>
          </div>
        </div>

        <!-- Coluna direita: sugestões -->
        <div class="c-suggestions">
          <div v-if="loadingSugestoes" class="v-loading">Buscando sugestões...</div>

          <!-- Sugestão humana -->
          <div
            v-if="sugestaoHumana"
            class="c-sug c-sug-human"
            :class="{ selected: naturezaEscolhida?.id === sugestaoHumana.id }"
            @click="escolherNatureza(sugestaoHumana)"
          >
            <div class="c-sug-top">
              <span class="c-sug-code">{{ sugestaoHumana.codigo }}</span>
              <span class="c-sug-tag human">⭐ SUGESTÃO HUMANA</span>
              <span class="c-sug-exp" v-if="sugestaoHumana.data_fim"
                >Exp: {{ formatDate(sugestaoHumana.data_fim) }}</span
              >
            </div>
            <div class="c-sug-name">{{ sugestaoHumana.nome }}</div>
            <div class="c-sug-desc">{{ sugestaoHumana.descricao }}</div>
            <div class="c-sug-hint" v-if="sugestaoTexto">{{ sugestaoTexto }}</div>
          </div>

          <!-- Score suggestions -->
          <template v-for="sug in scoreResults" :key="sug.id">
            <div
              class="c-sug"
              :class="{ selected: naturezaEscolhida?.id === sug.id, expired: sug.data_fim }"
              @click="escolherNatureza(sug)"
            >
              <div class="c-sug-top">
                <span class="c-sug-code">{{ sug.codigo }}</span>
                <span class="c-sug-score" v-if="sug.score > 0">{{ sug.score.toFixed(1) }}</span>
                <span class="c-sug-exp" v-if="sug.data_fim"
                  >Exp: {{ formatDate(sug.data_fim) }}</span
                >
              </div>
              <div class="c-sug-name">{{ sug.nome }}</div>
              <div class="c-sug-desc">{{ sug.descricao }}</div>
            </div>
          </template>

          <!-- Popular divider -->
          <div v-if="popularResults.length > 0" class="c-pop-divider">📊 Mais usadas</div>
          <template v-for="sug in popularResults" :key="'p-' + sug.id">
            <div
              class="c-sug c-sug-pop"
              :class="{ selected: naturezaEscolhida?.id === sug.id, expired: sug.data_fim }"
              @click="escolherNatureza(sug)"
            >
              <div class="c-sug-top">
                <span class="c-sug-code">{{ sug.codigo }}</span>
                <span class="c-sug-tag pop">Popular</span>
              </div>
              <div class="c-sug-name">{{ sug.nome }}</div>
              <div class="c-sug-desc">{{ sug.descricao }}</div>
            </div>
          </template>

          <div
            v-if="!loadingSugestoes && !sugestaoHumana && sugestoes.length === 0"
            class="v-empty"
          >
            Nenhuma sugestão encontrada. Use a busca manual.
          </div>
        </div>
      </div>

      <!-- Error -->
      <div v-if="error" class="v-error" style="margin-top: 12px">{{ error }}</div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import axios from 'axios'
import { useAuthStore } from '../stores/auth'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:3333/api'
const authStore = useAuthStore()

interface Rubrica {
  id: number
  codigoevento: string
  nome_evento: string
  natureza_atual: string
  natureza_codigo_atual: string
  observacao: string | null
  sugestao_col_f: string | null
  natureza_nova: string | null
  data_correcao: string | null
}

interface Sugestao {
  id: number
  codigo: string
  nome: string
  descricao: string
  data_inicio: string
  data_fim: string | null
  score: number
  origem: 'sugestao_humana' | 'score' | 'popular'
}

const modo = ref<'lista' | 'correcao'>('lista')
const progresso = ref<any>(null)
const rubricas = ref<Rubrica[]>([])
const rubricaSelecionada = ref<Rubrica | null>(null)
const sugestaoHumana = ref<Sugestao | null>(null)
const sugestaoTexto = ref<string | null>(null)
const sugestoes = ref<Sugestao[]>([])
const naturezaEscolhida = ref<Sugestao | null>(null)
const motivo = ref('')
const buscaManual = ref('')
const apenaPendentes = ref(true)
const loading = ref(false)
const loadingSugestoes = ref(false)
const salvando = ref(false)
const error = ref<string | null>(null)
const showRelatorio = ref(false)
const relatorio = ref<any[]>([])
const aplicando = ref(false)

// Computed: filter suggestions by type
const scoreResults = computed(() => sugestoes.value.filter((s) => s.origem === 'score'))
const popularResults = computed(() => sugestoes.value.filter((s) => s.origem === 'popular'))

// Computed: navigation within pendentes
const pendentes = computed(() => rubricas.value.filter((r) => !r.natureza_nova))
const totalPendentes = computed(() => pendentes.value.length)
const rubricaIndex = computed(() => {
  if (!rubricaSelecionada.value) return -1
  return pendentes.value.findIndex((r) => r.id === rubricaSelecionada.value!.id)
})
const temAnterior = computed(() => rubricaIndex.value > 0)
const temProxima = computed(() => rubricaIndex.value < pendentes.value.length - 1)

function formatDate(d: string | null) {
  if (!d) return '-'
  return new Date(d).toLocaleDateString('pt-BR')
}

async function fetchProgresso() {
  try {
    const resp = await axios.get(`${API_URL}/rubricas/progresso`)
    progresso.value = resp.data
  } catch {
    /* ignore */
  }
}

async function fetchRubricas() {
  loading.value = true
  error.value = null
  try {
    const resp = await axios.get(`${API_URL}/rubricas/com-problemas`, {
      params: { limit: 100, apenaPendentes: apenaPendentes.value },
    })
    rubricas.value = resp.data.data
  } catch (err: any) {
    error.value = err.response?.data?.error || 'Erro ao carregar rubricas'
  } finally {
    loading.value = false
  }
}

async function carregarSugestoes(rubrica: Rubrica) {
  naturezaEscolhida.value = null
  sugestaoHumana.value = null
  sugestaoTexto.value = null
  motivo.value = ''
  buscaManual.value = ''
  loadingSugestoes.value = true
  try {
    const resp = await axios.get(
      `${API_URL}/naturezas/buscar-similares/${encodeURIComponent(rubrica.nome_evento)}`,
      { params: { topN: 10, codigoEvento: rubrica.codigoevento } },
    )
    sugestaoHumana.value = resp.data.sugestaoHumana
    sugestaoTexto.value = resp.data.sugestaoTexto
    sugestoes.value = resp.data.resultados
  } catch {
    sugestaoHumana.value = null
    sugestoes.value = []
  } finally {
    loadingSugestoes.value = false
  }
}

function abrirCorrecao(rubrica: Rubrica) {
  rubricaSelecionada.value = rubrica
  modo.value = 'correcao'
  carregarSugestoes(rubrica)
}

function voltarLista() {
  modo.value = 'lista'
  rubricaSelecionada.value = null
  sugestoes.value = []
  naturezaEscolhida.value = null
}

function navegar(dir: number) {
  const idx = rubricaIndex.value + dir
  if (idx >= 0 && idx < pendentes.value.length) {
    rubricaSelecionada.value = pendentes.value[idx]
    carregarSugestoes(pendentes.value[idx])
  }
}

function escolherNatureza(sug: Sugestao) {
  naturezaEscolhida.value = sug
}

async function buscarManual() {
  if (!buscaManual.value.trim()) return
  loadingSugestoes.value = true
  try {
    const resp = await axios.get(
      `${API_URL}/naturezas/buscar-similares/${encodeURIComponent(buscaManual.value)}`,
      { params: { topN: 10 } },
    )
    sugestaoHumana.value = null
    sugestaoTexto.value = null
    sugestoes.value = resp.data.resultados
  } catch {
    sugestoes.value = []
  } finally {
    loadingSugestoes.value = false
  }
}

async function confirmarCorrecao() {
  if (!rubricaSelecionada.value || !naturezaEscolhida.value) return
  salvando.value = true
  try {
    await axios.post(`${API_URL}/rubricas/corrigir`, {
      id: rubricaSelecionada.value.id,
      naturezaCodigo: naturezaEscolhida.value.codigo,
      naturezaNome: naturezaEscolhida.value.nome,
      motivo: motivo.value,
      usuarioNome: authStore.user?.nome || 'sistema',
    })
    await fetchRubricas()
    await fetchProgresso()
    // Auto-advance to next pending
    const proxima = pendentes.value[0]
    if (proxima) {
      rubricaSelecionada.value = proxima
      carregarSugestoes(proxima)
    } else {
      voltarLista()
    }
  } catch (err: any) {
    error.value = err.response?.data?.error || 'Erro ao salvar correção'
  } finally {
    salvando.value = false
  }
}

function cancelarSelecao() {
  naturezaEscolhida.value = null
  motivo.value = ''
}

async function desfazerCorrecao() {
  if (!rubricaSelecionada.value) return
  try {
    await axios.post(`${API_URL}/rubricas/desfazer/${rubricaSelecionada.value.id}`)
    await fetchRubricas()
    await fetchProgresso()
    // Reload suggestions for current
    carregarSugestoes(rubricaSelecionada.value)
  } catch (err: any) {
    error.value = err.response?.data?.error || 'Erro ao desfazer correção'
  }
}

async function toggleRelatorio() {
  showRelatorio.value = !showRelatorio.value
  if (showRelatorio.value && relatorio.value.length === 0) {
    try {
      const resp = await axios.get(`${API_URL}/rubricas/relatorio-final`)
      relatorio.value = resp.data.data
    } catch {
      /* ignore */
    }
  }
}

async function aplicarCorrecoes() {
  if (!confirm('Tem certeza que deseja aplicar todas as correções pendentes?')) return
  aplicando.value = true
  try {
    const resp = await axios.post(`${API_URL}/rubricas/aplicar-correcoes`)
    alert(resp.data.message || 'Correções aplicadas!')
    await fetchProgresso()
    await fetchRubricas()
    relatorio.value = []
  } catch (err: any) {
    error.value = err.response?.data?.error || 'Erro ao aplicar correções'
  } finally {
    aplicando.value = false
  }
}

onMounted(() => {
  fetchProgresso()
  fetchRubricas()
})
</script>

<style scoped>
/* ═══════════ BASE ═══════════ */
.v-root {
  padding: 24px;
  max-width: 1400px;
  margin: 0 auto;
  font-family: var(--font-sans, 'Inter', sans-serif);
  color: #1e293b;
}

/* ═══════════ SHARED ═══════════ */
.v-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  border: none;
  border-radius: 8px;
  font-size: 0.85rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.15s;
}
.v-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
.v-btn-sm {
  padding: 6px 12px;
  font-size: 0.8rem;
  background: #e2e8f0;
  color: #334155;
  border-radius: 6px;
}
.v-btn-sm:hover:not(:disabled) {
  background: #cbd5e1;
}
.v-btn-ghost {
  background: transparent;
  color: #2563eb;
}
.v-btn-ghost:hover {
  background: #eff6ff;
}
.v-btn-back {
  background: #f1f5f9;
  color: #334155;
}
.v-btn-back:hover {
  background: #e2e8f0;
}
.v-btn-save {
  background: #059669;
  color: #fff;
  padding: 10px 24px;
  font-size: 0.9rem;
  border-radius: 10px;
}
.v-btn-save:hover:not(:disabled) {
  background: #047857;
}
.v-btn-apply {
  background: #059669;
  color: #fff;
}
.v-btn-apply:hover:not(:disabled) {
  background: #047857;
}
.v-btn-danger-sm {
  background: #fee2e2;
  color: #dc2626;
  padding: 6px 12px;
  font-size: 0.8rem;
  border-radius: 6px;
}
.v-btn-danger-sm:hover {
  background: #fecaca;
}

.v-loading {
  text-align: center;
  padding: 32px;
  color: #94a3b8;
  font-size: 0.9rem;
}
.v-empty {
  text-align: center;
  padding: 48px;
  color: #94a3b8;
}
.v-error {
  background: #fef2f2;
  color: #dc2626;
  padding: 10px 14px;
  border-radius: 8px;
  font-size: 0.85rem;
  margin-bottom: 12px;
}

/* ═══════════ MODO LISTA ═══════════ */
.v-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 12px;
  margin-bottom: 16px;
}
.v-title {
  font-size: 1.4rem;
  font-weight: 700;
  color: #0f172a;
  margin: 0;
}
.v-stats {
  display: flex;
  gap: 20px;
}
.v-stat {
  font-size: 0.85rem;
  color: #64748b;
}
.v-stat-n {
  font-weight: 700;
  font-size: 1.1rem;
  margin-right: 4px;
}
.v-stat-n.total {
  color: #2563eb;
}
.v-stat-n.pending {
  color: #d97706;
}
.v-stat-n.done {
  color: #059669;
}

.v-progress {
  height: 8px;
  background: #e2e8f0;
  border-radius: 99px;
  overflow: hidden;
  margin-bottom: 20px;
}
.v-progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #059669, #10b981);
  border-radius: 99px;
  font-size: 0;
  color: transparent;
  transition: width 0.5s;
  min-width: 2%;
}

.v-staging {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: #ecfdf5;
  border: 1px solid #a7f3d0;
  border-radius: 10px;
  padding: 10px 16px;
  margin-bottom: 16px;
  font-size: 0.85rem;
  color: #065f46;
}
.v-staging-left {
  display: flex;
  align-items: center;
  gap: 8px;
}
.v-staging-hint {
  font-size: 0.8rem;
  color: #6b7280;
  font-style: italic;
}

.v-filter {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 16px;
}
.v-checkbox {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 0.85rem;
  color: #475569;
  cursor: pointer;
}
.v-checkbox input {
  accent-color: #2563eb;
}

/* Relatório */
.v-relatorio {
  overflow-x: auto;
  margin-bottom: 20px;
  border-radius: 10px;
  border: 1px solid #e2e8f0;
}
.v-relatorio table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.8rem;
}
.v-relatorio th {
  background: #1e3a5f;
  color: #fff;
  padding: 8px 12px;
  text-align: left;
}
.v-relatorio td {
  padding: 8px 12px;
  border-bottom: 1px solid #f1f5f9;
}
.v-relatorio tr:hover td {
  background: #f8fafc;
}

/* Lista de rubricas */
.v-list {
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.v-item {
  display: flex;
  align-items: center;
  gap: 12px;
  background: #fff;
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  padding: 12px 16px;
  cursor: pointer;
  transition: all 0.15s;
}
.v-item:hover {
  border-color: #93c5fd;
  background: #eff6ff;
  transform: translateX(4px);
}
.v-item.done {
  opacity: 0.55;
  border-left: 4px solid #10b981;
}
.v-item-num {
  width: 28px;
  height: 28px;
  background: #f1f5f9;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.75rem;
  font-weight: 700;
  color: #64748b;
  flex-shrink: 0;
}
.v-item-body {
  flex: 1;
  min-width: 0;
}
.v-item-top {
  display: flex;
  gap: 10px;
  align-items: baseline;
}
.v-item-code {
  font-weight: 700;
  font-size: 0.85rem;
  color: #1e3a5f;
  flex-shrink: 0;
}
.v-item-name {
  font-size: 0.85rem;
  color: #334155;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.v-item-sub {
  font-size: 0.75rem;
  color: #94a3b8;
  margin-top: 2px;
}
.v-item-badge {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.7rem;
  flex-shrink: 0;
}
.v-item-badge.pend {
  background: #fef3c7;
  color: #d97706;
}
.v-item-badge.ok {
  background: #d1fae5;
  color: #059669;
}

/* ═══════════ MODO CORREÇÃO ═══════════ */
.c-topbar {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 20px;
  flex-wrap: wrap;
}
.c-counter {
  font-size: 0.9rem;
  font-weight: 700;
  color: #2563eb;
  background: #eff6ff;
  padding: 4px 14px;
  border-radius: 99px;
}
.c-nav {
  display: flex;
  gap: 6px;
  margin-left: auto;
}

.c-layout {
  display: grid;
  grid-template-columns: 340px 1fr;
  gap: 24px;
  align-items: start;
}
@media (max-width: 800px) {
  .c-layout {
    grid-template-columns: 1fr;
  }
}

/* Left column */
.c-info {
  position: sticky;
  top: 80px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}
.c-rubrica-card {
  background: #fff;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  padding: 20px;
}
.c-rubrica-code {
  font-size: 1.3rem;
  font-weight: 800;
  color: #1e3a5f;
  margin-bottom: 4px;
}
.c-rubrica-name {
  font-size: 1rem;
  font-weight: 600;
  color: #334155;
  margin-bottom: 12px;
}
.c-rubrica-nat {
  font-size: 0.85rem;
  color: #64748b;
  margin-bottom: 4px;
}
.c-rubrica-obs {
  font-size: 0.85rem;
  color: #64748b;
  margin-bottom: 4px;
}
.c-label {
  font-weight: 600;
  color: #475569;
}
.c-rubrica-hint {
  margin-top: 10px;
  padding: 8px 12px;
  background: #fffbeb;
  border-left: 3px solid #f59e0b;
  border-radius: 0 8px 8px 0;
  font-size: 0.85rem;
  color: #92400e;
}

/* Save box */
.c-save-box {
  background: #ecfdf5;
  border: 2px solid #10b981;
  border-radius: 12px;
  padding: 16px;
}
.c-chosen {
  display: flex;
  align-items: baseline;
  gap: 8px;
  margin-bottom: 10px;
}
.c-chosen-code {
  font-size: 1.1rem;
  font-weight: 800;
  color: #059669;
}
.c-chosen-name {
  font-size: 0.9rem;
  color: #065f46;
  font-weight: 500;
}
.c-motivo {
  width: 100%;
  padding: 8px 10px;
  border: 1px solid #a7f3d0;
  border-radius: 8px;
  font-size: 0.85rem;
  resize: vertical;
  margin-bottom: 10px;
  box-sizing: border-box;
  font-family: inherit;
}
.c-save-actions {
  display: flex;
  gap: 8px;
}

/* Undo */
.c-undo {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: #fff;
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  padding: 10px 14px;
}
.c-undo-text {
  font-size: 0.85rem;
  color: #059669;
  font-weight: 500;
}

/* Search */
.c-search {
  display: flex;
  gap: 6px;
}
.c-search-input {
  flex: 1;
  padding: 8px 12px;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  font-size: 0.85rem;
  font-family: inherit;
}
.c-search-input:focus {
  border-color: #93c5fd;
  outline: none;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

/* Right column: suggestions */
.c-suggestions {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.c-sug {
  background: #fff;
  border: 2px solid #e2e8f0;
  border-radius: 10px;
  padding: 14px 16px;
  cursor: pointer;
  transition: all 0.15s;
}
.c-sug:hover {
  border-color: #93c5fd;
  background: #f8fafc;
}
.c-sug.selected {
  border-color: #10b981;
  background: #ecfdf5;
  box-shadow: 0 0 0 3px rgba(16, 185, 129, 0.15);
}
.c-sug.expired {
  opacity: 0.6;
}

/* Human suggestion */
.c-sug-human {
  background: linear-gradient(135deg, #fffbeb 0%, #fef3c7 100%);
  border: 2px solid #f59e0b;
  position: relative;
}
.c-sug-human:hover {
  border-color: #d97706;
}
.c-sug-human.selected {
  border-color: #10b981;
  background: linear-gradient(135deg, #ecfdf5 0%, #d1fae5 100%);
}

.c-sug-top {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 4px;
  flex-wrap: wrap;
}
.c-sug-code {
  font-weight: 800;
  font-size: 1rem;
  color: #1e3a5f;
}
.c-sug-score {
  font-size: 0.7rem;
  background: #dbeafe;
  color: #1d4ed8;
  padding: 2px 8px;
  border-radius: 99px;
  font-weight: 600;
}
.c-sug-tag {
  font-size: 0.7rem;
  padding: 2px 8px;
  border-radius: 99px;
  font-weight: 700;
}
.c-sug-tag.human {
  background: linear-gradient(90deg, #f59e0b, #fbbf24);
  color: #fff;
}
.c-sug-tag.pop {
  background: #e2e8f0;
  color: #475569;
}
.c-sug-exp {
  font-size: 0.7rem;
  background: #fff7ed;
  color: #c2410c;
  padding: 2px 8px;
  border-radius: 99px;
}
.c-sug-name {
  font-size: 0.9rem;
  font-weight: 600;
  color: #1e293b;
}
.c-sug-desc {
  font-size: 0.8rem;
  color: #64748b;
  margin-top: 2px;
}
.c-sug-hint {
  margin-top: 6px;
  font-size: 0.8rem;
  color: #92400e;
  font-style: italic;
}

/* Popular divider */
.c-pop-divider {
  font-size: 0.8rem;
  color: #94a3b8;
  font-weight: 600;
  padding: 8px 0 4px;
  border-top: 1px dashed #e2e8f0;
  margin-top: 4px;
}
.c-sug-pop {
  background: #f8fafc;
  border-color: #f1f5f9;
}
.c-sug-pop:hover {
  border-color: #cbd5e1;
}
</style>
