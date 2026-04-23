<script setup lang="ts">
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import axios from 'axios'
import { PYTHON_API } from '@/lib/api'

// ── Tipos ──────────────────────────────────────────────────────────
interface FonteStatus {
  mes: string
  xlsx_nome: string
  xlsx_ok: boolean
  xlsx_mb: number
  zip_nome: string
  zip_ok: boolean
  zip_mb: number
  total_lote1_esperado: number
}

interface LoteResumo {
  total: number
  pendente: number
  ja_feito: number
  erro: number
  com_recibo_no_zip?: number
}

interface MesResumo {
  mes: string
  lotes: Record<string, LoteResumo>
}

interface ResultadoTeste {
  sucesso: boolean
  etapa: string
  cpf?: string
  mes?: string
  lote?: string
  protocolo?: string
  nr_recibo_original?: string
  nr_recibo_novo?: string
  codigo_resposta?: string
  descricao?: string
  ocorrencias?: Array<{ codigo?: string; descricao?: string }>
  erro?: string
}

interface BatchErro {
  cpf: string
  etapa: string
  erro: string
  codigo?: string
  ts: string
}

interface BatchState {
  status: 'idle' | 'running' | 'paused' | 'stopping' | 'finished' | 'error'
  run_id: string | null
  mes: string | null
  lote: string | null
  total: number
  processados: number
  sucessos: number
  erros: number
  pulados_sem_s1210: number
  started_at: string | null
  updated_at: string | null
  cpf_atual: string | null
  indice_atual: number | null
  ultimo_resultado: ResultadoTeste | null
  erros_recentes: BatchErro[]
  finalizado_em: string | null
  motivo_parada: string | null
  logs?: Array<{ seq: number; ts: string; level: string; msg: string; cpf?: string }>
  ultimo_log_seq?: number
}

// ── Estado ─────────────────────────────────────────────────────────
const fontes = ref<FonteStatus[]>([])
const downloadsPath = ref('')
const resumo = ref<MesResumo[]>([])
const loading = ref(false)
const loadingMsg = ref('')
const enviando = ref(false)

const resultadoTeste = ref<ResultadoTeste | null>(null)
const showResultado = ref(false)
const showInfoLotes = ref(false)

const logsTerminal = ref<Array<{ ts: string; level: string; msg: string; cpf?: string }>>([])

// ── Estado do batch ────────────────────────────────────────────────
const batchState = ref<BatchState | null>(null)
const lastLogSeq = ref(0)
let pollingTimer: number | null = null

const MESES = ['2025-02', '2025-03', '2025-04']
const LOTES = ['1_LOTE', '2_LOTE', '3_LOTE', '4_LOTE']
const LOTE_LABELS: Record<string, string> = {
  '1_LOTE': 'Lote 1 — sem plano de saúde',
  '2_LOTE': 'Lote 2 — plano de saúde (grupo A)',
  '3_LOTE': 'Lote 3 — plano de saúde (grupo B)',
  '4_LOTE': 'Lote 4 — casos manuais',
}
const MES_LABELS: Record<string, string> = {
  '2025-02': 'Fev / 2025',
  '2025-03': 'Mar / 2025',
  '2025-04': 'Abr / 2025',
}

// ── Derivadas ──────────────────────────────────────────────────────
const fontesOk = computed(() => fontes.value.every((f) => f.xlsx_ok && f.zip_ok))
const xlsxCarregado = computed(() => resumo.value.length > 0)

function getLote(mes: string, lote: string): LoteResumo | null {
  const m = resumo.value.find((r) => r.mes === mes)
  if (!m) return null
  return m.lotes[lote] ?? null
}

// ── Terminal log ───────────────────────────────────────────────────
function log(msg: string, level: 'info' | 'ok' | 'err' | 'warn' = 'info') {
  const ts = new Date().toLocaleTimeString('pt-BR')
  logsTerminal.value.push({ ts, level, msg })
  if (logsTerminal.value.length > 500) {
    logsTerminal.value.shift()
  }
}

// ── Actions ────────────────────────────────────────────────────────
async function carregarFontes() {
  loading.value = true
  loadingMsg.value = 'Validando arquivos em Downloads...'
  try {
    const resp = await axios.get(`${PYTHON_API}/api/esocial/s1210-missao/fontes`)
    fontes.value = resp.data.fontes
    downloadsPath.value = resp.data.downloads
    log(`Fontes validadas em ${resp.data.downloads}`, 'ok')
    fontes.value.forEach((f) => {
      if (f.xlsx_ok && f.zip_ok) {
        log(`✓ ${f.mes}: ${f.xlsx_nome} (${f.xlsx_mb} MB) + ${f.zip_nome} (${f.zip_mb} MB)`, 'ok')
      } else {
        log(
          `✗ ${f.mes}: XLSX=${f.xlsx_ok ? 'ok' : 'FALTA'} ZIP=${f.zip_ok ? 'ok' : 'FALTA'}`,
          'err',
        )
      }
    })
  } catch (e: any) {
    log(`Erro validando fontes: ${e?.message ?? e}`, 'err')
  } finally {
    loading.value = false
  }
}

