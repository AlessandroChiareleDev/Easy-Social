<template>
  33 ,
  <div class="v-root">
    <!-- Glass shapes -->
    <div class="glass-shapes">
      <div class="glass-shape shape-1"></div>
      <div class="glass-shape shape-2"></div>
      <div class="glass-shape shape-3"></div>
    </div>

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

          <!-- Busca manual: nome ou código -->
          <div class="c-search">
            <input
              v-model="buscaManual"
              placeholder="Buscar por nome ou código..."
              @keyup.enter="buscarManual"
              class="c-search-input"
            />
            <button
              class="v-btn v-btn-sm"
              @click="buscarManual"
              :disabled="!buscaManual.trim() || buscandoCodigo"
            >
              {{ buscandoCodigo ? '...' : 'Buscar' }}
            </button>
          </div>
          <div v-if="erroCodigoManual" class="c-code-error">{{ erroCodigoManual }}</div>

          <!-- Botão sem natureza (código 0) -->
          <button class="c-btn-vazio" @click="escolherVazio">⊘ Sem natureza (deixar vazio)</button>
        </div>

        <!-- Coluna direita: sugestões -->
        <div class="c-suggestions">
          <div v-if="loadingSugestoes" class="v-loading">Buscando sugestões...</div>

          <!-- Resultado de busca por código direto -->
          <div
            v-if="naturezaManual"
            class="c-sug c-sug-manual"
            :class="{
              selected: naturezaEscolhida?.id === naturezaManual.id,
              expired: naturezaManual.data_fim,
            }"
            @click="escolherNatureza(naturezaManual)"
          >
            <div class="c-sug-top">
              <span class="c-sug-code">{{ naturezaManual.codigo }}</span>
              <span class="c-sug-tag manual">🔢 CÓDIGO DIRETO</span>
              <span class="c-sug-exp" v-if="naturezaManual.data_fim"
                >Exp: {{ formatDate(naturezaManual.data_fim) }}</span
              >
            </div>
            <div class="c-sug-name">{{ naturezaManual.nome }}</div>
            <div class="c-sug-desc">{{ naturezaManual.descricao }}</div>
          </div>

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
const naturezaManual = ref<Sugestao | null>(null)
const buscandoCodigo = ref(false)
const erroCodigoManual = ref<string | null>(null)

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
  naturezaManual.value = null
  erroCodigoManual.value = null
  loadingSugestoes.value = true
  try {
    const resp = await axios.get(`${API_URL}/naturezas/buscar-similares`, {
      params: { nomeEvento: rubrica.nome_evento, topN: 10, codigoEvento: rubrica.codigoevento },
    })
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

function escolherVazio() {
  naturezaEscolhida.value = {
    id: -1,
    codigo: '0',
    nome: 'Sem natureza',
    descricao: 'Campo será deixado vazio',
    data_inicio: '',
    data_fim: null,
    score: 0,
    origem: 'score',
  } as Sugestao
}

async function buscarManual() {
  const termo = buscaManual.value.trim()
  if (!termo) return

  erroCodigoManual.value = null
  naturezaManual.value = null

  // Se é número puro → busca por código
  if (/^\d+$/.test(termo)) {
    buscandoCodigo.value = true
    try {
      const resp = await axios.get(`${API_URL}/naturezas/por-codigo/${encodeURIComponent(termo)}`)
      const nat = resp.data.data
      naturezaManual.value = {
        id: nat.id,
        codigo: nat.codigo,
        nome: nat.nome,
        descricao: nat.descricao,
        data_inicio: nat.data_inicio,
        data_fim: nat.data_fim,
        score: 0,
        origem: 'score',
      }
      // Limpar sugestões anteriores ao buscar por código
      sugestaoHumana.value = null
      sugestaoTexto.value = null
      sugestoes.value = []
    } catch {
      erroCodigoManual.value = `Código "${termo}" não encontrado na tabela de naturezas`
      naturezaManual.value = null
      sugestoes.value = []
    } finally {
      buscandoCodigo.value = false
    }
    return
  }

  // Senão → busca por nome (texto)
  loadingSugestoes.value = true
  naturezaManual.value = null
  try {
    const resp = await axios.get(`${API_URL}/naturezas/buscar-similares`, {
      params: { nomeEvento: termo, topN: 10 },
    })
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
/* ═══════════ BASE — Orbit Navy + Electric Blue ═══════════ */
.v-root {
  position: relative;
  overflow: hidden;
  padding: 24px;
  max-width: 1400px;
  margin: 0 auto;
  font-family: var(--font-sans, 'Inter', sans-serif);
  color: #e2e8f0;
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
  background: rgba(17, 27, 58, 0.7);
  backdrop-filter: blur(12px);
  color: #cbd5e1;
  border-radius: 6px;
}
.v-btn-sm:hover:not(:disabled) {
  background: #162044;
  color: #fff;
}
.v-btn-ghost {
  background: transparent;
  color: #0066ff;
}
.v-btn-ghost:hover {
  background: rgba(0, 102, 255, 0.1);
}
.v-btn-back {
  background: rgba(17, 27, 58, 0.7);
  backdrop-filter: blur(12px);
  color: #cbd5e1;
}
.v-btn-back:hover {
  background: #162044;
  color: #fff;
}
.v-btn-save {
  background: #0066ff;
  color: #fff;
  padding: 10px 24px;
  font-size: 0.9rem;
  border-radius: 10px;
}
.v-btn-save:hover:not(:disabled) {
  background: #0055dd;
}
.v-btn-apply {
  background: #0066ff;
  color: #fff;
}
.v-btn-apply:hover:not(:disabled) {
  background: #0055dd;
}
.v-btn-danger-sm {
  background: rgba(239, 68, 68, 0.15);
  color: #f87171;
  padding: 6px 12px;
  font-size: 0.8rem;
  border-radius: 6px;
}
.v-btn-danger-sm:hover {
  background: rgba(239, 68, 68, 0.25);
}

.v-loading {
  text-align: center;
  padding: 32px;
  color: #64748b;
  font-size: 0.9rem;
}
.v-empty {
  text-align: center;
  padding: 48px;
  color: #64748b;
}
.v-error {
  background: rgba(239, 68, 68, 0.1);
  color: #f87171;
  padding: 10px 14px;
  border-radius: 8px;
  font-size: 0.85rem;
  margin-bottom: 12px;
  border: 1px solid rgba(239, 68, 68, 0.2);
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
  color: #ffffff;
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
  color: #0066ff;
}
.v-stat-n.pending {
  color: #fbbf24;
}
.v-stat-n.done {
  color: #34d399;
}

.v-progress {
  height: 8px;
  background: rgba(17, 27, 58, 0.7);
  border-radius: 99px;
  overflow: hidden;
  margin-bottom: 20px;
}
.v-progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #0066ff, #3388ff);
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
  background: rgba(0, 102, 255, 0.08);
  border: 1px solid rgba(0, 102, 255, 0.2);
  border-radius: 10px;
  padding: 10px 16px;
  margin-bottom: 16px;
  font-size: 0.85rem;
  color: #cbd5e1;
}
.v-staging-left {
  display: flex;
  align-items: center;
  gap: 8px;
}
.v-staging-hint {
  font-size: 0.8rem;
  color: #64748b;
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
  color: #94a3b8;
  cursor: pointer;
}
.v-checkbox input {
  accent-color: #0066ff;
}

/* Relatório */
.v-relatorio {
  overflow-x: auto;
  margin-bottom: 20px;
  border-radius: 10px;
  border: 1px solid rgba(0, 102, 255, 0.12);
}
.v-relatorio table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.8rem;
}
.v-relatorio th {
  background: rgba(17, 27, 58, 0.8);
  color: #cbd5e1;
  padding: 8px 12px;
  text-align: left;
}
.v-relatorio td {
  padding: 8px 12px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.04);
  color: #cbd5e1;
}
.v-relatorio tr:hover td {
  background: rgba(0, 102, 255, 0.05);
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
  background: rgba(13, 21, 48, 0.7);
  backdrop-filter: blur(12px);
  border: 1px solid rgba(0, 102, 255, 0.12);
  border-radius: 10px;
  padding: 12px 16px;
  cursor: pointer;
  transition: all 0.15s;
}
.v-item:hover {
  border-color: rgba(0, 102, 255, 0.4);
  background: rgba(17, 27, 58, 0.8);
  transform: translateX(4px);
}
.v-item.done {
  opacity: 0.55;
  border-left: 4px solid #34d399;
}
.v-item-num {
  width: 28px;
  height: 28px;
  background: rgba(17, 27, 58, 0.8);
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
  color: #0066ff;
  flex-shrink: 0;
}
.v-item-name {
  font-size: 0.85rem;
  color: #cbd5e1;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.v-item-sub {
  font-size: 0.75rem;
  color: #64748b;
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
  background: rgba(245, 158, 11, 0.15);
  color: #fbbf24;
}
.v-item-badge.ok {
  background: rgba(16, 185, 129, 0.15);
  color: #34d399;
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
  color: #0066ff;
  background: rgba(0, 102, 255, 0.12);
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
  background: rgba(13, 21, 48, 0.7);
  backdrop-filter: blur(16px);
  border: 1px solid rgba(0, 102, 255, 0.15);
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 0 20px rgba(0, 102, 255, 0.04), 0 8px 32px rgba(0, 0, 0, 0.3);
}
.c-rubrica-code {
  font-size: 1.3rem;
  font-weight: 800;
  color: #0066ff;
  margin-bottom: 4px;
}
.c-rubrica-name {
  font-size: 1rem;
  font-weight: 600;
  color: #e2e8f0;
  margin-bottom: 12px;
}
.c-rubrica-nat {
  font-size: 0.85rem;
  color: #94a3b8;
  margin-bottom: 4px;
}
.c-rubrica-obs {
  font-size: 0.85rem;
  color: #94a3b8;
  margin-bottom: 4px;
}
.c-label {
  font-weight: 600;
  color: #cbd5e1;
}
.c-rubrica-hint {
  margin-top: 10px;
  padding: 8px 12px;
  background: rgba(245, 158, 11, 0.1);
  border-left: 3px solid #f59e0b;
  border-radius: 0 8px 8px 0;
  font-size: 0.85rem;
  color: #fbbf24;
}

