<template>
  <div class="dp-root">
    <!-- ═══════════ TOUR OVERLAY ═══════════ -->
    <Teleport to="body">
      <div v-if="tourActive" class="tour-overlay" @click.self="tourEnd">
        <div class="tour-spotlight" :style="spotlightStyle"></div>
        <div class="tour-popup" :style="popupStyle">
          <div class="tour-popup-header">
            <span class="tour-step-badge">{{ tourStep + 1 }}/{{ tourSteps.length }}</span>
            <button class="tour-close" @click="tourEnd" title="Fechar tour">✕</button>
          </div>
          <h3 class="tour-popup-title">{{ tourSteps[tourStep]?.title }}</h3>
          <p class="tour-popup-desc">{{ tourSteps[tourStep]?.description }}</p>
          <div class="tour-popup-footer">
            <button v-if="tourStep > 0" class="tour-btn tour-btn-secondary" @click="tourPrev">
              ← Anterior
            </button>
            <span v-else></span>
            <button
              v-if="tourStep < tourSteps.length - 1"
              class="tour-btn tour-btn-primary"
              @click="tourNext"
            >
              Próximo →
            </button>
            <button v-else class="tour-btn tour-btn-finish" @click="tourEnd">✓ Finalizar</button>
          </div>
          <div class="tour-dots">
            <span
              v-for="(_, i) in tourSteps"
              :key="i"
              :class="['tour-dot', { active: i === tourStep, done: i < tourStep }]"
              @click="tourGoTo(i)"
            ></span>
          </div>
        </div>
      </div>
    </Teleport>

    <!-- Header -->
    <div class="dp-header" data-tour="header">
      <div>
        <h1 class="dp-title">De-Para S-1010</h1>
        <p class="dp-subtitle">Mapeamento de campos obrigatórios para envio ao eSocial</p>
      </div>
      <div class="dp-header-actions">
        <button class="dp-btn dp-btn-tour" :class="{ active: tourActive }" @click="tourToggle">
          <svg
            class="dp-btn-icon"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
            stroke-linecap="round"
          >
            <circle cx="12" cy="12" r="10" />
            <path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3" />
            <line x1="12" y1="17" x2="12.01" y2="17" />
          </svg>
          {{ tourActive ? 'Parar Tour' : 'Tour Guiado' }}
        </button>
        <button
          data-tour="btn-auto"
          class="dp-btn dp-btn-auto"
          @click="autoPopular"
          :disabled="autoPopulando"
        >
          <svg
            class="dp-btn-icon"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
            stroke-linecap="round"
          >
            <polyline points="23 4 23 10 17 10" />
            <path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10" />
          </svg>
          {{ autoPopulando ? 'Populando...' : 'Auto-Popular' }}
        </button>
        <button
          data-tour="btn-preview"
          class="dp-btn dp-btn-preview"
          @click="fetchPreview"
          :disabled="loadingPreview"
        >
          <svg
            class="dp-btn-icon"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
            stroke-linecap="round"
          >
            <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z" />
            <circle cx="12" cy="12" r="3" />
          </svg>
          {{ loadingPreview ? 'Carregando...' : 'Preview S-1010' }}
        </button>
      </div>
    </div>

    <!-- Error -->
    <div v-if="error" class="dp-error">{{ error }}</div>

    <!-- Stats Cards -->
    <div class="dp-cards" v-if="resumo" data-tour="cards">
      <div class="dp-card dp-card-total">
        <span class="dp-card-number">{{ resumo.total_rubricas_gl }}</span>
        <span class="dp-card-label">Total Rubricas</span>
      </div>
      <div class="dp-card dp-card-bloqueada">
        <span class="dp-card-number">{{ resumo.natrubr.bloqueadas }}</span>
        <span class="dp-card-label">natRubr Bloqueadas</span>
      </div>
      <div class="dp-card dp-card-staging">
        <span class="dp-card-number">{{ resumo.natrubr.resolvidas_staging }}</span>
        <span class="dp-card-label">Resolvidas (Staging)</span>
      </div>
      <div class="dp-card dp-card-depara">
        <span class="dp-card-number">{{ totalDePara }}</span>
        <span class="dp-card-label">De-Para Mapeados</span>
      </div>
    </div>

    <!-- Tab Navigation -->
    <div class="dp-tabs" data-tour="tabs">
      <button
        v-for="tab in tabs"
        :key="tab.id"
        :class="['dp-tab', { active: activeTab === tab.id }]"
        @click="activeTab = tab.id"
      >
        {{ tab.label }}
        <span v-if="tab.count !== undefined" class="dp-tab-count">{{ tab.count }}</span>
      </button>
    </div>

    <!-- ═══════════ TAB: natRubr ═══════════ -->
    <div v-if="activeTab === 'natRubr'" class="dp-section" data-tour="natRubr">
      <div v-if="loadingBloqueadores" class="dp-loading">Carregando bloqueadores...</div>
      <div v-else-if="bloqueadores.length === 0" class="dp-empty">
        Nenhuma rubrica com natRubr bloqueada. Tudo OK!
      </div>
      <div v-else class="dp-table-container">
        <table class="dp-table">
          <thead>
            <tr>
              <th>Código</th>
              <th>Descrição</th>
              <th>natRubr Atual</th>
              <th>Situação</th>
              <th>Correção Staging</th>
              <th>De-Para</th>
              <th>Ação</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="b in bloqueadores" :key="b.cod_rubrica" :class="rowClass(b)">
              <td class="dp-cell-code">{{ b.cod_rubrica }}</td>
              <td class="dp-cell-desc">{{ b.nome_rubrica }}</td>
              <td class="dp-cell-nat">{{ b.natrubr_atual }}</td>
              <td>
                <span :class="['dp-badge', 'dp-badge-' + b.situacao]">{{ b.situacao }}</span>
              </td>
              <td>
                <span v-if="b.correcao_staging" class="dp-badge dp-badge-staging">
                  {{ b.correcao_staging }} - {{ b.correcao_staging_nome }}
                </span>
                <span v-else class="dp-text-muted">—</span>
              </td>
              <td>
                <span v-if="b.depara_valor" :class="['dp-badge', 'dp-badge-' + b.depara_status]">
                  {{ b.depara_valor }}
                </span>
                <span v-else class="dp-text-muted">—</span>
              </td>
              <td>
                <div v-if="!b.depara_valor && !b.correcao_staging" class="dp-action-cell">
                  <select v-model="natSelections[b.cod_rubrica]" class="dp-select">
                    <option value="">Selecionar...</option>
                    <option
                      v-for="n in naturezasVigentes"
                      :key="n.codigo"
                      :value="String(n.codigo)"
                    >
                      {{ n.codigo }} - {{ n.nome }}
                    </option>
                  </select>
                  <button
                    class="dp-btn dp-btn-sm dp-btn-map"
                    :disabled="!natSelections[b.cod_rubrica]"
                    @click="mapearNatRubr(b.cod_rubrica)"
                  >
                    Mapear
                  </button>
                </div>
                <span v-else-if="b.correcao_staging" class="dp-text-ok">Via Staging ✓</span>
                <span v-else class="dp-text-ok">Mapeado ✓</span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- ═══════════ TAB: tpRubr ═══════════ -->
    <div v-if="activeTab === 'tpRubr'" class="dp-section" data-tour="tpRubr">
      <div class="dp-info-box">
        <svg
          class="dp-info-icon"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="2"
        >
          <circle cx="12" cy="12" r="10" />
          <line x1="12" y1="16" x2="12" y2="12" />
          <line x1="12" y1="8" x2="12.01" y2="8" />
        </svg>
        <div>
          <strong>Mapeamento Automático</strong>
          <p>
            O campo <code>tpRubr</code> é derivado automaticamente do campo "Tipo" na planilha GL:
          </p>
          <p><code>Vencimento → 1</code> &nbsp;|&nbsp; <code>Desconto → 2</code></p>
          <p v-if="resumo">
            <strong>{{ resumo.tpRubr.disponiveis }}</strong> rubricas com tipo disponível.
            <strong>{{ resumo.tpRubr.depara.pendente + resumo.tpRubr.depara.aplicado }}</strong> já
            mapeadas no De-Para.
          </p>
        </div>
      </div>
      <button
        v-if="
          resumo &&
          resumo.tpRubr.depara.pendente + resumo.tpRubr.depara.aplicado < resumo.tpRubr.disponiveis
        "
        class="dp-btn dp-btn-auto dp-btn-lg"
        @click="autoPopular"
        :disabled="autoPopulando"
      >
        Gerar Mapeamentos Automáticos de tpRubr
      </button>
      <div v-else class="dp-success-box">✓ Todos os mapeamentos de tpRubr estão gerados.</div>
    </div>

    <!-- ═══════════ TAB: codIncPisPasep ═══════════ -->
    <div v-if="activeTab === 'codIncPisPasep'" class="dp-section" data-tour="codIncPisPasep">
      <div class="dp-info-box">
        <svg
          class="dp-info-icon"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="2"
        >
          <circle cx="12" cy="12" r="10" />
          <line x1="12" y1="16" x2="12" y2="12" />
          <line x1="12" y1="8" x2="12.01" y2="8" />
        </svg>
        <div>
          <strong>Campo Novo no S-1.3</strong>
          <p>
            O campo <code>codIncPisPasep</code> é obrigatório a partir da versão S-1.3 do leiaute.
          </p>
          <p>
            Todas as rubricas da empresa possuem <code>Cód. PIS/PASEP = 0</code> (Não é base de
            cálculo) → mapeado para <code>"00"</code>.
          </p>
          <p v-if="resumo">
            <strong>{{ resumo.codIncPisPasep.disponiveis }}</strong> rubricas disponíveis.
            <strong>{{
              resumo.codIncPisPasep.depara.pendente + resumo.codIncPisPasep.depara.aplicado
            }}</strong>
            já mapeadas.
          </p>
        </div>
      </div>
      <button
        v-if="
          resumo &&
          resumo.codIncPisPasep.depara.pendente + resumo.codIncPisPasep.depara.aplicado <
            resumo.codIncPisPasep.disponiveis
        "
        class="dp-btn dp-btn-auto dp-btn-lg"
        @click="autoPopular"
        :disabled="autoPopulando"
      >
        Gerar Mapeamentos Automáticos de codIncPisPasep
      </button>
      <div v-else class="dp-success-box">
        ✓ Todos os mapeamentos de codIncPisPasep estão gerados.
      </div>
    </div>

    <!-- ═══════════ TAB: Preview ═══════════ -->
    <div v-if="activeTab === 'preview'" class="dp-section" data-tour="preview">
      <div v-if="loadingPreview" class="dp-loading">Gerando preview...</div>
      <div v-else-if="!preview" class="dp-empty">
        Clique em "Preview S-1010" para visualizar o resultado final.
      </div>
      <template v-else>
        <!-- Preview Stats -->
        <div class="dp-cards dp-cards-sm">
          <div class="dp-card dp-card-ok">
            <span class="dp-card-number">{{ preview.prontas }}</span>
            <span class="dp-card-label">Prontas para Envio</span>
          </div>
          <div class="dp-card dp-card-bloqueada">
            <span class="dp-card-number">{{ preview.bloqueadas }}</span>
            <span class="dp-card-label">Ainda Bloqueadas</span>
          </div>
          <div class="dp-card dp-card-total">
            <span class="dp-card-number">{{ preview.total }}</span>
            <span class="dp-card-label">Total</span>
          </div>
        </div>

        <!-- Filter preview -->
        <div class="dp-filter-bar">
          <button
            :class="['dp-filter-btn', { active: previewFilter === 'all' }]"
            @click="previewFilter = 'all'"
          >
            Todas ({{ preview.total }})
          </button>
          <button
            :class="['dp-filter-btn dp-filter-ok', { active: previewFilter === 'prontas' }]"
            @click="previewFilter = 'prontas'"
          >
            Prontas ({{ preview.prontas }})
          </button>
          <button
            :class="['dp-filter-btn dp-filter-block', { active: previewFilter === 'bloqueadas' }]"
            @click="previewFilter = 'bloqueadas'"
          >
            Bloqueadas ({{ preview.bloqueadas }})
          </button>
        </div>

        <!-- Preview table -->
        <div class="dp-table-container">
          <table class="dp-table dp-table-preview">
            <thead>
              <tr>
                <th>Código</th>
                <th>Descrição</th>
                <th>natRubr</th>
                <th>tpRubr</th>
                <th>PisPasep</th>
                <th>INSS</th>
                <th>IRRF</th>
                <th>FGTS</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="r in filteredPreview"
                :key="r.cod_rubrica"
                :class="r.pronto ? 'dp-row-ok' : 'dp-row-block'"
              >
                <td class="dp-cell-code">{{ r.cod_rubrica }}</td>
                <td class="dp-cell-desc">{{ r.dsc_rubr }}</td>
                <td>
                  <span :class="['dp-val', 'dp-val-' + r.natRubr.fonte]">
                    {{ r.natRubr.valor || '—' }}
                  </span>
                  <span class="dp-fonte">{{ r.natRubr.fonte }}</span>
                </td>
                <td>
                  <span :class="['dp-val', 'dp-val-' + r.tpRubr.fonte]">
                    {{ r.tpRubr.valor || '—' }}
                  </span>
                  <span class="dp-fonte">{{ r.tpRubr.fonte }}</span>
                </td>
                <td>
                  <span :class="['dp-val', 'dp-val-' + r.codIncPisPasep.fonte]">
                    {{ r.codIncPisPasep.valor || '—' }}
                  </span>
                  <span class="dp-fonte">{{ r.codIncPisPasep.fonte }}</span>
                </td>
                <td>{{ r.codIncCP || '—' }}</td>
                <td>{{ r.codIncIRRF || '—' }}</td>
                <td>{{ r.codIncFGTS || '—' }}</td>
                <td>
                  <span :class="['dp-badge', r.pronto ? 'dp-badge-ok' : 'dp-badge-bloqueada']">
                    {{ r.pronto ? '✓ Pronta' : '✗ Bloqueada' }}
                  </span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </template>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, reactive, nextTick } from 'vue'