async function carregarEscopo() {
  if (!fontesOk.value) {
    log('Impossível carregar: fontes incompletas', 'err')
    return
  }
  const jaCarregado = xlsxCarregado.value
  loading.value = true
  loadingMsg.value = jaCarregado
    ? 'Atualizando contadores...'
    : 'Parseando 3 XLSX da Ana (~60-90s, XLSX grandes)...'
  if (!jaCarregado) {
    log('Carregando escopo dos 3 XLSX (aguarde ~1 minuto)...', 'info')
  }
  try {
    const resp = await axios.post(`${PYTHON_API}/api/esocial/s1210-missao/carregar`, null, {
      params: { indexar_zips: false },
      timeout: 300000,
    })
    if (resp.data.erro) {
      log(`Erro: ${resp.data.erro}`, 'err')
      return
    }
    resumo.value = resp.data.resumo
    log(`Escopo carregado: ${resumo.value.length} meses`, 'ok')
    resumo.value.forEach((m) => {
      const l1 = m.lotes['1_LOTE']?.total ?? 0
      const l2 = m.lotes['2_LOTE']?.total ?? 0
      const l3 = m.lotes['3_LOTE']?.total ?? 0
      const l4 = m.lotes['4_LOTE']?.total ?? 0
      log(`  ${m.mes}: L1=${l1}  L2=${l2}  L3=${l3}  L4=${l4}`, 'info')
    })
  } catch (e: any) {
    log(`Erro carregando XLSX: ${e?.response?.data?.detail ?? e?.message ?? e}`, 'err')
  } finally {
    loading.value = false
  }
}

async function testarPrimeiroCpf(mes: string, lote: string) {
  const confirmed = confirm(
    `⚠️ ATENÇÃO — ENVIO EM PRODUÇÃO\n\n` +
      `Vai pegar o PRIMEIRO CPF de ${MES_LABELS[mes]} ${LOTE_LABELS[lote]} e enviar S-1210 retif em PRODUÇÃO.\n\n` +
      `Deseja continuar?`,
  )
  if (!confirmed) return

  enviando.value = true
  resultadoTeste.value = null
  showResultado.value = false
  log(`Iniciando teste: ${mes} / ${lote} / indice 0 → PRODUÇÃO`, 'warn')

  try {
    const resp = await axios.post(
      `${PYTHON_API}/api/esocial/s1210-missao/testar-um-cpf`,
      {
        mes,
        lote: lote.replace('_LOTE', ''),
        indice: 0,
        confirmar_producao: true,
      },
      { timeout: 120_000 },
    )
    resultadoTeste.value = resp.data
    showResultado.value = true
    if (resp.data.sucesso) {
      log(`✅ SUCESSO CPF ${resp.data.cpf} — recibo novo: ${resp.data.nr_recibo_novo}`, 'ok')
    } else {
      log(
        `❌ FALHA etapa=${resp.data.etapa} CPF=${resp.data.cpf ?? '?'} erro=${resp.data.erro ?? '?'}`,
        'err',
      )
    }
  } catch (e: any) {
    const detail = e?.response?.data?.detail ?? e?.message ?? String(e)
    resultadoTeste.value = {
      sucesso: false,
      etapa: 'requisicao',
      erro: detail,
    }
    showResultado.value = true
    log(`❌ Erro na requisição: ${detail}`, 'err')
  } finally {
    enviando.value = false
    // atualiza contadores do grid pra refletir o novo CPF feito/erro
    carregarEscopo().catch(() => {})
  }
}

function copiarResultado() {
  if (!resultadoTeste.value) return
  const txt = JSON.stringify(resultadoTeste.value, null, 2)
  navigator.clipboard.writeText(txt).then(() => {
    log('Resultado copiado p/ clipboard', 'ok')
  })
}

// ── Batch ─────────────────────────────────────────────────────────
const batchBusy = ref(false)

const batchProgresso = computed(() => {
  const s = batchState.value
  if (!s || s.total === 0) return 0
  return Math.round((s.processados / s.total) * 100)
})