/* Save box */
.c-save-box {
  background: rgba(0, 102, 255, 0.08);
  border: 2px solid #0066ff;
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
  color: #0066ff;
}
.c-chosen-name {
  font-size: 0.9rem;
  color: #cbd5e1;
  font-weight: 500;
}
.c-motivo {
  width: 100%;
  padding: 8px 10px;
  border: 1px solid rgba(0, 102, 255, 0.2);
  border-radius: 8px;
  font-size: 0.85rem;
  resize: vertical;
  margin-bottom: 10px;
  box-sizing: border-box;
  font-family: inherit;
  background: #0a1024;
  color: #e2e8f0;
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
  background: rgba(13, 21, 48, 0.7);
  backdrop-filter: blur(12px);
  border: 1px solid rgba(0, 102, 255, 0.12);
  border-radius: 10px;
  padding: 10px 14px;
}
.c-undo-text {
  font-size: 0.85rem;
  color: #34d399;
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
  border: 1px solid rgba(0, 102, 255, 0.15);
  border-radius: 8px;
  font-size: 0.85rem;
  font-family: inherit;
  background: #0a1024;
  color: #e2e8f0;
}
.c-search-input:focus {
  border-color: #0066ff;
  outline: none;
  box-shadow: 0 0 0 3px rgba(0, 102, 255, 0.15);
}