import axios from 'axios'
import { PYTHON_API } from '@/lib/api'

// State
const resumo = ref<any>(null)
const bloqueadores = ref<any[]>([])
const naturezasVigentes = ref<any[]>([])
const preview = ref<any>(null)
const error = ref('')
const activeTab = ref('natRubr')
const previewFilter = ref('all')

// Loading states
const loading = ref(false)
const loadingBloqueadores = ref(false)
const loadingPreview = ref(false)
const autoPopulando = ref(false)

// natRubr selections (reactive map: cod_rubrica → selected natureza code)
const natSelections = reactive<Record<string, string>>({})

// ═══════════ TOUR GUIADO ═══════════
const tourActive = ref(false)
const tourStep = ref(0)
const spotlightStyle = ref<Record<string, string>>({})
const popupStyle = ref<Record<string, string>>({})

const tourSteps = [
  {
    target: 'header',
    title: '🗺️ Bem-vindo ao De-Para S-1010',
    description:
      'Esta página é o centro de mapeamento de campos obrigatórios para o envio de rubricas ao eSocial. Aqui você resolve todos os campos que estão faltando ou bloqueados antes de enviar o evento S-1010.',
  },
  {
    target: 'cards',
    title: '📊 Cards de Resumo',
    description:
      'Estes cards mostram o panorama geral: quantas rubricas existem no total, quantas estão com natRubr bloqueada (código expirado ou inexistente na Tabela 3 do eSocial), quantas já foram resolvidas pelo Validador (staging), e quantas já têm De-Para mapeado.',
  },
  {
    target: 'btn-auto',
    title: '⚡ Botão Auto-Popular',
    description:
      'Clique aqui para gerar automaticamente todos os mapeamentos possíveis de uma só vez. Ele faz 3 coisas: mapeia o tpRubr (Vencimento→1, Desconto→2), mapeia o codIncPisPasep (0→"00"), e importa as naturezas já corrigidas pelo Validador no staging.',
  },
  {
    target: 'btn-preview',
    title: '👁️ Botão Preview S-1010',
    description:
      'Gera uma pré-visualização de como cada rubrica ficará montada para o XML S-1010. Mostra todos os campos (natRubr, tpRubr, PisPasep, INSS, IRRF, FGTS) e se a rubrica está pronta ou ainda bloqueada.',
  },
  {
    target: 'tabs',
    title: '📑 Abas de Navegação',
    description:
      'Cada aba corresponde a um campo obrigatório do S-1010. O número ao lado mostra quantas rubricas precisam de atenção naquele campo. Clique em cada aba para ver os detalhes e resolver pendências.',
  },
  {
    target: 'natRubr',
    title: '🔢 Aba Natureza (natRubr)',
    description:
      'Esta é a aba mais importante. Mostra as rubricas cujo código de natureza está expirado ou não existe na Tabela 3 do eSocial. Para cada rubrica bloqueada, você pode escolher uma nova natureza vigente no dropdown e clicar "Mapear". Rubricas já resolvidas pelo staging aparecem com "Via Staging ✓".',
    activateTab: 'natRubr',
  },
  {
    target: 'tpRubr',
    title: '📋 Aba Tipo (tpRubr)',
    description:
      'O campo tpRubr (tipo da rubrica) indica se é Vencimento (1) ou Desconto (2). Esse mapeamento é 100% automático — o sistema lê o campo "Tipo" da planilha GL e converte. Basta clicar no Auto-Popular e está resolvido.',
    activateTab: 'tpRubr',
  },
  {
    target: 'codIncPisPasep',
    title: '💰 Aba PIS/PASEP',
    description:
      'O campo codIncPisPasep é novo no leiaute S-1.3 e obrigatório. Para esta empresa, TODAS as rubricas possuem "Cód. PIS/PASEP = 0" (Não é base de cálculo), que mapeia automaticamente para o código "00". Também é 100% automático.',
    activateTab: 'codIncPisPasep',
  },
  {
    target: 'preview',
    title: '🔍 Aba Preview S-1010',
    description:
      'Aqui você vê o resultado final de todos os mapeamentos. Cada rubrica mostra o valor final de cada campo, de onde veio (original, depara, staging, automático) e se está pronta para envio ao eSocial ou ainda tem algum campo bloqueado.',
    activateTab: 'preview',
  },
  {
    target: 'header',
    title: '✅ Tour Completo!',
    description:
      'Agora você conhece todas as seções do De-Para. O fluxo recomendado é: 1) Clique em "Auto-Popular" para resolver tpRubr, PisPasep e naturezas do staging. 2) Na aba natRubr, mapeie manualmente as naturezas que ainda estão bloqueadas. 3) Use o "Preview S-1010" para conferir tudo antes de ir para a tela do eSocial enviar.',
  },
]