const batchStatusLabel = computed(() => {
  const s = batchState.value?.status ?? 'idle'
  return (
    {
      idle: 'Parado',
      running: 'Rodando',
      paused: 'Pausado',
      stopping: 'Parando…',
      finished: 'Concluído',
      error: 'Erro fatal',
    }[s] ?? s
  )
})

async function refreshBatchStatus() {
  try {
    const resp = await axios.get(`${PYTHON_API}/api/esocial/s1210-missao/batch/status`, {
      params: { since_seq: lastLogSeq.value, log_limit: 100 },
      timeout: 10_000,
    })
    const data: BatchState = resp.data
    batchState.value = data
    if (data.logs && data.logs.length > 0) {
      for (const entry of data.logs) {
        logsTerminal.value.push({
          ts: entry.ts,
          level: entry.level,
          msg: entry.msg,
          cpf: entry.cpf,
        })
      }
      if (logsTerminal.value.length > 500) {
        logsTerminal.value.splice(0, logsTerminal.value.length - 500)
      }
      lastLogSeq.value = data.ultimo_log_seq ?? lastLogSeq.value
    }
  } catch (e) {
    // silencioso — polling não precisa poluir o terminal
  }
}

function startPolling() {
  if (pollingTimer !== null) return
  pollingTimer = window.setInterval(refreshBatchStatus, 1500)
}

function stopPolling() {
  if (pollingTimer !== null) {
    window.clearInterval(pollingTimer)
    pollingTimer = null
  }
}

async function iniciarLote(mes: string, lote: string) {
  const info = getLote(mes, lote)
  const total = info?.total ?? 0
  if (total === 0) {
    log('Lote sem CPFs', 'err')
    return
  }
  const confirmed = confirm(
    `⚠️ INICIAR PROCESSAMENTO EM LOTE — PRODUÇÃO\n\n` +
      `${MES_LABELS[mes]} / ${LOTE_LABELS[lote]}\n` +
      `Total de CPFs: ${total.toLocaleString('pt-BR')}\n\n` +
      `O processamento pode ser PAUSADO ou PARADO a qualquer momento.\n\n` +
      `Continuar?`,
  )
  if (!confirmed) return

  batchBusy.value = true
  try {
    const resp = await axios.post(
      `${PYTHON_API}/api/esocial/s1210-missao/batch/start`,
      {
        mes,
        lote: lote.replace('_LOTE', ''),
        offset: 0,
        limit: null,
        confirmar_producao: true,
      },
      { timeout: 30_000 },
    )
    batchState.value = resp.data
    log(`🚀 Batch iniciado — ${mes} / ${lote} / total=${resp.data.total}`, 'ok')
    startPolling()
  } catch (e: any) {
    const detail = e?.response?.data?.detail ?? e?.message ?? String(e)
    log(`❌ Erro iniciando batch: ${detail}`, 'err')
  } finally {
    batchBusy.value = false
  }
}

async function pausarLote() {
  batchBusy.value = true
  try {
    const resp = await axios.post(`${PYTHON_API}/api/esocial/s1210-missao/batch/pause`)
    batchState.value = resp.data
    log('⏸️  Pausa solicitada (termina o CPF atual e para)', 'warn')
  } catch (e: any) {
    log(`Erro pausando: ${e?.response?.data?.detail ?? e?.message}`, 'err')
  } finally {
    batchBusy.value = false
  }
}

async function retomarLote() {
  batchBusy.value = true
  try {
    const resp = await axios.post(`${PYTHON_API}/api/esocial/s1210-missao/batch/resume`)
    batchState.value = resp.data
    log('▶️  Retomado', 'ok')
  } catch (e: any) {
    log(`Erro retomando: ${e?.response?.data?.detail ?? e?.message}`, 'err')
  } finally {
    batchBusy.value = false
  }
}

async function pararLote() {
  const confirmed = confirm(
    'Parar o batch?\n\nO CPF atual termina e depois para.\nVocê pode iniciar de novo com offset novo depois.',
  )
  if (!confirmed) return
  batchBusy.value = true
  try {
    const resp = await axios.post(`${PYTHON_API}/api/esocial/s1210-missao/batch/stop`)
    batchState.value = resp.data
    log('⏹️  Stop solicitado', 'warn')
  } catch (e: any) {
    log(`Erro parando: ${e?.response?.data?.detail ?? e?.message}`, 'err')
  } finally {
    batchBusy.value = false
  }
}