/* Code lookup */
.c-code-error {
  font-size: 0.8rem;
  color: #f87171;
  padding: 2px 0;
}
.c-btn-vazio {
  margin-top: 24px;
  padding: 10px 14px;
  border: 1px dashed rgba(239, 68, 68, 0.4);
  border-radius: 8px;
  background: rgba(239, 68, 68, 0.08);
  color: #f87171;
  font-size: 0.82rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
  width: 100%;
  text-align: left;
}
.c-btn-vazio:hover {
  border-color: #ef4444;
  color: #ef4444;
  background: rgba(239, 68, 68, 0.14);
}
.c-sug-manual {
  border-color: rgba(16, 185, 129, 0.3);
  background: rgba(16, 185, 129, 0.06);
}
.c-sug-manual:hover {
  border-color: rgba(16, 185, 129, 0.5);
}
.c-sug-tag.manual {
  background: linear-gradient(90deg, #10b981, #34d399);
  color: #fff;
}

/* Right column: suggestions */
.c-suggestions {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.c-sug {
  background: rgba(13, 21, 48, 0.7);
  backdrop-filter: blur(12px);
  border: 2px solid rgba(0, 102, 255, 0.12);
  border-radius: 10px;
  padding: 14px 16px;
  cursor: pointer;
  transition: all 0.15s;
}
.c-sug:hover {
  border-color: rgba(0, 102, 255, 0.4);
  background: rgba(17, 27, 58, 0.8);
}
.c-sug.selected {
  border-color: #0066ff;
  background: rgba(0, 102, 255, 0.1);
  box-shadow: 0 0 0 3px rgba(0, 102, 255, 0.15);
}
.c-sug.expired {
  opacity: 0.6;
}

/* Human suggestion */
.c-sug-human {
  background: rgba(245, 158, 11, 0.08);
  border: 2px solid rgba(245, 158, 11, 0.4);
  position: relative;
}
.c-sug-human:hover {
  border-color: #f59e0b;
}
.c-sug-human.selected {
  border-color: #0066ff;
  background: rgba(0, 102, 255, 0.1);
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
  color: #0066ff;
}
.c-sug-score {
  font-size: 0.7rem;
  background: rgba(0, 102, 255, 0.15);
  color: #3388ff;
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
  background: rgba(255, 255, 255, 0.08);
  color: #94a3b8;
}
.c-sug-exp {
  font-size: 0.7rem;
  background: rgba(239, 68, 68, 0.1);
  color: #f87171;
  padding: 2px 8px;
  border-radius: 99px;
}
.c-sug-name {
  font-size: 0.9rem;
  font-weight: 600;
  color: #e2e8f0;
}
.c-sug-desc {
  font-size: 0.8rem;
  color: #64748b;
  margin-top: 2px;
}
.c-sug-hint {
  margin-top: 6px;
  font-size: 0.8rem;
  color: #fbbf24;
  font-style: italic;
}

/* Popular divider */
.c-pop-divider {
  font-size: 0.8rem;
  color: #64748b;
  font-weight: 600;
  padding: 8px 0 4px;
  border-top: 1px dashed rgba(0, 102, 255, 0.15);
  margin-top: 4px;
}
.c-sug-pop {
  background: rgba(10, 16, 36, 0.8);
  backdrop-filter: blur(12px);
  border-color: rgba(255, 255, 255, 0.06);
}
.c-sug-pop:hover {
  border-color: rgba(0, 102, 255, 0.3);
}

/* ── Glass Shapes ── */
.glass-shapes { position: absolute; inset: 0; pointer-events: none; overflow: hidden; }
.glass-shape {
  position: absolute;
  border-radius: 50%;
  border: 1px solid rgba(0, 102, 255, 0.15);
  background: rgba(0, 102, 255, 0.04);
  box-shadow: 0 0 15px rgba(0, 102, 255, 0.2), 0 0 40px rgba(0, 102, 255, 0.1);
}
.shape-1 { width: 280px; height: 280px; top: -60px; right: -60px; filter: blur(2px); animation: drift1 26s ease-in-out infinite; }
.shape-2 { width: 200px; height: 200px; bottom: 10%; left: -40px; border-radius: 36px; filter: blur(1.5px); animation: drift2 30s ease-in-out infinite; }
.shape-3 { width: 150px; height: 150px; top: 40%; left: 55%; filter: blur(3px); animation: drift3 22s ease-in-out infinite; animation-delay: -8s; }
@keyframes drift1 { 0%,100% { transform: translate(-10%,-15%) rotate(0deg); } 50% { transform: translate(30%,50%) rotate(25deg); } }
@keyframes drift2 { 0%,100% { transform: translate(10%,-20%) rotate(45deg); } 50% { transform: translate(-40%,60%) rotate(90deg); } }
@keyframes drift3 { 0%,100% { transform: translate(0,-20%) rotate(0deg); } 50% { transform: translate(-25%,70%) rotate(-20deg); } }
</style>