function tourToggle() {
  if (tourActive.value) {
    tourEnd()
  } else {
    tourStart()
  }
}

function tourStart() {
  tourStep.value = 0
  tourActive.value = true
  nextTick(() => tourHighlight())
}

function tourEnd() {
  tourActive.value = false
  tourStep.value = 0
}

function tourNext() {
  if (tourStep.value < tourSteps.length - 1) {
    tourStep.value++
    const step = tourSteps[tourStep.value]
    if (step?.activateTab) {
      activeTab.value = step.activateTab
    }
    nextTick(() => tourHighlight())
  }
}

function tourPrev() {
  if (tourStep.value > 0) {
    tourStep.value--
    const step = tourSteps[tourStep.value]
    if (step?.activateTab) {
      activeTab.value = step.activateTab
    }
    nextTick(() => tourHighlight())
  }
}

function tourGoTo(i: number) {
  tourStep.value = i
  const step = tourSteps[i]
  if (step?.activateTab) {
    activeTab.value = step.activateTab
  }
  nextTick(() => tourHighlight())
}

function tourHighlight() {
  const step = tourSteps[tourStep.value]
  if (!step) return
  const el = document.querySelector(`[data-tour="${step.target}"]`) as HTMLElement | null
  if (!el) {
    // Fallback — center popup
    spotlightStyle.value = { display: 'none' }
    popupStyle.value = {
      position: 'fixed',
      top: '50%',
      left: '50%',
      transform: 'translate(-50%, -50%)',
    }
    return
  }

  el.scrollIntoView({ behavior: 'smooth', block: 'center' })

  // Small delay for scroll to settle
  setTimeout(() => {
    const rect = el.getBoundingClientRect()
    const pad = 8

    spotlightStyle.value = {
      position: 'fixed',
      top: rect.top - pad + 'px',
      left: rect.left - pad + 'px',
      width: rect.width + pad * 2 + 'px',
      height: rect.height + pad * 2 + 'px',
      borderRadius: '12px',
      display: 'block',
    }

    // Position popup below or above the element
    const viewH = window.innerHeight
    const popupH = 280
    let popupTop: number
    let popupLeft: number

    if (rect.bottom + popupH + 20 < viewH) {
      popupTop = rect.bottom + 16
    } else {
      popupTop = Math.max(16, rect.top - popupH - 16)
    }

    popupLeft = Math.min(Math.max(16, rect.left + rect.width / 2 - 200), window.innerWidth - 416)

    popupStyle.value = {
      position: 'fixed',
      top: popupTop + 'px',
      left: popupLeft + 'px',
    }
  }, 150)
}