onMounted(() => {
  log('S-1210 Missão APPA inicializada', 'info')
  // 1) valida fontes → 2) carrega XLSX automaticamente → 3) checa batch em andamento
  carregarFontes().then(async () => {
    if (fontesOk.value) {
      await carregarEscopo()
    }
    await refreshBatchStatus()
    if (batchState.value && ['running', 'paused', 'stopping'].includes(batchState.value.status)) {
      log(`Batch ${batchState.value.status} detectado — retomando monitoramento`, 'warn')
      startPolling()
    }
  })
})

onBeforeUnmount(() => {
  stopPolling()
})
</script>

<template>
  <div class="min-h-screen bg-[#0a1024] text-white p-6">
    <!-- Header ─────────────────────────────────────────────── -->
    <div class="mb-6 flex items-start justify-between gap-4">
      <div>
        <h1 class="text-2xl font-bold text-white">S-1210 Missão APPA</h1>
        <p class="text-sm text-slate-400 mt-1">
          3 meses (fev / mar / abr 2025) × 4 lotes. Escopo: XLSX da Ana. Dados: ZIPs do eSocial.
          Envio direto em <span class="text-emerald-400 font-semibold">PRODUÇÃO</span>.
        </p>
      </div>
      <div class="flex items-center gap-2">
        <button
          @click="carregarFontes"
          :disabled="loading"
          class="px-3 py-1.5 rounded-lg bg-slate-700 hover:bg-slate-600 text-sm text-white disabled:opacity-50"
        >
          Revalidar fontes
        </button>
        <button
          @click="carregarEscopo"
          :disabled="loading || !fontesOk"
          :class="
            fontesOk && !loading
              ? 'bg-[#0066FF] hover:bg-[#0052cc] text-white'
              : 'bg-slate-700 text-slate-400 cursor-not-allowed opacity-50'
          "
          class="px-4 py-1.5 font-medium rounded-lg flex items-center gap-2 text-sm"
        >
          {{ xlsxCarregado ? 'Recarregar XLSX' : 'Carregar XLSX (3 meses)' }}
        </button>
      </div>
    </div>

    <!-- Info lotes (toggle) ───────────────────────────────── -->
    <div class="mb-4 rounded-xl border border-white/10 bg-slate-800/40">
      <button
        @click="showInfoLotes = !showInfoLotes"
        class="w-full flex items-center justify-between px-4 py-2.5 text-sm text-slate-200 hover:bg-white/5 rounded-xl"
      >
        <span class="flex items-center gap-2">
          <span class="text-[#0066FF]">ℹ</span>
          <span class="font-medium">O que é cada lote?</span>
          <span class="text-slate-500 text-xs"
            >(clique para {{ showInfoLotes ? 'ocultar' : 'ver' }})</span
          >
        </span>
        <span class="text-slate-400 text-lg leading-none">{{ showInfoLotes ? '−' : '+' }}</span>
      </button>
      <div
        v-if="showInfoLotes"
        class="px-4 pb-4 pt-1 border-t border-white/10 text-sm text-slate-300 space-y-3"
      >
        <div>
          <div class="text-white font-semibold mb-1">Lote 1 — sem plano de saúde</div>
          <div class="text-slate-400 text-xs">
            CPFs que NÃO aparecem na aba Operadoras do XLSX (não têm operadora vinculada). S-1210
            retificado sem o bloco <code class="text-slate-200">&lt;planSaude&gt;</code>.
          </div>
        </div>
        <div>
          <div class="text-white font-semibold mb-1">Lote 2 — plano de saúde (grupo A)</div>
          <div class="text-slate-400 text-xs">
            CPFs com operadora + titular identificado no XLSX, cujas rubricas já estão com a
            natureza correta no eSocial. S-1210 retif com
            <code class="text-slate-200">&lt;planSaude&gt;</code> agregado por CNPJ da operadora,
            somando valores das rubricas do CPF. Rubricas típicas: 516, 605, 607, 619, 631, 638,
            774, 775. Ignoramos 9279/9281 (informativas).
          </div>
        </div>
        <div>
          <div class="text-white font-semibold mb-1">Lote 3 — plano de saúde (grupo B)</div>
          <div class="text-slate-400 text-xs">
            Mesma estrutura do Lote 2 (operadora + titular), mas as rubricas deste grupo estão com
            <strong>natureza errada no eSocial</strong> e precisam ser reclassificadas antes do
            envio:
            <ul class="list-disc list-inside mt-1 space-y-0.5">
              <li><strong>774</strong>: plano empresarial → natureza <strong>9219</strong></li>
              <li>
                <strong>775</strong>: plano coletivo empresarial → <strong>outros descontos</strong>
              </li>
              <li>
                <strong>522</strong>: outros descontos → <strong>plano coletivo empresarial</strong>
              </li>
            </ul>
            <span class="text-amber-400">Bloqueado</span> até a Ana concluir a reclassificação.
          </div>
        </div>
        <div>
          <div class="text-white font-semibold mb-1">Lote 4 — casos manuais</div>
          <div class="text-slate-400 text-xs">
            Casos especiais que não se encaixam nos lotes 1-3. Tratados manualmente, CPF a CPF.
          </div>
        </div>
        <div class="pt-2 border-t border-white/5 text-xs text-slate-500">
          Dedup: linhas 100% idênticas em <code>(cpf, rubrica, cnpj, valor)</code> são consolidadas
          antes da soma. Blocklist atual: 4 CPFs excluídos do processamento.
        </div>
      </div>
    </div>

    <!-- Fontes status ───────────────────────────────────────── -->
    <div class="mb-6 rounded-xl border border-white/10 bg-slate-800/50 p-4">
      <div class="flex items-center justify-between mb-3">
        <div class="text-sm text-slate-300 font-medium">
          Fontes em {{ downloadsPath || 'C:\\Users\\…\\Downloads' }}
        </div>
        <span
          :class="
            fontesOk
              ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30'
              : 'bg-red-500/10 text-red-400 border-red-500/30'
          "
          class="text-xs px-2 py-0.5 rounded-full border"
        >
          {{ fontesOk ? 'Todas OK' : 'Verificar' }}
        </span>
      </div>
      <div class="grid grid-cols-1 md:grid-cols-3 gap-3">
        <div
          v-for="f in fontes"
          :key="f.mes"
          class="rounded-lg bg-white/5 border border-white/10 p-3"
        >
          <div class="text-xs text-slate-400 uppercase tracking-wide mb-2">
            {{ MES_LABELS[f.mes] ?? f.mes }}
          </div>
          <div class="flex items-center gap-2 text-xs">
            <span :class="f.xlsx_ok ? 'text-emerald-400' : 'text-red-400'" class="font-mono">
              {{ f.xlsx_ok ? '✓' : '✗' }}
            </span>
            <span class="text-slate-300 truncate" :title="f.xlsx_nome">{{ f.xlsx_nome }}</span>
            <span v-if="f.xlsx_ok" class="text-slate-500 ml-auto">{{ f.xlsx_mb }} MB</span>
          </div>
          <div class="flex items-center gap-2 text-xs mt-1">
            <span :class="f.zip_ok ? 'text-emerald-400' : 'text-red-400'" class="font-mono">
              {{ f.zip_ok ? '✓' : '✗' }}
            </span>
            <span class="text-slate-300 truncate" :title="f.zip_nome">{{ f.zip_nome }}</span>
            <span v-if="f.zip_ok" class="text-slate-500 ml-auto">{{ f.zip_mb }} MB</span>
          </div>
          <div class="text-xs text-slate-500 mt-2">
            Lote 1 esperado:
            <span class="text-slate-300 font-mono">{{
              f.total_lote1_esperado.toLocaleString('pt-BR')
            }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Grid 3×4 compartimentos ─────────────────────────────── -->
    <div class="mb-6">
      <h2 class="text-lg font-semibold mb-3 text-white">Compartimentos (3 meses × 4 lotes)</h2>

      <div
        v-if="!xlsxCarregado"
        class="rounded-xl border border-dashed border-white/10 bg-slate-800/30 p-8 text-center"
      >
        <div class="text-slate-400 text-sm">
          Aguardando carregamento das XLSX.<br />
          Clique em <span class="text-white font-medium">Carregar XLSX (3 meses)</span> no topo.
        </div>
      </div>

      <div v-else class="space-y-4">
        <div
          v-for="mes in MESES"
          :key="mes"
          class="rounded-xl border border-white/10 bg-slate-800/50 p-4"
        >
          <div class="flex items-center justify-between mb-3">
            <div class="text-white font-semibold">{{ MES_LABELS[mes] }}</div>
            <div class="text-xs text-slate-400">
              Total:
              <span class="text-white font-mono">{{
                LOTES.reduce((s, l) => s + (getLote(mes, l)?.total ?? 0), 0).toLocaleString('pt-BR')
              }}</span>
              CPFs
            </div>
          </div>
          <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-3">
            <div
              v-for="lote in LOTES"
              :key="lote"
              class="rounded-lg bg-white/5 border border-white/10 p-3 flex flex-col"
            >
              <div class="text-xs text-slate-400 mb-1">{{ LOTE_LABELS[lote] }}</div>
              <div class="text-2xl font-bold text-white">
                {{ (getLote(mes, lote)?.total ?? 0).toLocaleString('pt-BR') }}
              </div>
              <div class="grid grid-cols-3 gap-1 text-xs mt-2">
                <div class="rounded bg-slate-700/50 px-1.5 py-0.5">
                  <div class="text-slate-400">pend</div>
                  <div class="text-slate-200 font-mono">
                    {{ getLote(mes, lote)?.pendente ?? 0 }}
                  </div>
                </div>
                <div class="rounded bg-emerald-500/10 px-1.5 py-0.5">
                  <div class="text-emerald-400">feito</div>
                  <div class="text-emerald-300 font-mono">
                    {{ getLote(mes, lote)?.ja_feito ?? 0 }}
                  </div>
                </div>
                <div class="rounded bg-red-500/10 px-1.5 py-0.5">
                  <div class="text-red-400">erro</div>
                  <div class="text-red-300 font-mono">{{ getLote(mes, lote)?.erro ?? 0 }}</div>
                </div>
              </div>
              <button
                @click="testarPrimeiroCpf(mes, lote)"
                :disabled="enviando || (getLote(mes, lote)?.total ?? 0) === 0"
                :class="
                  !enviando && (getLote(mes, lote)?.total ?? 0) > 0
                    ? 'bg-emerald-600 hover:bg-emerald-500 text-white'
                    : 'bg-slate-700 text-slate-400 cursor-not-allowed'
                "
                class="mt-3 w-full px-2 py-1.5 rounded-md text-xs font-medium transition-colors"
                :title="`Envia o 1º CPF deste compartimento em PRODUÇÃO`"
              >
                {{ enviando ? 'enviando...' : 'Testar 1º CPF (PROD)' }}
              </button>
              <button
                @click="iniciarLote(mes, lote)"
                :disabled="
                  batchBusy ||
                  batchState?.status === 'running' ||
                  batchState?.status === 'paused' ||
                  (getLote(mes, lote)?.total ?? 0) === 0
                "
                :class="
                  !batchBusy &&
                  batchState?.status !== 'running' &&
                  batchState?.status !== 'paused' &&
                  (getLote(mes, lote)?.total ?? 0) > 0
                    ? 'bg-[#0066FF] hover:bg-[#0052cc] text-white'
                    : 'bg-slate-700 text-slate-400 cursor-not-allowed'
                "
                class="mt-1.5 w-full px-2 py-1.5 rounded-md text-xs font-medium transition-colors"
                :title="`Inicia processamento em LOTE (todos os CPFs do compartimento)`"
              >
                ▶ Iniciar LOTE ({{ (getLote(mes, lote)?.total ?? 0).toLocaleString('pt-BR') }})
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Resultado do teste ─────────────────────────────────── -->
    <div
      v-if="showResultado && resultadoTeste"
      class="mb-6 rounded-xl border p-5"
      :class="
        resultadoTeste.sucesso
          ? 'border-emerald-500/40 bg-emerald-500/5'
          : 'border-red-500/40 bg-red-500/5'
      "
    >
      <div class="flex items-start justify-between mb-3">
        <h3
          class="text-lg font-bold"
          :class="resultadoTeste.sucesso ? 'text-emerald-400' : 'text-red-400'"
        >
          {{ resultadoTeste.sucesso ? '✓ Sucesso' : '✗ Falha' }}
          <span class="text-sm text-slate-400 font-normal ml-2"
            >etapa: {{ resultadoTeste.etapa }}</span
          >
        </h3>
        <div class="flex items-center gap-2">
          <button
            @click="copiarResultado"
            class="text-xs px-2 py-1 rounded bg-slate-700 hover:bg-slate-600"
          >
            Copiar JSON
          </button>
          <button
            @click="showResultado = false"
            class="text-xs px-2 py-1 rounded bg-slate-700 hover:bg-slate-600"
          >
            Fechar
          </button>
        </div>
      </div>
      <div class="grid grid-cols-2 gap-3 text-sm">
        <div>
          <span class="text-slate-400">CPF:</span>
          <span class="font-mono text-white">{{ resultadoTeste.cpf ?? '—' }}</span>
        </div>
        <div>
          <span class="text-slate-400">Mês:</span>
          <span class="font-mono text-white">{{ resultadoTeste.mes ?? '—' }}</span>
        </div>
        <div>
          <span class="text-slate-400">Lote:</span>
          <span class="font-mono text-white">{{ resultadoTeste.lote ?? '—' }}</span>
        </div>
        <div>
          <span class="text-slate-400">Protocolo:</span>
          <span class="font-mono text-white text-xs">{{ resultadoTeste.protocolo ?? '—' }}</span>
        </div>
        <div class="col-span-2">
          <span class="text-slate-400">Recibo ORIGINAL:</span>
          <span class="font-mono text-white ml-2 text-xs">{{
            resultadoTeste.nr_recibo_original ?? '—'
          }}</span>
        </div>
        <div v-if="resultadoTeste.nr_recibo_novo" class="col-span-2">
          <span class="text-slate-400">Recibo NOVO:</span>
          <span class="font-mono text-emerald-300 ml-2 text-xs font-bold">{{
            resultadoTeste.nr_recibo_novo
          }}</span>
        </div>
        <div v-if="resultadoTeste.codigo_resposta" class="col-span-2">
          <span class="text-slate-400">Código resposta:</span>
          <span class="font-mono text-white ml-2">{{ resultadoTeste.codigo_resposta }}</span>
          —
          <span class="text-slate-300">{{ resultadoTeste.descricao }}</span>
        </div>
        <div v-if="resultadoTeste.erro" class="col-span-2">
          <span class="text-slate-400">Erro:</span>
          <div
            class="mt-1 p-2 rounded bg-slate-900/60 text-xs text-red-300 font-mono whitespace-pre-wrap"
          >
            {{ resultadoTeste.erro }}
          </div>
        </div>
        <div
          v-if="resultadoTeste.ocorrencias && resultadoTeste.ocorrencias.length"
          class="col-span-2"
        >
          <div class="text-slate-400 mb-1">
            Ocorrências ({{ resultadoTeste.ocorrencias.length }}):
          </div>
          <div class="space-y-1">
            <div
              v-for="(o, i) in resultadoTeste.ocorrencias"
              :key="i"
              class="p-2 rounded bg-slate-900/60 text-xs font-mono"
            >
              <span class="text-red-400">[{{ o.codigo ?? '?' }}]</span>
              <span class="text-slate-300 ml-2">{{ o.descricao ?? '' }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Painel de controle do BATCH + Terminal ────────────── -->
    <div class="rounded-xl border border-white/10 bg-slate-800/50 p-4 mb-4">
      <div class="flex items-center justify-between mb-3">
        <div class="flex items-center gap-3">
          <span class="text-sm text-slate-300 font-medium">Processamento em Lote</span>
          <span
            :class="{
              'bg-slate-700/50 text-slate-300': !batchState || batchState.status === 'idle',
              'bg-blue-500/20 text-blue-300 border border-blue-500/40':
                batchState?.status === 'running',
              'bg-yellow-500/20 text-yellow-300 border border-yellow-500/40':
                batchState?.status === 'paused',
              'bg-orange-500/20 text-orange-300 border border-orange-500/40':
                batchState?.status === 'stopping',
              'bg-emerald-500/20 text-emerald-300 border border-emerald-500/40':
                batchState?.status === 'finished',
              'bg-red-500/20 text-red-300 border border-red-500/40': batchState?.status === 'error',
            }"
            class="text-xs px-2 py-0.5 rounded-full font-mono"
          >
            {{ batchStatusLabel }}
          </span>
          <span v-if="batchState && batchState.mes" class="text-xs text-slate-400 font-mono">
            {{ batchState.mes }} / {{ batchState.lote }}
          </span>
        </div>
        <div class="flex items-center gap-2">
          <button
            v-if="batchState?.status === 'running'"
            @click="pausarLote"
            :disabled="batchBusy"
            class="px-3 py-1.5 rounded-md bg-yellow-600 hover:bg-yellow-500 text-white text-xs font-medium disabled:opacity-50"
          >
            ⏸ Pausar
          </button>
          <button
            v-if="batchState?.status === 'paused'"
            @click="retomarLote"
            :disabled="batchBusy"
            class="px-3 py-1.5 rounded-md bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-medium disabled:opacity-50"
          >
            ▶ Retomar
          </button>
          <button
            v-if="['running', 'paused', 'stopping'].includes(batchState?.status ?? '')"
            @click="pararLote"
            :disabled="batchBusy || batchState?.status === 'stopping'"
            class="px-3 py-1.5 rounded-md bg-red-600 hover:bg-red-500 text-white text-xs font-medium disabled:opacity-50"
          >
            ⏹ Parar
          </button>
        </div>
      </div>

      <!-- Progress bar + contadores -->
      <div v-if="batchState && batchState.total > 0" class="mb-3">
        <div class="flex items-center justify-between text-xs mb-1">
          <span class="text-slate-400">
            <span class="text-white font-mono">{{ batchState.processados }}</span>
            /
            <span class="text-white font-mono">{{ batchState.total }}</span>
            <span v-if="batchState.cpf_atual" class="ml-3">
              atual:
              <span class="font-mono text-blue-300">{{ batchState.cpf_atual }}</span>
            </span>
          </span>
          <span class="text-white font-mono">{{ batchProgresso }}%</span>
        </div>
        <div class="h-2 bg-slate-700 rounded-full overflow-hidden">
          <div
            class="h-full bg-gradient-to-r from-blue-500 to-emerald-500 transition-all duration-300"
            :style="{ width: batchProgresso + '%' }"
          ></div>
        </div>
        <div class="grid grid-cols-4 gap-2 mt-3 text-xs">
          <div class="rounded bg-emerald-500/10 px-2 py-1.5 border border-emerald-500/20">
            <div class="text-emerald-400">sucessos</div>
            <div class="text-emerald-300 font-mono text-lg">{{ batchState.sucessos }}</div>
          </div>
          <div class="rounded bg-red-500/10 px-2 py-1.5 border border-red-500/20">
            <div class="text-red-400">erros</div>
            <div class="text-red-300 font-mono text-lg">{{ batchState.erros }}</div>
          </div>
          <div class="rounded bg-yellow-500/10 px-2 py-1.5 border border-yellow-500/20">
            <div class="text-yellow-400">pulados</div>
            <div class="text-yellow-300 font-mono text-lg">
              {{ batchState.pulados_sem_s1210 }}
            </div>
          </div>
          <div class="rounded bg-slate-700/50 px-2 py-1.5">
            <div class="text-slate-400">pendentes</div>
            <div class="text-slate-200 font-mono text-lg">
              {{ batchState.total - batchState.processados }}
            </div>
          </div>
        </div>
      </div>

      <!-- Erros recentes -->
      <div
        v-if="batchState && batchState.erros_recentes && batchState.erros_recentes.length > 0"
        class="mt-3"
      >
        <div class="text-xs text-slate-400 mb-1">
          Últimos erros ({{ batchState.erros_recentes.length }}):
        </div>
        <div class="max-h-32 overflow-auto space-y-1">
          <div
            v-for="(e, i) in batchState.erros_recentes.slice().reverse()"
            :key="i"
            class="text-xs font-mono p-1.5 rounded bg-red-500/5 border border-red-500/20"
          >
            <span class="text-red-400">{{ e.cpf }}</span>
            <span class="text-slate-500 ml-2">[{{ e.etapa }}]</span>
            <span v-if="e.codigo" class="text-yellow-400 ml-2">{{ e.codigo }}</span>
            <span class="text-slate-300 ml-2">{{ e.erro }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Terminal ao vivo ────────────────────────────────────── -->
    <div class="rounded-xl border border-white/10 bg-black/60 p-4">
      <div class="flex items-center justify-between mb-2">
        <div class="text-sm text-slate-300 font-medium">Terminal (ao vivo)</div>
        <div class="flex items-center gap-2">
          <span class="text-xs text-slate-500">{{ logsTerminal.length }} linhas</span>
          <button @click="logsTerminal = []" class="text-xs text-slate-400 hover:text-white">
            limpar
          </button>
        </div>
      </div>
      <div class="max-h-[28rem] overflow-auto text-xs font-mono space-y-0.5">
        <div
          v-for="(l, i) in logsTerminal"
          :key="i"
          :class="{
            'text-slate-400': l.level === 'info',
            'text-emerald-400': l.level === 'ok',
            'text-red-400': l.level === 'err',
            'text-yellow-400': l.level === 'warn',
          }"
        >
          <span class="text-slate-600">{{ l.ts }}</span>
          <span v-if="l.cpf" class="text-blue-400 ml-2">[{{ l.cpf }}]</span>
          <span class="ml-2">{{ l.msg }}</span>
        </div>
        <div v-if="logsTerminal.length === 0" class="text-slate-600 italic">(vazio)</div>
      </div>
    </div>
    <div
      v-if="loading || enviando"
      class="fixed inset-0 bg-black/60 flex items-center justify-center z-50"
    >
      <div class="bg-slate-800 border border-white/10 rounded-xl p-6 text-center max-w-md">
        <div
          class="animate-spin h-10 w-10 border-4 border-[#0066FF] border-t-transparent rounded-full mx-auto mb-4"
        ></div>
        <div class="text-white font-medium">
          {{ enviando ? 'Enviando em PRODUÇÃO...' : loadingMsg || 'Carregando...' }}
        </div>
        <div v-if="enviando" class="text-slate-400 text-xs mt-2">
          busca recibo no ZIP → gera XML → assina → envia → consulta (pode levar 30-90s)
        </div>
      </div>
    </div>
  </div>
</template>