// Re-position on resize
function onResize() {
  if (tourActive.value) tourHighlight()
}

// Init
onMounted(async () => {
  window.addEventListener('resize', onResize)
  await Promise.all([fetchResumo(), fetchBloqueadores(), fetchNaturezas()])
})
onUnmounted(() => window.removeEventListener('resize', onResize))

// Tabs
const tabs = computed(() => [
  {
    id: 'natRubr',
    label: 'Natureza (natRubr)',
    count: resumo.value?.natrubr?.bloqueadas ?? 0,
  },
  {
    id: 'tpRubr',
    label: 'Tipo (tpRubr)',
    count: resumo.value?.tpRubr?.disponiveis ?? 0,
  },
  {
    id: 'codIncPisPasep',
    label: 'PIS/PASEP',
    count: resumo.value?.codIncPisPasep?.disponiveis ?? 0,
  },
  {
    id: 'preview',
    label: 'Preview S-1010',
    count: preview.value?.prontas,
  },
])

const totalDePara = computed(() => {
  if (!resumo.value) return 0
  const nat = resumo.value.natrubr.depara
  const tp = resumo.value.tpRubr.depara
  const pis = resumo.value.codIncPisPasep.depara
  return nat.pendente + nat.aplicado + (tp.pendente + tp.aplicado) + (pis.pendente + pis.aplicado)
})

const filteredPreview = computed(() => {
  if (!preview.value?.rubricas) return []
  if (previewFilter.value === 'prontas') return preview.value.rubricas.filter((r: any) => r.pronto)
  if (previewFilter.value === 'bloqueadas')
    return preview.value.rubricas.filter((r: any) => !r.pronto)
  return preview.value.rubricas
})

// Methods
async function fetchResumo() {
  try {
    const { data } = await axios.get(`${PYTHON_API}/api/depara/resumo`)
    resumo.value = data
  } catch (e: any) {
    error.value = 'Erro ao carregar resumo: ' + (e.response?.data?.detail || e.message)
  }
}

async function fetchBloqueadores() {
  loadingBloqueadores.value = true
  try {
    const { data } = await axios.get(`${PYTHON_API}/api/depara/bloqueadores`)
    bloqueadores.value = data.bloqueadores
  } catch (e: any) {
    error.value = 'Erro ao carregar bloqueadores: ' + (e.response?.data?.detail || e.message)
  } finally {
    loadingBloqueadores.value = false
  }
}

async function fetchNaturezas() {
  try {
    const { data } = await axios.get(`${PYTHON_API}/api/depara/naturezas`)
    naturezasVigentes.value = data.naturezas
  } catch (e: any) {
    error.value = 'Erro ao carregar naturezas: ' + (e.response?.data?.detail || e.message)
  }
}

async function fetchPreview() {
  loadingPreview.value = true
  activeTab.value = 'preview'
  try {
    const { data } = await axios.get(`${PYTHON_API}/api/depara/preview`)
    preview.value = data
  } catch (e: any) {
    error.value = 'Erro ao gerar preview: ' + (e.response?.data?.detail || e.message)
  } finally {
    loadingPreview.value = false
  }
}

async function autoPopular() {
  autoPopulando.value = true
  error.value = ''
  try {
    const { data } = await axios.post(`${PYTHON_API}/api/depara/auto-popular`)
    const r = data.resultados
    const msg = `Auto-popular: ${r.tpRubr} tpRubr, ${r.codIncPisPasep} PisPasep, ${r.natRubr_staging} natRubr (staging)`
    alert(msg)
    await fetchResumo()
    await fetchBloqueadores()
  } catch (e: any) {
    error.value = 'Erro ao auto-popular: ' + (e.response?.data?.detail || e.message)
  } finally {
    autoPopulando.value = false
  }
}

async function mapearNatRubr(codRubrica: string) {
  const valorNovo = natSelections[codRubrica]
  if (!valorNovo) return

  try {
    await axios.post(`${PYTHON_API}/api/depara/mapear`, {
      cod_rubrica: codRubrica,
      campo: 'natRubr',
      valor_novo: valorNovo,
    })
    // Refresh
    await fetchBloqueadores()
    await fetchResumo()
  } catch (e: any) {
    error.value = 'Erro ao mapear: ' + (e.response?.data?.detail || e.message)
  }
}

function rowClass(b: any) {
  if (b.depara_valor || b.correcao_staging) return 'dp-row-resolved'
  return ''
}
</script>

<style scoped>
/* ═══════════ ROOT ═══════════ */
.dp-root {
  color: #e2e8f0;
}

/* ═══════════ HEADER ═══════════ */
.dp-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 24px;
  flex-wrap: wrap;
  gap: 16px;
}
.dp-title {
  font-size: 1.75rem;
  font-weight: 700;
  color: #fff;
  margin: 0 0 4px;
}
.dp-subtitle {
  color: #94a3b8;
  font-size: 0.875rem;
  margin: 0;
}
.dp-header-actions {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

/* ═══════════ BUTTONS ═══════════ */
.dp-btn {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 10px 18px;
  border: none;
  border-radius: 10px;
  font-size: 0.875rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.15s;
}
.dp-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
.dp-btn-icon {
  width: 16px;
  height: 16px;
}
.dp-btn-auto {
  background: rgba(0, 102, 255, 0.15);
  color: #0066ff;
  border: 1px solid rgba(0, 102, 255, 0.3);
}
.dp-btn-auto:hover:not(:disabled) {
  background: rgba(0, 102, 255, 0.25);
}
.dp-btn-preview {
  background: rgba(139, 92, 246, 0.15);
  color: #a78bfa;
  border: 1px solid rgba(139, 92, 246, 0.3);
}
.dp-btn-preview:hover:not(:disabled) {
  background: rgba(139, 92, 246, 0.25);
}
.dp-btn-sm {
  padding: 6px 12px;
  font-size: 0.8rem;
  border-radius: 8px;
}
.dp-btn-map {
  background: #0066ff;
  color: #fff;
}
.dp-btn-map:hover:not(:disabled) {
  background: #0055dd;
}
.dp-btn-lg {
  padding: 14px 28px;
  font-size: 1rem;
  margin-top: 16px;
}

/* ═══════════ CARDS ═══════════ */
.dp-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 16px;
  margin-bottom: 24px;
}
.dp-cards-sm {
  margin-bottom: 20px;
}
.dp-card {
  background: #0d1530;
  border: 1px solid rgba(0, 102, 255, 0.12);
  border-radius: 12px;
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 6px;
  transition: border-color 0.2s;
}
.dp-card:hover {
  border-color: rgba(0, 102, 255, 0.3);
}
.dp-card-number {
  font-size: 2rem;
  font-weight: 700;
  line-height: 1;
}
.dp-card-label {
  font-size: 0.8rem;
  color: #94a3b8;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}
.dp-card-total .dp-card-number {
  color: #0066ff;
}
.dp-card-bloqueada .dp-card-number {
  color: #ef4444;
}
.dp-card-staging .dp-card-number {
  color: #f59e0b;
}
.dp-card-depara .dp-card-number {
  color: #22c55e;
}
.dp-card-ok .dp-card-number {
  color: #22c55e;
}

/* ═══════════ TABS ═══════════ */
.dp-tabs {
  display: flex;
  gap: 4px;
  border-bottom: 1px solid rgba(0, 102, 255, 0.12);
  margin-bottom: 24px;
  overflow-x: auto;
}
.dp-tab {
  padding: 12px 20px;
  background: none;
  border: none;
  color: #94a3b8;
  font-size: 0.875rem;
  font-weight: 500;
  cursor: pointer;
  border-bottom: 2px solid transparent;
  transition: all 0.15s;
  white-space: nowrap;
  display: flex;
  align-items: center;
  gap: 8px;
}
.dp-tab:hover {
  color: #e2e8f0;
}
.dp-tab.active {
  color: #0066ff;
  border-bottom-color: #0066ff;
}
.dp-tab-count {
  background: rgba(0, 102, 255, 0.15);
  color: #0066ff;
  font-size: 0.75rem;
  padding: 2px 8px;
  border-radius: 10px;
  font-weight: 600;
}
.dp-tab.active .dp-tab-count {
  background: #0066ff;
  color: #fff;
}

/* ═══════════ TABLE ═══════════ */
.dp-table-container {
  overflow-x: auto;
  border-radius: 12px;
  border: 1px solid rgba(0, 102, 255, 0.12);
}
.dp-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.85rem;
}
.dp-table thead {
  background: #0d1530;
  position: sticky;
  top: 0;
}
.dp-table th {
  padding: 12px 14px;
  text-align: left;
  font-weight: 600;
  color: #94a3b8;
  font-size: 0.75rem;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  border-bottom: 1px solid rgba(0, 102, 255, 0.12);
  white-space: nowrap;
}
.dp-table td {
  padding: 10px 14px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.04);
  vertical-align: middle;
}
.dp-table tbody tr:hover {
  background: rgba(0, 102, 255, 0.04);
}
.dp-cell-code {
  font-family: 'JetBrains Mono', monospace;
  font-weight: 600;
  color: #0066ff;
}
.dp-cell-desc {
  max-width: 250px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.dp-cell-nat {
  font-family: 'JetBrains Mono', monospace;
}

/* ═══════════ BADGES ═══════════ */
.dp-badge {
  display: inline-block;
  padding: 3px 10px;
  border-radius: 6px;
  font-size: 0.75rem;
  font-weight: 600;
  white-space: nowrap;
}
.dp-badge-expirado {
  background: rgba(239, 68, 68, 0.15);
  color: #ef4444;
}
.dp-badge-inexistente {
  background: rgba(239, 68, 68, 0.15);
  color: #f87171;
}
.dp-badge-ok {
  background: rgba(34, 197, 94, 0.15);
  color: #22c55e;
}
.dp-badge-staging {
  background: rgba(245, 158, 11, 0.15);
  color: #f59e0b;
}
.dp-badge-pendente {
  background: rgba(0, 102, 255, 0.15);
  color: #0066ff;
}
.dp-badge-aplicado {
  background: rgba(34, 197, 94, 0.15);
  color: #22c55e;
}
.dp-badge-bloqueada {
  background: rgba(239, 68, 68, 0.15);
  color: #ef4444;
}

/* ═══════════ VALUE + FONTE ═══════════ */
.dp-val {
  font-family: 'JetBrains Mono', monospace;
  font-weight: 600;
  font-size: 0.85rem;
}
.dp-val-original {
  color: #94a3b8;
}
.dp-val-depara {
  color: #0066ff;
}
.dp-val-staging {
  color: #f59e0b;
}
.dp-val-automatico {
  color: #22c55e;
}
.dp-val-BLOQUEADO {
  color: #ef4444;
}
.dp-fonte {
  display: block;
  font-size: 0.65rem;
  color: #64748b;
  text-transform: uppercase;
  letter-spacing: 0.3px;
}

/* ═══════════ SELECT ═══════════ */
.dp-select {
  background: #0d1530;
  color: #e2e8f0;
  border: 1px solid rgba(0, 102, 255, 0.2);
  border-radius: 8px;
  padding: 6px 10px;
  font-size: 0.8rem;
  min-width: 200px;
  cursor: pointer;
}
.dp-select:focus {
  outline: none;
  border-color: #0066ff;
  box-shadow: 0 0 0 2px rgba(0, 102, 255, 0.2);
}
.dp-action-cell {
  display: flex;
  gap: 8px;
  align-items: center;
}

/* ═══════════ INFO BOX ═══════════ */
.dp-info-box {
  background: #0d1530;
  border: 1px solid rgba(0, 102, 255, 0.15);
  border-radius: 12px;
  padding: 20px 24px;
  display: flex;
  gap: 16px;
  align-items: flex-start;
  margin-bottom: 16px;
}
.dp-info-box p {
  margin: 6px 0 0;
  color: #94a3b8;
  font-size: 0.875rem;
  line-height: 1.5;
}
.dp-info-box code {
  background: rgba(0, 102, 255, 0.1);
  color: #0066ff;
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 0.8rem;
  font-family: 'JetBrains Mono', monospace;
}
.dp-info-icon {
  width: 24px;
  height: 24px;
  color: #0066ff;
  flex-shrink: 0;
  margin-top: 2px;
}
.dp-success-box {
  background: rgba(34, 197, 94, 0.1);
  border: 1px solid rgba(34, 197, 94, 0.2);
  border-radius: 12px;
  padding: 16px 24px;
  color: #22c55e;
  font-weight: 600;
  font-size: 0.95rem;
  margin-top: 16px;
}

/* ═══════════ ROW STATES ═══════════ */
.dp-row-resolved {
  opacity: 0.65;
}
.dp-row-ok {
  border-left: 3px solid #22c55e;
}
.dp-row-block {
  border-left: 3px solid #ef4444;
}

/* ═══════════ FILTER BAR ═══════════ */
.dp-filter-bar {
  display: flex;
  gap: 8px;
  margin-bottom: 16px;
}
.dp-filter-btn {
  padding: 8px 16px;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 8px;
  color: #94a3b8;
  font-size: 0.8rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.15s;
}
.dp-filter-btn:hover {
  background: rgba(255, 255, 255, 0.08);
  color: #e2e8f0;
}
.dp-filter-btn.active {
  background: rgba(0, 102, 255, 0.15);
  border-color: rgba(0, 102, 255, 0.3);
  color: #0066ff;
}
.dp-filter-ok.active {
  background: rgba(34, 197, 94, 0.15);
  border-color: rgba(34, 197, 94, 0.3);
  color: #22c55e;
}
.dp-filter-block.active {
  background: rgba(239, 68, 68, 0.15);
  border-color: rgba(239, 68, 68, 0.3);
  color: #ef4444;
}

/* ═══════════ UTILITY ═══════════ */
.dp-text-muted {
  color: #475569;
  font-size: 0.85rem;
}
.dp-text-ok {
  color: #22c55e;
  font-size: 0.8rem;
  font-weight: 500;
}
.dp-error {
  background: rgba(239, 68, 68, 0.1);
  border: 1px solid rgba(239, 68, 68, 0.2);
  border-radius: 10px;
  color: #ef4444;
  padding: 12px 16px;
  margin-bottom: 16px;
  font-size: 0.875rem;
}
.dp-loading {
  text-align: center;
  color: #94a3b8;
  padding: 40px;
  font-size: 0.95rem;
}
.dp-empty {
  text-align: center;
  color: #64748b;
  padding: 40px;
  font-size: 0.95rem;
}
.dp-section {
  min-height: 200px;
}

/* ═══════════ TOUR BUTTON ═══════════ */
.dp-btn-tour {
  background: rgba(245, 158, 11, 0.12);
  color: #f59e0b;
  border: 1px solid rgba(245, 158, 11, 0.25);
}
.dp-btn-tour:hover:not(:disabled) {
  background: rgba(245, 158, 11, 0.22);
}
.dp-btn-tour.active {
  background: rgba(245, 158, 11, 0.25);
  border-color: #f59e0b;
  box-shadow: 0 0 12px rgba(245, 158, 11, 0.2);
}

/* ═══════════ TOUR OVERLAY ═══════════ */
.tour-overlay {
  position: fixed;
  inset: 0;
  z-index: 9998;
  background: rgba(0, 0, 0, 0.65);
  backdrop-filter: blur(2px);
}

.tour-spotlight {
  position: fixed;
  box-shadow:
    0 0 0 4000px rgba(0, 0, 0, 0.6),
    0 0 0 3px rgba(0, 102, 255, 0.5),
    0 0 20px rgba(0, 102, 255, 0.3);
  border-radius: 12px;
  z-index: 9999;
  pointer-events: none;
  transition: all 0.35s cubic-bezier(0.4, 0, 0.2, 1);
}

.tour-popup {
  z-index: 10000;
  width: 400px;
  background: #111b3a;
  border: 1px solid rgba(0, 102, 255, 0.25);
  border-radius: 14px;
  padding: 20px 24px;
  box-shadow:
    0 20px 60px rgba(0, 0, 0, 0.5),
    0 0 30px rgba(0, 102, 255, 0.1);
  animation: tourPopIn 0.25s ease-out;
}
@keyframes tourPopIn {
  from {
    opacity: 0;
    transform: translateY(8px) scale(0.96);
  }
  to {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}

.tour-popup-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}
.tour-step-badge {
  background: rgba(0, 102, 255, 0.15);
  color: #0066ff;
  font-size: 0.7rem;
  font-weight: 700;
  padding: 3px 10px;
  border-radius: 20px;
  letter-spacing: 0.5px;
}
.tour-close {
  background: none;
  border: none;
  color: #64748b;
  font-size: 1.1rem;
  cursor: pointer;
  padding: 4px 8px;
  border-radius: 6px;
  transition: all 0.15s;
}
.tour-close:hover {
  color: #ef4444;
  background: rgba(239, 68, 68, 0.1);
}

.tour-popup-title {
  font-size: 1.05rem;
  font-weight: 700;
  color: #fff;
  margin: 0 0 8px;
}
.tour-popup-desc {
  font-size: 0.85rem;
  color: #94a3b8;
  line-height: 1.6;
  margin: 0 0 16px;
}

.tour-popup-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 10px;
}

.tour-btn {
  padding: 8px 18px;
  border: none;
  border-radius: 8px;
  font-size: 0.8rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.15s;
}
.tour-btn-primary {
  background: #0066ff;
  color: #fff;
}
.tour-btn-primary:hover {
  background: #0055dd;
}
.tour-btn-secondary {
  background: rgba(255, 255, 255, 0.08);
  color: #94a3b8;
  border: 1px solid rgba(255, 255, 255, 0.1);
}
.tour-btn-secondary:hover {
  background: rgba(255, 255, 255, 0.12);
  color: #e2e8f0;
}
.tour-btn-finish {
  background: #22c55e;
  color: #fff;
}
.tour-btn-finish:hover {
  background: #16a34a;
}

.tour-dots {
  display: flex;
  justify-content: center;
  gap: 6px;
  margin-top: 14px;
}
.tour-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.12);
  cursor: pointer;
  transition: all 0.2s;
}
.tour-dot:hover {
  background: rgba(255, 255, 255, 0.3);
}
.tour-dot.active {
  background: #0066ff;
  box-shadow: 0 0 6px rgba(0, 102, 255, 0.5);
  transform: scale(1.3);
}
.tour-dot.done {
  background: rgba(0, 102, 255, 0.4);
}
</style>
